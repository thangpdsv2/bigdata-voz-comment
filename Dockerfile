FROM bitnami/spark:latest

RUN pip install torch
RUN pip install transformers

# Create a writable cache directory in /tmp
RUN mkdir -p /tmp/cache
ENV HF_HOME=/tmp/cache

# Copy the application files
COPY index.py /app/index.py
COPY trained_model.pth /app/trained_model.pth
COPY jar/* /app/jar/

# Set the working directory
WORKDIR /app

# Ensure spark-submit is available in PATH
ENV PATH="$PATH:/opt/bitnami/spark/bin"

# Command to run your Spark job
CMD ["spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2", "--master", "spark://spark-master:7077", "/app/index.py"]