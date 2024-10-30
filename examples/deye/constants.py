import os


kaa_kpc_host = os.environ.get('DEFAULT_KPC_HOST') or "mqtt.cloud.kaaiot.com"
if kaa_kpc_host.startswith("mqtt://"):
    kaa_kpc_host = kaa_kpc_host[len("mqtt://"):]

kaa_kpc_port = int(os.environ.get("DEFAULT_KPC_PORT", '1883'))
app_version = os.environ.get("APPLICATION_VERSION")
token = os.environ.get("ENDPOINT_TOKEN")

ip = os.environ.get('IP')
serial_number = int(os.environ.get('SERIAL_NUMBER'))