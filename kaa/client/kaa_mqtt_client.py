import json
import logging
import uuid
from functools import wraps
from typing import Callable, Any

import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTTMessage, Client as MqttClient

from kaa.client.command import Command, CommandResponse, BatchCommandsResponse, apply_commands
from kaa.client.configuration import Configuration, ConfigurationStatusResponse
from kaa.client.mqtt_topics import KaaClientTopicsConfig

logger = logging.getLogger(__name__)


class KaaMqttClient(object):
    def __init__(self, host, port, application_version, token, client_id = None,
                 on_message: Callable[[mqtt.Client, Any, MQTTMessage], None] = None):
        self.topics = KaaClientTopicsConfig(application_version, token)
        self.host = host
        self.port = port
        self.token = token
        self.application_version = application_version
        self.on_message = on_message or self.on_message_default
        self.client_id = client_id or str(uuid.uuid4())
        # start mqtt
        self.client = mqtt.Client(client_id=client_id)
        self.client.on_message = self.on_message

    def publish_metadata(self, payload: dict) -> None:
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        if not isinstance(payload, str):
            raise Exception("Not supported payload type")
        result = self.client.publish(topic=self.topics.get_metadata_topic(), payload=payload)
        self._check_send_result(result)

    def publish_data_collection(self, payload: dict) -> None:
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        if not isinstance(payload, str):
            raise Exception("Not supported payload type")
        topic = self.topics.get_data_collection_topic()
        result = self.client.publish(topic=topic, payload=payload)
        self._check_send_result(result)

    def add_configuration_handler(self, handler: Callable[[mqtt.Client, Any, MQTTMessage], None]) -> None:
        self.client.message_callback_add(self.topics.get_configuration_status_topic(), handler)

    def add_command_handler(self, command_name: str, handler: Callable[[mqtt.Client, Any, MQTTMessage], None]) -> None:
        self.client.message_callback_add(self.topics.get_command_topic(command_name), handler)

    def connect(self):
        self.client.connect(self.host, self.port, 60)
        self.client.on_message = self.on_message
        self.client.loop_start()

    def _check_send_result(self, result):
        if result.rc != 0:
            logger.error("Unable to send data to platform try to reconnect")
            self.connect()

    def configuration_handler(self):
        def decorator(func: Callable[[Configuration], ConfigurationStatusResponse]):
            @wraps(func)
            def _handle_inner(client: MqttClient, userdata: Any, message: MQTTMessage):
                logger.info(f"Received configuration: [{message.topic}] []")
                configuration_str = message.payload.decode('utf-8')
                configuration = Configuration(**json.loads(configuration_str))
                configuration_response= func(configuration)
                logger.info(f"Processed configuration request: {configuration_response.to_dict()}")
            self.add_configuration_handler(_handle_inner)
            return _handle_inner
        return decorator

    def command_handler(self, command_name: str):
        def decorator(func: Callable[[Command], CommandResponse]):
            @wraps(func)
            def _handle_inner(client: MqttClient, userdata: Any, message: MQTTMessage):
                logger.info(f"Received command: [{message.topic}] []")
                commands_payload_str = message.payload.decode('utf-8')
                response_topic = self.topics.get_command_response_topic(message.topic, command_name)
                commands = [Command(**c) for c in json.loads(commands_payload_str)]
                commands_responses = apply_commands(commands, func)
                client.publish(response_topic, commands_responses.to_json())
            self.add_command_handler(command_name, _handle_inner)
            return _handle_inner
        return decorator

    @staticmethod
    def on_message_default(client: mqtt.Client, userdata: Any, message: MQTTMessage):
        logger.info(f"Message received: topic [{message.topic}] body [{str(message.payload.decode('utf-8'))}]")