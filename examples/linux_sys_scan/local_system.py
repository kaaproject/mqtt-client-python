import platform
import cpuinfo
import psutil
import GPUtil
import subprocess

from getmac import get_mac_address 
from constants import logger

def bytes_to_gbs(bytes):
    return bytes / (1024 ** 3)

def get_gpu_info():
    gpu_info = get_machine_gpu()
    return {
        "gpu_memory_used": gpu_info.memoryUsed if gpu_info and not gpu_info['is_integrated'] else None,
        "gpu_load": gpu_info.load if gpu_info and not gpu_info['is_integrated'] else None,
        "gpu_temperature": gpu_info.temperature if gpu_info and not gpu_info['is_integrated'] else None
    }

def get_cpu_temperature_info():
    cpu_per_core_temp = get_cpu_temperature()
    if cpu_per_core_temp is None:
        return {}
    temp_values = [float(temp) for temp in cpu_per_core_temp.values()]
    if temp_values:
        average_temp = sum(temp_values) / len(temp_values)
        return {
            'cpu_per_core_temp': cpu_per_core_temp,
            'cpu_average_temp': average_temp
        }

    return {
        'cpu_average_temp': 0
    }


def get_cpu_temperature():
    try:
        output = subprocess.check_output(["sensors"]).decode()
        return {
            f'cpu_core{index+1}_temp': line.split('+')[1].split('°')[0]
            for index, line in enumerate(output.split('\n')) if "temp" in line and "°C" in line
        }
    except Exception as e:
        logger.error(f"Error retrieving CPU temperature: {e}")
        return None

def get_integrated_gpu_name():
    try:
        if platform.system() == "Linux":
            gpu_info = subprocess.check_output("lspci | grep -E 'VGA|3D|Display|Graphics'", shell=True).decode()
            return gpu_info.split(":")[-1].strip() if gpu_info else None
    except Exception as e:
        logger.error(f"Error fetching GPU info: {e}")
    return None

def get_machine_gpu():
    gpus = GPUtil.getGPUs()
    if gpus:
        gpu = gpus[0]  
        return {
            "name": gpu.name,
            "driver": gpu.driver,
            "memory": gpu.memoryTotal,
            "memory_used": gpu.memoryUsed,
            "load": gpu.load * 100,
            "temperature": gpu.temperature,
            "is_integrated": False
        }
    else:
        integrated_gpu_name = get_integrated_gpu_name()
        return {"name": integrated_gpu_name, "is_integrated": True}

def get_machine_metadata():
    cpu_details = cpuinfo.get_cpu_info()
    disk_info = psutil.disk_usage('/')
    memory_info = psutil.virtual_memory()
    
    result = {
        "mac_address": get_mac_address(),
        "system": platform.system(),
        "release": platform.release(),
        "node_name": platform.node(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_model": cpu_details['brand_raw'],
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "disk_space_gb": round(bytes_to_gbs(disk_info.total) ,2),
        "ram_gb": round(bytes_to_gbs(memory_info.total), 2),
    }

    gpu_info = get_machine_gpu_metadata()
    if gpu_info:
        result = {**result, **gpu_info}

    print(f'Result: {result}')
    return result

def get_machine_gpu_metadata():
    gpu_info = get_machine_gpu()

    gpu_name = gpu_info.get("name")
    gpu_driver = gpu_info.get("driver")
    gpu_memory = gpu_info.get("memory")

    if gpu_driver is not None and gpu_memory is not None:
        return {
            "gpu_name": gpu_name,
            "gpu_driver": gpu_driver,
            "gpu_memory_mb": gpu_memory
        }
    elif gpu_name is not None:
        return {
            "gpu_name": gpu_name
        }
    else:
        return {
            "gpu_name": "not found"
        }


def get_system_data():
    battery = psutil.sensors_battery()
    battery_power = 0
    battery_plugged = False
    
    if battery:
        battery_power = battery.percent
        battery_plugged = battery.power_plugged

    return {
        "cpu_load": psutil.cpu_percent(interval=1),
        "disk_free": psutil.disk_usage('/').free,
        "ram_free": psutil.virtual_memory().available,
        "ram_total": psutil.virtual_memory().total,
        "bytes_sent": psutil.net_io_counters().bytes_sent,
        "bytes_recv": psutil.net_io_counters().bytes_recv,
        "battery_power": battery_power,
        "battery_plugged": battery_plugged,
        **get_gpu_info(),
        **get_cpu_temperature_info()
    }

