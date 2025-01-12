FROM apache/airflow:2.9.3
USER root
RUN apt-get update && apt-get install -y \
    python3-dev \
        python3-virtualenv \
    libpq-dev

RUN mkdir /app
RUN chown airflow /app
RUN usermod -aG sudo airflow

WORKDIR /app
COPY . /app

RUN chmod +x /app/run_app.sh

USER airflow
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

ENTRYPOINT ["/app/run_app.sh"]
