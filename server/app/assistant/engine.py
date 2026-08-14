"""
JARVIS — Intent Engine

Processes transcribed text through Ollama to extract structured intents.
Validates intents against device registry before execution.
"""

import json
import asyncio
from typing import Optional, Dict, Any

from app.assistant.ollama_provider import OllamaProvider
from app.assistant.intents import VALID_INTENTS, VALID_DEVICE_ACTIONS, VALID_MUSIC_ACTIONS
from app.assistant.personality import SYSTEM_PROMPT, generate_response
from app.core.events import EventBus, JarvisEvent
from app.core.config import settings

import structlog

logger = structlog.get_logger("jarvis.intent")


class IntentEngine:
    """Extracts structured intents from natural language using Ollama.
    
    The AI ONLY produces structured JSON intents.
    The server validates before execution.
    """

    def __init__(self, device_manager, event_bus: EventBus, music_manager=None):
        self.device_manager = device_manager
        self.event_bus = event_bus
        self.music_manager = music_manager
        self.llm = OllamaProvider()
        self._ready = False

    async def initialize(self) -> None:
        """Initialize the LLM provider."""
        await self.llm.initialize()
        self._ready = self.llm.is_ready
        if self._ready:
            logger.info("intent_engine.ready")
        else:
            logger.warning("intent_engine.llm_not_available")

    @property
    def is_ready(self) -> bool:
        return self._ready

    async def process(self, text: str, message_id: str) -> Dict[str, Any]:
        """Process transcribed text into a validated intent and execute it.
        
        Returns:
            {
                "intent": str,
                "success": bool,
                "response_text": str,
                "data": dict,
            }
        """
        # Build the device context for the LLM
        devices = await self.device_manager.get_all()
        device_list = ", ".join(
            f'{d["id"]} ({d["name"]}, {d["state"]})'
            for d in devices
        ) or "No devices configured"

        # Build prompt
        prompt = self._build_prompt(text, device_list)

        # Get LLM response
        raw_response = await self.llm.generate(prompt, SYSTEM_PROMPT)

        if not raw_response:
            logger.warning("intent_engine.no_response", text=text)
            return {
                "intent": "unknown",
                "success": False,
                "response_text": "Sorry, I couldn't process that right now.",
                "data": {},
            }

        # Parse intent from LLM response
        intent_data = self._parse_intent(raw_response)
        intent_type = intent_data.get("intent", "unknown")

        logger.info(
            "intent_engine.parsed",
            text=text,
            intent=intent_type,
            data=intent_data,
            message_id=message_id,
        )

        # Publish intent event
        await self.event_bus.publish(JarvisEvent(
            type="ASSISTANT_INTENT",
            source="intent_engine",
            message_id=message_id,
            data={
                "intent": intent_type,
                "target": intent_data.get("target"),
                "action": intent_data.get("action"),
            },
        ))

        # Validate and execute
        result = await self._execute_intent(intent_data, message_id)

        return result

    def _build_prompt(self, text: str, device_list: str) -> str:
        """Build the prompt for intent extraction."""
        return f"""User said: "{text}"

Available devices: {device_list}

Extract the intent as JSON. Respond with ONLY valid JSON, no explanation.

For device control: {{"intent": "device_control", "target": "<device_id>", "action": "turn_on|turn_off|toggle"}}
For music: {{"intent": "spotify_play|spotify_pause|spotify_resume|spotify_skip|spotify_previous|spotify_volume_up|spotify_volume_down|spotify_current_track|spotify_search|spotify_play_playlist|spotify_play_liked|spotify_stop", "query": "<search query or playlist name>", "value": <optional number>}}
For scene: {{"intent": "scene_activate", "scene_name": "<name>"}}
For room query: {{"intent": "room_query", "query": "<what to query>"}}
For conversation: {{"intent": "conversation", "response": "<short friendly reply>"}}

Examples for music:
- "play Blinding Lights" -> {{"intent": "spotify_search", "query": "Blinding Lights"}}
- "pause music" -> {{"intent": "spotify_pause"}}
- "resume music" or "play" -> {{"intent": "spotify_resume"}}
- "skip track" or "next song" -> {{"intent": "spotify_skip"}}
- "previous song" or "go back" -> {{"intent": "spotify_previous"}}
- "volume up" or "make it louder" -> {{"intent": "spotify_volume_up"}}
- "volume down" or "quieter" -> {{"intent": "spotify_volume_down"}}
- "what is playing?" or "what song is this" -> {{"intent": "spotify_current_track"}}
- "play liked songs" -> {{"intent": "spotify_play_liked"}}
- "play playlist coding" -> {{"intent": "spotify_play_playlist", "query": "coding"}}
- "stop music" -> {{"intent": "spotify_stop"}}

JSON:"""

    def _parse_intent(self, raw_response: str) -> Dict[str, Any]:
        """Parse JSON intent from LLM response."""
        # Try to extract JSON from the response
        response = raw_response.strip()

        # Handle markdown code blocks
        if "```json" in response:
            start = response.index("```json") + 7
            end = response.index("```", start)
            response = response[start:end].strip()
        elif "```" in response:
            start = response.index("```") + 3
            end = response.index("```", start)
            response = response[start:end].strip()

        parsed = None

        # Find JSON object
        try:
            # Try direct parse
            parsed = json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            brace_start = response.find("{")
            brace_end = response.rfind("}") + 1
            if brace_start >= 0 and brace_end > brace_start:
                try:
                    cleaned = response[brace_start:brace_end]
                    # Strip trailing extra braces if model outputted double braces (e.g. }})
                    while cleaned.count("}") > cleaned.count("{"):
                        cleaned = cleaned.rstrip("}")
                    parsed = json.loads(cleaned)
                except json.JSONDecodeError:
                    pass

        # Fallback: treat as conversation if parse failed
        if not parsed:
            parsed = {"intent": "conversation", "response": response[:200]}

        # Check for nested JSON intent inside a conversation response (common with small models like llama3.2:1b)
        if isinstance(parsed, dict) and parsed.get("intent") == "conversation":
            resp_str = parsed.get("response", "").strip()
            brace_start = resp_str.find("{")
            brace_end = resp_str.rfind("}") + 1
            if brace_start >= 0 and brace_end > brace_start:
                try:
                    cleaned_nested = resp_str[brace_start:brace_end]
                    # Strip trailing extra braces
                    while cleaned_nested.count("}") > cleaned_nested.count("{"):
                        cleaned_nested = cleaned_nested.rstrip("}")
                    nested = json.loads(cleaned_nested)
                    if isinstance(nested, dict) and "intent" in nested:
                        logger.info("intent.parser.nested_fallback", nested_intent=nested["intent"])
                        return nested
                except json.JSONDecodeError:
                    pass

        return parsed

    async def _execute_intent(
        self, intent_data: Dict[str, Any], message_id: str
    ) -> Dict[str, Any]:
        """Validate and execute a parsed intent."""
        intent_type = intent_data.get("intent", "unknown")

        if intent_type == "device_control":
            return await self._execute_device_control(intent_data, message_id)
        elif intent_type == "music_control" or intent_type.startswith("spotify_"):
            return await self._execute_spotify_intent(intent_data, message_id)
        elif intent_type == "scene_activate":
            return await self._execute_scene(intent_data, message_id)
        elif intent_type == "room_query":
            return await self._execute_room_query(intent_data, message_id)
        elif intent_type == "conversation":
            response = intent_data.get("response", "I'm here to help.")
            return {
                "intent": "conversation",
                "success": True,
                "response_text": response,
                "data": intent_data,
            }
        else:
            return {
                "intent": "unknown",
                "success": False,
                "response_text": "I'm not sure what you mean.",
                "data": intent_data,
            }

    async def _execute_device_control(
        self, intent_data: Dict[str, Any], message_id: str
    ) -> Dict[str, Any]:
        """Execute a device control intent."""
        target = intent_data.get("target", "")
        action = intent_data.get("action", "")

        # Validate action
        if action not in VALID_DEVICE_ACTIONS:
            return {
                "intent": "device_control",
                "success": False,
                "response_text": f"I don't know how to {action} a device.",
                "data": intent_data,
            }

        # Validate device exists
        device = self.device_manager.get_device_sync(target)
        if not device:
            # Try fuzzy matching
            all_devices = await self.device_manager.get_all()
            for d in all_devices:
                if target.lower() in d["id"].lower() or target.lower() in d["name"].lower():
                    device = d
                    target = d["id"]
                    break

        if not device:
            return {
                "intent": "device_control",
                "success": False,
                "response_text": f"I couldn't find a device called {target}.",
                "data": intent_data,
            }

        # Publish executing event
        await self.event_bus.publish(JarvisEvent(
            type="ASSISTANT_EXECUTING",
            source="intent_engine",
            message_id=message_id,
            data={"description": f"{action.replace('_', ' ').title()} {device['name']}"},
        ))

        # Execute command
        try:
            result = await self.device_manager.execute_command(
                device_id=target,
                action=action,
                source="voice",
                message_id=message_id,
            )
            response_text = generate_response("device_control", {
                "device_name": device["name"],
                "action": action,
            })
            return {
                "intent": "device_control",
                "success": True,
                "response_text": response_text,
                "data": {**intent_data, "result": result},
            }
        except ValueError as e:
            return {
                "intent": "device_control",
                "success": False,
                "response_text": str(e),
                "data": intent_data,
            }

    async def _execute_spotify_intent(
        self, intent_data: Dict[str, Any], message_id: str
    ) -> Dict[str, Any]:
        """Execute a Spotify/music control intent."""
        intent_type = intent_data.get("intent", "")
        action = intent_data.get("action", "")
        query = intent_data.get("query")
        value = intent_data.get("value")

        # Map spotify_ intents to appropriate music_control actions
        if intent_type == "spotify_play" or intent_type == "spotify_search":
            action = "play" if query else "resume"
        elif intent_type == "spotify_pause" or intent_type == "spotify_stop":
            action = "pause"
        elif intent_type == "spotify_resume":
            action = "resume"
        elif intent_type == "spotify_skip":
            action = "next"
        elif intent_type == "spotify_previous":
            action = "previous"
        elif intent_type == "spotify_volume_up":
            action = "volume"
            value = 75
        elif intent_type == "spotify_volume_down":
            action = "volume"
            value = 35
        elif intent_type == "spotify_play_playlist":
            action = "play"
            if query:
                query = f"playlist {query}"
        elif intent_type == "spotify_play_liked":
            action = "play"
            query = "liked songs"
        elif intent_type == "spotify_current_track":
            response_text = "I couldn't check the current track."
            if self.music_manager:
                state = await self.music_manager.get_state()
                if state and state.get("track"):
                    track = state["track"]
                    response_text = f"You are listening to {track['title']} by {track['artist']}."
                else:
                    response_text = "No music is currently playing."
            return {
                "intent": "spotify_current_track",
                "success": True,
                "response_text": response_text,
                "data": intent_data,
            }

        # Validate action
        if not action:
            action = intent_data.get("action", "play")

        # Dispatch MUSIC_COMMAND
        await self.event_bus.publish(JarvisEvent(
            type="MUSIC_COMMAND",
            source="voice",
            message_id=message_id,
            data={"action": action, "query": query, "value": value},
        ))

        response_text = generate_response("music_control", {
            "action": action,
            "query": query,
        })

        return {
            "intent": intent_type,
            "success": True,
            "response_text": response_text,
            "data": intent_data,
        }

    async def _execute_scene(
        self, intent_data: Dict[str, Any], message_id: str
    ) -> Dict[str, Any]:
        """Execute a scene activation intent."""
        scene_name = intent_data.get("scene_name", "")

        await self.event_bus.publish(JarvisEvent(
            type="SCENE_ACTIVATE",
            source="voice",
            message_id=message_id,
            data={"scene_name": scene_name},
        ))

        return {
            "intent": "scene_activate",
            "success": True,
            "response_text": f"Activating {scene_name} mode.",
            "data": intent_data,
        }

    async def _execute_room_query(
        self, intent_data: Dict[str, Any], message_id: str
    ) -> Dict[str, Any]:
        """Execute a room query intent."""
        query = intent_data.get("query", "")

        # Get device states for the response
        devices = await self.device_manager.get_all()
        device_summary = ", ".join(
            f"{d['name']} is {d['state']}" for d in devices if d["confirmed"]
        )

        response = f"Here's what I know: {device_summary}" if device_summary else "No confirmed device states right now."

        return {
            "intent": "room_query",
            "success": True,
            "response_text": response,
            "data": intent_data,
        }
