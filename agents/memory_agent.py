"""
HIKARI v2.0 - Memory Agent
Manages conversation history, user preferences, and learning
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from agents.base import BaseAgent
from core.memory import MemorySystem


class MemoryAgent(BaseAgent):
    """Handles memory operations and user personalization"""

    def __init__(self, memory: MemorySystem):
        super().__init__("memory", "Conversation history, preferences, and learning")
        self.memory = memory

        self.register_tool("remember", self.remember)
        self.register_tool("recall", self.recall)
        self.register_tool("forget", self.forget)
        self.register_tool("search_memory", self.search_memory)
        self.register_tool("get_summary", self.get_summary)

    def handle(self, user_input: str, context: str = "") -> Optional[str]:
        lowered = user_input.lower()

        # Handle name updates
        if any(
            w in lowered
            for w in ["my name is", "call me", "update my name", "change my name"]
        ):
            import re

            match = re.search(
                r"(?:my name is|call me|update my name to|change my name to)\s+(\w+)",
                lowered,
            )
            if match:
                name = match.group(1).capitalize()
                self.memory.set_name(name)
                return f"Got it, {name}. I'll remember that from now on."

        # Handle location updates
        if any(
            w in lowered
            for w in [
                "i am in",
                "i live in",
                "i'm in",
                "im in",
                "update my location",
                "change my location",
            ]
        ):
            import re

            match = re.search(
                r"(?:i am in|i live in|i\'m in|im in|update my location to|change my location to)\s+([\w\s]+?)(?:\.|$|\s+so)",
                lowered,
            )
            if not match:
                match = re.search(
                    r"(?:i am in|i live in|i\'m in|im in|update my location to|change my location to)\s+([\w\s]+)",
                    lowered,
                )
            if match:
                location = match.group(1).strip().title()
                self.memory.set_location(location)
                return f"Updated your location to {location}. I'll use this for weather and local info."

        # Handle remember commands
        if any(
            w in lowered
            for w in ["remember that", "remember this", "note that", "save this"]
        ):
            fact = lowered.split("remember that")[-1].strip()
            if not fact:
                fact = lowered.split("remember this")[-1].strip()
            if not fact:
                fact = lowered.split("note that")[-1].strip()
            return self.remember(fact)

        # Handle "what do you know about me"
        if any(
            w in lowered
            for w in [
                "what do you know",
                "what do you remember",
                "what have i told you",
                "whats my name",
                "what's my name",
                "who am i",
            ]
        ):
            return self.get_summary()

        # Handle forget commands
        if any(w in lowered for w in ["forget", "remove from memory"]):
            key = (
                lowered.replace("forget", "").replace("remove from memory", "").strip()
            )
            return self.forget(key)

        # Handle memory search
        if any(
            w in lowered for w in ["search memory", "did i ask", "did we talk about"]
        ):
            query = (
                lowered.replace("search memory", "")
                .replace("did i ask", "")
                .replace("did we talk about", "")
                .strip()
            )
            return self.search_memory(query)

        return None

    def can_handle(self, user_input: str) -> float:
        lowered = user_input.lower()
        if any(
            w in lowered
            for w in [
                "remember",
                "recall",
                "forget",
                "memory",
                "what do you know",
                "what do you remember",
            ]
        ):
            return 0.9
        if any(
            w in lowered
            for w in [
                "my name",
                "who am i",
                "what's my name",
                "whats my name",
                "where do i live",
                "my location",
                "where am i",
                "update my",
                "change my",
                "set my",
            ]
        ):
            return 0.95
        # Handle casual location/name statements
        if any(
            w in lowered
            for w in [
                "i am in",
                "i live in",
                "i'm in",
                "im in",
                "call me",
                "my name is",
            ]
        ):
            return 0.9
        return 0.1

    def remember(self, fact: str) -> str:
        """Store a fact about the user"""
        if not fact:
            return "What would you like me to remember?"

        key = fact[:50].lower().strip()
        self.memory.store_fact(key, fact)
        return f"I'll remember that: {fact}"

    def recall(self, key: str) -> str:
        """Recall a specific fact"""
        value = self.memory.get_fact(key)
        if value:
            return f"You told me: {value}"
        return f"I don't have that in memory."

    def forget(self, key: str) -> str:
        """Forget a specific fact"""
        if key in self.memory.facts:
            del self.memory.facts[key]
            self.memory._save()
            return f"Forgotten: {key}"
        return f"I don't have '{key}' in memory."

    def search_memory(self, query: str) -> str:
        """Search past conversations"""
        if not query:
            return "What should I search for?"

        results = self.memory.search_conversations(query)
        if results:
            parts = [f"Found {len(results)} matches:"]
            for r in results[-5:]:
                parts.append(f"\nYou: {r['user']}")
                parts.append(f"Me: {r['ai']}")
            return "\n".join(parts)
        return f"No memories found for '{query}'."

    def get_summary(self) -> str:
        """Get summary of what HIKARI knows"""
        summary = self.memory.get_user_summary()

        parts = ["Here's what I know about you:", ""]
        if summary["preferences"]:
            parts.append("Preferences:")
            for k, v in summary["preferences"].items():
                parts.append(f"  - {k}: {v}")
            parts.append("")

        if summary["facts_learned"] > 0:
            parts.append(f"Facts learned: {summary['facts_learned']}")
            parts.append(f"Total conversations: {summary['total_conversations']}")

        if summary["recent_topics"]:
            parts.append("\nRecent topics:")
            for topic in summary["recent_topics"][-5:]:
                parts.append(f"  - {topic}")

        return "\n".join(parts)
