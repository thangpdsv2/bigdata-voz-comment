#!/bin/bash

if [ "$SPARK_MODE" == "master" ]; then
    /opt/bitnami/scripts/spark/entrypoint.sh /opt/bitnami/scripts/spark/run.sh
elif [ "$SPARK_MODE" == "worker" ]; then
    /opt/bitnami/scripts/spark/entrypoint.sh /opt/bitnami/scripts/spark/run.sh
else
    echo "Unsupported mode $SPARK_MODE"
    exit 1
fi
