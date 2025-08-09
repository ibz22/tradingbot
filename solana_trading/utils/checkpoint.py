import json
from datetime import datetime
from typing import Any, Dict, Optional

class DevelopmentCheckpoint:
    @staticmethod
    def save_progress(phase: str, completed_tasks: list[str], current_state: Dict[str, Any]) -> None:
        ckpt = {
            "phase": phase,
            "completed_tasks": completed_tasks,
            "timestamp": datetime.now().isoformat(),
            "current_state": current_state,
        }
        with open("CHECKPOINT.json", "w", encoding="utf-8") as f:
            json.dump(ckpt, f, indent=2)

    @staticmethod
    def load_progress() -> Optional[Dict[str, Any]]:
        try:
            with open("CHECKPOINT.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None
