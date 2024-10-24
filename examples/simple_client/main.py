import datetime
import logging
import os
import time
import uuid
import subprocess

from kaa_mqtt_client import KaaMqttClient, Command, CommandResponse, Configuration, ConfigurationResponse


SW_VERSION = "0.0.1"

logger = logging.getLogger(__name__)



class SimpleCounterClient:
    def __init__(self, client: KaaMqttClient, metadata: dict, update_interval: int = None):
        self.kaa_client = client
        self.time = time.time()
        self.config = dict()
        self.metadata = metadata
        self.counter = 0
        self.update_interval = update_interval
        self.define_handlers()
        self.is_running = True

    def define_handlers(self):
        @self.kaa_client.configuration_handler()
        def update_config(c: Configuration) -> ConfigurationResponse:
            for k, v in c.config.items():
                self.config[k] = v
            logger.info(f"Get new config: {self.config}")
            return ConfigurationResponse(c.config_id, 200, "applied")

        @self.kaa_client.ota_handler()
        def update_config(c: Configuration) -> ConfigurationResponse:
            for k, v in c.config.items():
                self.config[k] = v
            logger.info(f"Get new config: {self.config}")
            return ConfigurationResponse(c.config_id, 200, "applied")

        @self.kaa_client.command_handler("inc")
        def increment(command: Command) -> CommandResponse:
            inc = command.payload.get("increment")
            self.increment(inc)
            return CommandResponse(command, status_code=200, reason_phrase="DONE",
                                   payload={"current_inc": self.counter})

        @self.kaa_client.command_handler("reset")
        def reset(command: Command) -> CommandResponse:
            self.counter = 0
            return CommandResponse(command, status_code=200, reason_phrase="DONE")

        @self.kaa_client.command_handler("shell")
        def shell(command: Command) -> CommandResponse:
            result = subprocess.run(["bash", '-c', command.payload.get('cmd')], stdout=subprocess.PIPE)
            return CommandResponse(command, status_code=200, reason_phrase="DONE",
                                   payload=result.stdout.decode('utf-8')
                                   )

        @self.kaa_client.command_handler("upload_file")
        def handle_file_upload(command: Command) -> CommandResponse:
            return CommandResponse(command, status_code=200, reason_phrase="DONE",
                                   payload=f"file uploaded {command.payload}")

        @self.kaa_client.command_handler("get_config")
        def reset(command: Command) -> CommandResponse:
            self.counter = 0
            return CommandResponse(command, status_code=200, reason_phrase="DONE", payload=self.config)

        @self.kaa_client.command_handler("fail")
        def fail(command: Command) -> CommandResponse:
            raise Exception("Manually triggered exception to simulate kaa_mqtt_client side errors")

    def increment(self, inc: int = None):
        if inc is None:
            inc = self.config.get("default_increment", 1)
        self.counter += inc

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, metadata: dict):
        if not isinstance(metadata, dict):
            raise Exception("Not supported metadata format")
        if not hasattr(self, "_metadata"):
            self._metadata = metadata
            self._metadata["serial"] = str(uuid.uuid4())
        else:
            self._metadata.update(**metadata)
        self._metadata["lastMaintenance"] = str(datetime.datetime.now())
        self.publish_metadata()

    @property
    def counter(self):
        return self._counter

    @counter.setter
    def counter(self, value: int):
        self._counter = value
        # publish event based metric
        self.publish_data_sample()

    @property
    def data_sample(self):
        return {
            "counter": self.counter
        }

    def publish_data_sample(self):
        data = self.data_sample
        logger.info(f"Going to publish data sample: {data}")
        self.kaa_client.publish_data_collection(data)

    def publish_metadata(self):
        logger.info(f"Going to publish data sample: {self.metadata}")
        self.kaa_client.publish_metadata(self.metadata)

    def step(self):
        logger.info(f"Step counter={self._counter} config={self.config}")
        # publish periodic metric here
        self.increment()
        time.sleep(self.update_interval)


def run_endpoint(kpc_host, kpc_port, app_version, token, metadata, update_interval, path_to_bin_file = None):
    kaa_client = KaaMqttClient(host=kpc_host, port=kpc_port, application_version=app_version, token=token,
                               client_id='counter')

    kaa_client.connect()
    simple_counter_client = SimpleCounterClient(kaa_client, metadata, update_interval)
    logger.info(
        f"""
            Connect to kaa using:
            Host: [{kpc_host}]
            Port: [{kpc_port}]
            Application version name: [{app_version}]
            Token: [{token}]
        """
    )
    # logger.info(f"Send device metadata [{simple_counter_client.metadata}]")
    # kaa_client.publish_metadata(simple_counter_client.metadata)
    ota_config = Configuration(configId=SW_VERSION)
    kaa_client.publish_ota_config(ota_config)
    
    while kaa_client.bcx_token is None:
        time.sleep(1)

    if path_to_bin_file is not None:
        kaa_domain_url = kpc_host[len("mqtt."):]
        kaa_client.publish_binary_file(path_to_bin_file, kaa_domain_url)

    while simple_counter_client.is_running:
        simple_counter_client.step()


def main():
    kaa_kpc_host = os.environ.get("DEFAULT_KPC_HOST",  "mqtt.cloud.kaaiot.com")
    kaa_kpc_port = int(os.environ.get("DEFAULT_KPC_PORT", '1883'))
    app_version = os.environ.get("APPLICATION_VERSION")
    token = os.environ.get("ENDPOINT_TOKEN", "counter_token")
    run_endpoint(kaa_kpc_host, kaa_kpc_port, app_version, token, {"name": "simple counter v0"}, 120)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    main()
