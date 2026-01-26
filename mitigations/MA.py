from typing import Dict, Iterable, Any


def update_card_limit_hardened(data: Dict[str, Any], allowed_fields: Iterable[str]) -> None:
    allowed = set(allowed_fields)
    unexpected = set((data or {}).keys()) - allowed
    if unexpected:
        raise ValueError(f"Invalid field(s): {', '.join(sorted(unexpected))}. Allowed: {', '.join(allowed_fields)}")
