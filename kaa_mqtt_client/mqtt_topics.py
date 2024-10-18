import random


class KaaClientTopicsConfig:
    def __init__(self, application_version, token):
        self.token = token
        self.application_version = application_version

    def get_command_topic(self, name: str) -> str:
        return f"kp1/{self.application_version}/cex/{self.token}/command/{name}/status"

    def get_configuration_status_topic(self) -> str:
        return f"kp1/{self.application_version}/cmx/{self.token}/config/json/status"

    def get_configuration_status_reply_topic(self) -> str:
        return f"kp1/{self.application_version}/cmx/{self.token}/applied/json"

    def get_data_collection_topic(self, request_id: int = None) -> str:
        if not request_id:
            request_id = random.randint(1, 99)
        return f"kp1/{self.application_version}/dcx/{self.token}/json/{request_id}"

    def get_ota_configuration_status_topic(self) -> str:
        return f"kp1/{self.application_version}/cmx_ota/{self.token}/config/json/status"

    def get_ota_configuration_status_reply_topic(self, request_id: int = None) -> str:
        return f"kp1/{self.application_version}/cmx_ota/{self.token}/applied/json"

    def get_metadata_topic(self, request_id: int = None) -> str:
        if not request_id:
            request_id = random.randint(1, 99)
        return f"kp1/{self.application_version}/epmx/{self.token}/update/keys/{request_id}"

    def get_binary_token_topic(self, request_id: int = None) -> str:
        return f"kp1/{self.application_version}/bcx/{self.token}/token"

    def get_binary_token_status_topic(self, request_id: int = None) -> str:
        return f"kp1/{self.application_version}/bcx/{self.token}/token/status"

    @staticmethod
    def get_command_response_topic(command_topic, command_name: str) -> str:
        return f"{command_topic}".replace(f"command/{command_name}/status", f"result/{command_name}")
