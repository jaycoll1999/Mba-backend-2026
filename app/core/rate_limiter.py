import time
from collections import defaultdict
from fastapi import Request, HTTPException, status
from app.config import settings

class InMemoryRateLimiter:
    def __init__(self, requests_per_minute: int = 20):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)

    def check(self, request: Request, key_prefix: str = "auth"):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{key_prefix}:{client_ip}"
        current_time = time.time()
        
        # Clean timestamps older than 60 seconds
        window_start = current_time - 60.0
        self.requests[key] = [t for t in self.requests[key] if t > window_start]
        
        if len(self.requests[key]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute allowed."
            )
        
        self.requests[key].append(current_time)

auth_rate_limiter = InMemoryRateLimiter(settings.AUTH_RATE_LIMIT_PER_MINUTE)
