from datetime import datetime
from json import JSONEncoder, loads
from typing import Any


class JSONencoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime):
            return str(o)
        return JSONEncoder.default(self, o)


async def json_encoder(raw_response: dict[str, Any]) -> Any:
    return loads(JSONencoder().encode(raw_response))
