[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)

NKUST-AP-API
==========
   * [NKUST-AP-API](#nkust-ap-api)
      * [Requirement](#requirement)
      * [API Docs](#api-docs)
      * [Quick start](#quick-start)
         * [By Python](#by-python)
         * [By Docker-compose](#by-docker-compose)
            * [HTTP](#http)
            * [HTTPS](#https)
            * [Other port](#other-port)



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
[docs](https://github.com/NKUST-ITC/NKUST-AP-API/tree/master/docs)



Quick start
---
### By Python



#### 必須環境變數

請先在local設定/安裝好Redis 

如果Redis有自行調整port或是使用外部的Redis

請在shell 設定環境變數或是到對應系統下的`.profile`設定

`export REDIS_URL=redis://127.0.0.1:6666`

沒有設定會依照Redis預設的`redis://127.0.0.1:6379` 去跑

#### 非必須環境變數

`export NEWS_ADMIN="1106111111;1105293392"`

此環境變數會設定最新消息的管理員，可以透過`;`來新增多位管理員



使用gunicorn預設 (for debug)

```bash
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install -r requirement.txt
$ gunicorn web-server:app
```



使用gonicorn cfg (release)

```bash
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install -r requirement.txt
$ gunicorn -c gunicorn_config.py web-server:app
```



---



### By Docker-compose

* NKUST-AP-API
* Redis
* Nginx
* Certbot



```bash
$ cp env.example .env
```

如需要更改redis位置，可以到.env中修改。

---

#### HTTP

設定好以下幾項設定檔案

開設http

```bash
#預設文件備份，以及更換要執行的設定檔案
$ mv nginx/nginx_nkust_api.conf nginx/nginx_nkust_api.conf.backup

$ cp nginx/nginx_nkust_api_http.conf.Example nginx/nginx_nkust_api.conf

$ docker-compose up -d
```

---

#### HTTPS

如果需要開設https 麻煩修改 `nginx/nginx_nkust_api.conf`

取代"**所有**"`example.org`更改為要開設的網域



**第一次執行**請先修改`init-letsencrypt.sh` `line 8~9`

```bash
domains=(aaa.example.org aaa.example.org)
email="aaaa@example.org" 
```

**第一次執行**

```bash
$ sudo chmod +x init-letsencrypt.sh
$ sudo ./init-letsencrypt.sh
```

(沒有任何錯誤及架設完成)

後續執行**不需要**使用`init-letsencrypt.sh` 



```bash
$ docker-compose up -d 
```



---

#### Other port 

如有其他port 的需求

修改`nginx/nginx_nkust_api.conf` 像是一般的nginx設定檔案


Donate
---

[![BitCoin donate
button](http://img.shields.io/bitcoin/donate.png?color=yellow)](https://coinbase.com/checkouts/aa7cf80a2a85b4906cb98fc7b2aad5c5 "Donate
once-off to this project using BitCoin")