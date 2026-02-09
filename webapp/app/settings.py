# webapp/app/settings.py
from dataclasses import dataclass
from pathlib import Path
import os

@dataclass(frozen=True)
class WebSettings:
    project_root: Path
    configs_dir: Path
    artifacts_dir: Path

    @staticmethod
    def load() -> "WebSettings":
        # rag/webapp/app/settings.py -> rag/webapp/app -> rag/webapp -> rag/
        root = Path(__file__).resolve().parents[2]
        # Go up one more level since we're in webapp/app/
        root = root.parent  # Now at rag/
        return WebSettings(
            project_root=root,
            configs_dir=root / "configs",
            artifacts_dir=root / "artifacts",
        )
