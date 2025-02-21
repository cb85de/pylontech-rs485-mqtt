FROM python:3.11

WORKDIR /code

COPY src/main.py .






CMD [ "python", "./main.py" ]
