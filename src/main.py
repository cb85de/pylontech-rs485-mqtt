#!/usr/bin/env python3
import time
from pprint import pprint
import paho.mqtt.client as mqtt
from pylontech import PylontechStack
from pprint import pformat
import logging


mqttServer = "192.168.176.3"
batteryCount = 4
serialDevice = '/dev/ttyAMA0'
logLevel = logging.DEBUG
updateFrequence = 10 

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
mqttc.connect(mqttServer, 1883, 60)


logger.info('evaluating the stack of batteries (0..n batteries)')
x = PylontechStack(serialDevice, baud=115200, manualBattcountLimit=batteryCount)
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
                mqttc.publish("pylontech/" + key, "{\"value\":" + str(x.pylonData['Calculated'][key])+"}")
                logger.debug("pylontech/" + key +" => {\"value\":" + str(x.pylonData['Calculated'][key])+"}")


        logger.debug("--- SystemParameter:")
        logger.debug(pformat(x.pylonData['SystemParameter']))

        for key in (x.pylonData['SystemParameter']).keys():
            if not (key == "VER" or key == "ADR" or key == "PAYLOAD" or key == "LENGTH" or key == "RTN" or key == "ID"):
                mqttc.publish("pylontech/SystemParameter/" + key, "{\"value\":" + str(x.pylonData['SystemParameter'][key])+"}")
                logger.debug("pylontech/SystemParameter/" + key + " => {\"value\":" + str(x.pylonData['SystemParameter'][key])+"}")
        
       
        for batteryIndex in range(len(serials)):
            logger.info("Battery no. " + str(batteryIndex) + " found: " + serials[batteryIndex])
            logger.debug("pylontech/Unit/" + serials[batteryIndex] + "/SerialNumber" + " => {\"value\":\"" + str(x.pylonData['SerialNumbers'][batteryIndex])+"\"}")
            mqttc.publish("pylontech/Unit/" + serials[batteryIndex] + "/SerialNumber", "{\"value\":\"" + str(x.pylonData['SerialNumbers'][batteryIndex])+"\"}")

            logger.debug("--- ChargeDischargeManagementList:")
            battery = x.pylonData['ChargeDischargeManagementList'][batteryIndex]
            logger.debug(pformat(battery))

            for key in battery.keys():
                if not (key == "VER" or key == "ADR" or key == "PAYLOAD" or key == "LENGTH" or key == "RTN" or key == "ID"):
                    mqttc.publish("pylontech/Unit/" + serials[batteryIndex] + "/ChargeDischargeManagement/" + key, "{\"value\":" + str(battery[key])+"}")
                    logger.debug("pylontech/Unit/" + serials[batteryIndex] + "/ChargeDischargeManagement/" + key + " => {\"value\":" + str(battery[key])+"}")

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
                            logger.debug ("pylontech/Unit/" + serials[batteryIndex] + "/AlarmInfo/" + key + "/" + str(index+1) + " => {\"value\":" + str(value[index])+"}")
                            mqttc.publish("pylontech/Unit/" + serials[batteryIndex] + "/AlarmInfo/" + key + "/" + str(index+1), "{\"value\":" + str(value[index])+"}")
                    else:
                        logger.debug("pylontech/Unit/" + serials[batteryIndex] + "/AlarmInfo/"  + key + " => {\"value\":" + str(battery[key])+"}")
                        mqttc.publish("pylontech/Unit/" + serials[batteryIndex] + "/AlarmInfo/"  + key, "{\"value\":" + str(battery[key])+"}")


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
                            logger.debug ("pylontech/Unit/" + serials[batteryIndex]  + "/" + key + "/" + str(index+1) + " => {\"value\":" + str(value[index])+"}")
                            mqttc.publish("pylontech/Unit/" + serials[batteryIndex]  + "/" + key + "/" + str(index+1), "{\"value\":" + str(value[index])+"}")
                    else:
                        logger.debug("pylontech/Unit/" + serials[batteryIndex] + "/" + key + " => {\"value\":" + str(battery[key]) + "}")
                        mqttc.publish("pylontech/Unit/" + serials[batteryIndex] + "/" + key, "{\"value\":" + str(battery[key]) + "}")
 
        time.sleep(updateFrequence)
    except Exception as err:
        logger.error("Timeout ", err)
