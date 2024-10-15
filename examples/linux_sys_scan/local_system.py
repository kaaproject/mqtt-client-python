import platform
import cpuinfo
import psutil
import GPUtil
import subprocess

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
    average_temp = sum(temp_values) / len(temp_values)
    return {
        'cpu_per_core_temp': cpu_per_core_temp,
        'cpu_average_temp': average_temp
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
        gpu = gpus[0]  # Get the first GPU
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
        "system": platform.system(),
        "release": platform.release(),
        "node_name": platform.node(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_model": cpu_details['brand_raw'],
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "disk_space_gb": bytes_to_gbs(disk_info.total),
        "memory_gb": bytes_to_gbs(memory_info.total),
    }

    print(f'Result: {result}')
    return result

def get_machine_gpu_metadata():
    gpu_info = get_machine_gpu()
    if gpu_info:
        return {
            "gpu_name": gpu_info['name'],
            "gpu_driver": gpu_info['driver'] if not gpu_info['is_integrated'] else None,
            "gpu_memory_mb": gpu_info['memory'] if not gpu_info['is_integrated'] else None
        }
    return {
        "gpu_name": "not found"
    }
