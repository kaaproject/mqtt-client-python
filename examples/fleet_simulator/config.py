import os

import yaml


class Config(object):
    def __init__(self, config=f"{os.path.dirname(os.path.realpath(__file__))}/config/config.yaml"):
        self.config_path = config
        self.config = self.load()
        self.kpc_host = os.environ.get("DEFAULT_KPC_HOST", self.config["kpc_host"])
        self.kpc_port = os.environ.get("DEFAULT_KPC_PORT", int(self.config["kpc_port"]))
        self.application_version = os.environ.get("APPLICATION_VERSION", self.config["application_version"])
        self.update_interval = int(os.environ.get('DEFAULT_UPDATE_INTERVAL', self.config['update_interval']))
        self.endpoints = self.config["endpoints"]

    def load(self):
        with open(self.config_path) as config_file:
            config = yaml.safe_load(config_file)
            return config
