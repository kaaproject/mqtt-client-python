import datetime
import logging
import os
import time
import uuid
import platform
import cpuinfo
import psutil
import GPUtil
import subprocess

from kaa_mqtt_client import KaaMqttClient

logger = logging.getLogger(__name__)


class SysScanClient:
    def __init__(self, client: KaaMqttClient, metadata: dict, update_interval: int = None):
        self.kaa_client = client
        self.time = time.time()
        self.config = dict()
        self.metadata = metadata
        self.update_interval = update_interval
        self.is_running = True

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
    def data_sample(self):
        disk = psutil.disk_usage('/')
        memory = psutil.virtual_memory()
        battery = psutil.sensors_battery()
        net = psutil.net_io_counters()
        
        system_timestamp = {
            "disk_util": disk.percent,
            "memory_util": memory.percent,
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "battery_power": battery.percent,
            "battery_plugged": battery.power_plugged
        }   
        
        gpu_info = get_machine_gpu()
        if gpu_info and not gpu_info.is_integrated:
            system_timestamp = {
                **system_timestamp,
                "memory_used": gpu_info.memoryUsed,
                "load": gpu_info.load,
                "temperature": gpu_info.temperature,
            }

        return system_timestamp

    def publish_data_sample(self):
        data = self.data_sample
        logger.info(f"Going to publish data sample: {data}")
        self.kaa_client.publish_data_collection(data)

    def publish_metadata(self):
        logger.info(f"Going to publish data sample: {self.metadata}")
        self.kaa_client.publish_metadata(self.metadata)

    def step(self):
        logger.info(f"Step config={self.config}")
        # publish periodic metric here
        self.publish_data_sample()
        time.sleep(self.update_interval)


def run_endpoint(kpc_host, kpc_port, app_version, token, metadata, update_interval):
    kaa_client = KaaMqttClient(host=kpc_host, port=kpc_port, application_version=app_version, token=token,
                               client_id='counter')
    kaa_client.connect()
    sys_scan_client = SysScanClient(kaa_client, metadata, update_interval)
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
    while sys_scan_client.is_running:
        sys_scan_client.step()

def bytes_to_gbs(bytes):
    return bytes / (1024 ** 3)

def get_integrated_gpu_name():
    current_os = platform.system()

    try:
        current_os = platform.system()
        if current_os == "Linux":
            gpu_info = subprocess.check_output(
                "lspci | grep -E 'VGA|3D|Display|Graphics'", shell=True
            ).decode()
            # Extract GPU name by splitting on ':' and returning the second part (name only)
            gpu_names = [line.split(":")[-1].strip() for line in gpu_info.splitlines()]
            if not gpu_names:  # If no GPU names were found
                return None 

            return gpu_names[0] # return first gpu_name from the array
    except Exception as e:
        print([f"Error fetching GPU info: {e}"])
        return None

def get_machine_gpu(): 
    gpus = GPUtil.getGPUs()

    if not gpus:
        integrated_gpu_name = get_integrated_gpu_name()
        if not integrated_gpu_name: 
            return None
        
        return {
            "name": integrated_gpu_name,
            "is_integrated": True
        }
    else:
        for i, gpu in enumerate(gpus):
            return {
                "name": gpu.name,
                "driver": gpu.driver,
                "memory": gpu.memoryTotal,
                "memory_used": gpu.memoryUsed,
                "load": gpu.load * 100,
                "temperature": gpu.temperature,
                "is_integrated": False
            }

def get_machine_metadata(): 
    cpu_details = cpuinfo.get_cpu_info()
    disk_info = psutil.disk_usage('/')

    cpu_count = psutil.cpu_count(logical=False)
    logical_cpu_count = psutil.cpu_count(logical=True)

    memory_info = psutil.virtual_memory()
     
    system_info = {
        "System": platform.system(),
        "Release": platform.release(),
        "Node Name": platform.node(),
        "Version": platform.version(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        "CPU Model": cpu_details['brand_raw'],
        "Physical Cores": cpu_count,
        "Logical Cores": logical_cpu_count,
        "Disk Space GB": bytes_to_gbs(disk_info.total),
        "Memory GB": bytes_to_gbs(memory_info.available)
    }
    gpu_info = get_machine_gpu()

    if gpu_info:
        gpu_metadata = {
            "GPU Name": gpu_info.name,
        }
    
        if not gpu_info.is_integrated:
            gpu_metadata.update({
                "GPU Driver": gpu_info.driver,
                "GPU Memory MB": gpu_info.memoryTotal,
            })
        system_info = {**system_info, **gpu_metadata}

    return system_info

def main():
    kaa_kpc_host = os.environ.get("DEFAULT_KPC_HOST",  "mqtt.cloud.kaaiot.com")
    kaa_kpc_port = int(os.environ.get("DEFAULT_KPC_PORT", '1883'))
    app_version = os.environ.get("APPLICATION_VERSION")
    token = os.environ.get("ENDPOINT_TOKEN", "counter_token")
    metadata = get_machine_metadata()
    update_interval_seconds = 120

    run_endpoint(kaa_kpc_host, kaa_kpc_port, app_version, token, metadata, update_interval_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    main()


