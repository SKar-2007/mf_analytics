import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    _instance: Optional["Config"] = None
    _data: Dict[str, Any] = {}

    def __new__(cls, path: Optional[str] = None) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, path: Optional[str] = None) -> None:
        if self._data:
            return
        config_path = path or os.getenv("BLUESTOCK_CONFIG", "")
        if not config_path:
            config_path = str(Path(__file__).resolve().parent / "config.yaml")
        with open(config_path) as f:
            self._data = yaml.safe_load(f)
        self._base_dir = Path(__file__).resolve().parent.parent

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def resolve(self, *keys: str) -> Any:
        val: Any = self._data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return None
        return val

    def path(self, *keys: str) -> Path:
        rel = self.resolve(*keys)
        return self._base_dir / rel if rel else self._base_dir

    @property
    def raw_dir(self) -> Path:
        return self.path("paths", "raw_data")

    @property
    def processed_dir(self) -> Path:
        return self.path("paths", "processed_data")

    @property
    def db_path(self) -> Path:
        return self.path("paths", "database")

    @property
    def charts_dir(self) -> Path:
        return self.path("paths", "charts")

    @property
    def reports_dir(self) -> Path:
        return self.path("paths", "reports")

    @property
    def schema_path(self) -> Path:
        return self.path("paths", "schema")

    @property
    def dataset_path(self, name: str) -> Path:
        fname = self.resolve("datasets", name)
        return self.raw_dir / fname if fname else self.raw_dir

    def dataset_path_for(self, name: str) -> Path:
        fname = self.resolve("datasets", name)
        return self.raw_dir / fname if fname else self.raw_dir

    def schemes(self) -> Dict[str, int]:
        return self.resolve("live_nav", "schemes") or {}

    def scorecard_weights(self) -> Dict[str, float]:
        return self.resolve("analytics", "scorecard_weights") or {}


config = Config()
