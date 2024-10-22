import subprocess
import shlex
import docker
import os

from timestamp_logger import TimestampLogger
from constants import logger

class DockerManager:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.old_data = {}


    def pull_images(self, image_list):
        for img in image_list:
            image_name = f"{img['image']}:{img.get('tag', 'latest')}"
            command = ["docker", "pull", image_name]
            command_str = ' '.join(shlex.quote(arg) for arg in command)

            try:
                result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                logger.info(f"Pull result for {image_name}: {result.stdout.strip()}")
                TimestampLogger.combine_timestamp_logs(command_str, result.stdout.strip())  
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.strip() or 'An unknown error occurred.'
                logger.error(f"Failed to pull image {image_name}: {err_msg}")
                TimestampLogger.combine_timestamp_logs(command_str, err_msg)  
            
            self.old_data["images"].append(img)


    def remove_images(self, images_list): 
        for img in images_list:
            image_name = img['image']

            command = ["docker", "rmi", "-f", image_name]
            command_str = ' '.join(shlex.quote(arg) for arg in command)
            try:
                result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                logger.info(f"Deleting image {image_name}: {result.stdout.strip()}")
                TimestampLogger.combine_timestamp_logs(command_str, result.stdout.strip())
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.strip() or 'An unknown error occurred.'
                logger.error(f"Failed to delete image {image_name}: {err_msg}")
                TimestampLogger.combine_timestamp_logs(command_str, err_msg)  


    def remove_containers(self, containers_list):
        for cont in containers_list:
            cont_name = cont['container_name']

            command = ["docker", "rm", "-f", cont_name]
            command_str = ' '.join(shlex.quote(arg) for arg in command)
            try:
                result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                logger.info(f"Deleting container {cont_name}: {result.stdout.strip()}")
                TimestampLogger.combine_timestamp_logs(command_str, result.stdout.strip())
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.strip() or 'An unknown error occurred.'
                logger.error(f"Failed to delete container {cont_name}: {err_msg}")
                TimestampLogger.combine_timestamp_logs(command_str, err_msg)  


    def create_containers(self, container_list):
        for container in container_list:
            self.run_container(container)


    def run_container(self, container):
        command = ['docker', 'run', '-d', "--restart", "unless-stopped"]
        if 'container_name' in container:
            command += ['--name', container['container_name']]
        command += self.build_container_options(container)
        command_str = ' '.join(shlex.quote(arg) for arg in command)

        logger.info("Running command: " + command_str)
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("Container started successfully: " + result.stdout.strip())
            TimestampLogger.combine_timestamp_logs(command_str, result.stdout.strip())  
        else:
            logger.error("Error starting container: " + result.stderr.strip())
            TimestampLogger.combine_timestamp_logs(command_str, result.stderr.strip()) 
        
        self.old_data["containers"].append(container)
        logger.info(f"\n\nold_data {self.old_data}\n\n")

    def build_container_options(self, container):
        options = []
        options += [f"-e {env['name']}={env['value']}" for env in container.get('env', [])]
        options += [f"-v {os.path.expanduser(volume)}" for volume in container.get('volumes', [])]
        options += [f"-p {port}" for port in container.get('ports', [])]
        options += [f"--cap-add {cap}" for cap in container.get('cap-add', [])]

        if 'network_mode' in container:
            options += [f"--network {container['network_mode']}"]

        options.append(container['image'])
        final_options = []
        for option in options:
            final_options.extend(option.split())
        return final_options
    

    def detect_changes(self, new_data):
        logger.info(f"NEW_DATA {new_data}")
        
        for img in new_data.get('images', []):
            if 'tag' not in img or not img['tag']:
                img['tag'] = "latest"

        changes = {
            'removed_images': [],
            'added_images': [],
            'removed_containers': [],
            'added_containers': [],
        }

        old_images = {img['image']: img['tag'] for img in self.old_data.get('images', [])}
        new_images = {img['image']: img['tag'] for img in new_data.get('images', [])}

        for img_key, new_tag in new_images.items():
            if img_key not in old_images:
                changes['added_images'].append({'image': img_key, 'tag': new_tag})
            elif old_images[img_key] != new_tag:
                changes['removed_images'].append({'image': img_key, 'tag': old_images[img_key]})
                changes['added_images'].append({'image': img_key, 'tag': new_tag})

        for img_key in old_images.keys():
            if img_key not in new_images:
                changes['removed_images'].append({'image': img_key, 'tag': old_images[img_key]})

        old_containers = {cont['container_name']: cont for cont in self.old_data.get('containers', [])}
        new_containers = {cont['container_name']: cont for cont in new_data.get('containers', [])}

        for cont_key, new_cont in new_containers.items():
            if cont_key not in old_containers:
                changes['added_containers'].append(new_cont)
            elif old_containers[cont_key]["container_name"] == new_cont["container_name"]:
                    changes['removed_containers'].append(old_containers[cont_key])
                    changes['added_containers'].append(new_cont)

        for cont_key in old_containers.keys():
            if cont_key not in new_containers:
                changes['removed_containers'].append(old_containers[cont_key])

        self.old_data = new_data
        logger.info(f"\n\nCHANGES: {changes}\n\n")
        return changes


    def apply_docker_changes(self, docker_changes):
        self.remove_containers(docker_changes["removed_containers"])
        self.remove_images(docker_changes["removed_images"])

        self.pull_images(docker_changes["added_images"])
        self.create_containers(docker_changes["added_containers"])