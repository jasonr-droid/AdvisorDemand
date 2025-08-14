"""
Data adapters for government data sources
"""

from .cbp import CBPAdapter
from .qcew import QCEWAdapter
from .sba import SBAAdapter
from .sam import SAMAdapter
from .usaspending import USASpendingAdapter
from .licenses import LicensesAdapter
from .opencorporates import OpenCorporatesAdapter
from .bfs import BFSAdapter

__all__ = [
    'CBPAdapter',
    'QCEWAdapter', 
    'SBAAdapter',
    'SAMAdapter',
    'USASpendingAdapter',
    'LicensesAdapter',
    'OpenCorporatesAdapter',
    'BFSAdapter'
]
