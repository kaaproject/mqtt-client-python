import json
import logging
import uuid
import requests
from functools import wraps
from typing import Callable, Any

import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTTMessage, Client as MqttClient

from kaa_mqtt_client.command import Command, CommandResponse, apply_commands
from kaa_mqtt_client.configuration import Configuration, ConfigurationResponse
from kaa_mqtt_client.mqtt_topics import KaaClientTopicsConfig

logger = logging.getLogger(__name__)


class KaaMqttClient(object):
    bcx_token: str = None

    def __init__(self, host, port, application_version, token, client_id=None,
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

    def publish_ota_config(self, config: Configuration) -> None:
        if not isinstance(config, Configuration):
            raise TypeError(f"{type(config)} in not type of Configuration")
        logger.info(f"Publish version {config.to_json()}")
        result = self.client.publish(topic=self.topics.get_ota_configuration_status_reply_topic(),
                                     payload=config.to_json())
        self._check_send_result(result)

    def get_binary_upload_token(self):
        self.client.publish(topic=self.topics.get_binary_token_topic(),
                            payload=None)

    def add_bcx_token_handler(self, client: MqttClient, userdata: Any, message: MQTTMessage):
        token = json.loads(message.payload.decode('utf-8'))
        self.bcx_token = token.get('token')

    def publish_binary_file(self, file_name: str, kaa_domain_url="cloud.kaaiot.com"):
        with open(file_name, 'rb') as f:
            data = f.read()

        logger.info(f"Uploading file {file_name}")

        binary_data_url = f"https://{kaa_domain_url}/bcx/api/v1/binary-data"
        res = requests.post(
            url=binary_data_url,
            headers={
                "X-Auth-Token": self.bcx_token,
                "Content-Type": 'application/octet-stream'
            },
            params={
                "name": file_name.replace("/", "_")
            },
            data=data
        )


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
        self.get_binary_upload_token()
        self.client.message_callback_add(self.topics.get_binary_token_status_topic(), self.add_bcx_token_handler)
        self.client.on_message = self.on_message
        self.client.loop_start()

    def _check_send_result(self, result):
        if result.rc != 0:
            logger.error("Unable to send data to platform try to reconnect")
            self.connect()

    def configuration_handler(self):
        def decorator(func: Callable[[Configuration], ConfigurationResponse]):
            @wraps(func)
            def _handle_inner(client: MqttClient, userdata: Any, message: MQTTMessage):
                logger.info(f"Received configuration: [{message.topic}] []")
                configuration_str = message.payload.decode('utf-8')
                configuration = Configuration(**json.loads(configuration_str))
                configuration_response = func(configuration)
                logger.info(f"Processed configuration request: {configuration_response.to_dict()}")
                response_topic = self.topics.get_configuration_status_reply_topic()
                client.publish(response_topic, configuration_response.to_json())
            self.add_configuration_handler(_handle_inner)
            return _handle_inner
        return decorator

    def ota_handler(self):
        def decorator(func: Callable[[Configuration], ConfigurationResponse]):
            @wraps(func)
            def _handle_inner(client: MqttClient, userdata: Any, message: MQTTMessage):
                logger.info(f"Received ota configuration: [{message.topic}] []")
                configuration_str = message.payload.decode('utf-8')
                configuration = Configuration(**json.loads(configuration_str))
                configuration_response = func(configuration)
                logger.info(f"Processed configuration request: {configuration_response.to_dict()}")
                response_topic = self.topics.get_ota_configuration_status_reply_topic()
                client.publish(response_topic, configuration_response.to_json())
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