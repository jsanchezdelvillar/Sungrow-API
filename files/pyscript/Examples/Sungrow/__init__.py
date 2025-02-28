import json
import aiohttp
from datetime import timedelta

#config.yaml includes the following:
#  apps:
#    Sungrow:
#      appkey: !secret sungrow_appkey
#      sung_secret: !secret sungrow_secret
#      username: !secret sungrow_user
#      password: !secret sungrow_password

log.info(pyscript.config)
log.info(pyscript.app_config)
username = pyscript.app_config["username"]
password = pyscript.app_config["password"]
appkey = pyscript.app_config["appkey"]
x_access_key = pyscript.app_config["sung_secret"]

# Define URLs for login and device data
login_url = "https://gateway.isolarcloud.eu/openapi/login"
device_data_url = "https://gateway.isolarcloud.eu/openapi/getDeviceRealTimeData"

# Define payload and headers for login
login_payload = {
    "user_account": username,  
    "user_password": password,  
    "appkey": appkey  
}

login_headers = {
    "User-Agent": "Home Assistant",
    "x-access-key": x_access_key, 
    "Content-Type": "application/json",
    "sys_code": "901"
}

# Payload for device data
device_data_payload = {
    "appkey": appkey,  
    "device_type": 11,
    "point_id_list": [
        "83022", "83033", "83025", "83001", "83102", "83072", "83106"
    ],
    "ps_key_list": ["xxxxxxx_11_0_0"]
}

# Obtains a new token if current token is invalid
async def get_token():
    try:
        # login and obtaining token
        async with aiohttp.ClientSession() as session:
            async with session.post(login_url, json=login_payload, headers=login_headers) as response:
                if response.status == 200:
                    response_json = response.json()  # converts to python dict
                    log.info(response_json)
                    if response_json.get("result_code") == "1":  # success
                        if response_json.get("result_data", {}).get("login_state") == "1":
                            token = response_json["result_data"].get("token", "")
                            # store token in HA helper
                            state.set("input_text.token", token)
                        else:
                            log.error("Login error: login_state not valid")
                    else:
                        log.error("Error in answer: result_code is not 1")
                else:
                    log.error(f"Error in call: {response.status}")
                    state.set("input_text.token", "Error retrieving token")
    except Exception as e:
        log.error(f"Error retrieving token: {e}")
        state.set("input_text.token", "Error")

# Obtains device data using current token. If token invalid, calls for token update
async def get_device_data(token):
    try:
        headers = {
            "User-Agent": "Home Assistant",
            "x-access-key": x_access_key,
            "Content-Type": "application/json",
            "token": token,
            "sys_code": "901"
        }

        # obtain device data
        async with aiohttp.ClientSession() as session:
            async with session.post(device_data_url, json=device_data_payload, headers=headers) as response:
                if response.status == 200:
                    response_json = response.json()  # converts to python dict
                    log.info(response_json)
                    if response_json.get("result_code") == "1":  # verify if success
                        # extract data from device
                        device_data = response_json.get("result_data", {}).get("device_point_list", [{}])[0].get("device_point", {})
                        
                        # Update HA sensors with data
                        state.set("sensor.pv_daily_yield", device_data.get("p83022", "Unknown"), unit_of_measurement="Wh", state_class="TOTAL_INCREASING",icon="mdi-transmission-tower")
                        state.set("sensor.pv_power", device_data.get("p83033", "Unknown"), unit_of_measurement="W", state_class="MEASUREMENT",icon="mdi-lightning-bolt")
                        state.set("sensor.pv_eq_hours", device_data.get("p83025", "Unknown"), state_class="MEASUREMENT",unit_of_measurement="h")
                        state.set("sensor.pv_wwp", device_data.get("p83001", "Unknown"), state_class="MEASUREMENT",unit_of_measurement="W/Wp")
                        state.set("sensor.pv_energy_purchased_today", device_data.get("p83102", "Unknown"), unit_of_measurement="Wh", state_class="TOTAL_INCREASING",icon="mdi-transmission-tower")
                        state.set("sensor.pv_feed_in_energy_today", device_data.get("p83072", "Unknown"), unit_of_measurement="Wh", state_class="TOTAL_INCREASING",icon="mdi-transmission-tower")
                        state.set("sensor.pv_load_power", device_data.get("p83106", "Unknown"), unit_of_measurement="W", state_class="MEASUREMENT",icon="mdi-lightning-bolt")
                        #Calculates net power (Sungrow doesn't send a value for net power)
                        state.set("sensor.pv_exportada", float(device_data.get("p83033", "Unknown"))-float(device_data.get("p83106", "Unknown")), unit_of_measurement="W", state_class="MEASUREMENT",icon="mdi-lightning-bolt")
                    else:
                        log.warning("Token not valid or expired, asking for a new token.")
                        # In case token is not valid we get a new one
                        await get_token()
                        return  # exit to wait for token to update
                elif response.status == 401:  # Token not valid or expired?
                    log.warning("Token incorrecto o expirado, solicitando un nuevo token.")
                    # In case token is not valid we get a new one
                    await get_token()
                    return  # exit to wait for token to update
                else:
                    state.set("sensor.pv_data", "Error retrieving data")
    except Exception as e:
        log.error(f"Error retrieving data: {e}")
        state.set("sensor.pv_data", "Error")

# Controls the flow of data update
@service
async def update_device_data():
    # uses the stored token
    token = state.get("input_text.token")

    # If token is not empty and not error
    if token and token != "Error":
        await get_device_data(token)
    else:
        log.warning("Unavailable token, asking for a new one")
        # Asking for a new token
        await get_token()

# Replaced with a HA Automation
#from homeassistant.helpers.event import async_track_time_interval

#async def async_setup(hass, config):
#    # calls every 5 minutes
#    async_track_time_interval(hass, update_device_data, timedelta(minutes=5))
#
#    return True
