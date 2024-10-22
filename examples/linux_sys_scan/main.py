import logging
import time
import subprocess
import uuid
import datetime

from timestamp_logger import TimestampLogger
from kaa_mqtt_client import KaaMqttClient, Command, CommandResponse, Configuration, ConfigurationResponse
from local_system import get_machine_metadata, get_system_data
from docker_manager import DockerManager
from constants import logger, kaa_kpc_port, kaa_kpc_host, app_version, token
from dashboard import initialize_dashboards

class SysScanClient:
    def __init__(self, client: KaaMqttClient, metadata:dict, docker_manager_instance: DockerManager, update_interval: int = 120):
        self.kaa_client = client
        self.metadata = metadata
        self.docker_manager_instance = docker_manager_instance
        self.update_interval = update_interval
        self.is_running = True
        self.define_handlers()

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

    def publish_metadata(self):
        logger.info(f"Going to publish data sample: {self.metadata}")
        self.kaa_client.publish_metadata(self.metadata)

    def define_handlers(self):
        @self.kaa_client.command_handler("LINUX_COMMAND")
        def execute_linux_command(command: Command) -> CommandResponse:
            linux_command = command.payload.get("command")
            try:
                result = subprocess.run(linux_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                command.payload = {"command_output": result.stdout}
                TimestampLogger.combine_timestamp_logs(linux_command, result.stdout)
                return CommandResponse(command, status_code=200)
            except subprocess.CalledProcessError as e:
                logger.error(f"Command execution failed: {e}")
                TimestampLogger.combine_timestamp_logs(linux_command, f"Command execution failed: {e}")
                return CommandResponse(command, status_code=500)
            finally:
                self.send_timestamp_logs()

        @self.kaa_client.configuration_handler()
        def configuration(conf: Configuration) -> ConfigurationResponse:
            logger.info(f'Config: {conf.config}')
            docker_changes = self.docker_manager_instance.detect_changes(conf.config)

            try:
                self.docker_manager_instance.apply_docker_changes(docker_changes)
                return ConfigurationResponse(conf.config_id, status_code=200, reason_phrase="Success")
            except Exception as e:
                logger.error(f'Configuration handler error: {e}')
                return ConfigurationResponse(conf.config_id, status_code=500, reason_phrase=f"ERROR: '{e}'")
            finally:
                self.send_timestamp_logs()

    def step(self):
        logger.info("Publishing periodic metrics")
        data_sample = get_system_data()
        self.publish_data_sample(data_sample)
        time.sleep(self.update_interval)

    def publish_data_sample(self, data):
        logger.info(f"Publishing data sample: {data}")
        self.kaa_client.publish_data_collection(data)
        time.sleep(1)

    def send_timestamp_logs(self):
        logs = TimestampLogger.get_logs()
        if logs:
            logger.info(f"SENDING LOGS: {logs}")
            self.publish_data_sample({"console_logs": logs})
            TimestampLogger.reset_timestamp_logs()
        else:
            logger.error(f"ERROR. LOGS WERE EMPTY")

def run_endpoint(kpc_host, kpc_port, app_version, token, metadata, update_interval):
    kaa_client = KaaMqttClient(host=kpc_host, port=kpc_port, application_version=app_version, token=token, client_id='counter')
    kaa_client.connect()

    sys_scan_client = SysScanClient(kaa_client, metadata, DockerManager(), update_interval)

    logger.info(f"Connected to Kaa at {kpc_host}:{kpc_port} with app version {app_version} and token {token}")
    while sys_scan_client.is_running:
        sys_scan_client.step()

def main():
    initialize_dashboards()
    metadata = get_machine_metadata()
    run_endpoint(kaa_kpc_host, kaa_kpc_port, app_version, token, metadata, 120)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    main()
