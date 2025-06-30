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

pero cuando lo despliego en kubernetes con el deployment

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
          image: luis122448/data-ingestor-python:v1.0.2
          env:
            - name: LD_LIBRARY_PATH
              value: /opt/oracle_home/instantclient
            - name: ORACLE_HOME
              value: /opt/oracle_home/instantclient
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
(.venv) luis122448@dev-003:/var/www/api-sql-reports/data-ingestor-python$ kubectl logs data-ingestor-python-755f4b9848-f4qgs -n api-sql-reports
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

Esto se esta deplegando en un arquitectura ARM64, pero justamente el Docker Compose que te comente al inciio se realiza sibre en orangepi, a si de igual forma deberia funcionar.., ademas el script install-instantclient.sh, captura ambas logicas de arquitectura

```install-instantclient.sh
#!/bin/bash
# Description: Build and deploy application Docker image to Docker Hub.

# --- Configuration ---
DOCKER_USERNAME="luis122448"
IMAGE_NAME="data-ingestor-python"
IMAGE_TAG="v1.0.2" # Standardized version tag
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}"
DOCKERFILE_PATH="." # Path to the directory containing the Dockerfile

# --- Functions ---
error_exit() {
    echo "ERROR: $1" >&2
    exit 1
}

# --- Pre-checks ---
docker info > /dev/null 2>&1 || error_exit "Docker is not running or user lacks permissions."

docker info | grep "Username: $DOCKER_USERNAME" > /dev/null || \
    error_exit "Not logged in to Docker Hub as $DOCKER_USERNAME. Please run 'docker login' manually."

# --- Docker Buildx Setup ---
docker buildx inspect mybuilder > /dev/null 2>&1 || docker buildx create --name mybuilder --bootstrap || \
    error_exit "Failed to create Buildx builder."
docker buildx use mybuilder || error_exit "Failed to use Buildx builder 'mybuilder'."

# --- Build and Push Image ---
echo "Building and pushing ${FULL_IMAGE_NAME} for linux/amd64 and linux/arm64..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --no-cache \
  -t "${FULL_IMAGE_NAME}" \
  --push \
  "${DOCKERFILE_PATH}" || error_exit "Failed to build and push Docker image."

echo "Image ${FULL_IMAGE_NAME} successfully deployed to Docker Hub!"
```

no entiendo porque sigue sin ejecutarse en kubernmetes si ya funciona en amd64 y arm64