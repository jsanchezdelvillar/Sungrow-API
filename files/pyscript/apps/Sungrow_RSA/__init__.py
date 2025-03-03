import base64
import json
import random
import string
import time
import aiohttp
import logging
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding

username = pyscript.app_config["username"]
password = pyscript.app_config["password"]
appkey = pyscript.app_config["appkey"]
x_access_key = pyscript.app_config["sung_secret"]
public_key_base64 = pyscript.app_config["RSA_public"]

# Define URLs for login and device data
login_url = "https://gateway.isolarcloud.eu/openapi/login"
device_data_url = "https://gateway.isolarcloud.eu/openapi/getDeviceRealTimeData"


# Obtains a new token if current token is invalid
async def get_token():
    try:
        # login and obtaining token
        unenc_x_random_secret_key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        x_random_secret_key = public_encrypt(unenc_x_random_secret_key, public_key_base64)

        nonce = generate_nonce()
        timestamp = str(int(time.time() * 1000))

        login_payload = {
            "api_key_param": {
                "nonce": nonce,
                "timestamp": timestamp
            },
            "appkey": appkey,
            "login_type": "1",
            "user_account": username,
            "user_password": password
        }
        log.info (f"Login payload: {login_payload}")
        login_headers = {
            "User-Agent": "Home Assistant",
            "x-access-key": x_access_key, 
            "x-random-secret-key": x_random_secret_key,
            "Content-Type": "application/json",
            "sys_code": "901"
        }
        log.info (f"Login headers: {login_headers}")


        encrypted_request_body = encrypt(json.dumps(login_payload), unenc_x_random_secret_key)

        async with aiohttp.ClientSession() as session:
            async with session.post(login_url, headers=login_headers, data=encrypted_request_body) as response:
                if response.status == 200:
#                    response_json = response.json()  # converts to python dict
#                    log.info(response_json)
                    response_body = response.text()
                    log.info(f"Response body before decryption: {response_body}")
                    decrypted_response_body = decrypt(response_body, unenc_x_random_secret_key)
                    log.info(f"Response bocy after decryption: {decrypted_response_body}")
                    if decrypted_response_body.get("result_code") == "1":  # success
                        if decrypted_response_body.get("result_data", {}).get("login_state") == "1":
                            token = decrypted_response_body["result_data"].get("token", "")
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

    unenc_x_random_secret_key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    x_random_secret_key = public_encrypt(unenc_x_random_secret_key, public_key_base64)
    nonce = generate_nonce()
    timestamp = str(int(time.time() * 1000))

    try:
        headers = {
            "User-Agent": "Home Assistant",
            "x-access-key": x_access_key,
            "x-random-secret-key": x_random_secret_key,
            "Content-Type": "application/json",
            "token": token,
            "sys_code": "901"
        }
        device_data_payload = {
            "api_key_param": {
                "nonce": nonce,
                "timestamp": timestamp
            },
            "appkey": appkey,  
            "device_type": 11,
            "point_id_list": [
                "83022", "83033", "83025", "83001", "83102", "83072", "83106"
            ],
            "ps_key_list": ["xxxxxxx_11_0_0"]
        }
        log.info (f"Device payload: {device_data_payload}")
        encrypted_request_body = encrypt(json.dumps(device_data_payload), unenc_x_random_secret_key)
        log.info (f"Device payload encrypted: {encrypted_request_body}")
        
        # obtain device data
        async with aiohttp.ClientSession() as session:
            async with session.post(device_data_url, headers=headers, data=encrypted_request_body) as response:
                if response.status == 200:
#                    response_json = response.json()  # converts to python dict
#                    log.info(response_json)
                    response_body = response.text()
                    log.info(f"Response body before decryption: {response_body}")
                    decrypted_response_body = decrypt(response_body, unenc_x_random_secret_key)
                    log.info(f"Response bocy after decryption: {decrypted_response_body}")
                    # Assuming `decrypted_response_body` is a JSON string, parse it first
                    try:
                        decrypted_response_body = json.loads(decrypted_response_body)  # Parse JSON string to dictionary
                    except json.JSONDecodeError as e:
                        log.error(f"Error decoding JSON: {e}")
                        return  # Exit if the JSON is invalid
                    log.info(f"Response bocy after decryption as dict: {decrypted_response_body}")
                    log.info(f"decrypted result code {decrypted_response_body.get("result_code")}")
                    if decrypted_response_body.get("result_code") == "1":  # verify if success
                        # extract data from device
                        device_data = decrypted_response_body.get("result_data", {}).get("device_point_list", [{}])[0].get("device_point", {})
                        log.info(f"Device data: {device_data}")
                        # Update HA sensors with data
                        state.set("sensor.pv_daily_yield", device_data.get("p83022", "Unknown"), unit_of_measurement="Wh", state_class="total_increasing",icon="mdi-transmission-tower", device_class="energy")
                        state.set("sensor.pv_power", device_data.get("p83033", "Unknown"), unit_of_measurement="W", state_class="measurement",icon="mdi-lightning-bolt", device_class="power")
                        state.set("sensor.pv_eq_hours", device_data.get("p83025", "Unknown"), state_class="measurement",unit_of_measurement="h")
                        state.set("sensor.pv_wwp", device_data.get("p83001", "Unknown"), state_class="measurement",unit_of_measurement="W/Wp")
                        state.set("sensor.pv_energy_purchased_today", device_data.get("p83102", "Unknown"), unit_of_measurement="Wh", state_class="total_increasing",icon="mdi-transmission-tower", device_class="energy")
                        state.set("sensor.pv_feed_in_energy_today", device_data.get("p83072", "Unknown"), unit_of_measurement="Wh", state_class="total_increasing",icon="mdi-transmission-tower", device_class="energy")
                        state.set("sensor.pv_load_power", device_data.get("p83106", "Unknown"), unit_of_measurement="W", state_class="measurement",icon="mdi-lightning-bolt", device_class="power")
                        #Calculates net power (Sungrow doesn't send a value for net power)
                        state.set("sensor.pv_exportada", float(device_data.get("p83033", "Unknown"))-float(device_data.get("p83106", "Unknown")), unit_of_measurement="W", state_class="measurement",icon="mdi-lightning-bolt", device_class="power")
                        state.set("sensor.pv_net_grid", float(device_data.get("p83102", "Unknown"))-float(device_data.get("p83072", "Unknown")), unit_of_measurement="Wh", state_class="total", icon="mdi-transmission-tower", device_class="energy")
                        state.set("sensor.pv_solar_consumed", round((float(device_data.get("p83022", "Unknown"))-float(device_data.get("p83072", "Unknown")))*100/float(device_data.get("p83022", "Unknown")),2), unit_of_measurement="%", state_class="measurement", icon="mdi-percent")
                        state.set("sensor.pv_selfsufficiency", round((float(device_data.get("p83022", "Unknown"))-float(device_data.get("p83072", "Unknown")))*100/(float(device_data.get("p83022", "Unknown"))+float(device_data.get("p83102", "Unknown"))-float(device_data.get("p83072", "Unknown"))),2), unit_of_measurement="%", state_class="measurement", icon="mdi-percent")
                    else:
                        log.warning("Token not valid or expired, asking for a new token.")
                        # In case token is not valid we get a new one
                        await get_token()
                        return  # exit to wait for token to update
                elif response.status == 401:  # Token not valid or expired?
                    log.warning("Token not valid or expired, asking for a new token.")
                    # In case token is not valid we get a new one
                    await get_token()
                    return  # exit to wait for token to update
                else:
                    state.set("sensor.pv_data", "Error retrieving data")
    except Exception as e:
        log.error(f"Error retrieving data: {e}")
        state.set("sensor.pv_data", "Error")

# RSA Encryption rule
def rsa_encrypt(public_key, data, modulus_bit_length):
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    max_chunk_size = (modulus_bit_length // 8) - 11  # PKCS1 padding overhead
    chunks = [data[i:i + max_chunk_size] for i in range(0, len(data), max_chunk_size)]
    
    encrypted_chunks = []
    for chunk in chunks:
        encrypted_chunk = public_key.encrypt(
            chunk,
            padding.PKCS1v15()  # Use PKCS#1 v1.5 padding (default in Java)
        )
        encrypted_chunks.append(encrypted_chunk)
    return encrypted_chunks

# Function to encrypt data with the provided public key (Base64 encoded X.509 format)
def public_encrypt(data, public_key_base64):
    log.info('Starting encryption')
    log.info(f'Data to encrypt: {data}')
    
    try:
        # Decode the Base64 string (no PEM headers are needed here)
        public_key_bytes = base64.urlsafe_b64decode(public_key_base64.strip())
        
        # Load the public key from X.509 encoded bytes (without PEM headers)
        public_key = serialization.load_der_public_key(public_key_bytes, backend=default_backend())
        log.info(f'Public key loaded successfully')
    except Exception as e:
        log.error(f"Error loading public key: {e}")
        return None

    try:
        # Get modulus bit length from the public key
        modulus_bit_length = public_key.public_numbers().n.bit_length()

        # Encrypt the data
        encrypted_chunks = rsa_encrypt(public_key, data, modulus_bit_length)

        # Concatenate the encrypted chunks and encode as Base64 URL-safe string
        encrypted_data = b''.join(encrypted_chunks)
        base64_encoded = base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        log.info(f'Data encrypted: {base64_encoded}')

        return base64_encoded
    except Exception as e:
        log.error(f"Error during RSA encryption: {e}")
        return None

def get_secret_key(key):
    password_bytes = key.encode('utf-8')
    return password_bytes.ljust(16)[:16]

def parse_hex_str2_byte(hex_str):
    return bytes.fromhex(hex_str)

def generate_nonce(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def encrypt(content, password):
    try:
        log.info('Starting encryption')
        log.info(f'Data to encrypt: {content}')
        password_bytes = get_secret_key(password)
        cipher = Cipher(algorithms.AES(password_bytes), modes.ECB(), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = PKCS7(128).padder()
        padded_data = padder.update(content.encode('utf-8')) + padder.finalize()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        encrypted_data_hex = encrypted_data.hex().upper()
        log.info(f'Data encrypted: {encrypted_data_hex}')
        return encrypted_data_hex
    except Exception as e:
        log.error(f"Error during AES encryption: {e}")

def decrypt(content, password):
    try:
        log.info('Starting decryption')
        log.info(f'Data to decrypt: {content}')
        decrypt_from = parse_hex_str2_byte(content)
        password_bytes = get_secret_key(password)
        cipher = Cipher(algorithms.AES(password_bytes), modes.ECB(), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_padded_data = decryptor.update(decrypt_from) + decryptor.finalize()
        unpadder = PKCS7(128).unpadder()
        original = unpadder.update(decrypted_padded_data) + unpadder.finalize()
        decrypted_data = original.decode('utf-8')
        log.info(f'Data decrypted: {decrypted_data}')
        return decrypted_data
    except Exception as e:
        log.error(f"Error during AES decryption: {e}")

# Controls the flow of data update
@service
# Define payload and headers for login
async def update_device_data_RSA():

    # uses the stored token
    token = state.get("input_text.token")
    log.info (f"Token: {token}")

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
