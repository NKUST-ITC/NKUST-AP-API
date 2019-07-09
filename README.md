[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)

NKUST-AP-API
==========

高雄科技大學 API Server NKUST API Server
---------------------------
Requirement
---
- Ubuntu (18.04 or previous version)
- Python 3.6
- Redis server
- NodeJS (if host by python venv)

API Docs
---
[docs](https://github.com/NKUST-ITC/AP-API/tree/develop/docs/v3)



Quick start
---
Use gunicorn with default config.

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt

cd src/
gunicorn web-server:app
```





Donate
---

[![BitCoin donate
button](http://img.shields.io/bitcoin/donate.png?color=yellow)](https://coinbase.com/checkouts/aa7cf80a2a85b4906cb98fc7b2aad5c5 "Donate
once-off to this project using BitCoin")


