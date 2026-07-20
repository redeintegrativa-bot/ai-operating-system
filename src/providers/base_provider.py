from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


@dataclass
class ProviderResponse:
    normalized: Dict[str, Any] = field(default_factory=dict)
    raw: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)
    cached: bool = False
    fetched_at: Optional[datetime] = None


class BaseDefiProvider(ABC):
    cache_timeout_seconds: int = 300
    _cache: Dict[str, tuple] = {}

    def __init__(self):
        self._name = self.__class__.__name__.replace("Provider", "").lower()

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def _get_cache_key(self, **kwargs) -> str:
        parts = [self.get_name()]
        for key, value in sorted(kwargs.items()):
            parts.append(f"{key}={value}")
        return ":".join(parts)

    def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=self.cache_timeout_seconds):
                return cached_data
            del self._cache[cache_key]
        return None

    def _set_cache(self, cache_key: str, data: Dict[str, Any]):
        self._cache[cache_key] = (data, datetime.now())

    def _clear_expired_cache(self):
        now = datetime.now()
        expired = [
            key for key, (_, cached_time) in self._cache.items()
            if now - cached_time >= timedelta(seconds=self.cache_timeout_seconds)
        ]
        for key in expired:
            del self._cache[key]

    def get_data(self, force_refresh: bool = False, **kwargs) -> ProviderResponse:
        cache_key = self._get_cache_key(**kwargs)

        if not force_refresh:
            cached = self._check_cache(cache_key)
            if cached is not None:
                return ProviderResponse(
                    normalized=cached,
                    cached=True,
                    fetched_at=datetime.now(),
                )

        raw_data = self.fetch_data(**kwargs)
        parsed_data = self.parse_data(raw_data)

        self._set_cache(cache_key, parsed_data)

        return ProviderResponse(
            normalized=parsed_data,
            raw=raw_data,
            cached=False,
            fetched_at=datetime.now(),
        )

    def is_available(self) -> bool:
        try:
            response = self.get_data(timeout=5)
            return len(response.warnings) == 0
        except Exception:
            return False


    def _mock_fallback(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return {
            "fallback": True,
            "endpoint": endpoint,
            "message": "Using mock data - provider unavailable",
            "timestamp": datetime.now().isoformat(),
        }
