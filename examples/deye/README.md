# DEYE MQTT Client

This example integrates the DEYE inverter with the KAA platform. It utilizes the [deye-controller](https://github.com/githubDante/deye-controller) library to fetch data from the inverter and then uses `kaa_mqtt_client` to send data to the KAA platform.


## Environment Variables

This project requires the following environment variables to work:

```bash
export IP="{your-deye-ip}"
export SERIAL_NUMBER="{your-deye-serial-number}"
export DEFAULT_KPC_HOST="mqtt.cloud.kaaiot.com"
export DEFAULT_KPC_PORT="1883"
export APPLICATION_VERSION="{your-application-version}"
export ENDPOINT_TOKEN="{your-endpoint-token}"
```

To get `DEFAULT_KPC_HOST`, `DEFAULT_KPC_PORT`, `APPLICATION_VERSION`, and `ENDPOINT_TOKEN`, check out an example in this repository at `./examples/simple_client`. 
For `IP` and `SERIAL_NUMBER`, you can obtain them from the **DEYE web UI**. Check your inverter's manual for more details.


## Running the Project
To start the project, install required libraries by executing:

```bash
pip install -r requirements.txt
```

Then insert the environment variables into your terminal and execute `main.py`.