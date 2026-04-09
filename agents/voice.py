"""
HIKARI v2.0 - Voice Agent
Handles speech I/O, authentication, wake word routing
"""

import os
import re
import sys
import hashlib
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from agents.base import BaseAgent
from core.voice import VoiceSystem, ClapDetector
from security.auth import VoiceAuth

# Codename hash (sha256 of "harsha27")
CODENAME_HASH = hashlib.sha256("harsha27".encode()).hexdigest()
WAKE_WORDS = ["hikari", "shikari", "hickory", "hey hikari"]


class VoiceAgent(BaseAgent):
    """Handles voice input, authentication, and activation"""

    def __init__(self):
        super().__init__("voice", "Voice I/O, authentication, and activation")
        self.voice_system = VoiceSystem()
        self.voice_auth = VoiceAuth()
        self.clap_detector = ClapDetector(clap_count=2)
        self.is_authenticated = False
        self.last_auth_time = 0
        self.auth_timeout = 3600  # 1 hour auth session
        self.activation_history = []

    def handle(self, user_input: str, context: str = "") -> Optional[str]:
        """Process voice input - this is called with text from speech recognition"""
        if not user_input:
            return None

        lowered = user_input.lower().strip()

        # Check for codename
        if self._check_codename(lowered):
            self.is_authenticated = True
            self.last_auth_time = time.time()
            return "Authenticated via codename. How can I help?"

        # Check for wake word removal
        for wake in WAKE_WORDS:
            if lowered.startswith(wake):
                lowered = lowered.replace(wake, "", 1).strip()
                break

        # Check if authenticated
        if not self._is_session_valid():
            return None  # Not authenticated, ignore

        return lowered

    def listen_once(self, timeout: int = 10) -> Optional[str]:
        """Listen for one voice command"""
        text = self.voice_system.listen(timeout=timeout)
        if text:
            return self.handle(text)
        return None

    def speak(self, text: str):
        """Speak text using TTS"""
        self.voice_system.speak(text)

    def start_clap_detection(self):
        """Start background clap detection"""
        self.clap_detector.start(callback=self._on_clap_detected)

    def _on_clap_detected(self):
        """Handle clap detection"""
        print("[VOICE] Clap activation detected!")
        self.is_authenticated = True
        self.last_auth_time = time.time()
        self.activation_history.append(
            {
                "type": "clap",
                "time": datetime.now().isoformat(),
            }
        )

    def _check_codename(self, text: str) -> bool:
        """Check if input contains the codename"""
        text_hash = hashlib.sha256(text.strip().encode()).hexdigest()
        if text_hash == CODENAME_HASH:
            print("[AUTH] Codename authentication successful")
            return True
        # Also check if codename is embedded in text
        if "harsha27" in text.lower():
            print("[AUTH] Codename found in text")
            return True
        return False

    def _is_session_valid(self) -> bool:
        """Check if authentication session is still valid"""
        if self.is_authenticated:
            if time.time() - self.last_auth_time < self.auth_timeout:
                return True
            else:
                self.is_authenticated = False
                print("[AUTH] Session expired")
        return False

    def authenticate_voice_print(self, audio_data=None) -> bool:
        """Authenticate using voice print"""
        if audio_data:
            result = self.voice_auth.verify_speaker(audio_data)
            if result:
                self.is_authenticated = True
                self.last_auth_time = time.time()
            return result
        return False

    def get_status(self) -> Dict[str, Any]:
        status = super().get_status()
        status.update(
            {
                "authenticated": self.is_authenticated,
                "session_valid": self._is_session_valid(),
                "voice_system": self.voice_system.get_status(),
                "activation_history": self.activation_history[-10:],
            }
        )
        return status

    def can_handle(self, user_input: str) -> float:
        lowered = user_input.lower()
        # High confidence for voice-related commands
        if any(
            w in lowered
            for w in WAKE_WORDS + ["listen", "hear", "speak", "say", "repeat"]
        ):
            return 0.9
        return 0.3
