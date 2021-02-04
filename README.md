# presence2mqtt
Publish your teams presence to mqtt!

Being in a lockdown and all I wanted to be able to switch lights based on if was in a meeting or not. This way my family members know if i'm in a meeting or not.  
There are other solutons out there, but usually involve a windows client and have no integration with Home Assistant.  
By using mqtt this s not only easy to use with Home Assitant, but also with domoticz or other devices which can subscribe to mqtt directly.  

## Azure
The app will user the Graph API to retrieve your teams presence status, for this you need to log-in and also grant permissions to read your presence status.  
You need configure an azure tenant id and client id, these can be retrieved from an Azure app. 

### Registering an app in Azure
Go to https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade 
Choose New Registration
Choose a name and register
Go to API Permissions, click Add a permission, choose Microsoft Graph, then Delegated permissions, search for Presence.Read and add this. Do the same to add the offline_access permission.  
Next go to the authentication and below Advanced settings set Allow public client flows to Yes
In the Overview you will find your tenant id and client id   
Depending on your organization settings it's possible an Administrator needs to approve the app   

## Configuration
This app requires a config.ini  
Create a config directory and place a config.ini in there  
Mount this config directory in the container on /config
In the same config directory the authentication token cache will also be stored  

Here's a minimal config file  
```
[Azure]
tenant_id = <AZURE TENANT ID>
client_id = <AZURE CLIENT ID>

[MQTT]
server = mqtt.local.lan
port = 1883
availability_topic = presence2mqtt/availability
activity_topic= presence2mqtt/activity
```

Config with all options:  
```
[Main]
log_level = INFO

[Azure]
tenant_id = <AZURE TENANT ID>
client_id = <AZURE CLIENT ID>

[MQTT]
server = mqtt.local.lan
port = 1883
user = mqttuser
client = presence2mqtt
password = secret
availability_topic = presence2mqtt/availability
activity_topic= presence2mqtt/activity
```

Then run the container  
`docker run -d -v '/path/to/config:/config' renout/presence2mqtt`

Or use a compose file
```
version: '3.7'

services:
  presence2mqtt:
    container_name: presence2mqtt
    image: renout/presence2mqtt
    restart: unless-stopped
    volumes:
      - /path/to//config:/config
```

## Logging in
Next check the container logs for the authentication url and device id.  
`docker logs -f presence2mqtt`
Follow the url, enter the generated device id, log in and authorize your just created app  
Go back to you container logs and you should now see your logged in  
Your presence and activity will no be published to mqtt every 30 seconds  
The authetication tokens are max 1 hour valid, the app will automtically renew the tokens  

## Home Assistant
In home assistant mqtt sensors can easily be added, for example

```
sensor:
  - platform: mqtt
    name: "Teams Availability"
    state_topic: "presence2mqtt/availability"
  - platform: mqtt
    name: "Teams Activity"
    state_topic: "presence2mqtt/activity"
```

Now you will have a sensor available in HA and go nuts with automations based on your presence in mqtt  


## Credits
The authentication logic is mostly borrowed from: https://github.com/maxi07/Teams-Presence
