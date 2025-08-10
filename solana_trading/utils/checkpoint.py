import json
import os
from datetime import datetime
from typing import Any, Dict, Optional


def load_checkpoint(file_path: str, default_value: Any = None) -> Any:
    """
    Load checkpoint data from JSON file
    
    Args:
        file_path: Path to checkpoint file
        default_value: Default value if file doesn't exist
        
    Returns:
        Loaded data or default value
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default_value


def save_checkpoint(file_path: str, data: Any) -> None:
    """
    Save checkpoint data to JSON file
    
    Args:
        file_path: Path to checkpoint file
        data: Data to save
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)


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
