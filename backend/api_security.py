# backend/api_security.py
# API productization: key management, rate limiting, usage tracking

import os
import time
import hashlib
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, Request, Depends
from fastapi.security import APIKeyHeader

# ── API Key Header ────────────────────────────────────────────
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# ── Demo API keys (in production: use a database) ─────────────
# Format: {api_key: {name, tier, requests_per_day, description}}
VALID_API_KEYS = {
    "demo-key-free-001": {
        "name":               "Demo Free Tier",
        "tier":               "free",
        "requests_per_day":   10,
        "features":           ["analyze-disease", "diseases/examples"],
        "description":        "Free demo key — 10 requests/day"
    },
    "demo-key-pro-001": {
        "name":               "Demo Pro Tier",
        "tier":               "pro",
        "requests_per_day":   100,
        "features":           ["all"],
        "description":        "Pro demo key — 100 requests/day"
    },
    # Internal key (no limit)
    "internal-dev-key": {
        "name":               "Internal Development",
        "tier":               "internal",
        "requests_per_day":   999999,
        "features":           ["all"],
        "description":        "Internal development key"
    }
}

# ── Usage Tracking ────────────────────────────────────────────
class UsageTracker:
    """Track API usage per key per day."""

    def __init__(self):
        self._usage: dict = {}   # {api_key: {date: count}}
        self._log:   list = []   # Request log

    def record_request(self, api_key: str, endpoint: str,
                       status: int = 200):
        today = datetime.now().strftime("%Y-%m-%d")
        if api_key not in self._usage:
            self._usage[api_key] = {}
        self._usage[api_key][today] = \
            self._usage[api_key].get(today, 0) + 1

        self._log.append({
            "timestamp": datetime.now().isoformat(),
            "api_key":   api_key[:8] + "...",
            "endpoint":  endpoint,
            "status":    status
        })
        # Keep last 1000 logs
        self._log = self._log[-1000:]

    def get_usage_today(self, api_key: str) -> int:
        today = datetime.now().strftime("%Y-%m-%d")
        return self._usage.get(api_key, {}).get(today, 0)

    def get_stats(self, api_key: str = None) -> dict:
        today = datetime.now().strftime("%Y-%m-%d")
        if api_key:
            return {
                "api_key":      api_key[:8] + "...",
                "today":        self.get_usage_today(api_key),
                "all_time":     sum(self._usage.get(api_key,{}).values()),
                "recent_logs":  [l for l in self._log[-10:]
                                 if api_key[:8] in l["api_key"]]
            }
        return {
            "total_requests_today": sum(
                v.get(today, 0)
                for v in self._usage.values()
            ),
            "total_keys_active":    len(self._usage),
            "recent_logs":          self._log[-20:]
        }


usage_tracker = UsageTracker()


# ── Authentication Dependency ─────────────────────────────────
def get_api_key(
    request:  Request,
    api_key:  Optional[str] = Depends(API_KEY_HEADER)
) -> dict:
    """
    FastAPI dependency: validates API key and checks rate limits.
    Returns key info dict if valid.

    Usage in endpoints:
        @app.post("/endpoint")
        def my_endpoint(key_info: dict = Depends(get_api_key)):
            ...
    """
    # Allow no key for basic endpoints (health, examples)
    basic_endpoints = ["/", "/health", "/diseases/examples",
                       "/docs", "/openapi.json"]
    if request.url.path in basic_endpoints:
        return {"tier": "public", "name": "Public"}

    # Require key for all other endpoints
    if not api_key:
        raise HTTPException(
            status_code = 401,
            detail      = {
                "error":   "API key required",
                "message": "Add header: X-API-Key: your-key",
                "get_key": "Use 'demo-key-free-001' for testing"
            }
        )

    key_info = VALID_API_KEYS.get(api_key)
    if not key_info:
        raise HTTPException(
            status_code = 403,
            detail      = {
                "error":   "Invalid API key",
                "message": "Use 'demo-key-free-001' for testing"
            }
        )

    # Check rate limit
    daily_limit  = key_info["requests_per_day"]
    usage_today  = usage_tracker.get_usage_today(api_key)

    if usage_today >= daily_limit:
        raise HTTPException(
            status_code = 429,
            detail      = {
                "error":    "Rate limit exceeded",
                "limit":    daily_limit,
                "used":     usage_today,
                "resets":   "Tomorrow at midnight UTC",
                "upgrade":  "Contact us to upgrade your tier"
            }
        )

    # Record this request
    usage_tracker.record_request(api_key, request.url.path)

    return {
        **key_info,
        "api_key":     api_key,
        "usage_today": usage_today + 1,
        "limit":       daily_limit,
        "remaining":   daily_limit - usage_today - 1
    }


def optional_api_key(
    request: Request,
    api_key: Optional[str] = Depends(API_KEY_HEADER)
) -> dict:
    """
    Soft authentication — accepts requests without key
    but tracks usage if key provided.
    """
    if api_key and api_key in VALID_API_KEYS:
        usage_tracker.record_request(api_key, request.url.path)
        return VALID_API_KEYS[api_key]
    return {"tier": "anonymous", "name": "Anonymous"}