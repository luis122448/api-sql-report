Puedes decirma porque cuando despliego con docker compose con el comando sudo docker compose up --build --force-recreate --no-deps -d

no tengo ningun problema con la libreria instantclient

```Dockerfile
FROM python:3.11.12-slim
LABEL maintainer="luis122448"

WORKDIR /opt

COPY ./requirements.txt /opt/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /opt/requirements.txt
RUN apt-get update && \
    apt-get install -y --no-install-recommends unzip && \
    rm -rf /var/lib/apt/lists/*

COPY ./app /opt/app/
COPY ./oracle_home /opt/oracle_home/
COPY ./install-instantclient.sh /opt/install-instantclient.sh
RUN chmod +x /opt/install-instantclient.sh
RUN mkdir -p /opt/database

RUN /bin/bash -c "/opt/install-instantclient.sh"
RUN ls -l /opt/oracle_home/instantclient

RUN apt-get update && apt-get install -y libaio1

ENV LD_LIBRARY_PATH=/opt/oracle_home/instantclient
ENV ORACLE_HOME=/opt/oracle_home/instantclient

EXPOSE 8001
CMD [ "python", "app/server.py" ]
```

mis logs...

```log
luis122448@orange-001:/var/www/api-sql-reports/data-ingestor-python$ sudo docker-compose up --build --force-recreate --no-deps -d
[sudo] password for luis122448: 
WARN[0000] Docker Compose is configured to build using Bake, but buildx isn't installed 
[+] Building 11.5s (19/19) FINISHED                                                                              docker:default
 => [app internal] load build definition from Dockerfile                                                                   0.0s
 => => transferring dockerfile: 812B                                                                                       0.0s
 => [app internal] load metadata for docker.io/library/python:3.11.12-slim                                                11.1s
 => [app internal] load .dockerignore                                                                                      0.0s
 => => transferring context: 118B                                                                                          0.0s
 => [app  1/13] FROM docker.io/library/python:3.11.12-slim@sha256:dbf1de478a55d6763afaa39c2f3d7b54b25230614980276de5cacdd  0.0s
 => [app internal] load build context                                                                                      0.1s
 => => transferring context: 2.48kB                                                                                        0.0s
 => CACHED [app  2/13] WORKDIR /opt                                                                                        0.0s
 => CACHED [app  3/13] COPY ./requirements.txt /opt/requirements.txt                                                       0.0s
 => CACHED [app  4/13] RUN pip install --no-cache-dir --upgrade -r /opt/requirements.txt                                   0.0s
 => CACHED [app  5/13] RUN apt-get update &&     apt-get install -y --no-install-recommends unzip &&     rm -rf /var/lib/  0.0s
 => CACHED [app  6/13] COPY ./app /opt/app/                                                                                0.0s
 => CACHED [app  7/13] COPY ./oracle_home /opt/oracle_home/                                                                0.0s
 => CACHED [app  8/13] COPY ./install-instantclient.sh /opt/install-instantclient.sh                                       0.0s
 => CACHED [app  9/13] RUN chmod +x /opt/install-instantclient.sh                                                          0.0s
 => CACHED [app 10/13] RUN mkdir -p /opt/database                                                                          0.0s
 => CACHED [app 11/13] RUN /bin/bash -c "/opt/install-instantclient.sh"                                                    0.0s
 => CACHED [app 12/13] RUN ls -l /opt/oracle_home/instantclient                                                            0.0s
 => CACHED [app 13/13] RUN apt-get update && apt-get install -y libaio1                                                    0.0s
 => [app] exporting to image                                                                                               0.0s
 => => exporting layers                                                                                                    0.0s
 => => writing image sha256:1e73cfe87bb30d119d6e2b022998eab13b9e4f5ccc36aba825cab3c35271aa5c                               0.0s
 => => naming to docker.io/library/data-ingestor-python-app                                                                0.0s
 => [app] resolving provenance for metadata file                                                                           0.0s
[+] Running 2/2
 ! app Published ports are discarded when using host network mode                                                          0.1s 
 ✔ Container data-ingestor-python                                 Started                                                  1.1s 
luis122448@orange-001:/var/www/api-sql-reports/data-ingestor-python$ sudo docker ps
CONTAINER ID   IMAGE                      COMMAND                  CREATED          STATUS          PORTS     NAMES
08aa73eff742   data-ingestor-python-app   "python app/server.py"   14 seconds ago   Up 14 seconds             data-ingestor-python
luis122448@orange-001:/var/www/api-sql-reports/data-ingestor-python$ sudo docker logs 08aa73eff742
INFO:     Will watch for changes in these directories: ['/opt']
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process [1] using StatReload
INFO:configs.sqlite:Connecting to database at /opt/database/metadata.db
INFO:root:Database initialized successfully. Table METADATA_REPORT and SCHEDULED_JOBS_LOG are ready.
INFO:     Started server process [8]
INFO:     Waiting for application startup.
INFO:scheduling.scheduler:Starting report scheduler...
INFO:configs.sqlite:Connecting to database at /opt/database/metadata.db
INFO:scheduling.scheduler:Cleared SCHEDULED_JOBS_LOG on startup.
INFO:apscheduler.scheduler:Adding job tentatively -- it will be properly scheduled when the scheduler starts
INFO:scheduling.scheduler:Scheduled job to update report configurations every 60 minutes.
INFO:apscheduler.scheduler:Adding job tentatively -- it will be properly scheduled when the scheduler starts
INFO:scheduling.scheduler:Scheduled daily cleanup for old scheduler logs at 04:00 AM.
INFO:apscheduler.scheduler:Adding job tentatively -- it will be properly scheduled when the scheduler starts
INFO:scheduling.scheduler:Scheduled daily cleanup for old Minio objects at 05:00 AM.
INFO:scheduling.scheduler:Updating scheduled jobs from Oracle configuration
```

pero cuando lo despliego en kubernetes con el deploymen.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-ingestor-python
  namespace: api-sql-reports
spec:
  replicas: 2
  selector:
    matchLabels:
      app: data-ingestor-python
  template:
    metadata:
      labels:
        app: data-ingestor-python
    spec:
      containers:
        - name: data-ingestor-python
          image: luis122448/data-ingestor-python:v1.0.0
          env:
            - name: DB_ORACLE_USER
              valueFrom:
                secretKeyRef:
                  name: database-secrets
                  key: DB_ORACLE_USER
            - name: DB_ORACLE_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: database-secrets
                  key: DB_ORACLE_PASSWORD
            - name: DB_ORACLE_DSN
              valueFrom:
                secretKeyRef:
                  name: database-secrets
                  key: DB_ORACLE_DSN
            - name: MINIO_URL
              valueFrom:
                secretKeyRef:
                  name: database-secrets
                  key: MINIO_URL
            - name: MINIO_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: database-secrets
                  key: MINIO_ACCESS_KEY
            - name: MINIO_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: database-secrets
                  key: MINIO_SECRET_KEY
            - name: JWT_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: database-secrets
                  key: JWT_SECRET_KEY
          command: ["python", "app/server.py"]
          ports:
            - containerPort: 8001
          volumeMounts:
            - name: database-volume
              mountPath: /opt/database
      volumes:
        - name: database-volume
          persistentVolumeClaim:
            claimName: sqllite-pvc
        - name: openvpn-config
          secret:
            secretName: openvpn-client-config
        - name: openvpn-credentials
          secret:
            secretName: openvpn-credentials
      initContainers:
        - name: openvpn-client
          image: ghcr.io/wfg/openvpn-client:latest
          env:
            - name: VPN_CONFIG_FILE
              value: /tmp/client.ovpn
            - name: VPN_CREDENTIALS_FILE
              value: /tmp/credentials.txt
          volumeMounts:
            - name: openvpn-config
              mountPath: /etc/openvpn/config
              readOnly: true
            - name: openvpn-credentials
              mountPath: /etc/openvpn/credentials
              readOnly: true
          securityContext:
            capabilities:
              add: ["NET_ADMIN"]
          command: ["/bin/sh", "-c"]
          args:
            - |
              cp /etc/openvpn/config/client.ovpn /tmp/client.ovpn
              cp /etc/openvpn/credentials/credentials.txt /tmp/credentials.txt
              openvpn --config /tmp/client.ovpn --auth-user-pass /tmp/credentials.txt --daemon
              sleep 10 # Give OpenVPN some time to establish connection
      restartPolicy: Always
```

falla con el siguiente error:

```log
(.venv) luis122448@dev-003:/var/www/api-sql-reports/data-ingestor-python$ kubectl logs data-ingestor-python-6959499bd9-f8fgj -n api-sql-reports
Defaulted container "data-ingestor-python" out of: data-ingestor-python, openvpn-client (init)
INFO:     Will watch for changes in these directories: ['/opt']
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process [1] using StatReload
Process SpawnProcess-1:
Traceback (most recent call last):
  File "/usr/local/lib/python3.11/multiprocessing/process.py", line 314, in _bootstrap
    self.run()
  File "/usr/local/lib/python3.11/multiprocessing/process.py", line 108, in run
    self._target(*self._args, **self._kwargs)
  File "/usr/local/lib/python3.11/site-packages/uvicorn/_subprocess.py", line 80, in subprocess_started
    target(sockets=sockets)
  File "/usr/local/lib/python3.11/site-packages/uvicorn/server.py", line 67, in run
    return asyncio.run(self.serve(sockets=sockets))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/asyncio/runners.py", line 190, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/asyncio/base_events.py", line 654, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/uvicorn/server.py", line 71, in serve
    await self._serve(sockets)
  File "/usr/local/lib/python3.11/site-packages/uvicorn/server.py", line 78, in _serve
    config.load()
  File "/usr/local/lib/python3.11/site-packages/uvicorn/config.py", line 436, in load
    self.loaded_app = import_from_string(self.app)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/uvicorn/importer.py", line 19, in import_from_string
    module = importlib.import_module(module_str)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 940, in exec_module
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "/opt/app/main.py", line 2, in <module>
    from routers import extract_router, metadata_router, analytics_router
  File "/opt/app/routers/extract_router.py", line 4, in <module>
    from services.extract_service import ExtractService
  File "/opt/app/services/extract_service.py", line 6, in <module>
    from configs.oracle import OracleTransaction
  File "/opt/app/configs/oracle.py", line 26, in <module>
    oracledb.init_oracle_client(lib_dir=instant_client_path)
  File "src/oracledb/impl/thick/utils.pyx", line 527, in oracledb.thick_impl.init_oracle_client
  File "src/oracledb/impl/thick/utils.pyx", line 562, in oracledb.thick_impl.init_oracle_client
  File "src/oracledb/impl/thick/utils.pyx", line 474, in oracledb.thick_impl._raise_from_info
oracledb.exceptions.DatabaseError: DPI-1047: Cannot locate a 64-bit Oracle Client library: "/opt/oracle_home/instantclient/libclntsh.so: cannot open shared object file: No such file or directory". See https://python-oracledb.readthedocs.io/en/latest/user_guide/initialization.html for help
Help: https://python-oracledb.readthedocs.io/en/latest/user_guide/troubleshooting.html#dpi-1047
(.venv) luis122448@dev-003:/var/www/api-sql-reports/data-ingestor-python$ 
```

te paso ademaas los logs de la compilacion y publicacion de la imagen en docker hub

```log
Building and pushing luis122448/data-ingestor-python:v1.0.0 for linux/amd64 and linux/arm64...
#0 building with "mybuilder" instance using docker-container driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 765B done
#1 DONE 0.0s

#2 [auth] library/python:pull token for registry-1.docker.io
#2 DONE 0.0s

#3 [linux/amd64 internal] load metadata for docker.io/library/python:3.11.12-slim
#3 DONE 0.8s

#4 [linux/arm64 internal] load metadata for docker.io/library/python:3.11.12-slim
#4 DONE 0.9s

#5 [internal] load .dockerignore
#5 transferring context: 124B done
#5 DONE 0.1s

#6 [internal] load build context
#6 DONE 0.0s

#7 [linux/amd64  1/13] FROM docker.io/library/python:3.11.12-slim@sha256:dbf1de478a55d6763afaa39c2f3d7b54b25230614980276de5cacdde79529d0c
#7 resolve docker.io/library/python:3.11.12-slim@sha256:dbf1de478a55d6763afaa39c2f3d7b54b25230614980276de5cacdde79529d0c 0.1s done
#7 DONE 0.1s

#8 [linux/amd64  2/13] WORKDIR /opt
#8 CACHED

#9 [linux/arm64  1/13] FROM docker.io/library/python:3.11.12-slim@sha256:dbf1de478a55d6763afaa39c2f3d7b54b25230614980276de5cacdde79529d0c
#9 resolve docker.io/library/python:3.11.12-slim@sha256:dbf1de478a55d6763afaa39c2f3d7b54b25230614980276de5cacdde79529d0c 0.2s done
#9 DONE 0.2s

#10 [linux/arm64  2/13] WORKDIR /opt
#10 CACHED

#6 [internal] load build context
#6 transferring context: 9.76kB done
#6 DONE 0.1s

#11 [linux/amd64  3/13] COPY ./requirements.txt /opt/requirements.txt
#11 DONE 0.2s

#12 [linux/arm64  3/13] COPY ./requirements.txt /opt/requirements.txt
#12 DONE 0.2s

#13 [linux/arm64  4/13] RUN pip install --no-cache-dir --upgrade -r /opt/requirements.txt
#13 ...

#14 [linux/amd64  4/13] RUN pip install --no-cache-dir --upgrade -r /opt/requirements.txt
#14 2.654 Collecting annotated-types==0.7.0 (from -r /opt/requirements.txt (line 1))
#14 2.723   Downloading annotated_types-0.7.0-py3-none-any.whl.metadata (15 kB)
#14 2.742 Collecting anyio==4.9.0 (from -r /opt/requirements.txt (line 2))
#14 2.747   Downloading anyio-4.9.0-py3-none-any.whl.metadata (4.7 kB)
#14 2.823 Collecting cffi==1.17.1 (from -r /opt/requirements.txt (line 3))
#14 2.829   Downloading cffi-1.17.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (1.5 kB)
#14 2.846 Collecting click==8.2.1 (from -r /opt/requirements.txt (line 4))
#14 2.851   Downloading click-8.2.1-py3-none-any.whl.metadata (2.5 kB)
#14 2.960 Collecting cryptography==45.0.4 (from -r /opt/requirements.txt (line 5))
#14 2.981   Downloading cryptography-45.0.4-cp311-abi3-manylinux_2_34_x86_64.whl.metadata (5.7 kB)
#14 3.017 Collecting fastapi==0.115.14 (from -r /opt/requirements.txt (line 6))
#14 3.022   Downloading fastapi-0.115.14-py3-none-any.whl.metadata (27 kB)
#14 3.035 Collecting h11==0.16.0 (from -r /opt/requirements.txt (line 7))
#14 3.039   Downloading h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
#14 3.078 Collecting idna==3.10 (from -r /opt/requirements.txt (line 8))
#14 3.083   Downloading idna-3.10-py3-none-any.whl.metadata (10 kB)
#14 3.205 Collecting numpy==2.3.1 (from -r /opt/requirements.txt (line 9))
#14 3.211   Downloading numpy-2.3.1-cp311-cp311-manylinux_2_28_x86_64.whl.metadata (62 kB)
#14 3.214      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 62.1/62.1 kB 41.0 MB/s eta 0:00:00
#14 3.258 Collecting oracledb==3.2.0 (from -r /opt/requirements.txt (line 10))
#14 3.264   Downloading oracledb-3.2.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (6.5 kB)
#14 3.331 Collecting pandas==2.3.0 (from -r /opt/requirements.txt (line 11))
#14 3.336   Downloading pandas-2.3.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (91 kB)
#14 3.338      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 91.2/91.2 kB 280.4 MB/s eta 0:00:00
#14 3.395 Collecting pyarrow==20.0.0 (from -r /opt/requirements.txt (line 12))
#14 3.406   Downloading pyarrow-20.0.0-cp311-cp311-manylinux_2_28_x86_64.whl.metadata (3.3 kB)
#14 3.416 Collecting pycparser==2.22 (from -r /opt/requirements.txt (line 13))
#14 3.421   Downloading pycparser-2.22-py3-none-any.whl.metadata (943 bytes)
#14 3.540 Collecting pydantic==2.11.7 (from -r /opt/requirements.txt (line 14))
#14 3.545   Downloading pydantic-2.11.7-py3-none-any.whl.metadata (67 kB)
#14 3.547      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 68.0/68.0 kB 498.1 MB/s eta 0:00:00
#14 3.938 Collecting pydantic_core==2.33.2 (from -r /opt/requirements.txt (line 15))
#14 3.943   Downloading pydantic_core-2.33.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (6.8 kB)
#14 3.957 Collecting python-dateutil==2.9.0.post0 (from -r /opt/requirements.txt (line 16))
#14 3.970   Downloading python_dateutil-2.9.0.post0-py2.py3-none-any.whl.metadata (8.4 kB)
#14 3.997 Collecting python-dotenv==1.1.1 (from -r /opt/requirements.txt (line 17))
#14 4.001   Downloading python_dotenv-1.1.1-py3-none-any.whl.metadata (24 kB)
#14 4.032 Collecting pytz==2025.2 (from -r /opt/requirements.txt (line 18))
#14 4.037   Downloading pytz-2025.2-py2.py3-none-any.whl.metadata (22 kB)
#14 4.049 Collecting six==1.17.0 (from -r /opt/requirements.txt (line 19))
#14 4.053   Downloading six-1.17.0-py2.py3-none-any.whl.metadata (1.7 kB)
#14 4.071 Collecting sniffio==1.3.1 (from -r /opt/requirements.txt (line 20))
#14 4.076   Downloading sniffio-1.3.1-py3-none-any.whl.metadata (3.9 kB)
#14 4.120 Collecting starlette==0.46.2 (from -r /opt/requirements.txt (line 21))
#14 4.125   Downloading starlette-0.46.2-py3-none-any.whl.metadata (6.2 kB)
#14 4.136 Collecting typing-inspection==0.4.1 (from -r /opt/requirements.txt (line 22))
#14 4.141   Downloading typing_inspection-0.4.1-py3-none-any.whl.metadata (2.6 kB)
#14 4.155 Collecting typing_extensions==4.14.0 (from -r /opt/requirements.txt (line 23))
#14 4.159   Downloading typing_extensions-4.14.0-py3-none-any.whl.metadata (3.0 kB)
#14 4.172 Collecting tzdata==2025.2 (from -r /opt/requirements.txt (line 25))
#14 4.176   Downloading tzdata-2025.2-py2.py3-none-any.whl.metadata (1.4 kB)
#14 4.197 Collecting uvicorn==0.35.0 (from -r /opt/requirements.txt (line 26))
#14 4.201   Downloading uvicorn-0.35.0-py3-none-any.whl.metadata (6.5 kB)
#14 4.227 Collecting minio==7.2.7 (from -r /opt/requirements.txt (line 27))
#14 4.232   Downloading minio-7.2.7-py3-none-any.whl.metadata (6.4 kB)
#14 4.342 Collecting APScheduler==3.10.4 (from -r /opt/requirements.txt (line 28))
#14 4.348   Downloading APScheduler-3.10.4-py3-none-any.whl.metadata (5.7 kB)
#14 4.363 Collecting PyJWT==2.8.0 (from -r /opt/requirements.txt (line 29))
#14 4.371   Downloading PyJWT-2.8.0-py3-none-any.whl.metadata (4.2 kB)
#14 4.620 Collecting certifi (from minio==7.2.7->-r /opt/requirements.txt (line 27))
#14 4.626   Downloading certifi-2025.6.15-py3-none-any.whl.metadata (2.4 kB)
#14 4.651 Collecting urllib3 (from minio==7.2.7->-r /opt/requirements.txt (line 27))
#14 4.668   Downloading urllib3-2.5.0-py3-none-any.whl.metadata (6.5 kB)
#14 4.686 Collecting argon2-cffi (from minio==7.2.7->-r /opt/requirements.txt (line 27))
#14 4.698   Downloading argon2_cffi-25.1.0-py3-none-any.whl.metadata (4.1 kB)
#14 4.751 Collecting pycryptodome (from minio==7.2.7->-r /opt/requirements.txt (line 27))
#14 4.761   Downloading pycryptodome-3.23.0-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (3.4 kB)
#14 4.786 Collecting tzlocal!=3.*,>=2.0 (from APScheduler==3.10.4->-r /opt/requirements.txt (line 28))
#14 4.792   Downloading tzlocal-5.3.1-py3-none-any.whl.metadata (7.6 kB)
#14 4.816 Collecting argon2-cffi-bindings (from argon2-cffi->minio==7.2.7->-r /opt/requirements.txt (line 27))
#14 4.824   Downloading argon2_cffi_bindings-21.2.0-cp36-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (6.7 kB)
#14 4.847 Downloading annotated_types-0.7.0-py3-none-any.whl (13 kB)
#14 4.853 Downloading anyio-4.9.0-py3-none-any.whl (100 kB)
#14 4.854    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.9/100.9 kB 484.1 MB/s eta 0:00:00
#14 4.859 Downloading cffi-1.17.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (467 kB)
#14 4.865    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 467.2/467.2 kB 108.6 MB/s eta 0:00:00
#14 4.870 Downloading click-8.2.1-py3-none-any.whl (102 kB)
#14 4.872    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 102.2/102.2 kB 247.9 MB/s eta 0:00:00
#14 4.877 Downloading cryptography-45.0.4-cp311-abi3-manylinux_2_34_x86_64.whl (4.5 MB)
#14 4.921    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.5/4.5 MB 104.8 MB/s eta 0:00:00
#14 4.926 Downloading fastapi-0.115.14-py3-none-any.whl (95 kB)
#14 4.928    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 95.5/95.5 kB 581.8 MB/s eta 0:00:00
#14 4.931 Downloading h11-0.16.0-py3-none-any.whl (37 kB)
#14 4.936 Downloading idna-3.10-py3-none-any.whl (70 kB)
#14 4.937    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 70.4/70.4 kB 462.8 MB/s eta 0:00:00
#14 4.942 Downloading numpy-2.3.1-cp311-cp311-manylinux_2_28_x86_64.whl (16.9 MB)
#14 5.150    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 16.9/16.9 MB 98.5 MB/s eta 0:00:00
#14 5.156 Downloading oracledb-3.2.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (2.7 MB)
#14 5.181    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.7/2.7 MB 112.2 MB/s eta 0:00:00
#14 5.196 Downloading pandas-2.3.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (12.4 MB)
#14 5.368    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 12.4/12.4 MB 79.2 MB/s eta 0:00:00
#14 5.375 Downloading pyarrow-20.0.0-cp311-cp311-manylinux_2_28_x86_64.whl (42.3 MB)
#14 6.040    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 42.3/42.3 MB 48.8 MB/s eta 0:00:00
#14 6.044 Downloading pycparser-2.22-py3-none-any.whl (117 kB)
#14 6.047    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 117.6/117.6 kB 128.4 MB/s eta 0:00:00
#14 6.051 Downloading pydantic-2.11.7-py3-none-any.whl (444 kB)
#14 6.062    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 444.8/444.8 kB 47.4 MB/s eta 0:00:00
#14 6.070 Downloading pydantic_core-2.33.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.0 MB)
#14 6.111    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.0/2.0 MB 50.8 MB/s eta 0:00:00
#14 6.115 Downloading python_dateutil-2.9.0.post0-py2.py3-none-any.whl (229 kB)
#14 6.120    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 229.9/229.9 kB 67.5 MB/s eta 0:00:00
#14 6.124 Downloading python_dotenv-1.1.1-py3-none-any.whl (20 kB)
#14 6.129 Downloading pytz-2025.2-py2.py3-none-any.whl (509 kB)
#14 6.139    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 509.2/509.2 kB 58.7 MB/s eta 0:00:00
#14 6.143 Downloading six-1.17.0-py2.py3-none-any.whl (11 kB)
#14 6.148 Downloading sniffio-1.3.1-py3-none-any.whl (10 kB)
#14 6.153 Downloading starlette-0.46.2-py3-none-any.whl (72 kB)
#14 6.155    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 72.0/72.0 kB 160.7 MB/s eta 0:00:00
#14 6.159 Downloading typing_inspection-0.4.1-py3-none-any.whl (14 kB)
#14 6.164 Downloading typing_extensions-4.14.0-py3-none-any.whl (43 kB)
#14 6.165    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 43.8/43.8 kB 434.7 MB/s eta 0:00:00
#14 6.170 Downloading tzdata-2025.2-py2.py3-none-any.whl (347 kB)
#14 6.177    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 347.8/347.8 kB 59.7 MB/s eta 0:00:00
#14 6.182 Downloading uvicorn-0.35.0-py3-none-any.whl (66 kB)
#14 6.183    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 66.4/66.4 kB 460.6 MB/s eta 0:00:00
#14 6.189 Downloading minio-7.2.7-py3-none-any.whl (93 kB)
#14 6.191    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 93.5/93.5 kB 246.8 MB/s eta 0:00:00
#14 6.196 Downloading APScheduler-3.10.4-py3-none-any.whl (59 kB)
#14 6.198    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 59.3/59.3 kB 366.2 MB/s eta 0:00:00
#14 6.203 Downloading PyJWT-2.8.0-py3-none-any.whl (22 kB)
#14 6.207 Downloading tzlocal-5.3.1-py3-none-any.whl (18 kB)
#14 6.212 Downloading argon2_cffi-25.1.0-py3-none-any.whl (14 kB)
#14 6.216 Downloading certifi-2025.6.15-py3-none-any.whl (157 kB)
#14 6.220    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 157.7/157.7 kB 63.7 MB/s eta 0:00:00
#14 6.226 Downloading pycryptodome-3.23.0-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.3 MB)
#14 6.268    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.3/2.3 MB 55.8 MB/s eta 0:00:00
#14 6.272 Downloading urllib3-2.5.0-py3-none-any.whl (129 kB)
#14 6.275    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 129.8/129.8 kB 253.9 MB/s eta 0:00:00
#14 6.279 Downloading argon2_cffi_bindings-21.2.0-cp36-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (86 kB)
#14 6.280    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 86.2/86.2 kB 408.4 MB/s eta 0:00:00
#14 6.493 Installing collected packages: pytz, urllib3, tzlocal, tzdata, typing_extensions, sniffio, six, python-dotenv, PyJWT, pycryptodome, pycparser, pyarrow, numpy, idna, h11, click, certifi, annotated-types, uvicorn, typing-inspection, python-dateutil, pydantic_core, cffi, APScheduler, anyio, starlette, pydantic, pandas, cryptography, argon2-cffi-bindings, oracledb, fastapi, argon2-cffi, minio
#14 ...

#13 [linux/arm64  4/13] RUN pip install --no-cache-dir --upgrade -r /opt/requirements.txt
#13 11.15 Collecting annotated-types==0.7.0 (from -r /opt/requirements.txt (line 1))
#13 11.57   Downloading annotated_types-0.7.0-py3-none-any.whl.metadata (15 kB)
#13 11.83 Collecting anyio==4.9.0 (from -r /opt/requirements.txt (line 2))
#13 11.84   Downloading anyio-4.9.0-py3-none-any.whl.metadata (4.7 kB)
#13 12.78 Collecting cffi==1.17.1 (from -r /opt/requirements.txt (line 3))
#13 12.79   Downloading cffi-1.17.1-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl.metadata (1.5 kB)
#13 12.96 Collecting click==8.2.1 (from -r /opt/requirements.txt (line 4))
#13 12.98   Downloading click-8.2.1-py3-none-any.whl.metadata (2.5 kB)
#13 ...

#14 [linux/amd64  4/13] RUN pip install --no-cache-dir --upgrade -r /opt/requirements.txt
#14 12.57 Successfully installed APScheduler-3.10.4 PyJWT-2.8.0 annotated-types-0.7.0 anyio-4.9.0 argon2-cffi-25.1.0 argon2-cffi-bindings-21.2.0 certifi-2025.6.15 cffi-1.17.1 click-8.2.1 cryptography-45.0.4 fastapi-0.115.14 h11-0.16.0 idna-3.10 minio-7.2.7 numpy-2.3.1 oracledb-3.2.0 pandas-2.3.0 pyarrow-20.0.0 pycparser-2.22 pycryptodome-3.23.0 pydantic-2.11.7 pydantic_core-2.33.2 python-dateutil-2.9.0.post0 python-dotenv-1.1.1 pytz-2025.2 six-1.17.0 sniffio-1.3.1 starlette-0.46.2 typing-inspection-0.4.1 typing_extensions-4.14.0 tzdata-2025.2 tzlocal-5.3.1 urllib3-2.5.0 uvicorn-0.35.0
#14 12.57 WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv
#14 12.68 
#14 12.68 [notice] A new release of pip is available: 24.0 -> 25.1.1
#14 12.68 [notice] To update, run: pip install --upgrade pip
#14 DONE 14.1s

#15 [linux/amd64  5/13] RUN apt-get update &&     apt-get install -y --no-install-recommends unzip &&     rm -rf /var/lib/apt/lists/*
#15 0.329 Get:1 http://deb.debian.org/debian bookworm InRelease [151 kB]
#15 0.346 Get:2 http://deb.debian.org/debian bookworm-updates InRelease [55.4 kB]
#15 0.349 Get:3 http://deb.debian.org/debian-security bookworm-security InRelease [48.0 kB]
#15 0.533 Get:4 http://deb.debian.org/debian bookworm/main amd64 Packages [8793 kB]
#15 0.665 Get:5 http://deb.debian.org/debian bookworm-updates/main amd64 Packages [756 B]
#15 0.670 Get:6 http://deb.debian.org/debian-security bookworm-security/main amd64 Packages [269 kB]
#15 1.414 Fetched 9318 kB in 1s (8813 kB/s)
#15 1.414 Reading package lists...
#15 1.835 Reading package lists...
#15 2.241 Building dependency tree...
#15 2.355 Reading state information...
#15 2.536 Suggested packages:
#15 2.536   zip
#15 2.582 The following NEW packages will be installed:
#15 2.582   unzip
#15 2.698 0 upgraded, 1 newly installed, 0 to remove and 3 not upgraded.
#15 2.698 Need to get 166 kB of archives.
#15 2.698 After this operation, 388 kB of additional disk space will be used.
#15 2.698 Get:1 http://deb.debian.org/debian bookworm/main amd64 unzip amd64 6.0-28 [166 kB]
#15 4.228 debconf: delaying package configuration, since apt-utils is not installed
#15 4.369 Fetched 166 kB in 0s (1502 kB/s)
#15 4.544 Selecting previously unselected package unzip.
#15 4.544 (Reading database ... 
(Reading database ... 5%
(Reading database ... 10%
(Reading database ... 15%
(Reading database ... 20%
(Reading database ... 25%
(Reading database ... 30%
(Reading database ... 35%
(Reading database ... 40%
(Reading database ... 45%
(Reading database ... 50%
(Reading database ... 55%
(Reading database ... 60%
(Reading database ... 65%
(Reading database ... 70%
(Reading database ... 75%
(Reading database ... 80%
(Reading database ... 85%
(Reading database ... 90%
(Reading database ... 95%
(Reading database ... 100%
(Reading database ... 6686 files and directories currently installed.)
#15 6.023 Preparing to unpack .../unzip_6.0-28_amd64.deb ...
#15 6.051 Unpacking unzip (6.0-28) ...
#15 6.198 Setting up unzip (6.0-28) ...
#15 DONE 6.4s

#13 [linux/arm64  4/13] RUN pip install --no-cache-dir --upgrade -r /opt/requirements.txt
#13 14.71 Collecting cryptography==45.0.4 (from -r /opt/requirements.txt (line 5))
#13 14.73   Downloading cryptography-45.0.4-cp311-abi3-manylinux_2_34_aarch64.whl.metadata (5.7 kB)
#13 15.48 Collecting fastapi==0.115.14 (from -r /opt/requirements.txt (line 6))
#13 15.50   Downloading fastapi-0.115.14-py3-none-any.whl.metadata (27 kB)
#13 15.60 Collecting h11==0.16.0 (from -r /opt/requirements.txt (line 7))
#13 15.61   Downloading h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
#13 15.73 Collecting idna==3.10 (from -r /opt/requirements.txt (line 8))
#13 15.75   Downloading idna-3.10-py3-none-any.whl.metadata (10 kB)
#13 17.68 Collecting numpy==2.3.1 (from -r /opt/requirements.txt (line 9))
#13 17.78   Downloading numpy-2.3.1-cp311-cp311-manylinux_2_28_aarch64.whl.metadata (62 kB)
#13 17.81      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 62.1/62.1 kB 40.0 MB/s eta 0:00:00
#13 18.48 Collecting oracledb==3.2.0 (from -r /opt/requirements.txt (line 10))
#13 18.50   Downloading oracledb-3.2.0-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.metadata (6.5 kB)
#13 19.66 Collecting pandas==2.3.0 (from -r /opt/requirements.txt (line 11))
#13 19.67   Downloading pandas-2.3.0-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl.metadata (91 kB)
#13 19.69      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 91.2/91.2 kB 45.1 MB/s eta 0:00:00
#13 ...

#16 [linux/amd64  6/13] COPY ./app /opt/app/
#16 DONE 0.1s

#13 [linux/arm64  4/13] RUN pip install --no-cache-dir --upgrade -r /opt/requirements.txt
#13 20.71 Collecting pyarrow==20.0.0 (from -r /opt/requirements.txt (line 12))
#13 20.73   Downloading pyarrow-20.0.0-cp311-cp311-manylinux_2_28_aarch64.whl.metadata (3.3 kB)
#13 20.82 Collecting pycparser==2.22 (from -r /opt/requirements.txt (line 13))
#13 20.84   Downloading pycparser-2.22-py3-none-any.whl.metadata (943 bytes)
#13 ...

#17 [linux/amd64  7/13] COPY ./oracle_home /opt/oracle_home/
#17 DONE 1.4s

#18 [linux/amd64  8/13] COPY ./install-instantclient.sh /opt/install-instantclient.sh
#18 DONE 0.1s

#13 [linux/arm64  4/13] RUN pip install --no-cache-dir --upgrade -r /opt/requirements.txt
#13 22.27 Collecting pydantic==2.11.7 (from -r /opt/requirements.txt (line 14))
#13 ...

#19 [linux/amd64  9/13] RUN chmod +x /opt/install-instantclient.sh
#19 DONE 0.2s

#13 [linux/arm64  4/13] RUN pip install --no-cache-dir --upgrade -r /opt/requirements.txt
#13 22.29   Downloading pydantic-2.11.7-py3-none-any.whl.metadata (67 kB)
#13 22.30      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 68.0/68.0 kB 37.0 MB/s eta 0:00:00
#13 ...

#20 [linux/amd64 10/13] RUN mkdir -p /opt/database
#20 DONE 0.2s

#21 [linux/amd64 11/13] RUN /bin/bash -c "/opt/install-instantclient.sh"
#21 0.107 Archive:  ./oracle_home/instantclient-basic-linux.x64-23.8.0.25.04.zip
#21 0.112   inflating: /opt/oracle_home/META-INF/MANIFEST.MF  
#21 0.112   inflating: /opt/oracle_home/META-INF/ORACLE_C.SF  
#21 0.112   inflating: /opt/oracle_home/META-INF/ORACLE_C.RSA  
#21 0.112   inflating: /opt/oracle_home/instantclient_23_8/adrci  
#21 0.113   inflating: /opt/oracle_home/instantclient_23_8/BASIC_LICENSE  
#21 0.113   inflating: /opt/oracle_home/instantclient_23_8/BASIC_README  
#21 0.113   inflating: /opt/oracle_home/instantclient_23_8/fips.so  
#21 0.124   inflating: /opt/oracle_home/instantclient_23_8/genezi  
#21 0.125   inflating: /opt/oracle_home/instantclient_23_8/legacy.so  
#21 0.152     linking: /opt/oracle_home/instantclient_23_8/libclntshcore.so  -> libclntshcore.so.23.1 
#21 0.152     linking: /opt/oracle_home/instantclient_23_8/libclntshcore.so.12.1  -> libclntshcore.so.23.1 
#21 0.152     linking: /opt/oracle_home/instantclient_23_8/libclntshcore.so.18.1  -> libclntshcore.so.23.1 
#21 0.152     linking: /opt/oracle_home/instantclient_23_8/libclntshcore.so.19.1  -> libclntshcore.so.23.1 
#21 0.152     linking: /opt/oracle_home/instantclient_23_8/libclntshcore.so.20.1  -> libclntshcore.so.23.1 
#21 0.152     linking: /opt/oracle_home/instantclient_23_8/libclntshcore.so.21.1  -> libclntshcore.so.23.1 
#21 0.152     linking: /opt/oracle_home/instantclient_23_8/libclntshcore.so.22.1  -> libclntshcore.so.23.1 
#21 0.152   inflating: /opt/oracle_home/instantclient_23_8/libclntshcore.so.23.1  
#21 0.183     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so  -> libclntsh.so.23.1 
#21 0.183     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so.10.1  -> libclntsh.so.23.1 
#21 0.183     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so.11.1  -> libclntsh.so.23.1 
#21 0.183     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so.12.1  -> libclntsh.so.23.1 
#21 0.183     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so.18.1  -> libclntsh.so.23.1 
#21 0.183     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so.19.1  -> libclntsh.so.23.1 
#21 0.183     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so.20.1  -> libclntsh.so.23.1 
#21 0.183     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so.21.1  -> libclntsh.so.23.1 
#21 0.183     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so.22.1  -> libclntsh.so.23.1 
#21 0.183   inflating: /opt/oracle_home/instantclient_23_8/libclntsh.so.23.1  
#21 0.668   inflating: /opt/oracle_home/instantclient_23_8/libnnz.so  
#21 0.721     linking: /opt/oracle_home/instantclient_23_8/libocci.so  -> libocci.so.23.1 
#21 0.721     linking: /opt/oracle_home/instantclient_23_8/libocci.so.10.1  -> libocci.so.23.1 
#21 0.722     linking: /opt/oracle_home/instantclient_23_8/libocci.so.11.1  -> libocci.so.23.1 
#21 0.722     linking: /opt/oracle_home/instantclient_23_8/libocci.so.12.1  -> libocci.so.23.1 
#21 0.722     linking: /opt/oracle_home/instantclient_23_8/libocci.so.18.1  -> libocci.so.23.1 
#21 0.722     linking: /opt/oracle_home/instantclient_23_8/libocci.so.19.1  -> libocci.so.23.1 
#21 0.722     linking: /opt/oracle_home/instantclient_23_8/libocci.so.20.1  -> libocci.so.23.1 
#21 0.722     linking: /opt/oracle_home/instantclient_23_8/libocci.so.21.1  -> libocci.so.23.1 
#21 0.722     linking: /opt/oracle_home/instantclient_23_8/libocci.so.22.1  -> libocci.so.23.1 
#21 0.722   inflating: /opt/oracle_home/instantclient_23_8/libocci.so.23.1  
#21 0.728   inflating: /opt/oracle_home/instantclient_23_8/libociei.so  
#21 1.696   inflating: /opt/oracle_home/instantclient_23_8/libocijdbc23.so  
#21 1.697   inflating: /opt/oracle_home/instantclient_23_8/libtfojdbc1.so  
#21 1.697    creating: /opt/oracle_home/instantclient_23_8/network/
#21 1.697   inflating: /opt/oracle_home/instantclient_23_8/ojdbc11.jar  
#21 1.737   inflating: /opt/oracle_home/instantclient_23_8/ojdbc17.jar  
#21 1.769   inflating: /opt/oracle_home/instantclient_23_8/ojdbc8.jar  
#21 1.804   inflating: /opt/oracle_home/instantclient_23_8/pkcs11.so  
#21 1.834   inflating: /opt/oracle_home/instantclient_23_8/ucp11.jar  
#21 1.842   inflating: /opt/oracle_home/instantclient_23_8/ucp17.jar  
#21 1.850   inflating: /opt/oracle_home/instantclient_23_8/ucp.jar  
#21 1.857   inflating: /opt/oracle_home/instantclient_23_8/uidrvci  
#21 1.858   inflating: /opt/oracle_home/instantclient_23_8/xstreams.jar  
#21 1.858    creating: /opt/oracle_home/instantclient_23_8/network/admin/
#21 1.858   inflating: /opt/oracle_home/instantclient_23_8/network/admin/README  
#21 1.858 finishing deferred symbolic links:
#21 1.858   /opt/oracle_home/instantclient_23_8/libclntshcore.so -> libclntshcore.so.23.1
#21 1.858   /opt/oracle_home/instantclient_23_8/libclntshcore.so.12.1 -> libclntshcore.so.23.1
#21 1.858   /opt/oracle_home/instantclient_23_8/libclntshcore.so.18.1 -> libclntshcore.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libclntshcore.so.19.1 -> libclntshcore.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libclntshcore.so.20.1 -> libclntshcore.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libclntshcore.so.21.1 -> libclntshcore.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libclntshcore.so.22.1 -> libclntshcore.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libclntsh.so -> libclntsh.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libclntsh.so.10.1 -> libclntsh.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libclntsh.so.11.1 -> libclntsh.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libclntsh.so.12.1 -> libclntsh.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libclntsh.so.18.1 -> libclntsh.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libclntsh.so.19.1 -> libclntsh.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libclntsh.so.20.1 -> libclntsh.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libclntsh.so.21.1 -> libclntsh.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libclntsh.so.22.1 -> libclntsh.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libocci.so -> libocci.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libocci.so.10.1 -> libocci.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libocci.so.11.1 -> libocci.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libocci.so.12.1 -> libocci.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libocci.so.18.1 -> libocci.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libocci.so.19.1 -> libocci.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libocci.so.20.1 -> libocci.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libocci.so.21.1 -> libocci.so.23.1
#21 1.859   /opt/oracle_home/instantclient_23_8/libocci.so.22.1 -> libocci.so.23.1
#21 1.861 Archive:  ./oracle_home/instantclient-sqlplus-linux.x64-23.8.0.25.04.zip
#21 1.861   inflating: /opt/oracle_home/instantclient_23_8/glogin.sql  
#21 1.861   inflating: /opt/oracle_home/instantclient_23_8/libsqlplusic.so  
#21 1.963   inflating: /opt/oracle_home/instantclient_23_8/libsqlplus.so  
#21 1.971   inflating: /opt/oracle_home/instantclient_23_8/sqlplus  
#21 1.971   inflating: /opt/oracle_home/instantclient_23_8/SQLPLUS_LICENSE  
#21 1.971   inflating: /opt/oracle_home/instantclient_23_8/SQLPLUS_README  
#21 1.973 Archive:  ./oracle_home/instantclient-tools-linux.x64-23.8.0.25.04.zip
#21 1.975   inflating: /opt/oracle_home/instantclient_23_8/exp  
#21 1.977   inflating: /opt/oracle_home/instantclient_23_8/expdp  
#21 1.979   inflating: /opt/oracle_home/instantclient_23_8/imp  
#21 1.981   inflating: /opt/oracle_home/instantclient_23_8/impdp  
#21 1.983   inflating: /opt/oracle_home/instantclient_23_8/libnfsodm.so  
#21 1.983   inflating: /opt/oracle_home/instantclient_23_8/libopcodm.so  
#21 1.984   inflating: /opt/oracle_home/instantclient_23_8/sqlldr  
#21 1.996   inflating: /opt/oracle_home/instantclient_23_8/TOOLS_LICENSE  
#21 1.996   inflating: /opt/oracle_home/instantclient_23_8/TOOLS_README  
#21 1.996   inflating: /opt/oracle_home/instantclient_23_8/wrc  
#21 DONE 3.0s

#13 [linux/arm64  4/13] RUN pip install --no-cache-dir --upgrade -r /opt/requirements.txt
#13 ...

#22 [linux/amd64 12/13] RUN ls -l /opt/oracle_home/instantclient
#22 0.153 total 374836
#22 0.153 -rw-r--r-- 1 root root      6506 Jun 28 19:15 BASIC_LICENSE
#22 0.153 -rw-r--r-- 1 root root       408 Jun 28 19:15 BASIC_README
#22 0.153 -rw-r--r-- 1 root root      6506 Jun 28 19:15 SQLPLUS_LICENSE
#22 0.153 -rw-r--r-- 1 root root       414 Jun 28 19:15 SQLPLUS_README
#22 0.153 -rw-r--r-- 1 root root      6506 Jun 28 19:15 TOOLS_LICENSE
#22 0.153 -rw-r--r-- 1 root root       408 Jun 28 19:15 TOOLS_README
#22 0.153 -rwxr-xr-x 1 root root     42768 Jun 28 19:15 adrci
#22 0.153 -rwxr-xr-x 1 root root    658144 Jun 28 19:15 exp
#22 0.153 -rwxr-xr-x 1 root root    247600 Jun 28 19:15 expdp
#22 0.153 -rwxr-xr-x 1 root root   2127136 Jun 28 19:15 fips.so
#22 0.153 -rwxr-xr-x 1 root root     72888 Jun 28 19:15 genezi
#22 0.153 -rw-r--r-- 1 root root       342 Jun 28 19:15 glogin.sql
#22 0.153 -rwxr-xr-x 1 root root    372480 Jun 28 19:15 imp
#22 0.153 -rwxr-xr-x 1 root root    251216 Jun 28 19:15 impdp
#22 0.153 drwxr-xr-x 3 root root      4096 Jun 30 01:19 instantclient_23_8
#22 0.153 -rwxr-xr-x 1 root root   5475184 Jun 28 19:15 legacy.so
#22 0.153 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so -> libclntsh.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so.10.1 -> libclntsh.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so.11.1 -> libclntsh.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so.12.1 -> libclntsh.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so.18.1 -> libclntsh.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so.19.1 -> libclntsh.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so.20.1 -> libclntsh.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so.21.1 -> libclntsh.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so.22.1 -> libclntsh.so.23.1
#22 0.153 -rwxr-xr-x 1 root root  96505025 Jun 28 22:18 libclntsh.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        21 Jun 28 19:15 libclntshcore.so -> libclntshcore.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        21 Jun 28 19:15 libclntshcore.so.12.1 -> libclntshcore.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        21 Jun 28 19:15 libclntshcore.so.18.1 -> libclntshcore.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        21 Jun 28 19:15 libclntshcore.so.19.1 -> libclntshcore.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        21 Jun 28 19:15 libclntshcore.so.20.1 -> libclntshcore.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        21 Jun 28 19:15 libclntshcore.so.21.1 -> libclntshcore.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        21 Jun 28 19:15 libclntshcore.so.22.1 -> libclntshcore.so.23.1
#22 0.153 -rwxr-xr-x 1 root root   5357424 Jun 28 19:15 libclntshcore.so.23.1
#22 0.153 -rwxr-xr-x 1 root root     70112 Jun 28 19:15 libnfsodm.so
#22 0.153 -rwxr-xr-x 1 root root   9879664 Jun 28 19:15 libnnz.so
#22 0.153 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so -> libocci.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so.10.1 -> libocci.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so.11.1 -> libocci.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so.12.1 -> libocci.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so.18.1 -> libocci.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so.19.1 -> libocci.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so.20.1 -> libocci.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so.21.1 -> libocci.so.23.1
#22 0.153 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so.22.1 -> libocci.so.23.1
#22 0.153 -rwxr-xr-x 1 root root   1342224 Jun 28 19:15 libocci.so.23.1
#22 0.153 -rwxr-xr-x 1 root root 201581008 Jun 28 19:15 libociei.so
#22 0.153 -rwxr-xr-x 1 root root    164328 Jun 28 19:15 libocijdbc23.so
#22 0.153 -rwxr-xr-x 1 root root     78120 Jun 28 19:15 libopcodm.so
#22 0.153 -rwxr-xr-x 1 root root   1136120 Jun 28 19:15 libsqlplus.so
#22 0.153 -rwxr-xr-x 1 root root  22835768 Jun 28 19:15 libsqlplusic.so
#22 0.153 -rwxr-xr-x 1 root root     18792 Jun 28 19:15 libtfojdbc1.so
#22 0.153 drwxr-xr-x 1 root root      4096 Jun 28 19:15 network
#22 0.153 -rw-r--r-- 1 root root   7367467 Jun 28 19:15 ojdbc11.jar
#22 0.153 -rw-r--r-- 1 root root   7368928 Jun 28 19:15 ojdbc17.jar
#22 0.153 -rw-r--r-- 1 root root   7251331 Jun 28 19:15 ojdbc8.jar
#22 0.153 -rwxr-xr-x 1 root root   5496752 Jun 28 19:15 pkcs11.so
#22 0.153 -rwxr-xr-x 1 root root   2299288 Jun 28 19:15 sqlldr
#22 0.153 -rwxr-xr-x 1 root root     41568 Jun 28 19:15 sqlplus
#22 0.153 -rw-r--r-- 1 root root   1501858 Jun 28 19:15 ucp.jar
#22 0.153 -rw-r--r-- 1 root root   1545200 Jun 28 19:15 ucp11.jar
#22 0.153 -rw-r--r-- 1 root root   1545419 Jun 28 19:15 ucp17.jar
#22 0.153 -rwxr-xr-x 1 root root    183696 Jun 28 19:15 uidrvci
#22 0.153 -rwxr-xr-x 1 root root    862384 Jun 28 19:15 wrc
#22 0.153 -rw-r--r-- 1 root root     32669 Jun 28 19:15 xstreams.jar
#22 DONE 0.2s

#23 [linux/amd64 13/13] RUN apt-get update && apt-get install -y libaio1
#23 0.324 Get:1 http://deb.debian.org/debian bookworm InRelease [151 kB]
#23 0.356 Get:2 http://deb.debian.org/debian bookworm-updates InRelease [55.4 kB]
#23 0.360 Get:3 http://deb.debian.org/debian-security bookworm-security InRelease [48.0 kB]
#23 0.456 Get:4 http://deb.debian.org/debian bookworm/main amd64 Packages [8793 kB]
#23 0.578 Get:5 http://deb.debian.org/debian bookworm-updates/main amd64 Packages [756 B]
#23 0.586 Get:6 http://deb.debian.org/debian-security bookworm-security/main amd64 Packages [269 kB]
#23 1.239 Fetched 9318 kB in 1s (9114 kB/s)
#23 1.239 Reading package lists...
#23 1.663 Reading package lists...
#23 2.086 Building dependency tree...
#23 2.218 Reading state information...
#23 2.427 The following NEW packages will be installed:
#23 2.428   libaio1
#23 2.535 0 upgraded, 1 newly installed, 0 to remove and 3 not upgraded.
#23 2.535 Need to get 13.4 kB of archives.
#23 2.535 After this operation, 37.9 kB of additional disk space will be used.
#23 2.535 Get:1 http://deb.debian.org/debian bookworm/main amd64 libaio1 amd64 0.3.113-4 [13.4 kB]
#23 3.225 debconf: delaying package configuration, since apt-utils is not installed
#23 3.278 Fetched 13.4 kB in 0s (134 kB/s)
#23 3.405 Selecting previously unselected package libaio1:amd64.
#23 3.405 (Reading database ... 
(Reading database ... 5%
(Reading database ... 10%
(Reading database ... 15%
(Reading database ... 20%
(Reading database ... 25%
(Reading database ... 30%
(Reading database ... 35%
(Reading database ... 40%
(Reading database ... 45%
(Reading database ... 50%
(Reading database ... 55%
(Reading database ... 60%
(Reading database ... 65%
(Reading database ... 70%
(Reading database ... 75%
(Reading database ... 80%
(Reading database ... 85%
(Reading database ... 90%
(Reading database ... 95%
(Reading database ... 100%
(Reading database ... 6704 files and directories currently installed.)
#23 4.186 Preparing to unpack .../libaio1_0.3.113-4_amd64.deb ...
#23 4.210 Unpacking libaio1:amd64 (0.3.113-4) ...
#23 4.362 Setting up libaio1:amd64 (0.3.113-4) ...
#23 4.382 Processing triggers for libc-bin (2.36-9+deb12u10) ...
#23 DONE 4.7s

#13 [linux/arm64  4/13] RUN pip install --no-cache-dir --upgrade -r /opt/requirements.txt
#13 28.66 Collecting pydantic_core==2.33.2 (from -r /opt/requirements.txt (line 15))
#13 28.67   Downloading pydantic_core-2.33.2-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl.metadata (6.8 kB)
#13 28.81 Collecting python-dateutil==2.9.0.post0 (from -r /opt/requirements.txt (line 16))
#13 28.83   Downloading python_dateutil-2.9.0.post0-py2.py3-none-any.whl.metadata (8.4 kB)
#13 29.00 Collecting python-dotenv==1.1.1 (from -r /opt/requirements.txt (line 17))
#13 29.01   Downloading python_dotenv-1.1.1-py3-none-any.whl.metadata (24 kB)
#13 29.46 Collecting pytz==2025.2 (from -r /opt/requirements.txt (line 18))
#13 29.47   Downloading pytz-2025.2-py2.py3-none-any.whl.metadata (22 kB)
#13 29.58 Collecting six==1.17.0 (from -r /opt/requirements.txt (line 19))
#13 29.59   Downloading six-1.17.0-py2.py3-none-any.whl.metadata (1.7 kB)
#13 29.66 Collecting sniffio==1.3.1 (from -r /opt/requirements.txt (line 20))
#13 29.67   Downloading sniffio-1.3.1-py3-none-any.whl.metadata (3.9 kB)
#13 30.01 Collecting starlette==0.46.2 (from -r /opt/requirements.txt (line 21))
#13 30.03   Downloading starlette-0.46.2-py3-none-any.whl.metadata (6.2 kB)
#13 30.12 Collecting typing-inspection==0.4.1 (from -r /opt/requirements.txt (line 22))
#13 30.13   Downloading typing_inspection-0.4.1-py3-none-any.whl.metadata (2.6 kB)
#13 30.29 Collecting typing_extensions==4.14.0 (from -r /opt/requirements.txt (line 23))
#13 30.30   Downloading typing_extensions-4.14.0-py3-none-any.whl.metadata (3.0 kB)
#13 30.43 Collecting tzdata==2025.2 (from -r /opt/requirements.txt (line 25))
#13 30.48   Downloading tzdata-2025.2-py2.py3-none-any.whl.metadata (1.4 kB)
#13 30.75 Collecting uvicorn==0.35.0 (from -r /opt/requirements.txt (line 26))
#13 30.77   Downloading uvicorn-0.35.0-py3-none-any.whl.metadata (6.5 kB)
#13 31.08 Collecting minio==7.2.7 (from -r /opt/requirements.txt (line 27))
#13 31.10   Downloading minio-7.2.7-py3-none-any.whl.metadata (6.4 kB)
#13 31.27 Collecting APScheduler==3.10.4 (from -r /opt/requirements.txt (line 28))
#13 31.28   Downloading APScheduler-3.10.4-py3-none-any.whl.metadata (5.7 kB)
#13 31.42 Collecting PyJWT==2.8.0 (from -r /opt/requirements.txt (line 29))
#13 31.44   Downloading PyJWT-2.8.0-py3-none-any.whl.metadata (4.2 kB)
#13 34.38 Collecting certifi (from minio==7.2.7->-r /opt/requirements.txt (line 27))
#13 34.39   Downloading certifi-2025.6.15-py3-none-any.whl.metadata (2.4 kB)
#13 34.77 Collecting urllib3 (from minio==7.2.7->-r /opt/requirements.txt (line 27))
#13 34.79   Downloading urllib3-2.5.0-py3-none-any.whl.metadata (6.5 kB)
#13 34.95 Collecting argon2-cffi (from minio==7.2.7->-r /opt/requirements.txt (line 27))
#13 34.97   Downloading argon2_cffi-25.1.0-py3-none-any.whl.metadata (4.1 kB)
#13 35.81 Collecting pycryptodome (from minio==7.2.7->-r /opt/requirements.txt (line 27))
#13 35.82   Downloading pycryptodome-3.23.0-cp37-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl.metadata (3.4 kB)
#13 36.09 Collecting tzlocal!=3.*,>=2.0 (from APScheduler==3.10.4->-r /opt/requirements.txt (line 28))
#13 36.11   Downloading tzlocal-5.3.1-py3-none-any.whl.metadata (7.6 kB)
#13 36.42 Collecting argon2-cffi-bindings (from argon2-cffi->minio==7.2.7->-r /opt/requirements.txt (line 27))
#13 36.44   Downloading argon2_cffi_bindings-21.2.0-cp36-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl.metadata (6.7 kB)
#13 36.81 Downloading annotated_types-0.7.0-py3-none-any.whl (13 kB)
#13 36.82 Downloading anyio-4.9.0-py3-none-any.whl (100 kB)
#13 36.84    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.9/100.9 kB 34.1 MB/s eta 0:00:00
#13 36.86 Downloading cffi-1.17.1-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl (469 kB)
#13 36.88    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 469.2/469.2 kB 50.5 MB/s eta 0:00:00
#13 36.89 Downloading click-8.2.1-py3-none-any.whl (102 kB)
#13 36.91    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 102.2/102.2 kB 48.3 MB/s eta 0:00:00
#13 36.93 Downloading cryptography-45.0.4-cp311-abi3-manylinux_2_34_aarch64.whl (4.2 MB)
#13 37.05    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.2/4.2 MB 37.3 MB/s eta 0:00:00
#13 37.06 Downloading fastapi-0.115.14-py3-none-any.whl (95 kB)
#13 37.08    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 95.5/95.5 kB 43.4 MB/s eta 0:00:00
#13 37.10 Downloading h11-0.16.0-py3-none-any.whl (37 kB)
#13 37.11 Downloading idna-3.10-py3-none-any.whl (70 kB)
#13 37.14    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 70.4/70.4 kB 22.3 MB/s eta 0:00:00
#13 37.16 Downloading numpy-2.3.1-cp311-cp311-manylinux_2_28_aarch64.whl (14.6 MB)
#13 37.59    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 14.6/14.6 MB 34.8 MB/s eta 0:00:00
#13 37.62 Downloading oracledb-3.2.0-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl (2.5 MB)
#13 37.74    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.5/2.5 MB 25.9 MB/s eta 0:00:00
#13 37.76 Downloading pandas-2.3.0-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl (11.8 MB)
#13 38.11    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 11.8/11.8 MB 36.6 MB/s eta 0:00:00
#13 38.13 Downloading pyarrow-20.0.0-cp311-cp311-manylinux_2_28_aarch64.whl (40.7 MB)
#13 39.41    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 40.7/40.7 MB 35.0 MB/s eta 0:00:00
#13 39.42 Downloading pycparser-2.22-py3-none-any.whl (117 kB)
#13 39.44    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 117.6/117.6 kB 45.3 MB/s eta 0:00:00
#13 39.45 Downloading pydantic-2.11.7-py3-none-any.whl (444 kB)
#13 39.48    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 444.8/444.8 kB 44.4 MB/s eta 0:00:00
#13 39.49 Downloading pydantic_core-2.33.2-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl (1.9 MB)
#13 39.57    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.9/1.9 MB 30.1 MB/s eta 0:00:00
#13 39.59 Downloading python_dateutil-2.9.0.post0-py2.py3-none-any.whl (229 kB)
#13 39.60    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 229.9/229.9 kB 48.8 MB/s eta 0:00:00
#13 39.62 Downloading python_dotenv-1.1.1-py3-none-any.whl (20 kB)
#13 39.63 Downloading pytz-2025.2-py2.py3-none-any.whl (509 kB)
#13 39.66    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 509.2/509.2 kB 44.6 MB/s eta 0:00:00
#13 39.68 Downloading six-1.17.0-py2.py3-none-any.whl (11 kB)
#13 39.70 Downloading sniffio-1.3.1-py3-none-any.whl (10 kB)
#13 39.72 Downloading starlette-0.46.2-py3-none-any.whl (72 kB)
#13 39.73    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 72.0/72.0 kB 34.4 MB/s eta 0:00:00
#13 39.75 Downloading typing_inspection-0.4.1-py3-none-any.whl (14 kB)
#13 39.76 Downloading typing_extensions-4.14.0-py3-none-any.whl (43 kB)
#13 39.78    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 43.8/43.8 kB 38.7 MB/s eta 0:00:00
#13 39.79 Downloading tzdata-2025.2-py2.py3-none-any.whl (347 kB)
#13 39.82    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 347.8/347.8 kB 42.4 MB/s eta 0:00:00
#13 39.84 Downloading uvicorn-0.35.0-py3-none-any.whl (66 kB)
#13 39.86    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 66.4/66.4 kB 17.2 MB/s eta 0:00:00
#13 39.88 Downloading minio-7.2.7-py3-none-any.whl (93 kB)
#13 39.89    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 93.5/93.5 kB 44.1 MB/s eta 0:00:00
#13 39.91 Downloading APScheduler-3.10.4-py3-none-any.whl (59 kB)
#13 39.93    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 59.3/59.3 kB 26.2 MB/s eta 0:00:00
#13 39.94 Downloading PyJWT-2.8.0-py3-none-any.whl (22 kB)
#13 39.96 Downloading tzlocal-5.3.1-py3-none-any.whl (18 kB)
#13 39.98 Downloading argon2_cffi-25.1.0-py3-none-any.whl (14 kB)
#13 40.00 Downloading certifi-2025.6.15-py3-none-any.whl (157 kB)
#13 40.02    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 157.7/157.7 kB 44.0 MB/s eta 0:00:00
#13 40.04 Downloading pycryptodome-3.23.0-cp37-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl (2.2 MB)
#13 40.10    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.2/2.2 MB 41.7 MB/s eta 0:00:00
#13 40.12 Downloading urllib3-2.5.0-py3-none-any.whl (129 kB)
#13 40.15    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 129.8/129.8 kB 27.2 MB/s eta 0:00:00
#13 40.17 Downloading argon2_cffi_bindings-21.2.0-cp36-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl (80 kB)
#13 40.18    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 80.6/80.6 kB 49.5 MB/s eta 0:00:00
#13 43.57 Installing collected packages: pytz, urllib3, tzlocal, tzdata, typing_extensions, sniffio, six, python-dotenv, PyJWT, pycryptodome, pycparser, pyarrow, numpy, idna, h11, click, certifi, annotated-types, uvicorn, typing-inspection, python-dateutil, pydantic_core, cffi, APScheduler, anyio, starlette, pydantic, pandas, cryptography, argon2-cffi-bindings, oracledb, fastapi, argon2-cffi, minio
#13 96.01 Successfully installed APScheduler-3.10.4 PyJWT-2.8.0 annotated-types-0.7.0 anyio-4.9.0 argon2-cffi-25.1.0 argon2-cffi-bindings-21.2.0 certifi-2025.6.15 cffi-1.17.1 click-8.2.1 cryptography-45.0.4 fastapi-0.115.14 h11-0.16.0 idna-3.10 minio-7.2.7 numpy-2.3.1 oracledb-3.2.0 pandas-2.3.0 pyarrow-20.0.0 pycparser-2.22 pycryptodome-3.23.0 pydantic-2.11.7 pydantic_core-2.33.2 python-dateutil-2.9.0.post0 python-dotenv-1.1.1 pytz-2025.2 six-1.17.0 sniffio-1.3.1 starlette-0.46.2 typing-inspection-0.4.1 typing_extensions-4.14.0 tzdata-2025.2 tzlocal-5.3.1 urllib3-2.5.0 uvicorn-0.35.0
#13 96.01 WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv
#13 96.74 
#13 96.74 [notice] A new release of pip is available: 24.0 -> 25.1.1
#13 96.74 [notice] To update, run: pip install --upgrade pip
#13 DONE 97.9s

#24 [linux/arm64  5/13] RUN apt-get update &&     apt-get install -y --no-install-recommends unzip &&     rm -rf /var/lib/apt/lists/*
#24 0.518 Get:1 http://deb.debian.org/debian bookworm InRelease [151 kB]
#24 0.583 Get:2 http://deb.debian.org/debian bookworm-updates InRelease [55.4 kB]
#24 0.583 Get:3 http://deb.debian.org/debian-security bookworm-security InRelease [48.0 kB]
#24 1.323 Get:4 http://deb.debian.org/debian bookworm/main arm64 Packages [8693 kB]
#24 2.015 Get:5 http://deb.debian.org/debian bookworm-updates/main arm64 Packages [756 B]
#24 2.712 Get:6 http://deb.debian.org/debian-security bookworm-security/main arm64 Packages [265 kB]
#24 4.202 Fetched 9214 kB in 4s (2415 kB/s)
#24 4.202 Reading package lists...
#24 7.457 Reading package lists...
#24 10.69 Building dependency tree...
#24 11.21 Reading state information...
#24 11.69 Suggested packages:
#24 11.69   zip
#24 11.97 The following NEW packages will be installed:
#24 11.97   unzip
#24 12.18 0 upgraded, 1 newly installed, 0 to remove and 3 not upgraded.
#24 12.18 Need to get 157 kB of archives.
#24 12.18 After this operation, 502 kB of additional disk space will be used.
#24 12.18 Get:1 http://deb.debian.org/debian bookworm/main arm64 unzip arm64 6.0-28 [157 kB]
#24 12.90 debconf: delaying package configuration, since apt-utils is not installed
#24 13.04 Fetched 157 kB in 0s (802 kB/s)
#24 13.20 Selecting previously unselected package unzip.
#24 13.20 (Reading database ... 
(Reading database ... 5%
(Reading database ... 10%
(Reading database ... 15%
(Reading database ... 20%
(Reading database ... 25%
(Reading database ... 30%
(Reading database ... 35%
(Reading database ... 40%
(Reading database ... 45%
(Reading database ... 50%
(Reading database ... 55%
(Reading database ... 60%
(Reading database ... 65%
(Reading database ... 70%
(Reading database ... 75%
(Reading database ... 80%
(Reading database ... 85%
(Reading database ... 90%
(Reading database ... 95%
(Reading database ... 100%
(Reading database ... 6680 files and directories currently installed.)
#24 13.28 Preparing to unpack .../unzip_6.0-28_arm64.deb ...
#24 13.28 Unpacking unzip (6.0-28) ...
#24 13.47 Setting up unzip (6.0-28) ...
#24 DONE 13.7s

#25 [linux/arm64  6/13] COPY ./app /opt/app/
#25 DONE 0.1s

#26 [linux/arm64  7/13] COPY ./oracle_home /opt/oracle_home/
#26 DONE 0.9s

#27 [linux/arm64  8/13] COPY ./install-instantclient.sh /opt/install-instantclient.sh
#27 DONE 0.1s

#28 [linux/arm64  9/13] RUN chmod +x /opt/install-instantclient.sh
#28 DONE 0.1s

#29 [linux/arm64 10/13] RUN mkdir -p /opt/database
#29 DONE 0.2s

#30 [linux/arm64 11/13] RUN /bin/bash -c "/opt/install-instantclient.sh"
#30 0.226 Archive:  ./oracle_home/instantclient-basic-linux.x64-23.8.0.25.04.zip
#30 0.234   inflating: /opt/oracle_home/META-INF/MANIFEST.MF  
#30 0.237   inflating: /opt/oracle_home/META-INF/ORACLE_C.SF  
#30 0.237   inflating: /opt/oracle_home/META-INF/ORACLE_C.RSA  
#30 0.237   inflating: /opt/oracle_home/instantclient_23_8/adrci  
#30 0.238   inflating: /opt/oracle_home/instantclient_23_8/BASIC_LICENSE  
#30 0.238   inflating: /opt/oracle_home/instantclient_23_8/BASIC_README  
#30 0.238   inflating: /opt/oracle_home/instantclient_23_8/fips.so  
#30 0.262   inflating: /opt/oracle_home/instantclient_23_8/genezi  
#30 0.263   inflating: /opt/oracle_home/instantclient_23_8/legacy.so  
#30 0.326     linking: /opt/oracle_home/instantclient_23_8/libclntshcore.so  -> libclntshcore.so.23.1 
#30 0.327     linking: /opt/oracle_home/instantclient_23_8/libclntshcore.so.12.1  -> libclntshcore.so.23.1 
#30 0.327     linking: /opt/oracle_home/instantclient_23_8/libclntshcore.so.18.1  -> libclntshcore.so.23.1 
#30 0.327     linking: /opt/oracle_home/instantclient_23_8/libclntshcore.so.19.1  -> libclntshcore.so.23.1 
#30 0.327     linking: /opt/oracle_home/instantclient_23_8/libclntshcore.so.20.1  -> libclntshcore.so.23.1 
#30 0.327     linking: /opt/oracle_home/instantclient_23_8/libclntshcore.so.21.1  -> libclntshcore.so.23.1 
#30 0.327     linking: /opt/oracle_home/instantclient_23_8/libclntshcore.so.22.1  -> libclntshcore.so.23.1 
#30 0.327   inflating: /opt/oracle_home/instantclient_23_8/libclntshcore.so.23.1  
#30 0.387     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so  -> libclntsh.so.23.1 
#30 0.387     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so.10.1  -> libclntsh.so.23.1 
#30 0.387     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so.11.1  -> libclntsh.so.23.1 
#30 0.387     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so.12.1  -> libclntsh.so.23.1 
#30 0.387     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so.18.1  -> libclntsh.so.23.1 
#30 0.387     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so.19.1  -> libclntsh.so.23.1 
#30 0.387     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so.20.1  -> libclntsh.so.23.1 
#30 0.387     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so.21.1  -> libclntsh.so.23.1 
#30 0.387     linking: /opt/oracle_home/instantclient_23_8/libclntsh.so.22.1  -> libclntsh.so.23.1 
#30 0.387   inflating: /opt/oracle_home/instantclient_23_8/libclntsh.so.23.1  
#30 1.383   inflating: /opt/oracle_home/instantclient_23_8/libnnz.so  
#30 1.494     linking: /opt/oracle_home/instantclient_23_8/libocci.so  -> libocci.so.23.1 
#30 1.494     linking: /opt/oracle_home/instantclient_23_8/libocci.so.10.1  -> libocci.so.23.1 
#30 1.494     linking: /opt/oracle_home/instantclient_23_8/libocci.so.11.1  -> libocci.so.23.1 
#30 1.494     linking: /opt/oracle_home/instantclient_23_8/libocci.so.12.1  -> libocci.so.23.1 
#30 1.494     linking: /opt/oracle_home/instantclient_23_8/libocci.so.18.1  -> libocci.so.23.1 
#30 1.494     linking: /opt/oracle_home/instantclient_23_8/libocci.so.19.1  -> libocci.so.23.1 
#30 1.494     linking: /opt/oracle_home/instantclient_23_8/libocci.so.20.1  -> libocci.so.23.1 
#30 1.494     linking: /opt/oracle_home/instantclient_23_8/libocci.so.21.1  -> libocci.so.23.1 
#30 1.494     linking: /opt/oracle_home/instantclient_23_8/libocci.so.22.1  -> libocci.so.23.1 
#30 1.494   inflating: /opt/oracle_home/instantclient_23_8/libocci.so.23.1  
#30 1.507   inflating: /opt/oracle_home/instantclient_23_8/libociei.so  
#30 3.520   inflating: /opt/oracle_home/instantclient_23_8/libocijdbc23.so  
#30 3.522   inflating: /opt/oracle_home/instantclient_23_8/libtfojdbc1.so  
#30 3.522    creating: /opt/oracle_home/instantclient_23_8/network/
#30 3.523   inflating: /opt/oracle_home/instantclient_23_8/ojdbc11.jar  
#30 3.623   inflating: /opt/oracle_home/instantclient_23_8/ojdbc17.jar  
#30 3.719   inflating: /opt/oracle_home/instantclient_23_8/ojdbc8.jar  
#30 3.813   inflating: /opt/oracle_home/instantclient_23_8/pkcs11.so  
#30 3.873   inflating: /opt/oracle_home/instantclient_23_8/ucp11.jar  
#30 3.892   inflating: /opt/oracle_home/instantclient_23_8/ucp17.jar  
#30 3.911   inflating: /opt/oracle_home/instantclient_23_8/ucp.jar  
#30 3.931   inflating: /opt/oracle_home/instantclient_23_8/uidrvci  
#30 3.933   inflating: /opt/oracle_home/instantclient_23_8/xstreams.jar  
#30 3.934    creating: /opt/oracle_home/instantclient_23_8/network/admin/
#30 3.934   inflating: /opt/oracle_home/instantclient_23_8/network/admin/README  
#30 3.934 finishing deferred symbolic links:
#30 3.934   /opt/oracle_home/instantclient_23_8/libclntshcore.so -> libclntshcore.so.23.1
#30 3.935   /opt/oracle_home/instantclient_23_8/libclntshcore.so.12.1 -> libclntshcore.so.23.1
#30 3.935   /opt/oracle_home/instantclient_23_8/libclntshcore.so.18.1 -> libclntshcore.so.23.1
#30 3.935   /opt/oracle_home/instantclient_23_8/libclntshcore.so.19.1 -> libclntshcore.so.23.1
#30 3.935   /opt/oracle_home/instantclient_23_8/libclntshcore.so.20.1 -> libclntshcore.so.23.1
#30 3.935   /opt/oracle_home/instantclient_23_8/libclntshcore.so.21.1 -> libclntshcore.so.23.1
#30 3.935   /opt/oracle_home/instantclient_23_8/libclntshcore.so.22.1 -> libclntshcore.so.23.1
#30 3.935   /opt/oracle_home/instantclient_23_8/libclntsh.so -> libclntsh.so.23.1
#30 3.935   /opt/oracle_home/instantclient_23_8/libclntsh.so.10.1 -> libclntsh.so.23.1
#30 3.935   /opt/oracle_home/instantclient_23_8/libclntsh.so.11.1 -> libclntsh.so.23.1
#30 3.935   /opt/oracle_home/instantclient_23_8/libclntsh.so.12.1 -> libclntsh.so.23.1
#30 3.935   /opt/oracle_home/instantclient_23_8/libclntsh.so.18.1 -> libclntsh.so.23.1
#30 3.935   /opt/oracle_home/instantclient_23_8/libclntsh.so.19.1 -> libclntsh.so.23.1
#30 3.935   /opt/oracle_home/instantclient_23_8/libclntsh.so.20.1 -> libclntsh.so.23.1
#30 3.935   /opt/oracle_home/instantclient_23_8/libclntsh.so.21.1 -> libclntsh.so.23.1
#30 3.935   /opt/oracle_home/instantclient_23_8/libclntsh.so.22.1 -> libclntsh.so.23.1
#30 3.935   /opt/oracle_home/instantclient_23_8/libocci.so -> libocci.so.23.1
#30 3.936   /opt/oracle_home/instantclient_23_8/libocci.so.10.1 -> libocci.so.23.1
#30 3.936   /opt/oracle_home/instantclient_23_8/libocci.so.11.1 -> libocci.so.23.1
#30 3.936   /opt/oracle_home/instantclient_23_8/libocci.so.12.1 -> libocci.so.23.1
#30 3.936   /opt/oracle_home/instantclient_23_8/libocci.so.18.1 -> libocci.so.23.1
#30 3.936   /opt/oracle_home/instantclient_23_8/libocci.so.19.1 -> libocci.so.23.1
#30 3.936   /opt/oracle_home/instantclient_23_8/libocci.so.20.1 -> libocci.so.23.1
#30 3.936   /opt/oracle_home/instantclient_23_8/libocci.so.21.1 -> libocci.so.23.1
#30 3.936   /opt/oracle_home/instantclient_23_8/libocci.so.22.1 -> libocci.so.23.1
#30 3.966 Archive:  ./oracle_home/instantclient-sqlplus-linux.x64-23.8.0.25.04.zip
#30 3.970   inflating: /opt/oracle_home/instantclient_23_8/glogin.sql  
#30 3.971   inflating: /opt/oracle_home/instantclient_23_8/libsqlplusic.so  
#30 4.168   inflating: /opt/oracle_home/instantclient_23_8/libsqlplus.so  
#30 4.184   inflating: /opt/oracle_home/instantclient_23_8/sqlplus  
#30 4.184   inflating: /opt/oracle_home/instantclient_23_8/SQLPLUS_LICENSE  
#30 4.184   inflating: /opt/oracle_home/instantclient_23_8/SQLPLUS_README  
#30 4.208 Archive:  ./oracle_home/instantclient-tools-linux.x64-23.8.0.25.04.zip
#30 4.212   inflating: /opt/oracle_home/instantclient_23_8/exp  
#30 4.222   inflating: /opt/oracle_home/instantclient_23_8/expdp  
#30 4.226   inflating: /opt/oracle_home/instantclient_23_8/imp  
#30 4.230   inflating: /opt/oracle_home/instantclient_23_8/impdp  
#30 4.233   inflating: /opt/oracle_home/instantclient_23_8/libnfsodm.so  
#30 4.234   inflating: /opt/oracle_home/instantclient_23_8/libopcodm.so  
#30 4.235   inflating: /opt/oracle_home/instantclient_23_8/sqlldr  
#30 4.256   inflating: /opt/oracle_home/instantclient_23_8/TOOLS_LICENSE  
#30 4.256   inflating: /opt/oracle_home/instantclient_23_8/TOOLS_README  
#30 4.256   inflating: /opt/oracle_home/instantclient_23_8/wrc  
#30 DONE 4.9s

#31 [linux/arm64 12/13] RUN ls -l /opt/oracle_home/instantclient
#31 0.164 total 374836
#31 0.164 -rw-r--r-- 1 root root      6506 Jun 28 19:15 BASIC_LICENSE
#31 0.164 -rw-r--r-- 1 root root       408 Jun 28 19:15 BASIC_README
#31 0.164 -rw-r--r-- 1 root root      6506 Jun 28 19:15 SQLPLUS_LICENSE
#31 0.164 -rw-r--r-- 1 root root       414 Jun 28 19:15 SQLPLUS_README
#31 0.164 -rw-r--r-- 1 root root      6506 Jun 28 19:15 TOOLS_LICENSE
#31 0.164 -rw-r--r-- 1 root root       408 Jun 28 19:15 TOOLS_README
#31 0.164 -rwxr-xr-x 1 root root     42768 Jun 28 19:15 adrci
#31 0.164 -rwxr-xr-x 1 root root    658144 Jun 28 19:15 exp
#31 0.164 -rwxr-xr-x 1 root root    247600 Jun 28 19:15 expdp
#31 0.164 -rwxr-xr-x 1 root root   2127136 Jun 28 19:15 fips.so
#31 0.164 -rwxr-xr-x 1 root root     72888 Jun 28 19:15 genezi
#31 0.164 -rw-r--r-- 1 root root       342 Jun 28 19:15 glogin.sql
#31 0.164 -rwxr-xr-x 1 root root    372480 Jun 28 19:15 imp
#31 0.164 -rwxr-xr-x 1 root root    251216 Jun 28 19:15 impdp
#31 0.164 drwxr-xr-x 3 root root      4096 Jun 30 01:20 instantclient_23_8
#31 0.164 -rwxr-xr-x 1 root root   5475184 Jun 28 19:15 legacy.so
#31 0.164 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so -> libclntsh.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so.10.1 -> libclntsh.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so.11.1 -> libclntsh.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so.12.1 -> libclntsh.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so.18.1 -> libclntsh.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so.19.1 -> libclntsh.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so.20.1 -> libclntsh.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so.21.1 -> libclntsh.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        17 Jun 28 19:15 libclntsh.so.22.1 -> libclntsh.so.23.1
#31 0.164 -rwxr-xr-x 1 root root  96505025 Jun 28 22:18 libclntsh.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        21 Jun 28 19:15 libclntshcore.so -> libclntshcore.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        21 Jun 28 19:15 libclntshcore.so.12.1 -> libclntshcore.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        21 Jun 28 19:15 libclntshcore.so.18.1 -> libclntshcore.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        21 Jun 28 19:15 libclntshcore.so.19.1 -> libclntshcore.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        21 Jun 28 19:15 libclntshcore.so.20.1 -> libclntshcore.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        21 Jun 28 19:15 libclntshcore.so.21.1 -> libclntshcore.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        21 Jun 28 19:15 libclntshcore.so.22.1 -> libclntshcore.so.23.1
#31 0.164 -rwxr-xr-x 1 root root   5357424 Jun 28 19:15 libclntshcore.so.23.1
#31 0.164 -rwxr-xr-x 1 root root     70112 Jun 28 19:15 libnfsodm.so
#31 0.164 -rwxr-xr-x 1 root root   9879664 Jun 28 19:15 libnnz.so
#31 0.164 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so -> libocci.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so.10.1 -> libocci.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so.11.1 -> libocci.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so.12.1 -> libocci.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so.18.1 -> libocci.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so.19.1 -> libocci.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so.20.1 -> libocci.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so.21.1 -> libocci.so.23.1
#31 0.164 lrwxrwxrwx 1 root root        15 Jun 28 19:15 libocci.so.22.1 -> libocci.so.23.1
#31 0.164 -rwxr-xr-x 1 root root   1342224 Jun 28 19:15 libocci.so.23.1
#31 0.164 -rwxr-xr-x 1 root root 201581008 Jun 28 19:15 libociei.so
#31 0.164 -rwxr-xr-x 1 root root    164328 Jun 28 19:15 libocijdbc23.so
#31 0.164 -rwxr-xr-x 1 root root     78120 Jun 28 19:15 libopcodm.so
#31 0.164 -rwxr-xr-x 1 root root   1136120 Jun 28 19:15 libsqlplus.so
#31 0.164 -rwxr-xr-x 1 root root  22835768 Jun 28 19:15 libsqlplusic.so
#31 0.164 -rwxr-xr-x 1 root root     18792 Jun 28 19:15 libtfojdbc1.so
#31 0.164 drwxr-xr-x 1 root root      4096 Jun 28 19:15 network
#31 0.164 -rw-r--r-- 1 root root   7367467 Jun 28 19:15 ojdbc11.jar
#31 0.164 -rw-r--r-- 1 root root   7368928 Jun 28 19:15 ojdbc17.jar
#31 0.164 -rw-r--r-- 1 root root   7251331 Jun 28 19:15 ojdbc8.jar
#31 0.164 -rwxr-xr-x 1 root root   5496752 Jun 28 19:15 pkcs11.so
#31 0.164 -rwxr-xr-x 1 root root   2299288 Jun 28 19:15 sqlldr
#31 0.164 -rwxr-xr-x 1 root root     41568 Jun 28 19:15 sqlplus
#31 0.165 -rw-r--r-- 1 root root   1501858 Jun 28 19:15 ucp.jar
#31 0.165 -rw-r--r-- 1 root root   1545200 Jun 28 19:15 ucp11.jar
#31 0.165 -rw-r--r-- 1 root root   1545419 Jun 28 19:15 ucp17.jar
#31 0.165 -rwxr-xr-x 1 root root    183696 Jun 28 19:15 uidrvci
#31 0.165 -rwxr-xr-x 1 root root    862384 Jun 28 19:15 wrc
#31 0.165 -rw-r--r-- 1 root root     32669 Jun 28 19:15 xstreams.jar
#31 DONE 0.2s

#32 [linux/arm64 13/13] RUN apt-get update && apt-get install -y libaio1
#32 0.482 Get:1 http://deb.debian.org/debian bookworm InRelease [151 kB]
#32 0.548 Get:2 http://deb.debian.org/debian bookworm-updates InRelease [55.4 kB]
#32 0.548 Get:3 http://deb.debian.org/debian-security bookworm-security InRelease [48.0 kB]
#32 1.320 Get:4 http://deb.debian.org/debian bookworm/main arm64 Packages [8693 kB]
#32 1.996 Get:5 http://deb.debian.org/debian bookworm-updates/main arm64 Packages [756 B]
#32 2.689 Get:6 http://deb.debian.org/debian-security bookworm-security/main arm64 Packages [265 kB]
#32 4.226 Fetched 9214 kB in 4s (2369 kB/s)
#32 4.226 Reading package lists...
#32 7.450 Reading package lists...
#32 10.55 Building dependency tree...
#32 11.05 Reading state information...
#32 11.67 The following NEW packages will be installed:
#32 11.67   libaio1
#32 11.89 0 upgraded, 1 newly installed, 0 to remove and 3 not upgraded.
#32 11.89 Need to get 13.3 kB of archives.
#32 11.89 After this operation, 91.1 kB of additional disk space will be used.
#32 11.89 Get:1 http://deb.debian.org/debian bookworm/main arm64 libaio1 arm64 0.3.113-4 [13.3 kB]
#32 12.51 debconf: delaying package configuration, since apt-utils is not installed
#32 12.65 Fetched 13.3 kB in 0s (64.9 kB/s)
#32 12.81 Selecting previously unselected package libaio1:arm64.
#32 12.81 (Reading database ... 
(Reading database ... 5%
(Reading database ... 10%
(Reading database ... 15%
(Reading database ... 20%
(Reading database ... 25%
(Reading database ... 30%
(Reading database ... 35%
(Reading database ... 40%
(Reading database ... 45%
(Reading database ... 50%
(Reading database ... 55%
(Reading database ... 60%
(Reading database ... 65%
(Reading database ... 70%
(Reading database ... 75%
(Reading database ... 80%
(Reading database ... 85%
(Reading database ... 90%
(Reading database ... 95%
(Reading database ... 100%
(Reading database ... 6698 files and directories currently installed.)
#32 12.89 Preparing to unpack .../libaio1_0.3.113-4_arm64.deb ...
#32 12.90 Unpacking libaio1:arm64 (0.3.113-4) ...
#32 13.09 Setting up libaio1:arm64 (0.3.113-4) ...
#32 13.10 Processing triggers for libc-bin (2.36-9+deb12u10) ...
#32 DONE 13.3s

#33 exporting to image
#33 exporting layers
#33 exporting layers 11.1s done
#33 exporting manifest sha256:c7e6caa0d9dd5ac46126538d4588a52433d35b906454a3d7433560b8fa13cd57 0.0s done
#33 exporting config sha256:cfebb0cd9bb6b6488fc680ed70ed49b32babc24907aa2760a79a2db4fe1d4320 done
#33 exporting attestation manifest sha256:f6d0d268262ac7a97ab6d175bf30f589ec5da5cf08841aebb3b96b9beeb025c7 0.0s done
#33 exporting manifest sha256:f067649b9f4511efbb200f6c3726aed7e7a1fe050e64b5806ee701f860b144ca 0.0s done
#33 exporting config sha256:af2c088e8271c9e1b4e1ff0eff6bd0994172ab2f5745e85120e2ec8afceb3b1b 0.0s done
#33 exporting attestation manifest sha256:5c311293b645a72f564a08f6611924b2230edc813fa94b0097d9f51d7840a8ff 0.0s done
#33 exporting manifest list sha256:21841d889dbd805986838dea33a79f288ff1ddcd5b483172fabeb28a8a0c3660 0.0s done
#33 pushing layers
#33 ...

#34 [auth] luis122448/data-ingestor-python:pull,push token for registry-1.docker.io
#34 DONE 0.0s

#33 exporting to image
#33 pushing layers 24.4s done
#33 pushing manifest for docker.io/luis122448/data-ingestor-python:v1.0.0@sha256:21841d889dbd805986838dea33a79f288ff1ddcd5b483172fabeb28a8a0c3660
#33 pushing manifest for docker.io/luis122448/data-ingestor-python:v1.0.0@sha256:21841d889dbd805986838dea33a79f288ff1ddcd5b483172fabeb28a8a0c3660 3.5s done
#33 DONE 39.2s
Image luis122448/data-ingestor-python:v1.0.0 successfully deployed to Docker Hub!


### Copy Oracle Instant Client Libraries to Remote Server

```bash
scp -i /home/luis122448/Desktop/repository-tsi/keys/putty/private_service \
./oracle_home/instantclient-basic-linux.x64-23.8.0.25.04.zip \
./oracle_home/instantclient-sqlplus-linux.x64-23.8.0.25.04.zip \
./oracle_home/instantclient-tools-linux.x64-23.8.0.25.04.zip \
./oracle_home/instantclient-basic-linux.arm64-23.8.0.25.04.zip \
./oracle_home/instantclient-sdk-linux.arm64-23.8.0.25.04.zip \
./oracle_home/instantclient-sdk-linux.arm64-23.8.0.25.04.zip \
luis122448@192.168.100.141:/var/www/api-sql-reports/data-ingestor-python
```

### Copy Oracle Instant Client Libraries to Remote Server

```bash
scp -i /home/luis122448/Desktop/repository-tsi/keys/putty/private_service \
./oracle_home/instantclient-basic-linux.x64-23.8.0.25.04.zip \
./oracle_home/instantclient-basic-linux.arm64-23.8.0.25.04.zip \
./oracle_home/instantclient-sqlplus-linux.x64-23.8.0.25.04.zip \
./oracle_home/instantclient-sqlplus-linux.arm64-23.8.0.25.04.zip \
./oracle_home/instantclient-tools-linux.x64-23.8.0.25.04.zip \
./oracle_home/instantclient-tools-linux.arm64-23.8.0.25.04.zip \
./oracle_home/instantclient-sdk-linux.x64-23.8.0.25.04.zip \
./oracle_home/instantclient-sdk-linux.arm64-23.8.0.25.04.zip \
luis122448@192.168.100.141:/var/www/api-sql-reports/data-ingestor-python/oracle_home/
```

### Copy Oracle Instant Client Libraries to Remote Server

```bash
scp -i /home/luis122448/Desktop/repository-tsi/keys/putty/private_service \
./app/wallet/sqlnet.ora \
./app/wallet/tnsnames.ora \
./app/wallet/cwallet.sso \
luis122448@192.168.100.141:/var/www/api-sql-reports/data-ingestor-python/app/wallet/
```
