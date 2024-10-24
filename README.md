# Python Kaa Mqtt Client 

This Python MQTT client is tailored for the Kaa IoT platform, providing a range of methods to interact with the platform's features. It encapsulates the complexity of MQTT communication, offering a user-friendly interface for IoT applications.


## Overview

This repository consists of two parts: 
1. The `kaa_mqtt_client` library.
2. An `examples` folder containing implementations of the `kaa_mqtt_client`.


## Basic Installation

1. Ensure Python is installed on your system:

    ```bash
    sudo apt install python3.12-venv
    pip install setuptools
    ```

2. Install the project using the following commands:

    ```bash
    git clone https://github.com/kaaproject/mqtt-client-python
    cd mqtt-client-python
    python3 -m venv env
    source env/bin/activate
    pip install -r requirements.txt
   ```


## Examples Folder

Navigate to `examples/simple_client`. It contains the most straightforward example of how to utilize the `kaa_mqtt_client` library.
