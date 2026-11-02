from typing import Any, TypedDict


class MLUEState(TypedDict, total=False):
    question: str
    route: str
    result: dict[str, Any]
    answer: str
    error: str