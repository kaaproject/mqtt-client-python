import json
import logging
import threading
import time

from examples.fleet_simulator.config import Config
from examples.fleet_simulator.vehicle import Vehicle
from kaa.client.kaa_mqtt_client import KaaMqttClient

logger = logging.getLogger(__name__)


def run_endpoint(app_version, kpc_host, kpc_port, token, metadata, routes_file, update_interval):
    kaa_client = KaaMqttClient(host=kpc_host, port=kpc_port, application_version=app_version, token=token)
    kaa_client.connect()
    routes = []
    if routes_file:
        routes = json.load(open(f'./data/{routes_file}'))
    vehicle = Vehicle(kaa_client, metadata, routes)
    logger.info(
        f"""
            Connect to kaa using:
            Host: [{kpc_host}]
            Port: [{kpc_port}]
            Application version name: [{app_version}]
            Token: [{token}]
        """
    )

    logger.info(f"Send device metadata [{vehicle.get_device_metadata()}]")
    kaa_client.publish_metadata(vehicle.get_device_metadata())
    while vehicle.is_running:
        logger.info("Send Vehicle data")
        data_sample = vehicle.get_data_sample()
        logger.info(f"{data_sample}")
        kaa_client.publish_data_collection(data_sample)
        time.sleep(update_interval)


def main():
    config = Config()
    for endpoint in config.endpoints:
        thread = threading.Thread(target=run_endpoint, args=(
            config.application_version,
            config.kpc_host,
            config.kpc_port,
            endpoint["token"],
            endpoint["metadata"],
            endpoint["routes_file"],
            config.update_interval
        ))
        thread.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    main()
