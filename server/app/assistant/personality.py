"""
JARVIS — Agent Personality

Defines JARVIS's personality and response generation.
Responses are short, friendly, and concise.
"""

import random

# System prompt for the LLM — defines how JARVIS behaves
SYSTEM_PROMPT = """You are JARVIS, a smart room assistant. You help control devices in the user's room.

Rules:
1. Extract the user's intent from their speech.
2. Output ONLY a JSON object — no explanation, no text before or after.
3. Be precise with device IDs — use the exact device_id from the available devices list.
4. If the user mentions a device that closely matches an available device, use the closest match.
5. If you cannot determine an intent, respond with a conversation intent.
6. Never make up devices that aren't in the list.
7. For music, use the Spotify action names: play, pause, next, previous, volume.
8. For device control, only use: turn_on, turn_off, toggle.

You are friendly, calm, slightly playful, concise, and helpful.
Keep responses under 15 words."""


def generate_response(intent_type: str, data: dict) -> str:
    """Generate a short spoken response for JARVIS.
    
    Responses are intentionally brief — they'll be spoken aloud via TTS.
    """
    if intent_type == "device_control":
        device_name = data.get("device_name", "device")
        action = data.get("action", "")

        if action == "turn_on":
            return random.choice([
                f"Sure, the {device_name} is on.",
                f"Done. {device_name} turned on.",
                f"Got it, {device_name} is on.",
                f"{device_name} is on.",
            ])
        elif action == "turn_off":
            return random.choice([
                f"Done. The {device_name} is off.",
                f"Got it, {device_name} turned off.",
                f"{device_name} is off.",
                f"Sure, turning off the {device_name}.",
            ])
        elif action == "toggle":
            return random.choice([
                f"Toggled the {device_name}.",
                f"Done, {device_name} toggled.",
            ])
        return f"Command sent to {device_name}."

    elif intent_type == "music_control":
        action = data.get("action", "")
        query = data.get("query")

        if action == "play" and query:
            return random.choice([
                f"Playing {query}.",
                f"Sure, playing {query}.",
            ])
        elif action == "play":
            return "Resuming playback."
        elif action == "pause":
            return random.choice(["Paused.", "Music paused."])
        elif action == "next":
            return random.choice(["Next track.", "Skipping."])
        elif action == "previous":
            return "Playing previous track."
        elif action == "volume":
            value = data.get("value", "")
            return f"Volume set to {value}."
        return "Music command sent."

    elif intent_type == "scene_activate":
        scene = data.get("scene_name", "scene")
        return f"Activating {scene} mode."

    elif intent_type == "error":
        return data.get("message", "Something went wrong.")

    elif intent_type == "greeting":
        return random.choice([
            "Hey! How can I help?",
            "Hello! What do you need?",
            "Hi there! What can I do for you?",
        ])

    return "Got it."
