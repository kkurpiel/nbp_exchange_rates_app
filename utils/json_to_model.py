from datetime import datetime
from typing import List
from models.rates import Rates
from models.tables import Tables

##### Konwertuje otrzymany JSON na obiekt modelu Tables #####
def json_to_model(data: dict) -> Tables:
    rates: List[Rates] = []

    for item in data["rates"]:
        rate = Rates(
            currency=item.get("currency"),
            code=item.get("code"),
            bid=item.get("bid"),
            ask=item.get("ask"),
            mid = item.get("mid")
        )
        rates.append(rate)

    return Tables(
        table = data.get("table"),
        no = data.get("no"),
        effectiveDate = datetime.strptime(data.get("effectiveDate"), "%Y-%m-%d"),
        tradingDate = datetime.strptime(data.get("tradingDate"), "%Y-%m-%d") if "tradingDate" in data else None,
        rates = rates
    )
