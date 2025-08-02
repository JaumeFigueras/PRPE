# PRPE

## Plataforma de Resposta als Problemes d'Endarreriment (PRPE)

This project aims to get the Rodalies RENFE and ADIF data of trains and how delayed they are.  


## Install all dependencies in a virtual environment

```
python3 -m venv .venv
pip3 install --upgrade -r requirements.txt
```

Upgrade pip3 if necessary

```
 pip3 install --upgrade pip
```

## To use the documenting system

You can create the docs using. If the docs are already created only the build command is necessary

```
sphinx-build --version
sphinx-quickstart docs
sphinx-build -M html docs/source/ docs/build/
```


## Database

Create the database isolated cluster. The DBMS system is PostgresSQL with version 15 on a Debian 12, 
if necessary create the directories

``
sudo mkdir /home/postgresql-15
sudo mkdir /home/postgresql-15/clusters
sudo mkdir /home/postgresql-15/logs
``

then create the database cluster, change the port if necessary and choose the usernames that you like

``
sudo pg_createcluster -d /home/postgresql-15/clusters/prpe -l /home/postgresql-15/logs/prpe.log -p 5435 --start --start-conf auto 15 prpe
``

When the cluster is running, create the local user a remote user (that will have only read privileges) and the database

``
sudo -i -u postgres
createuser -p 5435 -P prpe_user
createuser -p 5435 -P prpe_remoteuser
createdb -p 5435 -E UTF8 -O prpe_user prpe_db
psql -p 5435 -d prpe_db
create extension hstore;
``
