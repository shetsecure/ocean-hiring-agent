#!/usr/bin/env python3
"""
Rate Limiter Module

Handles rate limiting for API requests to respect service limits.
"""

import time
import random
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RateLimiter:
    """Handles rate limiting for API requests."""
    
    def __init__(self, requests_per_second: float = 1.0):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum requests per second (default: 1.0)
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
        self.request_count = 0
        
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            # Add small random jitter to avoid thundering herd
            sleep_time += random.uniform(0, 0.1)
            logger.info(f"⏳ Rate limiting: waiting {sleep_time:.2f}s before next API request")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
        
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        return {
            "total_requests": self.request_count,
            "requests_per_second_limit": self.requests_per_second,
            "total_wait_time": max(0, self.request_count * self.min_interval - (time.time() - self.last_request_time))
        } 