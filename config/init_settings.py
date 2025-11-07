import json

def init_settings(path: str = "appsettings.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
