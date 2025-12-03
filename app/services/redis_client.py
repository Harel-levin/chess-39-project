"""
Redis client for caching and pub/sub.
"""

import redis
import json
from typing import Optional, Any
from ..core.config import settings


# Create Redis client
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True  # Automatically decode bytes to strings
)


def cache_game_state(game_id: str, game_state: dict, ttl: int = 86400):
    """
    Cache game state in Redis.
    
    Args:
        game_id: Game ID
        game_state: Game state dictionary
        ttl: Time to live in seconds (default: 24 hours)
    """
    key = f"game:{game_id}"
    redis_client.setex(key, ttl, json.dumps(game_state))


def get_cached_game_state(game_id: str) -> Optional[dict]:
    """
    Get cached game state from Redis.
    
    Returns:
        Game state dict or None if not cached
    """
    key = f"game:{game_id}"
    data = redis_client.get(key)
    return json.loads(data) if data else None


def delete_cached_game(game_id: str):
    """Delete game from cache."""
    key = f"game:{game_id}"
    redis_client.delete(key)


def publish_game_update(game_id: str, message: dict):
    """
    Publish game update to Redis pub/sub channel.
    
    Args:
        game_id: Game ID
        message: Message dictionary to broadcast
    """
    channel = f"game:{game_id}"
    redis_client.publish(channel, json.dumps(message))


def subscribe_to_game(game_id: str):
    """
    Subscribe to game updates channel.
    
    Returns:
        Redis PubSub object
    """
    pubsub = redis_client.pubsub()
    channel = f"game:{game_id}"
    pubsub.subscribe(channel)
    return pubsub
