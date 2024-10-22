import json
import logging
from typing import Union, Dict, Any, Callable

logger = logging.getLogger(__name__)


class Configuration:
    config_id: Union[int, str]
    config: Dict[str, Any]

    def __init__(self, **kwargs):
        self.config_id = kwargs.get("configId")
        self.config = kwargs.get("config")

    def to_dict(self) -> Dict[str, Any]:
        config = {
            "configId": self.config_id,
            "config": self.config
        }
        return {k: v for k, v in config.items() if v}

    def to_json(self):
        return json.dumps(self.to_dict())


class ConfigurationResponse(object):
    config_id: str
    status_code: int
    reason_phrase: str

    def __init__(self, config_id: str, status_code: int = None, reason_phrase: str = None):
        self.config_id = config_id
        self.status_code = status_code
        self.reason_phrase = reason_phrase

    def to_dict(self) -> Dict[str, Any]:
        return {
            "configId": self.config_id,
            "statusCode": self.status_code,
            "reasonPhrase": self.reason_phrase
        }

    def to_json(self):
        return json.dumps(self.to_dict())


def apply_configuration(configuration: Configuration,
                        func: Callable[[Configuration], ConfigurationResponse]) -> ConfigurationResponse:
    try:
        return func(configuration)
    except Exception as e:
        logger.error(f"Failed to apply configuration: {e}")
        return ConfigurationResponse(configuration.config_id, 500, reason_phrase=str(e))
