from dataclasses import dataclass, field
from datetime import datetime
from models.rates import Rates
from typing import Optional, List

@dataclass
class Tables:
    table: str
    no: str
    effectiveDate: datetime
    tradingDate: Optional[datetime] = None
    rates: List[Rates] = field(default_factory=list)