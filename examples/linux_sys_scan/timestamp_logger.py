import time

class TimestampLogger:
    _instance = None
    _timestamp_logs = ""

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TimestampLogger, cls).__new__(cls)
        return cls._instance

    @classmethod
    def combine_timestamp_logs(self, command, command_output):
        self._timestamp_logs += f"""[{time.strftime('%Y-%m-%d %H:%M:%S')}] {command}\n\n{command_output}\n\n\n{"="*50}\n\n\n"""

    @classmethod
    def reset_timestamp_logs(self):
        self._timestamp_logs = ""

    @classmethod
    def get_logs(self):
        return self._timestamp_logs