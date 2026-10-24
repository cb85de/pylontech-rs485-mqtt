# slim instead of the full image: ~130 MB instead of ~870 MB on the Pi's SD
# card. Debian armel (linux/arm/v5) runs on the Pi Zero's ARMv6.
FROM python:3.11.11-slim-bookworm

ENV PYLONTECH_MQTT_HOST=localhost
ENV PYLONTECH_MQTT_PORT=1883
ENV PYLONTECH_MQTT_TOPIC="pylontech/"
ENV PYLONTECH_LOGGING_LEVEL=INFO
ENV PYLONTECH_UDATE_INTERVAL=10
ENV PYLONTECH_SERIAL_PORT=/dev/ttyAMA0
ENV PYLONTECH_BATTERY_COUNT=4

WORKDIR /code

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src/main.py .

CMD [ "python", "./main.py" ]
