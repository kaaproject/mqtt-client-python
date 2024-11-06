import time
import datetime

from constants import ip, serial_number
from kaa_mqtt_client import KaaMqttClient, Command, CommandResponse
from inverter import get_timestamp
from pysolarmanv5 import PySolarmanV5


class DeyeClient:
    def __init__(self, client: KaaMqttClient, metadata:dict, update_interval: int = 120):
        self.kaa_client = client
        self.metadata = metadata
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
        else:
            self._metadata.update(**metadata)
        self._metadata["lastMaintenance"] = str(datetime.datetime.now())
        self.publish_metadata()


    def define_handlers(self):
        @self.kaa_client.command_handler("deye_write")
        def execute_deye_command(command: Command) -> CommandResponse:
            register_list = command.payload['settings']
            print(register_list)
            response_object = {}

            for register_item in register_list:
                pysolarman_instance = PySolarmanV5(address=ip, serial=serial_number)
                register_id = int(register_item["register"])
                new_register_value = int(register_item["value"])
                amount_of_values_to_read = 1
                initial_register_value = None
                updated_register_value = None
                
                try:
                    initial_register_value = pysolarman_instance.read_holding_register_formatted(register_id, amount_of_values_to_read)
                    pysolarman_instance.write_multiple_holding_registers(register_id, [new_register_value])
                    updated_register_value = pysolarman_instance.read_holding_register_formatted(register_id, amount_of_values_to_read)
                    
                    if initial_register_value is None or updated_register_value is None or new_register_value != int(updated_register_value):
                        raise Exception("Client could not write the required value.")
                    
                    response_message = f"Success: Value '{new_register_value}' written to register '{register_id}'."
                    response_object[register_id] = response_message
                    print(response_message)
                except Exception as e:
                    pysolarman_instance.write_multiple_holding_registers(register_id, [initial_register_value])
                    response_message = f"Error: Value '{new_register_value}' for register '{register_id}' is invalid. Skipping... \nReason: {str(e)}"
                    response_object[register_id] = response_message
                    print(response_message)
                    continue
                finally:
                    pysolarman_instance.disconnect()
            
            return CommandResponse(command=command, status_code=200, reason_phrase="DONE", payload=response_object)
        
        @self.kaa_client.command_handler("deye_read")
        def read_deye_value(command: Command) -> CommandResponse:
            register_list = command.payload['settings']
            response_object = {}

            for register_item in register_list:
                pysolarman_instance = PySolarmanV5(address=ip, serial=serial_number)
                register_id = int(register_item["register"])
                amount_of_values_to_read = 1
                    
                try:
                    register_value = pysolarman_instance.read_holding_register_formatted(register_id, amount_of_values_to_read)
                    
                    if register_value is None:
                        raise Exception("Client could not read the required register.")
                    
                    response_message = f"Success: Value of register_id '{register_id}' is '{register_value}'"
                    response_object[register_id] = response_message
                    print(response_message)
                except Exception as e:
                    response_message = f"Error: register_id of '{register_id}' is invalid. Skipping... \nReason: {str(e)}"
                    response_object[register_id] = response_message
                    print(response_message)
                    continue
                finally:
                    pysolarman_instance.disconnect()
                
            return CommandResponse(command=command, status_code=200, reason_phrase="DONE", payload=response_object)


    def publish_metadata(self):
        self.kaa_client.publish_metadata(self.metadata)


    def step(self):
        data_sample = get_timestamp()
        self.publish_data_sample(data_sample)
        time.sleep(self.update_interval)


    def publish_data_sample(self, data):
        self.kaa_client.publish_data_collection(data)
        time.sleep(1)
