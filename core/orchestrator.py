"""
HIKARI v3 - Main Orchestrator
Central brain that coordinates everything
"""

import os
import sys
import time
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Import all core systems
from agents.base import BaseAgent
from agents.voice import VoiceAgent
from agents.research import ResearchAgent
from agents.files import FileAgent
from agents.system import SystemAgent
from agents.code import CodeAgent
from agents.memory_agent import MemoryAgent

from core.router import AIRouter, get_router
from core.memory import MemorySystem, get_memory
from core.voice import VoiceSystem
from core.scheduler import Scheduler, setup_default_scheduler
from core.voice_memory import VoiceMemory
from core.user_profile import UserProfile
from core.knowledge_graph import KnowledgeGraph
from core.health_awareness import HealthAwareness
from core.semantic_memory import SemanticMemory
from core.action_system import ActionSystem, get_action_system
from core.desktop_awareness import DesktopAwareness, get_desktop_awareness
from core.browser_automation import BrowserAutomation, get_browser_automation
from core.mac_integration import MacIntegration, get_mac_integration
from core.task_planner import TaskPlanner, get_task_planner
from core.build_executor import BuildExecutor, get_build_executor
from skills.skill_system import SkillRegistry, register_builtin_skills
from core.server import WebSocketServer
from security.auth import CodenameAuth

# Import new systems
from core.personality import get_personality, get_emotional_iq
from core.mac_control import get_mac_control
from core.smart_home import get_smart_home

# Wake words that activate HIKARI
WAKE_WORDS = ["hikari", "hey hikari", "okay hikari", "hi hikari"]


class HIKARI_Orchestrator:
    """Central brain of HIKARI - coordinates everything"""

    def __init__(self):
        print("[HIKARI] Initializing brain...")
        self.authenticated = False
        self.codename_auth = CodenameAuth()

        # Core memory
        self.memory = get_memory()
        self.semantic_memory = SemanticMemory()
        self.neural_memory = None
        self.neural_memory_enabled = False

        # Personality & emotions
        self.personality = get_personality()
        self.emotional_iq = get_emotional_iq()

        # User profile & knowledge
        self.user_profile = UserProfile()
        self.knowledge_graph = KnowledgeGraph()
        self.health = HealthAwareness()

        # Voice system
        self.voice = VoiceSystem()
        self.voice_memory = VoiceMemory()

        # AI Router
        self.router = get_router()

        # Agents
        self.agents: Dict[str, BaseAgent] = {}
        self._init_agents()

        # Mac & Smart Home control
        self.mac_control = get_mac_control()
        self.smart_home = get_smart_home()

        # Additional systems
        self.action_system = get_action_system()
        self.desktop = get_desktop_awareness()
        self.browser = get_browser_automation()
        self.mac = get_mac_integration()
        self.planner = get_task_planner()
        self.build_executor = get_build_executor()

        # Skills
        self.skill_registry = SkillRegistry()
        self._init_skills()

        # Scheduler
        self.scheduler = None
        self._init_scheduler()

        self._init_neural_memory()

        print("[HIKARI] Brain initialized!")
        print("[HIKARI] Memory:", len(self.memory.conversations), "conversations")
        print("[HIKARI] Personality traits:", self.personality.traits)

    def _init_neural_memory(self):
        """Initialize optional SQLite neural memory in ~/.hikari/brain."""
        try:
            from core import neural_memory_bridge

            if neural_memory_bridge.init_neural_memory():
                self.neural_memory = neural_memory_bridge
                self.neural_memory_enabled = True
                print("[HIKARI] Neural memory connected")
            else:
                print("[HIKARI] Neural memory unavailable")
        except Exception as e:
            self.neural_memory = None
            self.neural_memory_enabled = False
            print(f"[HIKARI] Neural memory skipped: {e}")

    def _init_agents(self):
        """Initialize all agents"""
        self.agents["voice"] = VoiceAgent()
        self.agents["research"] = ResearchAgent()
        self.agents["files"] = FileAgent()
        self.agents["system"] = SystemAgent()
        self.agents["code"] = CodeAgent()
        self.agents["memory"] = MemoryAgent(self.memory)

        print(f"[HIKARI] Initialized {len(self.agents)} agents")

    def _init_skills(self):
        """Initialize built-in skills"""
        register_builtin_skills(self.skill_registry)
        print(f"[HIKARI] Registered {len(self.skill_registry.skills)} skills")

    def _init_scheduler(self):
        """Initialize proactive scheduler"""
        try:
            self.scheduler = setup_default_scheduler(self)
            self.scheduler.start()
        except Exception as e:
            print(f"[HIKARI] Scheduler init failed: {e}")

    def process_input(self, user_input: str, source: str = "text") -> Optional[str]:
        """Main entry point - process any user input"""
        if not user_input or not user_input.strip():
            return None

        print(f"\n[INPUT] ({source}): {user_input}")

        # Handle special commands
        response = self._handle_special_commands(user_input)
        if response:
            return response

        # Detect and adapt to emotions
        emotions = self.emotional_iq.detect_emotion(user_input)
        dominant_emotion, emotion_score = self.emotional_iq.get_dominant_emotion(emotions)

        if emotion_score > 0.3:
            self.emotional_iq.log_emotion(dominant_emotion, emotion_score, user_input)

        # Learn from interaction
        self.personality.learn_from_interaction(user_input, "", "")
        self.user_profile.extract_info_from_conversation(user_input, "")
        self.knowledge_graph.extract_from_conversation(user_input, "")

        # Check for sick indicators
        self._check_health(user_input)

        # Strip wake words
        lowered = user_input.lower().strip()
        for wake in WAKE_WORDS:
            if lowered.startswith(wake):
                lowered = lowered.replace(wake, "", 1).strip()
                break

        if not lowered:
            return self.personality.get_greeting() + "! How can I help?"

        # Route to appropriate agent
        response = self._route_to_agent(lowered)

        # If no response, use AI
        if not response:
            response = self._get_ai_response(lowered, dominant_emotion, emotion_score)

        # Adapt response to emotions
        if response and emotion_score > 0.4:
            response = self.emotional_iq.adapt_response(response, dominant_emotion, emotion_score)

        # Format based on personality
        if response:
            response = self.personality.format_response(response)

        # Log conversation
        self.memory.add_conversation(user_input, response or "")
        if self.neural_memory_enabled and self.neural_memory:
            try:
                self.neural_memory.remember(user_input, response or "", {"source": source})
            except Exception as e:
                print(f"[MEMORY] Neural remember failed: {e}")

        return response

    def _handle_special_commands(self, user_input: str) -> Optional[str]:
        """Handle special system commands"""
        lowered = user_input.lower().strip()

        # Exit commands
        if any(w in lowered for w in ["exit", "quit", "goodbye", "bye"]):
            return "Goodbye! Call me when you need me. I'm always here."

        # Status command
        if lowered in ["status", "hikari status", "system status"]:
            return self._get_status_report()

        # Codename authentication fallback
        configured_codename = os.getenv("CODENAME", "change-me").strip().lower()
        if lowered == configured_codename and self.codename_auth.verify(user_input):
            self.authenticated = True
            return "Authentication confirmed. I'm ready."

        # Who am I command
        if any(w in lowered for w in ["who am i", "what do you know about me"]):
            return self._get_user_summary()

        # Mood check
        if any(w in lowered for w in ["how am i doing", "how have i been", "my mood"]):
            return self.emotional_iq.get_mood_summary()

        # Memory check
        if any(w in lowered for w in ["what do you remember", "what have we talked about"]):
            return self._get_memory_summary()

        # Help
        if lowered in ["help", "what can you do", "commands"]:
            return self._get_help()

        return None

    def _route_to_agent(self, user_input: str) -> Optional[str]:
        """Route input to best agent, but only for specific commands - not conversation"""
        scores = {}
        for name, agent in self.agents.items():
            scores[name] = agent.can_handle(user_input)

        print(f"[ROUTE] Agent scores: {scores}")

        best_agent = max(scores, key=scores.get)
        best_score = scores[best_agent]

        # Only route to agent if confidence is high (> 0.6) - this is a specific command
        # Otherwise, let AI handle it (conversation goes to AI)
        if best_score < 0.5:
            return None

        try:
            response = self.agents[best_agent].handle(user_input)
            # If agent returns the same input (not a command), use AI instead
            if response == user_input.lower():
                return None
            return response
        except Exception as e:
            print(f"[ROUTE] Agent error: {e}")
            return None

    def _get_ai_response(self, user_input: str, emotion: str = "neutral", emotion_score: float = 0.0) -> str:
        """Get AI response for general queries"""
        # Build context
        context = self.personality.get_user_context()
        if context:
            context = f"User context: {context}\n\n"

        if self.neural_memory_enabled and self.neural_memory:
            try:
                memory_context = self.neural_memory.build_memory_prompt(user_input)
                if memory_context:
                    context += f"{memory_context}\n\n"
            except Exception as e:
                print(f"[MEMORY] Neural recall failed: {e}")

        # Add emotion context
        if emotion != "neutral" and emotion_score > 0.4:
            context += f"User is feeling {emotion}. "

        # Build prompt
        system_prompt = f"""You are HIKARI, a helpful AI assistant. Adapt your responses to be:
- Formal level: {self.personality.traits['formality']:.0%} formal
- Verbose level: {self.personality.traits['verbosity']:.0%} detailed
- Humorous: {'yes' if self.personality.traits['humor'] > 0.5 else 'no'}
- Always helpful and friendly"""

        # Get AI response
        try:
            response = self.router.generate(
                user_input=user_input,
                system_prompt=system_prompt,
                context=context,
                max_tokens=500,
                temperature=0.7
            )
            return response if response else "I'm having trouble thinking right now."
        except Exception as e:
            print(f"[AI] Error: {e}")
            return "I'm having trouble thinking right now. Try again in a moment."

    def _check_health(self, text: str):
        """Check for health indicators"""
        if self.emotional_iq.detect_emotion(text).get("sick", 0) > 0.5:
            self.voice_memory.is_sick_mode = True
            self.user_profile.log_mood("sick", 0.7, text)

    def _get_status_report(self) -> str:
        """Get system status"""
        memory_summary = self.memory.get_user_summary()

        status = f"""HIKARI Status
================
Agents: {len(self.agents)} active
Memory: {memory_summary.get('total_conversations', 0)} conversations
Facts: {memory_summary.get('facts_learned', 0)} learned
Neural memory: {"connected" if self.neural_memory_enabled else "not connected"}

Personality:
  Formal: {self.personality.traits['formality']:.0%}
  Verbose: {self.personality.traits['verbosity']:.0%}
  Humor: {self.personality.traits['humor']:.0%}
  Helpful: {self.personality.traits['helpfulness']:.0%}

Mood: {self.emotional_iq.current_mood}
"""
        if self.neural_memory_enabled and self.neural_memory:
            try:
                stats = self.neural_memory.get_memory_stats()
                status += (
                    f"Neural nodes: {stats.get('nodes', 0)}\n"
                    f"Neural edges: {stats.get('edges', 0)}\n"
                )
            except Exception as e:
                status += f"Neural memory stats unavailable: {e}\n"
        return status

    def _get_user_summary(self) -> str:
        """Get what HIKARI knows about the user"""
        if self.neural_memory_enabled and self.neural_memory:
            try:
                return self.neural_memory.format_whoami()
            except Exception as e:
                print(f"[MEMORY] Neural whoami failed: {e}")

        name = self.personality.user_prefs.get("name") or self.user_profile.name or "you"
        prefs = self.personality.user_prefs

        summary = f"What I know about {name}:\n"

        if prefs.get("name"):
            summary += f"- Name: {prefs['name']}\n"
        if prefs.get("favorite_topics"):
            summary += f"- Interests: {', '.join(prefs['favorite_topics'][-3:])}\n"
        if prefs.get("health_concerns"):
            summary += f"- Health: {prefs['health_concerns'][-1]}\n"

        memory_count = len(self.memory.conversations)
        summary += f"- We've talked {memory_count} times\n"

        return summary

    def _get_memory_summary(self) -> str:
        """Get memory summary"""
        recent = self.memory.get_recent_conversations(5)
        if not recent:
            return "We haven't talked much yet!"

        summary = "Recent conversations:\n"
        for i, conv in enumerate(recent, 1):
            user = conv.get("user", "")[:50]
            summary += f"{i}. You: {user}\n"

        return summary

    def _get_help(self) -> str:
        """Get help information"""
        return """HIKARI Commands
================
- "Open [app]" - Open applications
- "What's on my calendar?" - Calendar events
- "Play [song]" - Play music
- "Remember that..." - Store facts
- "What do you know about me?" - User info
- "Status" - System status
- "Lock screen" - Lock Mac
- "Turn off lights" - Smart home
- Plus: Ask anything!

Just speak naturally - I'm here to help."""


# Singleton
_orchestrator = None

# Backward-compatible name used by tests and older integrations.
Orchestrator = HIKARI_Orchestrator

def get_orchestrator() -> HIKARI_Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = HIKARI_Orchestrator()
    return _orchestrator
