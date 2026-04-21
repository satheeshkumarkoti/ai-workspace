"""
Redis Store — Shared A2A Memory
Stores user sessions, learning progress, and agent interaction history.
Falls back gracefully if Redis is not running.
"""
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime


class RedisStore:
    def __init__(self):
        self._client = None
        self._connect()

    def _connect(self):
        """Connect to Redis — fail silently if unavailable."""
        try:
            import redis
            self._client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=0,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            self._client.ping()
        except Exception:
            self._client = None   # Redis unavailable — run without persistence

    @property
    def available(self) -> bool:
        return self._client is not None

    # ── Learning progress ──

    def get_learning_progress(self, user_id: str) -> Optional[Dict]:
        if not self.available:
            return None
        try:
            data = self._client.get(f"finnie:progress:{user_id}")
            return json.loads(data) if data else {}
        except Exception:
            return None

    def update_learning_progress(
        self,
        user_id: str,
        module: str,
        progress_pct: int
    ) -> bool:
        if not self.available:
            return False
        try:
            key  = f"finnie:progress:{user_id}"
            data = self._client.get(key)
            progress = json.loads(data) if data else {"modules": {}, "completed_modules": []}
            progress["modules"][module] = progress_pct
            if progress_pct == 100 and module not in progress["completed_modules"]:
                progress["completed_modules"].append(module)
            self._client.set(key, json.dumps(progress), ex=86400 * 30)  # 30-day TTL
            return True
        except Exception:
            return False

    # ── User profile ──

    def save_user_profile(self, user_id: str, profile: Dict) -> bool:
        if not self.available:
            return False
        try:
            self._client.set(
                f"finnie:profile:{user_id}",
                json.dumps(profile),
                ex=86400 * 90   # 90-day TTL
            )
            return True
        except Exception:
            return False

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        if not self.available:
            return None
        try:
            data = self._client.get(f"finnie:profile:{user_id}")
            return json.loads(data) if data else None
        except Exception:
            return None

    # ── Interaction log (A2A audit trail) ──

    def log_interaction(
        self,
        user_id: str,
        agent: str,
        query: str
    ) -> bool:
        if not self.available:
            return False
        try:
            entry = json.dumps({
                "agent":     agent,
                "query":     query[:200],
                "timestamp": datetime.utcnow().isoformat(),
            })
            self._client.lpush(f"finnie:history:{user_id}", entry)
            self._client.ltrim(f"finnie:history:{user_id}", 0, 49)  # keep last 50
            return True
        except Exception:
            return False

    def get_history(self, user_id: str, limit: int = 10) -> list:
        if not self.available:
            return []
        try:
            raw = self._client.lrange(f"finnie:history:{user_id}", 0, limit - 1)
            return [json.loads(r) for r in raw]
        except Exception:
            return []

    # ── A2A shared state (agents passing data to each other) ──

    def set_a2a_state(self, session_id: str, key: str, value: Any) -> bool:
        if not self.available:
            return False
        try:
            field = f"finnie:a2a:{session_id}"
            existing = self._client.get(field)
            state = json.loads(existing) if existing else {}
            state[key] = value
            self._client.set(field, json.dumps(state), ex=3600)  # 1-hour TTL
            return True
        except Exception:
            return False

    def get_a2a_state(self, session_id: str) -> Dict:
        if not self.available:
            return {}
        try:
            data = self._client.get(f"finnie:a2a:{session_id}")
            return json.loads(data) if data else {}
        except Exception:
            return {}
