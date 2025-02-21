#!/usr/bin/env python3
import time
from pprint import pprint
import paho.mqtt.client as mqtt
from pylontech import PylontechStack


mqttServer = "192.168.176.3"
batteryCount = 2
serialDevice = '/dev/ttyAMA0'


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

mqttc.connect(mqttServer, 1883, 60)


print('evaluating the stack of batteries (0..n batteries)')
x = PylontechStack(serialDevice, baud=115200, manualBattcountLimit=batteryCount)
print('number of batteries found: {}'.format(x.battcount))
# print('received data:')
# print(x.pylonData)


# Get list of unit serial
serials = x.pylonData['SerialNumbers']



while 1:
    try:
        x.update()
        print("--- Calculated:")
        pprint(x.pylonData['Calculated'])
        print ("---\n\n")

        for key in (x.pylonData['Calculated']).keys():
            if not (key == "VER" or key == "ADR" or key == "PAYLOAD" or key == "LENGTH" or key == "RTN" or key == "ID"):
                mqttc.publish("pylontech/" + key, "{\"value\":" + str(x.pylonData['Calculated'][key])+"}")


        print("--- SystemParameter:")
        pprint(x.pylonData['SystemParameter'])

        for key in (x.pylonData['SystemParameter']).keys():
            if not (key == "VER" or key == "ADR" or key == "PAYLOAD" or key == "LENGTH" or key == "RTN" or key == "ID"):
                mqttc.publish("pylontech/SystemParameter/" + key, "{\"value\":" + str(x.pylonData['SystemParameter'][key])+"}")
#            print( "Key: " + key + "  Value:"  +str( x.pylonData['SystemParameter'][key]))
 
        
       
        for batteryIndex in range(len(serials)):
            print("- Expected battery lable is: " + serials[batteryIndex])
            print("BatteryIndex: " + str(batteryIndex))
            mqttc.publish("pylontech/Unit/" + serials[batteryIndex] + "/SerialNumber", "{\"value\":\"" + str(x.pylonData['SerialNumbers'][batteryIndex])+"\"}")

            print("--- ChargeDischargeManagementList:")
            battery = x.pylonData['ChargeDischargeManagementList'][batteryIndex]
            pprint(battery)

            for key in battery.keys():
                if not (key == "VER" or key == "ADR" or key == "PAYLOAD" or key == "LENGTH" or key == "RTN" or key == "ID"):
                    mqttc.publish("pylontech/Unit/" + serials[batteryIndex] + "/ChargeDischargeManagement/" + key, "{\"value\":" + str(battery[key])+"}")



            print("--- AlarmInfoList:")
            # Set Battery Pointer to new scope
            battery = x.pylonData['AlarmInfoList'][batteryIndex]
            pprint(battery)
            for key in battery.keys():
                if not (key == "VER" or key == "ADR" or key == "PAYLOAD" or key == "LENGTH" or key == "RTN" or key == "ID"):
                    value = battery[key]
                    if isinstance(value, list):
                        for index in range(len(value)):
                     # Publish each item in the list
#                           pprint ("key: " + key +  "  Status: " + str(value[index]))
                            mqttc.publish("pylontech/Unit/" + serials[batteryIndex] + "/AlarmInfo/" + key + "/" + str(index+1), "{\"value\":" + str(value[index])+"}")
                    else:
#                       print("  Key: " + key + "  Value: " + str(x.pylonData['AlarmInfoList'][batteryIndex][key]))
                        mqttc.publish("pylontech/Unit/" + serials[batteryIndex] + "/AlarmInfo/"  + key, "{\"value\":" + str(battery[key])+"}")


            print("--- AnaloglList:")
            pprint(x.pylonData['AnaloglList'])
#        for batteryIndex in range(len(x.pylonData['AnaloglList'])):
            print("BatteryIndex: " + str(batteryIndex))
            battery = x.pylonData['AnaloglList'][batteryIndex]

#            for key in battery.keys():
#                mqttc.publish("pylontech/Unit/" + str(batteryIndex) + "/Analog/" + key, battery[key])

            print("AnalogList:")
            for key in battery.keys():
                if not (key == "VER" or key == "ADR" or key == "PAYLOAD" or key == "LENGTH" or key == "RTN" or key == "ID"):

                    value = battery[key]
                    if isinstance(value, list):
                        for index in range(len(value)):
                        # Publish each item in the list
#                           pprint ("key: " + key +  "  Status: " + str(value[index]))
                            mqttc.publish("pylontech/Unit/" + serials[batteryIndex]  + "/" + key + "/" + str(index+1), "{\"value\":" + str(value[index])+"}")
                    else:
#                       print("  Key: " + key + "  Value: " + str(battery[key]))
                        mqttc.publish("pylontech/Unit/" + serials[batteryIndex] + "/" + key, "{\"value\":" + str(battery[key]) + "}")
 
        time.sleep(10)
    except Exception as err:
        print("Timeout ", err)
