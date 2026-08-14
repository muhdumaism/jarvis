"""
JARVIS — Persistent Memory Manager

Allows the assistant to save, list, clear, and inject facts about the user.
"""

import json
import os
from typing import List

MEMORY_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "memory.json"))

class MemoryManager:
    """Manages persistent memory facts stored in memory.json."""

    @staticmethod
    def load_memories() -> List[str]:
        if not os.path.exists(MEMORY_FILE):
            return []
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    @staticmethod
    def save_memories(memories: List[str]) -> None:
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(memories, f, indent=2, ensure_ascii=False)
        except Exception as e:
            # Fallback console log
            print(f"[MEMORY] Failed to save memory file: {e}")

    @classmethod
    def add_memory(cls, fact: str) -> None:
        memories = cls.load_memories()
        cleaned = fact.strip()
        if cleaned and cleaned not in memories:
            memories.append(cleaned)
            cls.save_memories(memories)

    @classmethod
    def remove_memory(cls, fact: str) -> bool:
        memories = cls.load_memories()
        if fact in memories:
            memories.remove(fact)
            cls.save_memories(memories)
            return True
        return False

    @classmethod
    def clear_memories(cls) -> None:
        cls.save_memories([])

    @classmethod
    def get_system_prompt_extension(cls) -> str:
        memories = cls.load_memories()
        if not memories:
            return ""
        
        bullet_points = "\n".join(f"- {m}" for m in memories)
        return f"\n\nHere are some progressive facts you have noted down about the user. Use these facts to answer questions or personalize your response:\n{bullet_points}"
