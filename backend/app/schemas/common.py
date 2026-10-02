from decimal import Decimal
from typing import Annotated

from pydantic import PlainSerializer

# Decimal in Python (exact math), plain JSON number on the way out.
# Without this, Pydantic would send decimals as strings like "12.50".
Money = Annotated[
    Decimal,
    PlainSerializer(float, return_type=float, when_used="json"),
]
