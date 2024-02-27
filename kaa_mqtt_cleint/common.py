import re
from typing import Generic, Type, TypeVar, List


def to_snake_case(field_name: str) -> str:
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', field_name).lower()


def to_dict(obj):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = to_dict(v)
        return data
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [to_dict(v) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, to_dict(value))
                     for key, value in obj.__dict__.items()
                     if not callable(value) and not key.startswith('_')])
        return data
    else:
        return obj


T = TypeVar('T')


class KaaEntityResponse(Generic[T]):
    payload: T

    def __init__(self, base_class: Type[T], payload: dict):
        if isinstance(payload, base_class):
            self.payload = payload
        elif isinstance(payload, dict):
            self.payload = base_class(**payload)


class KaaEntitiesResponse(Generic[T]):
    data: List[T]
    count: int
    page: int
    page_size: int

    def __init__(self, base_class: Type[T], data: List[dict], **kwargs):
        if not isinstance(data, list):
            raise Exception(f"Unexpected response format")

        self.data = [
            base_class.of(item)
            for item in data
        ]

        for k, v in kwargs.items():
            attr = to_snake_case(k)
            setattr(self, attr, v)
