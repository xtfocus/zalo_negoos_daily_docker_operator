# Docker Image for zalo daily prediction tasks

**INTENDED USE**: This image is to be used as a single task in an Airflow DAG. Such a DAG can be found [here](https://github.com/xtfocus/airflow_dockeroperator_gpu). The Airflow DAG fires up this Docker image and execute the `kedro` pipeline daily. This pipeline writes to `OOS_PREDICTION` and `NEGATIVE_PREDICTION` tables in the LC Server.

To use this Image:
- Set up Airflow running in a container correctly (see the [example airflow repo](https://github.com/xtfocus/airflow_dockeroperator_gpu) above for inspiration). You should be able to open the Airflow web UI, and command `docker ps` should shows healthy running containers like this
```
CONTAINER ID   IMAGE                  COMMAND                  CREATED         STATUS                    PORTS                                       NAMES
5f0fa9f7831d   apache/airflow:2.9.1   "/usr/bin/dumb-init …"   2 hours ago     Up 47 minutes (healthy)   8080/tcp                                    airflow_docker-airflow-triggerer-1
a0e20b623d64   apache/airflow:2.9.1   "/usr/bin/dumb-init …"   2 hours ago     Up 2 hours (healthy)      0.0.0.0:8080->8080/tcp, :::8080->8080/tcp   airflow_docker-airflow-webserver-1
a16313c69c9d   apache/airflow:2.9.1   "/usr/bin/dumb-init …"   2 hours ago     Up 48 minutes (healthy)   8080/tcp                                    airflow_docker-airflow-worker-1
0adc61702ae2   apache/airflow:2.9.1   "/usr/bin/dumb-init …"   2 hours ago     Up 47 minutes (healthy)   8080/tcp                                    airflow_docker-airflow-scheduler-1
4ef8ab9b2ddb   postgres:13            "docker-entrypoint.s…"   2 hours ago     Up 47 minutes (healthy)   5432/tcp                                    airflow_docker-postgres-1
99845eed1647   redis:7.2-bookworm     "docker-entrypoint.s…"   2 hours ago     Up 2 hours (healthy)      6379/tcp                                    airflow_docker-redis-1
t
```
- Clone this repo. Build this image with 
```bash
docker build -t kedro-docker:v1 .
```
This will create an image named `kedro-docker:v1`

- Make sure the DAG code is updated by
```bash
docker exec -it airflow_docker-airflow-scheduler-1 airflow dags list
```

where `airflow_docker-airflow-scheduler-1` is the container name running the Airflow scheduler.

(everytime you make a change to the `kedro` pipelines code, just rebuild this image, then execute the command above. No need to set up Airflow from square one)
- You should now be able to trigger the DAG. You can backfill the DAG with 
```bash
docker exec -it airflow_docker-airflow-scheduler-1 airflow dags backfill docker_dag --start-date 2024-05-25 --end-date 2024-05-31
```
Replace the dates with interval you want to backfill.

If you don't trigger for backfill now, the DAG will be automatically triggered daily at 7AM.
