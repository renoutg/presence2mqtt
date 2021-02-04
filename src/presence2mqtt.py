#!/usr/bin/env python

# Get teams presence and publish to mqtt
# A config.ini is required, see README.md

import logging
import requests
import paho.mqtt.client as mqtt
import msal
import atexit
import os.path
import configparser
from time import sleep
import pyqrcode

config = configparser.ConfigParser()
if os.path.isfile("/config/config.ini"):
  config.read("/config/config.ini")
  tenant_id = config["Azure"]["Tenant_Id"]
  client_id = config["Azure"]["Client_Id"]
  mqtt_server = config["MQTT"]["server"]
  mqtt_port = int(config["MQTT"]["port"])
  mqtt_availability_topic = config["MQTT"]["availability_topic"]
  mqtt_activity_topic = config["MQTT"]["activity_topic"]
  if config.has_option('MQTT', 'user'):
    mqtt_user = config["MQTT"]["user"]
  if config.has_option('MQTT', 'password'):
    mqtt_password = config["MQTT"]["password"]
  if config.has_option('MQTT', 'client'):
    mqtt_client = config["MQTT"]["client"]
  else:
    mqtt_client = 'presence2mqtt'
  if config.has_option('Main', 'log_level'):
    log_level = config["Main"]["log_level"]
  else:
    log_level = 'INFO'
 else:
   print("config.ini not found!")
   raise SystemExit(1)

level = logging.getLevelName(log_level)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%y %H:%M:%S', level=level)

authority = 'https://login.microsoftonline.com/' + tenant_id
endpoint = 'https://graph.microsoft.com/v1.0'
scopes = [
  'Presence.Read'
]

def Authorize():
  global token
  global fullname
  logging.info("Starting authentication workflow")
  try:
    cache = msal.SerializableTokenCache()
    if os.path.exists('/config/token_cache.bin'):
      cache.deserialize(open('/config/token_cache.bin', 'r').read())
  
    atexit.register(lambda: open('/config/token_cache.bin', 'w').write(cache.serialize()) if cache.has_state_changed else None)
  
    app = msal.PublicClientApplication(client_id, authority=authority, token_cache=cache)
  
    accounts = app.get_accounts()
    result = None
    if len(accounts) > 0:
      result = app.acquire_token_silent(scopes, account=accounts[0])
  
    if result is None:
      # Create QR code
      qr = pyqrcode.create("https://microsoft.com/devicelogin")
      print(qr.terminal(module_color=0, background=231, quiet_zone=1))
  
      # Initiate flow
      flow = app.initiate_device_flow(scopes=scopes)
      if 'user_code' not in flow:
        raise Exception('Failed to create device flow')
      logging.info(flow['message'])
      result = app.acquire_token_by_device_flow(flow)
      token = result['access_token']
      logging.info("Aquired token")
      token_claim = result['id_token_claims']
      logging.info("Welcome " + token_claim.get('name') + "!")
      fullname = token_claim.get('name')
      return True
    if 'access_token' in result:
      token = result['access_token']
      try:
        result = requests.get(f'{endpoint}/me', headers={'Authorization': 'Bearer ' + result['access_token']}, timeout=5)
        result.raise_for_status()
        y = result.json()
        fullname = y['givenName'] + " " + y['surname']
        logging.info("Token found, welcome " + y['givenName'] + "!")
        return True
      except requests.exceptions.HTTPError as err:
        if err.response.status_code == 404:
          logging.warning("MS Graph URL is invalid!")
        elif err.response.status_code == 401:
          logging.warning("MS Graph is not authorized. Trying to reauthorize the app (401)")
          return False
      except requests.exceptions.Timeout as timeerr:
        logging.error("The authentication request timed out. " + str(timeerr))
    else:
      raise Exception('no access token in result')
  except Exception as e:
    logging.error("Failed to authenticate. " + str(e))
    sleep(2)
    return False

Authorize()
client = mqtt.Client(mqtt_client)
try:
  mqtt_password    
except NameError:
  logging.info("Skippping password authentication")
else:
  client.username_pw_set(username=mqtt_user, password=mqtt_password)

logging.info("Authenticating to mqtt server")
client.connect(mqtt_server, port=mqtt_port, keepalive=60)
client.loop_start()

while True:
  headers={'Authorization': 'Bearer ' + token}
  jsonresult = ''
  
  try:
    result = requests.get(f'https://graph.microsoft.com/beta/me/presence', headers=headers, timeout=5)
    result.raise_for_status()
    jsonresult = result.json()
    logging.debug("Got result: " + str(jsonresult))
    client.publish(mqtt_availability_topic,jsonresult['availability'])
    client.publish(mqtt_activity_topic,jsonresult['activity'])
  except requests.exceptions.Timeout as timeerr:
    logging.error("The request for Graph API timed out! " + str(timeerr))
  except requests.exceptions.HTTPError as err:
    if err.response.status_code == 404:
      logging.error("MS Graph URL is invalid!")
    elif err.response.status_code == 401:
      logging.warning("MS Graph is not authorized. Trying to reauthorize the app (401)")
      Authorize()
  except requests.exceptions.ConnectionError as connerr:
    logging.error("Connection Error: " + str(connerr))
  
  sleep(30)
