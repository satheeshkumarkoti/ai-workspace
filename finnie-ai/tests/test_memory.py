"""
Tests for Redis Store — shared agent memory
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
import json


class TestRedisStore:

    def _get_store_no_redis(self):
        """Return a RedisStore instance with no Redis connection."""
        with patch("redis.Redis") as mock_redis:
            mock_redis.return_value.ping.side_effect = Exception("No Redis")
            from memory.redis_store import RedisStore
            return RedisStore()

    def _get_store_with_redis(self):
        """Return a RedisStore instance with mocked Redis."""
        with patch("redis.Redis") as mock_redis:
            mock_redis.return_value.ping.return_value = True
            from memory.redis_store import RedisStore
            store = RedisStore()
            store._client = mock_redis.return_value
            return store, mock_redis.return_value

    # ── Availability ──

    def test_store_unavailable_when_no_redis(self):
        store = self._get_store_no_redis()
        assert store.available is False

    def test_store_available_with_redis(self):
        with patch("redis.Redis") as mock_redis:
            mock_redis.return_value.ping.return_value = True
            from memory.redis_store import RedisStore
            store = RedisStore()
            store._client = mock_redis.return_value
            assert store.available is True

    # ── Learning Progress ──

    def test_get_learning_progress_no_redis_returns_none(self):
        store = self._get_store_no_redis()
        result = store.get_learning_progress("user123")
        assert result is None

    def test_get_learning_progress_with_data(self):
        with patch("redis.Redis") as mock_redis:
            mock_redis.return_value.ping.return_value = True
            mock_redis.return_value.get.return_value = json.dumps({
                "modules": {"SIP Basics": 100},
                "completed_modules": ["SIP Basics"]
            })
            from memory.redis_store import RedisStore
            store = RedisStore()
            store._client = mock_redis.return_value
            result = store.get_learning_progress("user123")
            assert result["completed_modules"] == ["SIP Basics"]

    def test_get_learning_progress_missing_key_returns_empty(self):
        with patch("redis.Redis") as mock_redis:
            mock_redis.return_value.ping.return_value = True
            mock_redis.return_value.get.return_value = None
            from memory.redis_store import RedisStore
            store = RedisStore()
            store._client = mock_redis.return_value
            result = store.get_learning_progress("newuser")
            assert result == {}

    def test_update_learning_progress_no_redis(self):
        store = self._get_store_no_redis()
        result = store.update_learning_progress("user123", "SIP Basics", 60)
        assert result is False

    def test_update_learning_progress_marks_complete(self):
        with patch("redis.Redis") as mock_redis:
            mock_redis.return_value.ping.return_value = True
            mock_redis.return_value.get.return_value = json.dumps({
                "modules": {}, "completed_modules": []
            })
            from memory.redis_store import RedisStore
            store = RedisStore()
            store._client = mock_redis.return_value
            result = store.update_learning_progress("user123", "SIP Basics", 100)
            assert result is True
            store._client.set.assert_called_once()

    # ── User Profile ──

    def test_save_user_profile_no_redis(self):
        store = self._get_store_no_redis()
        result = store.save_user_profile("user123", {"name": "Test"})
        assert result is False

    def test_save_user_profile_with_redis(self):
        with patch("redis.Redis") as mock_redis:
            mock_redis.return_value.ping.return_value = True
            from memory.redis_store import RedisStore
            store = RedisStore()
            store._client = mock_redis.return_value
            result = store.save_user_profile("user123", {"name": "Satheesh"})
            assert result is True

    def test_get_user_profile_no_redis(self):
        store = self._get_store_no_redis()
        result = store.get_user_profile("user123")
        assert result is None

    # ── Interaction Log ──

    def test_log_interaction_no_redis(self):
        store = self._get_store_no_redis()
        result = store.log_interaction("user123", "literacy", "What is SIP?")
        assert result is False

    def test_log_interaction_with_redis(self):
        with patch("redis.Redis") as mock_redis:
            mock_redis.return_value.ping.return_value = True
            from memory.redis_store import RedisStore
            store = RedisStore()
            store._client = mock_redis.return_value
            result = store.log_interaction("user123", "literacy", "What is SIP?")
            assert result is True
            store._client.lpush.assert_called_once()

    def test_get_history_no_redis_returns_empty(self):
        store = self._get_store_no_redis()
        result = store.get_history("user123")
        assert result == []

    def test_get_history_with_redis(self):
        with patch("redis.Redis") as mock_redis:
            mock_redis.return_value.ping.return_value = True
            entry = json.dumps({"agent": "literacy", "query": "What is SIP?", "timestamp": "2026-01-01"})
            mock_redis.return_value.lrange.return_value = [entry]
            from memory.redis_store import RedisStore
            store = RedisStore()
            store._client = mock_redis.return_value
            result = store.get_history("user123", limit=5)
            assert len(result) == 1
            assert result[0]["agent"] == "literacy"

    # ── A2A Shared State ──

    def test_set_a2a_state_no_redis(self):
        store = self._get_store_no_redis()
        result = store.set_a2a_state("session1", "live_prices", {"INFY": 1842})
        assert result is False

    def test_get_a2a_state_no_redis_returns_empty(self):
        store = self._get_store_no_redis()
        result = store.get_a2a_state("session1")
        assert result == {}

    def test_set_and_get_a2a_state_with_redis(self):
        with patch("redis.Redis") as mock_redis:
            mock_redis.return_value.ping.return_value = True
            mock_redis.return_value.get.return_value = json.dumps(
                {"live_prices": {"INFY": 1842}}
            )
            from memory.redis_store import RedisStore
            store = RedisStore()
            store._client = mock_redis.return_value
            state = store.get_a2a_state("session1")
            assert "live_prices" in state
