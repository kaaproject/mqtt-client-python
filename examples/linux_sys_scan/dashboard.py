import json
from constants import app_version, app_name, tenant_id

json_file_paths = ['./dashboards/home.json', './dashboards/device_overview.json', './test.json']

def initialize_dashboards():
    def replace_placeholders(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    obj[key] = value.replace('{APP_NAME}', app_name).replace('{APP_VERSION}', app_version).replace('{TENANT_ID}', tenant_id)
                else:
                    replace_placeholders(value) 
        elif isinstance(obj, list):
            for item in obj:
                replace_placeholders(item)

    for json_file_path in json_file_paths:
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)

            if isinstance(data, dict):
                replace_placeholders(data)
            else:
                print(f"Warning: {json_file_path} does not contain a JSON object.")

            with open(json_file_path, 'w') as file:
                json.dump(data, file, indent=4)

            print(f"Placeholders replaced successfully in {json_file_path}.")
        except Exception as e:
            print(f"ERROR: An error occurred while processing {json_file_path}. {e}")
