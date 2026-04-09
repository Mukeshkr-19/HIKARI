"""
HIKARI v2.0 - Authentication System
Voice print verification, codename hashing, session management
"""

import os
import hashlib
import json
import time
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parent.parent / "data"
VOICE_PRINT_DIR = DATA_DIR / "voice_prints"
AUTH_FILE = DATA_DIR / "auth.json"


class VoiceAuth:
    """Voice-based authentication using speaker embeddings"""

    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        VOICE_PRINT_DIR.mkdir(exist_ok=True)
        self.enrolled = False
        self._load_auth_state()

    def _load_auth_state(self):
        try:
            if AUTH_FILE.exists():
                with open(AUTH_FILE, "r") as f:
                    state = json.load(f)
                self.enrolled = state.get("enrolled", False)
        except Exception:
            pass

    def _save_auth_state(self):
        try:
            with open(AUTH_FILE, "w") as f:
                json.dump({"enrolled": self.enrolled}, f)
        except Exception as e:
            print(f"[AUTH] Save error: {e}")

    def enroll_voice(self, audio_samples: list) -> bool:
        """Enroll a voice print from audio samples"""
        try:
            # Create a simple voice signature (RMS energy profile)
            # In production, this would use ECAPA-TDNN embeddings
            signature = self._compute_voice_signature(audio_samples)

            voice_file = VOICE_PRINT_DIR / "user_voice.json"
            with open(voice_file, "w") as f:
                json.dump(
                    {
                        "signature": signature,
                        "enrolled_at": time.time(),
                        "samples": len(audio_samples),
                    },
                    f,
                )

            self.enrolled = True
            self._save_auth_state()
            print("[AUTH] Voice enrolled successfully")
            return True
        except Exception as e:
            print(f"[AUTH] Enrollment error: {e}")
            return False

    def verify_speaker(self, audio_samples: list) -> bool:
        """Verify speaker against enrolled voice print"""
        if not self.enrolled:
            return False

        try:
            voice_file = VOICE_PRINT_DIR / "user_voice.json"
            if not voice_file.exists():
                return False

            with open(voice_file, "r") as f:
                stored = json.load(f)

            current_signature = self._compute_voice_signature(audio_samples)
            stored_signature = stored.get("signature", "")

            # Simple similarity check (in production, use cosine similarity of embeddings)
            similarity = self._compute_similarity(current_signature, stored_signature)
            print(f"[AUTH] Voice similarity: {similarity:.2f}")

            return similarity > 0.7
        except Exception as e:
            print(f"[AUTH] Verification error: {e}")
            return False

    def _compute_voice_signature(self, audio_samples: list) -> str:
        """Compute a simple voice signature from audio samples"""
        # Simple approach: hash the audio data
        # In production, use proper speaker embedding model
        data = "".join(str(s) for s in audio_samples[:1000])
        return hashlib.sha256(data.encode()).hexdigest()

    def _compute_similarity(self, sig1: str, sig2: str) -> float:
        """Compute similarity between two signatures"""
        if sig1 == sig2:
            return 1.0

        # Simple character-level similarity
        matches = sum(1 for a, b in zip(sig1, sig2) if a == b)
        return matches / max(len(sig1), len(sig2))

    def get_status(self) -> Dict[str, Any]:
        return {
            "enrolled": self.enrolled,
            "voice_print_exists": (VOICE_PRINT_DIR / "user_voice.json").exists(),
        }


class CodenameAuth:
    """Codename-based authentication fallback"""

    def __init__(self, codename: str = "harsha27"):
        self.codename_hash = hashlib.sha256(codename.encode()).hexdigest()
        self.attempts = 0
        self.max_attempts = 5
        self.lockout_time = 300  # 5 minutes
        self.last_attempt = 0
        self.locked = False

    def verify(self, input_codename: str) -> bool:
        """Verify codename input"""
        if self.locked:
            if time.time() - self.last_attempt < self.lockout_time:
                print("[AUTH] Codename auth locked - too many attempts")
                return False
            else:
                self.locked = False
                self.attempts = 0

        input_hash = hashlib.sha256(input_codename.strip().encode()).hexdigest()
        self.last_attempt = time.time()
        self.attempts += 1

        if input_hash == self.codename_hash:
            print("[AUTH] Codename verified")
            self.attempts = 0
            return True

        print(f"[AUTH] Invalid codename (attempt {self.attempts}/{self.max_attempts})")
        if self.attempts >= self.max_attempts:
            self.locked = True
            print("[AUTH] Codename auth locked for 5 minutes")

        return False


class SecurityPolicy:
    """Enforces security policies for agent actions"""

    def __init__(self):
        self.allowed_paths = set()
        self.blocked_actions = set()
        self.audit_log = []

    def allow_path(self, path: str):
        """Whitelist a path for agent access"""
        self.allowed_paths.add(path)

    def block_action(self, action: str):
        """Block a specific action"""
        self.blocked_actions.add(action)

    def check_action(self, agent: str, action: str, target: str = "") -> bool:
        """Check if an action is allowed"""
        if action in self.blocked_actions:
            self._log("BLOCKED", agent, action, target)
            return False

        self._log("ALLOWED", agent, action, target)
        return True

    def _log(self, status: str, agent: str, action: str, target: str):
        self.audit_log.append(
            {
                "status": status,
                "agent": agent,
                "action": action,
                "target": target,
                "time": time.time(),
            }
        )
        if len(self.audit_log) > 500:
            self.audit_log = self.audit_log[-500:]

    def get_audit_log(self, limit: int = 20) -> list:
        return self.audit_log[-limit:]
