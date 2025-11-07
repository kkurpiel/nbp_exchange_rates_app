from dataclasses import dataclass
from typing import Optional

@dataclass
class Rates:
    currency: str
    code: str
    mid: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None