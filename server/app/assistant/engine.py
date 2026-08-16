"""
JARVIS — Intent Engine

Processes transcribed text through Ollama to extract structured intents.
Validates intents against device registry before execution.
"""

import json
import asyncio
import httpx
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

    def __init__(self, device_manager, event_bus: EventBus, music_manager=None, alarm_manager=None):
        self.device_manager = device_manager
        self.event_bus = event_bus
        self.music_manager = music_manager
        self.alarm_manager = alarm_manager
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
        cleaned_text = text.lower().strip().replace(".", "").replace(",", "").replace("!", "").replace("?", "")
        for ww in ["jarvis", "pathu", "pattu", "patho", "pathe", "java", "jarves", "jarve"]:
            cleaned_text = cleaned_text.replace(ww, "")
        cleaned_text = cleaned_text.strip()


        # Handle Memory clear command
        if "forget everything" in cleaned_text or "clear all memories" in cleaned_text or "clear your memory" in cleaned_text:
            from app.assistant.memory import MemoryManager
            MemoryManager.clear_memories()
            return {
                "intent": "memory_clear",
                "success": True,
                "response_text": "I have cleared all my saved notes and memories.",
                "data": {},
            }

        # Handle Memory list query
        if "what do you know about me" in cleaned_text or "what is in your memory" in cleaned_text or "show my notes" in cleaned_text or "list my notes" in cleaned_text:
            from app.assistant.memory import MemoryManager
            memories = MemoryManager.load_memories()
            if not memories:
                response_text = "I don't have any saved facts or notes about you yet. Tell me something to remember by saying 'remember that...'"
            else:
                response_text = "Here is what I've noted down about you: " + ". ".join(memories)
            return {
                "intent": "memory_list",
                "success": True,
                "response_text": response_text,
                "data": {"memories": memories},
            }

        # Handle Explicit Memory write commands
        for prefix in ["remember that ", "remember ", "note down that ", "note down ", "write down that ", "write down "]:
            if cleaned_text.startswith(prefix):
                fact = cleaned_text[len(prefix):].strip()
                if fact:
                    from app.assistant.memory import MemoryManager
                    MemoryManager.add_memory(fact)
                    return {
                        "intent": "memory_add",
                        "success": True,
                        "response_text": f"Got it, I've noted that: {fact}.",
                        "data": {"fact": fact},
                    }
                break

        intent_data = None

        # Rule-based intent overrides for instant and 100% reliable music and alarm control
        if cleaned_text in ["stop", "stop music", "stop the music", "pause", "pause music", "pause the music", "stop playback"]:
            intent_data = {"intent": "spotify_stop"}
        elif cleaned_text in ["resume", "resume music", "play music", "play", "resume playback"]:
            intent_data = {"intent": "spotify_resume"}
        elif cleaned_text in ["next", "next song", "next track", "skip", "skip song", "skip track"]:
            intent_data = {"intent": "spotify_skip"}
        elif cleaned_text in ["previous", "previous song", "previous track", "go back", "play previous"]:
            intent_data = {"intent": "spotify_previous"}
        elif cleaned_text in ["stop alarm", "cancel alarm", "turn off alarm", "dismiss alarm", "stop ringing", "quiet"]:
            intent_data = {"intent": "stop_alarm"}

        if intent_data is None:
            # Build the device context for the LLM
            devices = await self.device_manager.get_all()
            device_list = ", ".join(
                f'{d["id"]} ({d["name"]}, {d["state"]})'
                for d in devices
            ) or "No devices configured"

            # Build prompt
            prompt = self._build_prompt(text, device_list)

            # Inject memory prompt extension
            from app.assistant.memory import MemoryManager
            memory_ext = MemoryManager.get_system_prompt_extension()
            full_system_prompt = SYSTEM_PROMPT + memory_ext

            # Get LLM response
            raw_response = await self.llm.generate(prompt, full_system_prompt)

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
For weather: {{"intent": "weather_query", "location": "<city name, default to {settings.default_weather_location}>"}}
For setting alarm or timer: {{"intent": "set_alarm", "time": "HH:MM", "am_pm": "AM|PM", "delay_minutes": <optional minutes as float>, "delay_seconds": <optional seconds as float>, "is_timer": <bool>}}
For stopping alarm or timer: {{"intent": "stop_alarm"}}
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
                    while cleaned.count("}") > cleaned.count("{") and cleaned.endswith("}"):
                        cleaned = cleaned[:-1]
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
                    # Strip trailing extra braces one by one using slicing
                    while cleaned_nested.count("}") > cleaned_nested.count("{") and cleaned_nested.endswith("}"):
                        cleaned_nested = cleaned_nested[:-1]
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
        elif intent_type == "weather_query":
            return await self._execute_weather_query(intent_data, message_id)
        elif intent_type == "set_alarm":
            return await self._execute_set_alarm(intent_data, message_id)
        elif intent_type == "stop_alarm":
            return await self._execute_stop_alarm(intent_data, message_id)
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

    async def _execute_weather_query(
        self, intent_data: Dict[str, Any], message_id: str
    ) -> Dict[str, Any]:
        """Execute a weather forecast intent query using Open-Meteo API."""
        location = intent_data.get("location") or settings.default_weather_location
        
        # Publish executing event
        await self.event_bus.publish(JarvisEvent(
            type="ASSISTANT_EXECUTING",
            source="intent_engine",
            message_id=message_id,
            data={"description": f"Checking weather for {location}"},
        ))

        try:
            city = location.strip() if location else settings.default_weather_location
            
            # 1. Geocode location name to latitude and longitude
            geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
            async with httpx.AsyncClient() as client:
                geo_resp = await client.get(geocode_url, timeout=5.0)
                if geo_resp.status_code != 200:
                    return {
                        "intent": "weather_query",
                        "success": False,
                        "response_text": "Sorry, I couldn't reach the weather service right now.",
                        "data": intent_data,
                    }
                
                geo_data = geo_resp.json()
                results = geo_data.get("results")
                if not results:
                    return {
                        "intent": "weather_query",
                        "success": False,
                        "response_text": f"Sorry, I couldn't find the location '{city}'.",
                        "data": intent_data,
                    }
                
                location_info = results[0]
                lat = location_info.get("latitude")
                lon = location_info.get("longitude")
                formatted_name = f"{location_info.get('name')}, {location_info.get('country')}"

                # 2. Fetch weather forecast using coordinates
                weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code"
                weather_resp = await client.get(weather_url, timeout=5.0)
                if weather_resp.status_code != 200:
                    return {
                        "intent": "weather_query",
                        "success": False,
                        "response_text": f"Sorry, I couldn't get the forecast for {formatted_name}.",
                        "data": intent_data,
                    }
                
                weather_data = weather_resp.json()
                current = weather_data.get("current", {})
                temp = current.get("temperature_2m", 0.0)
                code = current.get("weather_code", 0)

                # Map weather codes
                conditions = {
                    0: "Clear sky",
                    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                    45: "Foggy", 48: "Depositing rime fog",
                    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                    71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
                    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
                    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
                }
                condition = conditions.get(code, "Cloudy")
                
                response_text = f"The current weather in {formatted_name} is {condition} at {temp:.1f} degrees Celsius."
                return {
                    "intent": "weather_query",
                    "success": True,
                    "response_text": response_text,
                    "data": intent_data,
                }
        except Exception as e:
            logger.error("weather.execute_failed", error=str(e))
            return {
                "intent": "weather_query",
                "success": False,
                "response_text": "Sorry, I had trouble retrieving the weather report.",
                "data": intent_data,
            }

    async def _execute_set_alarm(
        self, intent_data: Dict[str, Any], message_id: str
    ) -> Dict[str, Any]:
        """Schedule a new alarm or timer using the AlarmManager."""
        if not self.alarm_manager:
            return {
                "intent": "set_alarm",
                "success": False,
                "response_text": "Alarm system is not initialized.",
                "data": intent_data,
            }

        time_str = intent_data.get("time")
        am_pm = intent_data.get("am_pm")
        delay_minutes = intent_data.get("delay_minutes")
        delay_seconds = intent_data.get("delay_seconds")
        is_timer = intent_data.get("is_timer", False)
        
        label = "timer" if is_timer else "alarm"

        try:
            if delay_seconds is not None:
                secs = float(delay_seconds)
                trigger_time = await self.alarm_manager.set_alarm_delay(secs / 60.0, label)
                if label == "timer":
                    response_text = f"Got it. Timer set for {int(secs)} seconds, which will be {trigger_time}."
                else:
                    response_text = f"Got it. Alarm set in {int(secs)} seconds, which will be {trigger_time}."
            elif delay_minutes is not None:
                mins = float(delay_minutes)
                trigger_time = await self.alarm_manager.set_alarm_delay(mins, label)
                min_str = f"{mins:.1f}" if mins % 1 != 0 else f"{int(mins)}"
                if label == "timer":
                    response_text = f"Got it. Timer set for {min_str} minutes, which will be {trigger_time}."
                else:
                    response_text = f"Got it. Alarm set in {min_str} minutes, which will be {trigger_time}."
            elif time_str:
                trigger_time = await self.alarm_manager.set_alarm(time_str, am_pm)
                if label == "timer":
                    response_text = f"Got it. Timer scheduled for {trigger_time}."
                else:
                    response_text = f"Got it. Alarm scheduled for {trigger_time}."
            else:
                return {
                    "intent": "set_alarm",
                    "success": False,
                    "response_text": "I need a specific time or delay to set an alarm or timer.",
                    "data": intent_data,
                }

            return {
                "intent": "set_alarm",
                "success": True,
                "response_text": response_text,
                "data": intent_data,
            }
        except Exception as e:
            logger.error("alarm.execute_failed", error=str(e))
            return {
                "intent": "set_alarm",
                "success": False,
                "response_text": f"Sorry, I failed to schedule the alarm: {e}",
                "data": intent_data,
            }

    async def _execute_stop_alarm(
        self, intent_data: Dict[str, Any], message_id: str
    ) -> Dict[str, Any]:
        """Silence any currently ringing alarms."""
        if not self.alarm_manager:
            return {
                "intent": "stop_alarm",
                "success": False,
                "response_text": "Alarm system is not initialized.",
                "data": intent_data,
            }

        stopped = await self.alarm_manager.stop_ringing()
        if stopped:
            response_text = "Alarm stopped."
        else:
            response_text = "No active alarms are ringing right now."

        return {
            "intent": "stop_alarm",
            "success": True,
            "response_text": response_text,
            "data": intent_data,
        }
