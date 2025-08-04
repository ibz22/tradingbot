"""
Utilities for loading halal screening rules from configuration.

Halal compliance rules evolve over time and should be easy to update by
non‑developers.  By moving the lists of approved cryptocurrencies and
prohibited features into a YAML file, stakeholders can add or modify
classifications without changing the Python source code.  This module
provides a single ``load_rules`` function that reads the rules from a
specified YAML file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def load_rules(config_path: str) -> Dict[str, Any]:
    """Load halal crypto and prohibited feature definitions from a YAML config.

    The YAML file should contain two top level keys:

    ``halal_crypto``
        A mapping of trading pairs to metadata describing why they are
        considered permissible and their relative risk/utility.

    ``prohibited_features``
        A mapping of categories to explanatory text that describes why a
        particular feature or business activity is disallowed.

    Parameters
    ----------
    config_path:
        Path to the YAML configuration file.

    Returns
    -------
    Dict[str, Any]
        A dictionary with two keys: ``halal_crypto`` and
        ``prohibited_features``.
    """
    cfg_path = Path(config_path)
    if not cfg_path.exists():
        return {"halal_crypto": {}, "prohibited_features": {}}
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        halal_crypto = data.get("halal_crypto", {})
        prohibited_features = data.get("prohibited_features", {})
        return {
            "halal_crypto": halal_crypto,
            "prohibited_features": prohibited_features,
        }
    except Exception:
        return {"halal_crypto": {}, "prohibited_features": {}}
