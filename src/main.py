#!/usr/bin/env python3
"""Polls a Pylontech battery stack over RS485 and publishes every value to MQTT.

Runs on a Raspberry Pi Zero W (one ARMv6 core, 512 MB RAM), so it is written
to be cheap per cycle (measured on the Pi, 2026-10-24):
- one persistent MQTT connection instead of paho's publish.single() per value
  (10.8 ms vs 1.5 ms CPU per message, ~455 messages per cycle)
- debug output (pformat, payload strings) is only built when DEBUG is on
- the RS485 receive buffer is flushed without the library's 1 s wait per battery
- the interval is the cycle period, not a pause after the work
- logs go to stdout only (no file growing inside the container on the SD card)
"""
import json
import logging
import os
import time
from pprint import pformat

import paho.mqtt.client as mqtt
from pylontech import PylontechStack

mqttServer = os.environ.get('PYLONTECH_MQTT_HOST', 'localhost')
mqttPort = int(os.environ.get('PYLONTECH_MQTT_PORT', 1883))
# PYLONTECH_MQTT_USER / _PASS are not used: the broker (Venus OS on the
# Cerbo GX) takes anonymous clients, and the publisher never sent them.
mqttTopic = os.environ.get('PYLONTECH_MQTT_TOPIC', 'pylontech/')
batteryCount = int(os.environ.get('PYLONTECH_BATTERY_COUNT'))
serialDevice = os.environ.get('PYLONTECH_SERIAL_PORT', '/dev/ttyAMA0')
logLevel = os.environ.get('PYLONTECH_LOGGING_LEVEL', 'INFO').upper()
updateInterval = float(os.environ.get('PYLONTECH_UDATE_INTERVAL', 10))
# After a failed poll (RS485 timeout, checksum): wait this long before the next try.
retryDelay = float(os.environ.get('PYLONTECH_RETRY_DELAY', 5))

# Keys of the decoded frames that are protocol fields, not measurements.
SKIP_KEYS = {"VER", "ADR", "PAYLOAD", "LENGTH", "RTN", "ID"}

logging.basicConfig(level=logLevel, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)
debug = logger.isEnabledFor(logging.DEBUG)


# MQTT payload {"value": ...} as valid JSON. Telegraf parses it with
# data_format = "json" into the float field "value" (bucket pv), so:
# - booleans go out as 1/0: a JSON boolean would conflict with the float
#   field type in InfluxDB
# - strings ("Ok", ">65Ah") are quoted; Telegraf ignores string fields
# Before, str() produced {"value":Ok} / {"value":True} - invalid JSON,
# several hundred Telegraf parse errors per minute.
# - other number types (e.g. Decimal) as float, so they stay measurements
def _json_default(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def payload(value):
    if isinstance(value, bool):
        value = int(value)
    return json.dumps({"value": value}, default=_json_default)


# --- MQTT: one connection for the whole run -----------------------------------------
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="pylontech-rs485-mqtt")
client.reconnect_delay_set(min_delay=1, max_delay=60)
# QoS 0: while the broker is away, messages are dropped, not queued in RAM.
client.max_queued_messages_set(1000)


def on_connect(client, userdata, flags, reason_code, properties):
    logger.info("MQTT connected to %s:%s (%s)", mqttServer, mqttPort, reason_code)


def on_disconnect(client, userdata, flags, reason_code, properties):
    logger.warning("MQTT disconnected (%s), reconnecting", reason_code)


client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.connect_async(mqttServer, mqttPort, keepalive=60)
client.loop_start()

failed_publishes = 0


def publish(topic, value):
    global failed_publishes
    msg = payload(value)
    if client.publish(mqttTopic + topic, msg).rc != mqtt.MQTT_ERR_SUCCESS:
        failed_publishes += 1
    if debug:
        logger.debug("%s%s => %s", mqttTopic, topic, msg)


def publish_values(prefix, values):
    """Publishes a decoded frame; list values as <key>/1..n."""
    for key, value in values.items():
        if key in SKIP_KEYS:
            continue
        if isinstance(value, list):
            for index, item in enumerate(value, start=1):
                publish("{}{}/{}".format(prefix, key, index), item)
        else:
            publish(prefix + key, value)


# --- RS485 ---------------------------------------------------------------------------
logger.info('evaluating the stack of batteries (0..n batteries)')
x = PylontechStack(serialDevice, baud=115200, manualBattcountLimit=batteryCount)
logger.info("connected to serial device %s with battery count limit %s", serialDevice, batteryCount)
logger.info('number of batteries found: %s', x.battcount)

# The library flushes the receive buffer before each battery by reading with a
# 1 s timeout until nothing comes: ~1 s idle per battery, 6 s per cycle. A
# local UART needs no waiting: drop the OS buffer and whatever is already in
# flight. receive_frame() skips anything before the start byte anyway.
handler = x.pylon.rs485


def fast_clear_rx_buffer():
    ser = handler.ser  # reconnect() replaces it
    ser.reset_input_buffer()
    restore_timeout = ser.timeout
    ser.timeout = 0.02
    while ser.read(256):
        pass
    ser.timeout = restore_timeout


handler.clear_rx_buffer = fast_clear_rx_buffer

serials = x.pylonData['SerialNumbers']

# --- main loop -----------------------------------------------------------------------
next_run = time.monotonic()
while True:
    started = time.monotonic()
    try:
        x.update()
    except Exception:
        # The library already reconnected the serial port.
        logger.warning("poll failed, retrying in %.0f s", retryDelay, exc_info=debug)
        time.sleep(retryDelay)
        next_run = time.monotonic()
        continue

    if debug:
        logger.debug("--- Calculated:\n%s", pformat(x.pylonData['Calculated']))
        logger.debug("--- SystemParameter:\n%s", pformat(x.pylonData['SystemParameter']))
    publish_values("", x.pylonData['Calculated'])
    publish_values("SystemParameter/", x.pylonData['SystemParameter'])

    for batteryIndex, serial in enumerate(serials):
        unit = "Unit/" + serial + "/"
        publish(unit + "SerialNumber", str(serial))
        publish_values(unit + "ChargeDischargeManagement/", x.pylonData['ChargeDischargeManagementList'][batteryIndex])
        publish_values(unit + "AlarmInfo/", x.pylonData['AlarmInfoList'][batteryIndex])
        publish_values(unit, x.pylonData['AnaloglList'][batteryIndex])

    if failed_publishes:
        logger.warning("%d MQTT messages not sent (broker not connected)", failed_publishes)
        failed_publishes = 0
    logger.debug("cycle took %.2f s", time.monotonic() - started)

    # Fixed period; if a cycle overruns, start the next one right away.
    next_run += updateInterval
    delay = next_run - time.monotonic()
    if delay > 0:
        time.sleep(delay)
    else:
        next_run = time.monotonic()
