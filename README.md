# Repository Setup and Access

This document outlines the steps required to set up and access the `py-etl-oracle` repository.

---
## Prerequisites

* An SSH key pair is required for secure access to the Bitbucket repository and the remote server.
* Git must be installed on your local machine.
* An SSH client is needed for connecting to the remote server.
* For Oracle connectivity, the Oracle Instant Client libraries will be required on the remote server.

---
## Repository Access

### Clone the Repository

```bash
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_lcalvo" git clone git@bitbucket.org:grupotsi/py-etl-oracle.git
```

### Pull Lastest Changes

```bash
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_lcalvo" git pull origin master
```

### Push Local Changes

```bash
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_lcalvo" git push origin master
```

---
## Remote Server Access and Setup for Deployment

### Verify IP Address ON Remote Server

```bash
cat /home/luis122448/Desktop/repository-tsi/keys/putty/leer.txt
```

### Connect to the Remote Server

```bash
ssh -i /home/luis122448/Desktop/repository-tsi/keys/putty/private_service opc@150.136.40.237
```

### Copy Oracle Instant Client Libraries to Remote Server

```bash
scp -i /home/luis122448/Desktop/repository-tsi/keys/putty/private_service \
./oracle_home/instantclient-basic-linux.x64-23.8.0.25.04.zip \
./oracle_home/instantclient-sqlplus-linux.x64-23.8.0.25.04.zip \
./oracle_home/instantclient-tools-linux.x64-23.8.0.25.04.zip \
opc@150.136.40.237:/home/opc/py-etl-oracle/oracle_home
```

### Post-Connection Setup on Remote Server

```bash
sudo su
export PATH=/home/opc/.local/bin:/home/opc/bin:/usr/share/Modules/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin
ssh-agent /bin/bash
ssh-add /etc/ssh/id_repo
```