import datetime
import logging
import math
import random
import time
import uuid

from kaa.client.command import Command, CommandResponse
from kaa.client.configuration import Configuration, ConfigurationStatusResponse
from kaa.client.kaa_mqtt_client import KaaMqttClient

logger = logging.getLogger(__name__)

class Vehicle:
    def __init__(self, client: KaaMqttClient, metadata: dict, routes=None):
        self.is_running = True
        self.kaa_client = client
        self.time = time.time()
        self.trip_start_time = None
        self.config = {
            "maxSpeed": 185,
            "maxRange": 555,
            "maintenanceInterval": 15000,
            "climateSetpoint": 21
        }

        self.mileage = random.randint(0, 200)
        self.routes = routes or []
        self.route_point = -1

        self.engine = 1
        self.trunk = 1
        self.windows = 1
        self.lock = 1
        self.lights = 0
        self.beep = 0
        self.climate = 1

        self.statuses = ['engine', 'trunk', 'windows', 'lock', 'lights', 'beep', 'climate']

        self.range = self.config['maxRange']
        self.metadata = metadata
        self.define_handlers()

    def define_handlers(self):
        @self.kaa_client.configuration_handler()
        def update_config(c: Configuration) -> ConfigurationStatusResponse:
            for k, v in c.config.items():
                self.config[k] = v
            return ConfigurationStatusResponse(c.config_id, 200)

        @self.kaa_client.command_handler("remote_toggle")
        def remote_toggle(command: Command) -> CommandResponse:
            try:
                for key, value in command.payload.items():
                    payload_value = int(value)
                    setattr(self, key, payload_value)
                    self.log_command(key, payload_value)
                    return CommandResponse(command, status_code=200)
            except Exception as error:
                logger.error(
                    f"Invalid command payload [{error}] [{command.to_dict()}]")

        @self.kaa_client.command_handler("change_trip_status")
        def trip_status(command: Command) -> CommandResponse:
            if 'trip_status' in command.payload:
                end_trip = command.payload['trip_status'] == 'end'
                self.metadata['trip_active'] = not end_trip
                if end_trip and self.trip_start_time is not None:
                    self.kaa_client.publish_data_collection({
                        'trip': {
                            'start_date': self.trip_start_time,
                            'end_date': datetime.datetime.now().isoformat(),
                            'distance': random.randint(10, 30)
                        }
                    })
                else:
                    self.trip_start_time = datetime.datetime.now().isoformat()
                self.kaa_client.publish_metadata(self.metadata)
            return CommandResponse(command, status_code=200)

    def get_device_metadata(self):
        self.metadata["lastMaintenance"] = str(datetime.datetime.now())
        self.metadata["serial"] = str(uuid.uuid4())
        return self.metadata

    """
    Generates tiers data
    """

    def get_tiers_data(self):
        if self.engine == 0:
            return {}
        else:
            front_tires = random.uniform(2.35, 2.4)
            rear_tires = random.uniform(2.2, 2.3)

            return {
                'tiers': {
                    'front_left': front_tires,
                    'front_right': front_tires,
                    'back_left': rear_tires,
                    'back_right': rear_tires
                }
            }

    """
    Generates hill assist data
    """

    def get_hill_assist_data(self):
        if self.engine == 0:
            return {}
        else:
            return {
                'gyro_x': random.randint(0, 20),
                'gyro_y': random.randint(0, 15),
                'gyro_z': random.randint(0, 5),
            }

    def get_climate_data(self):
        if self.engine == 0:
            return {}
        else:
            now = datetime.datetime.now()
            return {
                'climate_temperature': (self.config['climateSetpoint'] - 3) + 3 * math.cos(
                    now.minute + now.second / 60.0)
            }

    """
    Generates engine data
    """

    def get_engine_data(self):
        if self.engine == 0:
            return {}
        else:
            self.mileage += random.randint(10, 40)
            self.range -= random.randint(1, 5)

            if self.range < 0:
                self.range = self.config['maxRange']
                self.kaa_client.publish_data_collection({
                    'log': {
                        'message': 'Max range exceeded. Vehicle filled up',
                        'location': 'UK, London'
                    }
                })

            maintenance_in = self.config['maintenanceInterval'] - self.mileage

            return {
                'speed': random.randint(40, 110),
                'rpm': random.randint(600, 2000),
                'mileage': self.mileage,
                'range': self.range,
                'maintenance_in': 0 if maintenance_in < 0 else maintenance_in,
                'engine_temperature': random.randint(62, 95)
            }

    """
    Generates location data
    """

    def get_location_data(self):
        if self.engine == 0:
            return {}
        else:
            next_point = [self.metadata['lat'], self.metadata['lon']]

            try:
                self.route_point += 1
                next_point = self.routes[self.route_point]
            except:
                self.route_point = 0
                next_point = self.routes[self.route_point]

            return {
                'location': {
                    'lat': next_point[0],
                    'lon': next_point[1]
                }
            }

    """
    Generates telemetry data sample.
    """

    def get_data_sample(self):
        data = {}

        for name in self.statuses:
            data[f"{name}_status"] = getattr(self, name)

        data.update(self.get_tiers_data())
        data.update(self.get_engine_data())
        data.update(self.get_hill_assist_data())
        data.update(self.get_location_data())
        data.update(self.get_climate_data())

        return data

    """
    Logs command as telemetry
    """

    def log_command(self, key: str, value: int):
        messages = {
            'engine': {0: 'Engine off', 1: 'Engine on'},
            'trunk': {0: 'Trunk closed', 1: 'Trunk opened'},
            'windows': {0: 'Windows closed', 1: 'Windows opened'},
            'lock': {0: 'Car locked', 1: 'Car opened'},
            'beep': {0: 'Horn sound off', 1: 'Horn on'},
            'climate': {0: 'AC off', 1: 'AC on'}
        }
        if key in messages:
            self.kaa_client.publish_data_collection({
                'log': {
                    'message': messages[key][value],
                    'location': 'UK, London'
                }
            })