import subprocess
import shlex
import docker
import os

from constants import logger

class DockerManager:
    def __init__(self, log_function):
        self.docker_client = docker.from_env()
        self.log_function = log_function  # Function to log timestamped messages

    def pull_images(self, image_list):
        for img in image_list:
            image_name = f"{img['image']}:{img.get('tag', 'latest')}"
            command = ["docker", "pull", image_name]
            command_str = ' '.join(shlex.quote(arg) for arg in command)
            try:
                result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                logger.info(f"Pull result for {image_name}: {result.stdout.strip()}")
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.strip() or 'An unknown error occurred.'
                logger.error(f"Failed to pull image {image_name}: {err_msg}")
                self.log_function(command_str, err_msg)  # Log the error

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
            self.log_function(command_str, result.stdout.strip())  # Log success
        else:
            logger.error("Error starting container: " + result.stderr.strip())
            self.log_function(command_str, result.stderr.strip())  # Log error

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
