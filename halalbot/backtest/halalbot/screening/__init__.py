"""
Screening utilities for assessing halal compliance.

This package contains abstractions for retrieving financial statements and
classifying them according to Islamic finance principles.  Use
``data_gateway`` to fetch fundamental data from external providers and
``halal_rules`` to load lists of halal approved crypto assets and
prohibited features from configuration.
"""

from .data_gateway import DataGateway, FMPGateway  # noqa: F401
from .halal_rules import load_rules  # noqa: F401
from .advanced_screener import AdvancedHalalScreener  # noqa: F401