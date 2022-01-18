FROM python:3.11.0a4-alpine

WORKDIR /app

COPY requirements.txt .
RUN apk add --no-cache --virtual build-dependencies gcc musl-dev python3-dev libffi-dev openssl-dev cargo \
  && pip install -r requirements.txt \
  && apk del build-dependencies

COPY src/ .

CMD ["python", "-u", "presence2mqtt.py"]
