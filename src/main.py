#!/usr/bin/env python3
import time
import paho.mqtt.client as mqtt
import logging
import os
from pprint import pprint
from pylontech import PylontechStack
from pprint import pformat

mqttServer = os.environ.get('PYLONTECH_MQTT_HOST', 'localhost')
mqttPort = os.environ.get('PYLONTECH_MQTT_PORT', 1883)
mqttUser = os.environ.get('PYLONTECH_MQTT_USER')
mqttPassword = os.environ.get('PYLONTECH_MQTT_PASSWORD')
mqttTopic = os.environ.get('PYLONTECH_MQTT_TOPIC', 'pylontech/')
batteryCount = os.environ.get('PYLONTECH_BATTERY_COUNT')
serialDevice = os.environ.get('PYLONTECH_SERIAL_PORT', '/dev/ttyAMA0')
logLevel = os.environ.get('PYLONTECH_LOGGING_LEVEL', 'INFO').upper()
updateFrequence = os.environ.get('PYLONTECH_UDATE_INTERVAL', 10) 

# Define global Objects
logger = logging.getLogger(__name__)
logging.basicConfig(filename='pylontech-monitor.log', level=logLevel)

# define logger for std out
console = logging.StreamHandler()
console.setLevel(logging.INFO)
#formatter = logging.Formatter('%(levelname)-8s %(message)s')
#console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.connect(mqttServer, mqttPort, 60)
logger.info("Connected to MQTT Server: " + mqttServer + ":" + str(mqttPort))

logger.info('evaluating the stack of batteries (0..n batteries)')
x = PylontechStack(serialDevice, baud=115200, manualBattcountLimit=batteryCount)
logger.info("connected to serial device: " + serialDevice + " with battery count limit: " + str(batteryCount))
logger.info('number of batteries found: {}'.format(x.battcount))
logger.debug('received data:')
logger.debug(pformat(x.pylonData))


# Get list of unit serial
serials = x.pylonData['SerialNumbers']



while 1:
    try:
        x.update()
        logger.debug("--- Calculated:")
        logger.debug(pformat(x.pylonData['Calculated']))

        for key in (x.pylonData['Calculated']).keys():
            if not (key == "VER" or key == "ADR" or key == "PAYLOAD" or key == "LENGTH" or key == "RTN" or key == "ID"):
                mqttc.publish(mqttTopic + key, "{\"value\":" + str(x.pylonData['Calculated'][key])+"}")
                logger.debug(mqttTopic + key +" => {\"value\":" + str(x.pylonData['Calculated'][key])+"}")


        logger.debug("--- SystemParameter:")
        logger.debug(pformat(x.pylonData['SystemParameter']))

        for key in (x.pylonData['SystemParameter']).keys():
            if not (key == "VER" or key == "ADR" or key == "PAYLOAD" or key == "LENGTH" or key == "RTN" or key == "ID"):
                mqttc.publish(mqttTopic + "SystemParameter/" + key, "{\"value\":" + str(x.pylonData['SystemParameter'][key])+"}")
                logger.debug(mqttTopic + "SystemParameter/" + key + " => {\"value\":" + str(x.pylonData['SystemParameter'][key])+"}")
        
       
        for batteryIndex in range(len(serials)):
            logger.info("Battery no. " + str(batteryIndex) + " found: " + serials[batteryIndex])
            logger.debug(mqttTopic + "Unit/" + serials[batteryIndex] + "/SerialNumber" + " => {\"value\":\"" + str(x.pylonData['SerialNumbers'][batteryIndex])+"\"}")
            mqttc.publish(mqttTopic + "Unit/" + serials[batteryIndex] + "/SerialNumber", "{\"value\":\"" + str(x.pylonData['SerialNumbers'][batteryIndex])+"\"}")

            logger.debug("--- ChargeDischargeManagementList:")
            battery = x.pylonData['ChargeDischargeManagementList'][batteryIndex]
            logger.debug(pformat(battery))

            for key in battery.keys():
                if not (key == "VER" or key == "ADR" or key == "PAYLOAD" or key == "LENGTH" or key == "RTN" or key == "ID"):
                    mqttc.publish(mqttTopic + "Unit/" + serials[batteryIndex] + "/ChargeDischargeManagement/" + key, "{\"value\":" + str(battery[key])+"}")
                    logger.debug( mqttTopic + "Unit/" + serials[batteryIndex] + "/ChargeDischargeManagement/" + key + " => {\"value\":" + str(battery[key])+"}")

            logger.debug("--- AlarmInfoList:")
            # Set Battery Pointer to new scope
            battery = x.pylonData['AlarmInfoList'][batteryIndex]
            logger.debug(pformat(battery))
            for key in battery.keys():
                if not (key == "VER" or key == "ADR" or key == "PAYLOAD" or key == "LENGTH" or key == "RTN" or key == "ID"):
                    value = battery[key]
                    if isinstance(value, list):
                        for index in range(len(value)):
                     # Publish each item in the list
                            logger.debug (mqttTopic + "Unit/" + serials[batteryIndex] + "/AlarmInfo/" + key + "/" + str(index+1) + " => {\"value\":" + str(value[index])+"}")
                            mqttc.publish(mqttTopic + "Unit/" + serials[batteryIndex] + "/AlarmInfo/" + key + "/" + str(index+1), "{\"value\":" + str(value[index])+"}")
                    else:
                        logger.debug(mqttTopic + "Unit/" + serials[batteryIndex] + "/AlarmInfo/"  + key + " => {\"value\":" + str(battery[key])+"}")
                        mqttc.publish(mqttTopic + "Unit/" + serials[batteryIndex] + "/AlarmInfo/"  + key, "{\"value\":" + str(battery[key])+"}")


            logger.debug("--- AnaloglList:")
            logger.debug(pformat(x.pylonData['AnaloglList']))
            logger.debug("BatteryIndex: " + str(batteryIndex))
            battery = x.pylonData['AnaloglList'][batteryIndex]

            for key in battery.keys():
                if not (key == "VER" or key == "ADR" or key == "PAYLOAD" or key == "LENGTH" or key == "RTN" or key == "ID"):

                    value = battery[key]
                    if isinstance(value, list):
                        for index in range(len(value)):
                        # Publish each item in the list
                            logger.debug (mqttTopic + "Unit/" + serials[batteryIndex]  + "/" + key + "/" + str(index+1) + " => {\"value\":" + str(value[index])+"}")
                            mqttc.publish(mqttTopic + "Unit/" + serials[batteryIndex]  + "/" + key + "/" + str(index+1), "{\"value\":" + str(value[index])+"}")
                    else:
                        logger.debug(mqttTopic + "Unit/" + serials[batteryIndex] + "/" + key + " => {\"value\":" + str(battery[key]) + "}")
                        mqttc.publish(mqttTopic + "Unit/" + serials[batteryIndex] + "/" + key, "{\"value\":" + str(battery[key]) + "}")
 
        time.sleep(updateFrequence)
    except Exception as err:
        logger.error("Timeout ", err)
