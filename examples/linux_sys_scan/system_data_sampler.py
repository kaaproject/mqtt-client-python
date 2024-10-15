
import psutil
from local_system import get_gpu_info, get_cpu_temperature_info

class SystemDataSampler:
    @staticmethod
    def get_system_data():
        return {
            "cpu_load": psutil.cpu_percent(interval=1),
            "disk_free": psutil.disk_usage('/').free,
            "ram_free": psutil.virtual_memory().available,
            "bytes_sent": psutil.net_io_counters().bytes_sent,
            "bytes_recv": psutil.net_io_counters().bytes_recv,
            "battery_power": psutil.sensors_battery().percent,
            "battery_plugged": psutil.sensors_battery().power_plugged,
            **get_gpu_info(),
            **get_cpu_temperature_info()
        }