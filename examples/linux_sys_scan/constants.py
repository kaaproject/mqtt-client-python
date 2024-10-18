import logging
import os

logger = logging.getLogger(__name__)
kaa_kpc_host = f"mqtt.{os.environ.get('DEFAULT_KPC_HOST')}"
kaa_kpc_port = int(os.environ.get("DEFAULT_KPC_PORT", '1883'))
app_version = os.environ.get("APPLICATION_VERSION")
token = os.environ.get("ENDPOINT_TOKEN")