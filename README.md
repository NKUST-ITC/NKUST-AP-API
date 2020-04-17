[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)


 NKUST API Server(高雄科技大學 API Server)
==========
* [Requirement](#requirement)
* [API Docs](#api-docs)
* [Quick start](#quick-start)
   * [Using Python virtual enviroment & Gunicorn](#using-python-virtual-enviroment-&-gunicorn)
   * [Using Docker-compose](#using-docker-compose)
     

Requirement
---
- Ubuntu (18.04 or previous version)
- Python 3.6
- Redis server
- NodeJS (if host by python venv)

### [API Docs](https://nkust-itc.github.io/NKUST-AP-API/docs/api-page.html)



Quick start
---
### Using Python virtual enviroment & Gunicorn

需要先在本地端設定/安裝好 [Redis server](https://redis.io/)

如果Redis有自行調整Host或Port或是使用外部的Redis，需執行

預設為本地的位置 `redis://127.0.0.1:6379` 執行

```bash
$ export REDIS_URL=redis://127.0.0.1:6666
```

若設定最新消息的管理員，可以透過`;`來新增多位管理員(非必須)

```bash
$ export NEWS_ADMIN="1106111111;1105293392"
```

或是設定一個帳號密碼，來登入管理員。

```bash
$ export NEWS_ADMIN_ACCOUNT="admin"
$ export NEWS_ADMIN_PASSWORD="1234567"
```

創建Python virtual enviroment

```bash
$ python3 -m venv venv
```

啟動 virtual enviroment

```bash
$ source venv/bin/activate
```

安裝相關packages

```bash
$ pip3 install -r requirement.txt
```

啟動伺服器(Debug 模式)

```bash
$ gunicorn web-server:app
```

啟動伺服器(Release 模式)

```bash
$ gunicorn -c gunicorn_config.py web-server:app
```

---



### Using Docker-compose (Production Stage)

#### docker-compose中的docker image

* [NKUST-AP-API](https://cloud.docker.com/u/nkustitc/repository/docker/nkustitc/nkust-ap-api/general)
* Redis
* Nginx
* Certbot



```bash
$ cp env.example .env
```

如果有要設定`最新消息`的管理者，可以在`.env`中修改 `NEWS_ADMIN` 參數

```
REDIS_URL=redis://redis:6379
```

如需要更改redis位置，可以在`.env`中修改 `REDIS_URL` 參數，

**這邊redis中的host是套用 `dokcer network` 的設定**

```
REDIS_URL=redis://redis:6379
```

複製 nginx 設定檔(HTTPS)

```bash
$ cp nginx/nginx_nkust_api.conf.Example nginx/nginx_nkust_api.conf
```

若需要單純使用 HTTP 則需複製 `nginx_nkust_api_http.conf.Example`

```bash
$ cp nginx/nginx_nkust_api_http.conf.Example nginx/nginx_nkust_api.conf
```

將`nginx_nkust_api_http.conf` 設定檔中 "**所有**"`example.org`取代為要目標的網域

```
2  server_name example.org;
...
17 server_name example.org;
```
更改為
```
2 server_name 目標網域;
...
17 server_name 目標網域;
```

### 註冊SSL憑證

修改`init-letsencrypt.sh` `line 8~9` 中的網域及email

```bash
8 domains=(aaa.example.org aaa.example.org)
9 email="aaaa@example.org" 
```

給予shell sript 權限

```bash
$ sudo chmod +x init-letsencrypt.sh
```

並執行shell sript註冊，此過程會開啟伺服器

```bash
$ sudo ./init-letsencrypt.sh
```

後續再次開啟**不需要**使用`init-letsencrypt.sh` 

最後執行docker-compose 開啟伺服器

-d 為背景執行，若不需要可以不用加

```bash
$ docker-compose up -d 
```

#### Other port 

如有其他port 的需求

修改`nginx/nginx_nkust_api.conf` 像是一般的nginx設定檔案