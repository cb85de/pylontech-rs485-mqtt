FROM python:3.11

WORKDIR /code

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src/main.py .






CMD [ "python", "./main.py" ]
