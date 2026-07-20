"""Configuration manager for the AI Operating System.

Loads configuration from multiple sources (default file, env overrides,
environment variables) with caching and change detection.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from threading import Lock


ENV_PREFIX = "AIOS_"
ENV_CONFIG_PATH = "AIOS_CONFIG_PATH"


class ConfigManager:
    """Loads and caches configuration with env-var overrides."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self._config: Dict[str, Any] = {}
        self._lock = Lock()
        self._load()

    def _default_paths(self):
        return [
            self.project_root / "config" / "default.json",
            self.project_root / "config.json",
        ]

    def _load(self):
        config_path = os.environ.get(ENV_CONFIG_PATH)
        paths = [Path(config_path)] if config_path else self._default_paths()

        merged: Dict[str, Any] = {}
        for p in paths:
            if p.exists():
                try:
                    data = json.loads(p.read_text())
                    self._deep_merge(merged, data)
                except (json.JSONDecodeError, OSError) as e:
                    raise RuntimeError(f"Failed to load config {p}: {e}")

        self._apply_env_overrides(merged)
        with self._lock:
            self._config = merged

    def _deep_merge(self, base: Dict, overrides: Dict):
        for key, value in overrides.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self, config: Dict):
        for key, value in os.environ.items():
            if key.startswith(ENV_PREFIX):
                config_key = key[len(ENV_PREFIX):].lower().replace("__", ".").split(".")
                target = config
                for part in config_key[:-1]:
                    if part not in target:
                        target[part] = {}
                    target = target[part]
                target[config_key[-1]] = self._coerce(value)

    def _coerce(self, value: str) -> Any:
        v = value.strip()
        if v.lower() in ("true", "yes", "1"):
            return True
        if v.lower() in ("false", "no", "0"):
            return False
        try:
            return int(v)
        except ValueError:
            pass
        try:
            return float(v)
        except ValueError:
            pass
        return v

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        with self._lock:
            target = self._config
            for k in keys:
                if isinstance(target, dict):
                    target = target.get(k)
                    if target is None:
                        return default
                else:
                    return default
            return target

    def get_all(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._config)

    def reload(self):
        self._load()
