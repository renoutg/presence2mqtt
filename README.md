# presence2mqtt
Publish your teams presence to mqtt

## Configuration
This app requires a config.ini  
Mount a volume on /config and place a config.ini in there  
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
