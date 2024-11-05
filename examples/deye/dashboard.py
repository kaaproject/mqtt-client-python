import json
import os
from constants import tenant_id, app_version, app_name


def process_dashboards(template_folder:str, output_folder:str):
    if not tenant_id or not app_version or not app_name:
        print("\nNo 'tenant_id', 'app_version', or 'app_name' provided. Skipping template provision.\n")
        return

    json_file_paths = [os.path.join(template_folder, file) for file in os.listdir(template_folder) if file.endswith('.json')]
    os.makedirs(output_folder, exist_ok=True)

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

            output_file_path = os.path.join(output_folder, os.path.basename(json_file_path))
            with open(output_file_path, 'w') as file:
                json.dump(data, file, indent=4)

            print(f"Placeholders replaced successfully in {output_file_path}.")
        except Exception as e:
            print(f"ERROR: An error occurred while processing {json_file_path}. {e}")
