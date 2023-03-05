# Life 360 to CoT
### A PyTAK application that gets members location in Life360 and pushes it to TAK as a CoT Event.


## Installation

1. Install `pipenv` using `python -m pip install pipenv`
2. Run `python -m pipenv install` to install the prerequisites.
3. Create a `config.ini` and adjust the settings to your use-case.

## Usage/Setup

### Running (as a standalone application)

Run `python -m pipenv run python main.py` to start the application.

### Running (as a service)

1. Modify `l360tocot.service` to the correct working directory, user, and shell script directory.
2. Copy it to the right directory using `cp l360tocot.service /etc/systemd/system/`
3. Run `sudo systemctl daemon-reload`
4. Run `sudo systemctl enable l360tocot` (if you want to run it at boot, otherwise skip this step)
5. Run `sudo systemctl start l360tocot` to start the service

### Example Config
This config connects to a TAK server instance via TLS (using a self-signed cert), pulls data and pushes CoT events every 30 minutes.

`config.ini`
```ini
[l360tocot]
COT_URL = tls://XX.XX.XX.XX:8089
PYTAK_TLS_CLIENT_CERT = private_key.pem
PYTAK_TLS_CLIENT_KEY = private_key.pem
PYTAK_TLS_DONT_VERIFY = true
POLL_INTERVAL = 1800
L360_USER_NAME = XXX
L360_PASSWORD = XXX
L360_AUTH_TOKEN = OWE5MDc4YTcxMjRkNjFkYjc1NGNjNzI4NjY2OTRkNWYwNDk2ODY2NDA6NjA2Nzk3MzkwODViYmMxZWY2ZjQyZjlmMDc3YjIwNTA
L360_GET_ALL_CIRCLES = false
```

## Credits:
### [life360-python](https://github.com/harperreed/life360-python) 
