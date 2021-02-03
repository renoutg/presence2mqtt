FROM python:slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ .

CMD ["python", "-u", "presence2mqtt.py"]
