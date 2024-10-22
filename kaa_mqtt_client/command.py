import json
import logging
from typing import List, Union, Any, Dict, Callable

logger = logging.getLogger(__name__)


class Command:
    command_id: Union[int, str] = None
    payload: Dict[str,Any] = None

    def __init__(self, **kwargs):
        self.command_id = kwargs.get("id")
        self.payload = kwargs.get("payload")

    def to_dict(self) -> dict:
        return {
            "id": self.command_id,
            "payload": self.payload
        }


class CommandResponse:
    command_id: Union[int, str] = None
    status_code: int = None
    reason_phrase: str = None
    payload: Dict[str, Any] = None

    def __init__(self, command: Command, status_code: int, reason_phrase: str = None, payload: str = None):
        self.command_id = command.command_id
        self.status_code = status_code
        self.payload = payload
        self.reason_phrase = reason_phrase

    def to_dict(self) -> dict:
        data = {
            "id": self.command_id,
            "statusCode": self.status_code,
            "reasonPhrase": self.reason_phrase,
            "payload": self.payload
        }
        return {k: v for k, v in data.items() if v}

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class BatchCommandsResponse(object):
    commands: List[CommandResponse]

    def __init__(self, commands: List[CommandResponse] = None):
        if commands:
            self.commands = commands
        else:
            self.commands = []

    def to_json(self) -> str:
        return json.dumps([command.to_dict() for command in self.commands])


def apply_commands(commands: List[Command], func: Callable[[Command], CommandResponse]) -> BatchCommandsResponse:
    if not commands:
        return BatchCommandsResponse()
    commands_responses = []
    for command in commands:
        try:
            commands_responses.append(func(command))
        except Exception as e:
            logger.error(f"Failed to execute command {e}")
            commands_responses.append(CommandResponse(command, 500, reason_phrase=str(e)))
    return BatchCommandsResponse(commands_responses)
