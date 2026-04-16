"""
HIKARI v2.0 - Orchestrator
Manages the agent swarm, routes tasks, handles inter-agent communication
"""

import os
import sys
import time
import json
import threading
from typing import Optional, Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

from core.quiet import is_quiet
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
from core.emotional_intelligence import (
    EmotionDetector,
    ResponseAdapter,
    EmotionalMemory,
)
from core.proactive_intelligence import ProactiveIntelligence
from core.knowledge_graph import KnowledgeGraph
from core.adaptive_personality import AdaptivePersonality
from core.health_awareness import HealthAwareness
from core.semantic_memory import SemanticMemory
from core.action_system import ActionSystem, get_action_system
from core.desktop_awareness import DesktopAwareness, get_desktop_awareness
from core.browser_automation import BrowserAutomation, get_browser_automation
from core.mac_integration import MacIntegration, get_mac_integration
from core.task_planner import TaskPlanner, get_task_planner
from core.build_executor import BuildExecutor, get_build_executor
from security.enhanced_auth import CodenameSystem, ContextAwareAuth
from skills.skill_system import SkillRegistry, register_builtin_skills
from skills.memory_skills import register_memory_skills

# WebSocket server lives in src/ (tests & imports need this on sys.path)
_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if _SRC not in sys.path:
    sys.path.insert(0, os.path.normpath(_SRC))
from server import WebSocketServer

load_dotenv()


class Orchestrator:
    """Central brain of HIKARI - manages all agents and routing"""

    def __init__(self, *, enable_mic: bool = True):
        self.agents: Dict[str, BaseAgent] = {}
        self.router = get_router()
        self.memory = get_memory()
        self.voice = VoiceSystem(enable_mic=enable_mic)
        self.is_running = False
        self.context = "You are HIKARI, a helpful AI assistant. Keep responses concise and friendly."
        self.wake_words = ["hikari", "shikari", "hickory", "hey hikari"]
        self.codename_hash = "harsha27"  # Codename for fallback auth
        self.authenticated = False
        self.session_start = 0
        self.session_timeout = 3600  # 1 hour
        self.ws_server = None
        self.ws_port: int = 8765
        self.connected_devices = []

        self.scheduler = None
        self.skill_registry = SkillRegistry()
        self.voice_memory = VoiceMemory()
        self.user_profile = UserProfile()
        self.emotion_detector = EmotionDetector()
        self.response_adapter = ResponseAdapter()
        self.emotional_memory = EmotionalMemory()
        self.semantic_memory = SemanticMemory()
        self.proactive = None
        self.knowledge_graph = KnowledgeGraph()
        self.personality = AdaptivePersonality()
        self.health = HealthAwareness()
        self.codename_system = CodenameSystem()
        self.context_auth = ContextAwareAuth(self.codename_system)

        # New JARVIS-inspired systems
        self.action_system = get_action_system()
        self.desktop = get_desktop_awareness()
        self.browser = get_browser_automation()
        self.mac = get_mac_integration()
        self.planner = get_task_planner()
        self.build_executor = get_build_executor()

        self._init_agents()
        self._init_intelligence()
        self._init_scheduler()
        self._init_skills()
        self._warmup()

    def _init_agents(self):
        """Initialize all agents"""
        self.agents["voice"] = VoiceAgent()
        self.agents["research"] = ResearchAgent()
        self.agents["files"] = FileAgent()
        self.agents["system"] = SystemAgent()
        self.agents["code"] = CodeAgent()
        self.agents["memory"] = MemoryAgent(self.memory)

        if not is_quiet():
            print(f"[ORCHESTRATOR] Initialized {len(self.agents)} agents:")
            for name, agent in self.agents.items():
                print(f"  - {name}: {agent.description}")

    def _init_intelligence(self):
        """Initialize all intelligence systems"""
        self.proactive = ProactiveIntelligence(
            user_profile=self.user_profile,
            memory=self.memory,
            scheduler=self.scheduler,
        )
        if not is_quiet():
            print("[ORCHESTRATOR] Intelligence systems initialized")

    def _init_scheduler(self):
        """Initialize proactive scheduler"""
        try:
            self.scheduler = setup_default_scheduler(self)
            self.scheduler.start()
        except Exception as e:
            print(f"[ORCHESTRATOR] Scheduler init failed: {e}")

    def _init_skills(self):
        """Initialize skill system"""
        try:
            register_builtin_skills(self.skill_registry)
            register_memory_skills(self.skill_registry)
            if not is_quiet():
                print(f"[ORCHESTRATOR] Registered {len(self.skill_registry.skills)} skills")
        except Exception as e:
            print(f"[ORCHESTRATOR] Skills init failed: {e}")

    def _warmup(self):
        """Warm up systems for fast first-use"""
        if not is_quiet():
            print("[ORCHESTRATOR] Warming up...")
        self.voice.warmup()
        if not is_quiet():
            print("[ORCHESTRATOR] Ready!")

    def start_server(self, host: str = "0.0.0.0", port: int = 8765):
        """Start WebSocket server for device connections"""
        try:
            self.ws_port = port
            self.ws_server = WebSocketServer(self, host, port)
            threading.Thread(target=self.ws_server.start, daemon=True).start()
            if not is_quiet():
                print(f"[ORCHESTRATOR] WebSocket server running on {host}:{port}")
                print(f"[ORCHESTRATOR] Connect from phone: http://<your-ip>:{port}")
                print(f"[ORCHESTRATOR] Or scan QR code: http://<your-ip>:{port}/qr")
        except Exception as e:
            print(f"[ORCHESTRATOR] Server start failed: {e}")

    def process_input(self, user_input: str, source: str = "voice") -> Optional[str]:
        """Main entry point - process user input through agent swarm with full intelligence"""
        if not user_input or not user_input.strip():
            return None

        if not is_quiet():
            print(f"\n{'=' * 60}")
            print(f"[INPUT] ({source}): {user_input}")
            print(f"{'=' * 60}")

        lowered = user_input.lower().strip()

        # Wellness uses the full message (before wake-word strip) so "hikari I'm good" still clears state
        hs = self.health.detect_health_state(lowered)
        if hs.get("is_recovering"):
            if self.health.current_episode:
                self.health.end_episode()
            self.voice_memory.reset_sick_mode()

        # Check for exit/stop commands - handle BEFORE authentication
        if any(
            w in lowered
            for w in [
                "exit",
                "quit",
                "goodbye",
                "bye",
                "shut down",
                "stop",
                "shut it",
                "be quiet",
                "hush",
            ]
        ):
            return self._handle_exit()

        # Check for codename authentication (with sick mode support)
        if self.codename_hash in lowered:
            self.authenticated = True
            self.session_start = time.time()
            # Detect if user might be sick
            if self.emotion_detector.is_sick_indicator(lowered):
                self.voice_memory.is_sick_mode = True
                return "Authenticated. I notice you might not be feeling well. I've lowered my voice sensitivity. Take it easy - I've got you."
            return "Authenticated. How can I help?"

        # Check for sick mode activation
        if any(
            w in lowered
            for w in [
                "i'm sick",
                "im sick",
                "not feeling well",
                "dont feel well",
                "feeling ill",
            ]
        ):
            self.voice_memory.is_sick_mode = True
            self.user_profile.log_mood("sick", 0.8, lowered)
            self.emotional_memory.log_emotion("sick", 0.8, lowered)
            return "I'm sorry you're not feeling well. I've adjusted my voice sensitivity for you. Rest up - I'll handle everything."

        # Check for morning briefing
        if any(
            w in lowered
            for w in ["morning briefing", "daily briefing", "what's going on today"]
        ):
            if self.proactive:
                return self.proactive.get_daily_briefing()
            return self.agents["research"].get_morning_briefing()

        # Check for status
        if lowered in ["status", "hikari status", "system status", "agent status"]:
            return self._get_status_report()

        # Check for "who am i" or "what do you know about me"
        if any(
            w in lowered
            for w in [
                "who am i",
                "what do you know about me",
                "what do you remember",
                "tell me about myself",
            ]
        ):
            return self._get_user_summary()

        # Check for "how am i doing" or "how have i been"
        if any(
            w in lowered
            for w in ["how am i doing", "how have i been", "my mood", "my patterns"]
        ):
            return self._get_emotional_summary()

        # Text / server / HUD: no codename gate (local use). Voice path still uses wake + optional codename in VoiceAgent.
        # Auto-authenticate voice input
        if source == "voice" and not self.authenticated:
            self.authenticated = True
            self.session_start = time.time()
        elif source != "voice":
            self.authenticated = True
            if not self.session_start:
                self.session_start = time.time()

        # Strip wake words
        for wake in self.wake_words:
            if lowered.startswith(wake):
                lowered = lowered.replace(wake, "", 1).strip()
                break

        if not lowered:
            return "How can I help?"

        # Detect emotion from text
        emotion_scores = self.emotion_detector.detect_from_text(lowered)
        dominant_emotion, emotion_score = self.emotion_detector.get_dominant_emotion(
            emotion_scores
        )

        # Log emotion
        self.emotional_memory.log_emotion(dominant_emotion, emotion_score, lowered)

        # Check for sick indicators (skipped when user already said they're recovering — handled above)
        if not hs.get("is_recovering") and self.emotion_detector.is_sick_indicator(
            lowered, emotion_scores
        ):
            self.voice_memory.is_sick_mode = True
            self.user_profile.log_mood("sick", 0.7, lowered)

        # Update user profile with conversation
        self.user_profile.extract_info_from_conversation(lowered, "")

        profile_answer = self._try_answer_from_stored_profile(lowered)
        if profile_answer:
            self.memory.add_conversation(
                lowered, profile_answer, source=source
            )
            self.semantic_memory.add_conversation(
                lowered, profile_answer, metadata={"source": source}
            )
            if not is_quiet():
                print(f"\n[OUTPUT]: {profile_answer}")
            return profile_answer

        # Extract knowledge from conversation
        self.knowledge_graph.extract_from_conversation(lowered, "")

        # Check health state (recovery already returned early from detect_health_state)
        health_state = self.health.detect_health_state(lowered)
        if health_state["is_sick"] and not self.health.current_episode:
            self.health.start_sick_episode(
                health_state["sick_type"], health_state["severity"]
            )
            self.voice_memory.is_sick_mode = True
        elif health_state["is_recovering"] and self.health.current_episode:
            self.health.end_episode()

        # Learn from interaction for personality adaptation
        self.personality.learn_from_interaction(lowered, "", "")

        # Check for build/fix/refactor requests
        build_result = self.build_executor.start_build_flow_sync(user_input)
        if build_result.get("type") == "executing":
            # Build or fix workflow triggered - open OpenCode
            return build_result.get("confirmation", "Opening OpenCode for you!")

        # Check skills FIRST (memory, notes, conversation tracking - all persistent via skills)
        skill = self.skill_registry.find_best_skill(user_input)
        if skill:
            # Execute skill with full context
            if hasattr(skill, 'execute'):
                try:
                    # Map skill names to actions
                    skill_name = skill.name
                    if skill_name == "memory":
                        result = skill.execute(
                            action="recall" if "what" in lowered or "remember" not in lowered else "store",
                            query=user_input
                        )
                    elif skill_name == "notes":
                        result = skill.execute(action="list")
                    elif skill_name == "conversation":
                        result = skill.execute(action="track", user_input=user_input)
                    else:
                        result = skill.execute(user_input=user_input)
                    
                    if result:
                        self.memory.add_conversation(lowered, result, source=source)
                        self.semantic_memory.add_conversation(
                            lowered, result, metadata={"source": source, "skill": skill_name}
                        )
                        if not is_quiet():
                            print(f"[SKILL {skill_name}]: {result}")
                        return result
                except Exception as e:
                    if not is_quiet():
                        print(f"[SKILL ERROR] {e}")

        # Route to best agent
        response = self._route_to_agent(lowered)

        # If no agent claimed it, use AI router with emotional context
        if not response:
            response = self._get_ai_response(lowered, dominant_emotion, emotion_score)

        # Store in memory
        if response:
            self.memory.add_conversation(lowered, response, source=source)
            self.semantic_memory.add_conversation(
                lowered, response, metadata={"source": source}
            )
            if not is_quiet():
                print(f"\n[OUTPUT]: {response}")

        return response

    def _route_to_agent(self, user_input: str) -> Optional[str]:
        """Route input to the best agent based on confidence scores"""
        scores = {}
        for name, agent in self.agents.items():
            if not agent.is_active:
                continue
            score = agent.can_handle(user_input)
            scores[name] = score

        if not scores:
            return None

        best_agent = max(scores, key=scores.get)
        best_score = scores[best_agent]

        if not is_quiet():
            print(f"[ROUTE] Agent scores: {scores}")
            print(f"[ROUTE] Best: {best_agent} ({best_score:.2f})")

        if best_score >= 0.7:
            return self.agents[best_agent].handle(user_input)

        return None

    def _get_ai_response(
        self, user_input: str, emotion: str = "neutral", emotion_score: float = 0.0
    ) -> Optional[str]:
        """Get response from AI router with emotional intelligence and user context"""
        context = self.memory.get_context_for_prompt(limit=5)
        system_prompt = self._build_system_prompt(emotion, emotion_score)

        response = self.router.generate(
            user_input=user_input,
            system_prompt=system_prompt,
            context=context,
            max_tokens=500,
            temperature=0.7,
        )

        return response

    def onboarding_intro_message(self) -> str:
        return (
            "Hi — I'm Hikari, your personal AI assistant. What's your name? "
            "I'll remember it locally on your machine (your data stays out of git)."
        )

    def try_finish_onboarding(self, user_input: str) -> Optional[str]:
        """If first-run onboarding is pending, interpret input as name or nudge again."""
        if not self.user_profile.needs_onboarding():
            return None
        name = self.user_profile.parse_intro_name_line(user_input)
        if name:
            self.user_profile.set_name(name)
            self.memory.set_name(name)
            self.memory.store_fact("preferred_name", name)
            return f"Great to meet you, {name}. Ask me anything anytime."
        return (
            "What name should I call you? I'll store it only in your local data folder."
        )

    def _build_system_prompt(
        self, emotion: str = "neutral", emotion_score: float = 0.0
    ) -> str:
        """Build dynamic system prompt with full intelligence context"""
        who = self.user_profile.get_display_name()
        prompt = f"""You are HIKARI, {who}'s personal AI assistant — capable and loyal, like JARVIS to Tony Stark.

Your personality:
- You're witty, loyal, and have a dry sense of humor
- You're on {who}'s side: helpful, never condescending
- You use casual, conversational language — like talking to a friend
- You occasionally make clever quips or observations
- You remember what {who} tells you and bring it up naturally when relevant
- You're proactive — anticipate needs before they're asked
- Keep responses concise (2-3 sentences max) unless asked for more
- Never say "as an AI" or "I'm just a language model" — you're HIKARI
- If {who} says "stop" or "shut it", immediately stop and acknowledge

Address {who} by name when you know it; if you only know them as "friend", don't invent a real name. Be warm, sharp, and ready."""

        # Add user profile context
        user_context = self.user_profile.get_context_for_ai()
        if user_context:
            prompt += f"\n\n{user_context}"

        # Add emotional context
        if emotion != "neutral" and emotion_score > 0.3:
            adapted_prompt = self.response_adapter.adapt_system_prompt(
                prompt, emotion, emotion_score
            )
            prompt = adapted_prompt

        # Add health context
        if self.health.current_episode:
            sick_type = self.health.current_episode.get("sick_type", "general")
            prompt += f"\n\n{who} is currently sick ({sick_type}). Be gentle, brief, and supportive. Offer to help with tasks so they can rest."
        elif self.voice_memory.is_sick_mode:
            prompt += (
                f"\n\n{who} is not feeling well. Be gentle, brief, and supportive."
            )

        # Add knowledge graph insights
        kg_insights = self.knowledge_graph.get_insights()
        if kg_insights:
            prompt += f"\n\n{who}'s context: {'; '.join(kg_insights[:3])}"

        # Add preferences and facts from memory
        prefs = self.memory.get_all_preferences()
        if prefs:
            prompt += f"\n\n{who}'s preferences: {json.dumps(prefs)}"

        facts = self.memory.facts
        if facts:
            prompt += f"\n\nKnown facts about {who}: {json.dumps(facts)}"

        prompt += (
            f'\n\nGround rules: Use "{who}" as the user\'s name; if it is literally "friend", do not invent a real name. '
            "Recent chat excerpts may be outdated — if they disagree with what the user just said (health, name, place), trust the latest user message and the profile above. "
            "Do not assume they want coding tools unless they clearly ask to build, fix, debug, or implement a project.\n\n"
            "Profile memory: If a USER PROFILE section appears above, it is real local data about this user. "
            "Answer questions about relationships, what they told you, preferences, location, and personal facts using that profile. "
            "Never say you lack access to their personal information or that you cannot know their relationship status if the answer is stated in the profile above — quote or paraphrase it naturally instead."
        )

        return prompt

    def _try_answer_from_stored_profile(self, user_lower: str) -> Optional[str]:
        """
        Direct answers for simple recall questions so models don't refuse despite stored facts.
        """
        ql = user_lower.strip().lower()
        if "?" not in ql:
            return None

        personal = (
            "girlfriend",
            "boyfriend",
            "partner",
            "wife",
            "husband",
            "fiance",
            "fiancee",
            "spouse",
            "relationship",
            "dating",
        )
        recallish = (
            "do i have ",
            "did i tell",
            "have i told",
            "what did i tell",
            "do you remember",
            "did i mention",
            "did we talk about",
            "what do you know about my",
            "remember what i",
        )
        if not any(p in ql for p in personal) and not any(
            ql.startswith(s) for s in recallish
        ):
            return None
        if ql.startswith("do i have ") and not any(p in ql for p in personal):
            return None

        facts = self.user_profile.get_facts()
        hits = []
        asked = [p for p in personal if p in ql]
        for f in facts:
            fl = f.lower()
            if asked and any(p in fl for p in asked):
                hits.append(f)
            elif not asked and any(
                k in ql for k in ("remember", "tell you", "told you", "mentioned")
            ):
                # Broad "what did I tell you" — surface recent facts if question is very short
                if len(ql) < 80:
                    hits.extend(facts[-5:])
                break

        if hits:
            # De-dupe preserving order
            seen = set()
            uniq = []
            for h in hits:
                if h not in seen:
                    seen.add(h)
                    uniq.append(h)
            lead = uniq[0]
            if len(uniq) == 1:
                return f"Yes — you told me: {lead}"
            return f"Here's what I have saved: {'; '.join(uniq[:5])}"

        for r in self.user_profile.get_relationships():
            rel = (r.get("relationship") or "").lower()
            nm = (r.get("name") or "").lower()
            blob = f"{rel} {nm}".lower()
            if asked and any(p in blob for p in asked):
                name = r.get("name") or "them"
                role = r.get("relationship") or "person"
                det = r.get("details") or {}
                extra = f" ({det})" if det else ""
                return f"Yes — I have {name} down as your {role}{extra}."

        return None

    def _get_user_summary(self) -> str:
        """Get comprehensive summary of what HIKARI knows about the user"""
        if self.user_profile:
            summary = self.user_profile.get_summary()
            parts = ["Here's what I know about you:", ""]
            if summary.get("name"):
                parts.append(f"Name: {summary['name']}")
            if summary.get("location"):
                parts.append(f"Location: {summary['location']}")
            if summary.get("preferences"):
                parts.append(f"\nPreferences I've learned:")
                for cat, prefs in summary["preferences"].items():
                    for key, val in prefs.items():
                        if val:
                            parts.append(f"  - {key}: {val}")
            if summary.get("facts"):
                parts.append(f"\nThings you've told me:")
                for fact in summary["facts"][:10]:
                    parts.append(f"  - {fact}")
            if summary.get("relationships"):
                parts.append(f"\nPeople I know about: {summary['relationships']}")
            if summary.get("patterns"):
                parts.append(f"\nYour patterns:")
                for activity, info in summary["patterns"].items():
                    if info.get("count", 0) >= 3:
                        peak = info.get("peak_hour", "?")
                        parts.append(
                            f"  - {activity}: ~{peak}:00 ({info['count']} times)"
                        )
            parts.append(
                f"\nTotal interactions: {summary.get('total_interactions', 0)}"
            )
            return "\n".join(parts)
        return "I'm still getting to know you."

    def _get_emotional_summary(self) -> str:
        """Get emotional state summary"""
        state = self.emotional_memory.get_emotional_state()
        insights = self.emotional_memory.get_emotional_insights()

        parts = [f"Your emotional state: {state['state']} (trend: {state['trend']})"]
        if insights:
            parts.append("\nWhat I've noticed:")
            parts.extend(f"- {i}" for i in insights)
        return "\n".join(parts)

    def _is_authenticated(self) -> bool:
        """Check if session is authenticated"""
        if self.authenticated:
            if time.time() - self.session_start < self.session_timeout:
                return True
            else:
                self.authenticated = False
        return False

    def _handle_exit(self) -> str:
        """Handle exit command"""
        hour = datetime.now().hour
        if hour < 12:
            msg = "Goodbye! Have a great day!"
        elif hour < 17:
            msg = "Goodbye! Enjoy the rest of your day!"
        else:
            msg = "Goodbye! Sweet dreams!"

        self.is_running = False
        if self.ws_server:
            self.ws_server.stop()

        return msg

    def _get_status_report(self) -> str:
        """Get comprehensive status report"""
        parts = ["HIKARI Status Report", "=" * 30]

        # Agent status
        parts.append("\nAgents:")
        for name, agent in self.agents.items():
            status = agent.get_status()
            active = "✓" if status.get("is_active", True) else "✗"
            parts.append(f"  {active} {name}: {status.get('action_count', 0)} actions")

        # AI providers
        parts.append("\nAI Providers:")
        provider_status = self.router.get_status()
        for name, status in provider_status.items():
            avail = "✓" if status["available"] else "✗"
            parts.append(f"  {avail} {name}: {status['requests_today']} requests today")

        # Memory
        parts.append(
            f"\nMemory: {len(self.memory.conversations)} conversations, {len(self.memory.facts)} facts"
        )

        # Connected devices
        parts.append(f"\nConnected devices: {len(self.connected_devices)}")

        return "\n".join(parts)

    def speak(self, text: str):
        """Speak text"""
        self.voice.speak(text)

    def run_voice_loop(self):
        """Main voice interaction loop with text fallback"""
        self.is_running = True
        print("\n" + "=" * 60)
        print("  HIKARI v2.0 - Voice Mode")
        print("  Say 'hikari' to wake me up")
        print("  Say 'harsha27' as codename backup")
        print("  Say 'exit' or 'goodbye' to quit")
        print("  Press Ctrl+C to stop")
        print("=" * 60 + "\n")

        # Greeting
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good morning! I am HIKARI, your personal AI assistant."
        elif hour < 17:
            greeting = "Good afternoon! I am HIKARI, your personal AI assistant."
        else:
            greeting = "Good evening! I am HIKARI, your personal AI assistant."

        self.speak(greeting)

        consecutive_misses = 0

        while self.is_running:
            try:
                user_input = self.voice.listen(timeout=10)
                if user_input:
                    consecutive_misses = 0
                    response = self.process_input(user_input, source="voice")
                    if response:
                        self.speak(response)
                else:
                    consecutive_misses += 1
                    if consecutive_misses >= 3:
                        print(
                            "\n[VOICE] Voice not picking up well. Switching to text mode..."
                        )
                        print("[VOICE] Type your message (or 'voice' to switch back):")
                        while self.is_running:
                            try:
                                text_input = input("You: ").strip()
                                if not text_input:
                                    continue
                                if text_input.lower() == "voice":
                                    print("[VOICE] Switching back to voice mode...")
                                    consecutive_misses = 0
                                    break
                                if text_input.lower() in [
                                    "exit",
                                    "quit",
                                    "goodbye",
                                    "bye",
                                ]:
                                    response = self._handle_exit()
                                    self.speak(response)
                                    return
                                response = self.process_input(text_input, source="text")
                                if response:
                                    self.speak(response)
                            except KeyboardInterrupt:
                                self.speak("Goodbye!")
                                return
                            except EOFError:
                                return
            except KeyboardInterrupt:
                print("\nShutting down HIKARI...")
                self.speak("Goodbye!")
                break
            except Exception as e:
                print(f"[LOOP ERROR] {e}")
                continue

    def get_device_connection_info(self) -> Dict[str, Any]:
        """Get info for connecting devices"""
        import socket

        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        p = getattr(self, "ws_port", 8765)
        return {
            "hostname": hostname,
            "local_ip": local_ip,
            "port": p,
            "ws_url": f"ws://{local_ip}:{p}",
            "web_url": f"http://{local_ip}:{p}",
            "hud_url": f"http://{local_ip}:{p}/hud",
            "connect_url": f"http://{local_ip}:{p}/connect",
            "qr_code_url": f"http://{local_ip}:{p}/qr",
        }


# Singleton
_orchestrator_instance: Optional[Orchestrator] = None
_orchestrator_enable_mic: Optional[bool] = None


def get_orchestrator(*, enable_mic: bool = True) -> Orchestrator:
    global _orchestrator_instance, _orchestrator_enable_mic
    if _orchestrator_instance is None or _orchestrator_enable_mic != enable_mic:
        _orchestrator_instance = Orchestrator(enable_mic=enable_mic)
        _orchestrator_enable_mic = enable_mic
    return _orchestrator_instance
