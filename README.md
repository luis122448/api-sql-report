# Data Ingestor Python Application

This README provides instructions for deploying the Data Ingestor Python application using both Docker Compose for local development and Kubernetes for production environments.

## Deployment with Docker Compose

For local development and testing, you can use Docker Compose to run the application.

### 1. Environment Variables Setup

Create a `.env` file in the root directory of the project. This file will contain the environment variables required by the application. Replace the placeholder values with your actual credentials and configurations.

```
DB_ORACLE_USER=your_oracle_user
DB_ORACLE_PASSWORD=your_oracle_password
DB_ORACLE_DSN=your_oracle_dsn
MINIO_URL=your_minio_url
MINIO_ACCESS_KEY=your_minio_access_key
MINIO_SECRET_KEY=your_minio_secret_key
JWT_SECRET_KEY=your_jwt_secret_key
```

### 2. Running the Application with Docker Compose

The `compileDocker.sh` script automates the process of pulling the latest code, building the Docker image, and starting the services using Docker Compose.

To deploy the application using Docker Compose, execute the following command:

```bash
./compileDocker.sh
```

This script will:
- Pull the latest changes from your Git repository.
- Build the Docker image for the `app` service defined in `docker-compose.yml`.
- Recreate and start the `app` service in detached mode (`-d`).
- The application will be accessible on port `8001` on your host machine, as it uses `network_mode: "host"`.

## Deployment with Kubernetes

For production deployments, the application can be deployed to a Kubernetes cluster. This setup includes an OpenVPN sidecar container to connect to an Oracle database via VPN.

### 1. Build and Push Docker Image

First, you need to build the Docker image and push it to Docker Hub (or your preferred container registry). Ensure you are logged in to Docker Hub (`docker login`).

The `build-release.sh` script handles the multi-architecture build and push process:

```bash
./build-release.sh
```

This script will:
- Build the `luis122448/data-ingestor-python:v1.0.0` image for `linux/amd64` and `linux/arm64` platforms.
- Push the built image to Docker Hub.

### 2. Kubernetes Manifests Deployment

The Kubernetes manifests are located in the `kubernetes/` directory. They must be applied in a specific order to ensure all dependencies are met.

#### a. Create OpenVPN Secrets

The `client.ovpn` and `credentials.txt` files are used to establish the VPN connection. These need to be stored as Kubernetes secrets.

```bash
kubectl create secret generic openvpn-client-config --from-file=./vpn/client.ovpn -n api-sql-reports
kubectl create secret generic openvpn-credentials --from-file=./vpn/credentials.txt -n api-sql-reports
```

#### b. Deploy Persistent Volume Claim (PVC)

The `pvc.yaml` defines the PersistentVolumeClaim for the SQLite database.

```bash
kubectl apply -f ./kubernetes/pvc.yaml -n api-sql-reports
```

#### c. Deploy Application Deployment

The `deployment.yaml` defines the main application deployment, including the `data-ingestor-python` container and the `openvpn-client` initContainer. The initContainer ensures the VPN connection is established before the main application starts.

```bash
kubectl apply -f ./kubernetes/deployment.yaml -n api-sql-reports
```

#### d. Deploy Service

The `service.yml` defines the Kubernetes Service that exposes the application within the cluster.

```bash
kubectl apply -f ./kubernetes/service.yml -n api-sql-reports
```

#### e. Deploy Ingress (Optional, for external access)

The `ingress.yml` defines the Ingress resource for external access to the application, typically configured with a domain and TLS.

```bash
kubectl apply -f ./kubernetes/ingress.yml -n api-sql-reports
```

### 3. Verifying Deployment

You can check the status of your pods and services using the following commands:

- Check pod status:
```bash
kubectl get pods -n api-sql-reports -l app=data-ingestor-python
```
- Describe a pod to see events and detailed status (replace `<pod-name>` with an actual pod name):
```bash
kubectl describe pod <pod-name> -n api-sql-reports
```
- View logs for the OpenVPN initContainer (replace `<pod-name>` with an actual pod name):
```bash
kubectl logs <pod-name> -n api-sql-reports -c openvpn-client
```
- View logs for the main application container (replace `<pod-name>` with an actual pod name):
```bash
kubectl logs <pod-name> -n api-sql-reports -c data-ingestor-python
```
