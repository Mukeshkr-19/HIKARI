"""Configuration and path resolution for Hikari Neural Memory."""

import os
import json
from pathlib import Path
from typing import Optional


class MemoryConfig:
    # Anonymous default; override in ~/.hikari/brain/config.json -> "user_id"
    DEFAULT_USER_ID = "local_user"
    BRAIN_DIR = Path.home() / ".hikari" / "brain"
    DB_NAME = "hikari_memory.db"
    CACHE_DIR = BRAIN_DIR / "cache"
    EMBEDDINGS_DIR = BRAIN_DIR / "embeddings"
    LOGS_DIR = BRAIN_DIR / "logs"
    BACKUPS_DIR = BRAIN_DIR / "backups"
    CONFIG_FILE = BRAIN_DIR / "config.json"

    DB_PATH: Path = BRAIN_DIR / DB_NAME
    SCHEMA_PATH = Path(__file__).parent / "db" / "memory_schema.sql"

    CACHE_MAX_SIZE = 1000
    CACHE_TTL_SECONDS = 3600

    CONSOLIDATION_INTERVALS = {"micro": 0, "bounded": 10, "session": 0, "daily": 0}

    SALIENCE_DECAY_RATE = 0.01
    MIN_SALIENCE_THRESHOLD = 0.1
    ARCHIVE_SALIENCE_THRESHOLD = 0.05

    MAX_NODES_PER_RETRIEVAL = 50
    MAX_EDGES_PER_RETRIEVAL = 100

    _instance: Optional["MemoryConfig"] = None
    _config: dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        self.BRAIN_DIR.mkdir(parents=True, exist_ok=True)
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE) as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._config = {}
        else:
            self._config = self._default_config()
            self._save_config()

    def _default_config(self) -> dict:
        return {
            "version": 1,
            "user_id": self.DEFAULT_USER_ID,
            "brain_path": str(self.BRAIN_DIR),
            "salience_decay_rate": self.SALIENCE_DECAY_RATE,
            "cache_enabled": True,
            "vector_fallback_enabled": True,
            "auto_consolidation": True,
        }

    def _save_config(self):
        with open(self.CONFIG_FILE, "w") as f:
            json.dump(self._config, f, indent=2)

    def get(self, key: str, default=None):
        return self._config.get(key, default)

    def set(self, key: str, value):
        self._config[key] = value
        self._save_config()

    @property
    def user_id(self) -> str:
        return self._config.get("user_id", self.DEFAULT_USER_ID)

    @user_id.setter
    def user_id(self, value: str):
        self._config["user_id"] = value
        self._save_config()

    def ensure_directories(self):
        for d in [
            self.BRAIN_DIR,
            self.CACHE_DIR,
            self.EMBEDDINGS_DIR,
            self.LOGS_DIR,
            self.BACKUPS_DIR,
        ]:
            d.mkdir(parents=True, exist_ok=True)


config = MemoryConfig()
