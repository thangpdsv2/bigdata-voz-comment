FROM bitnami/spark:latest

# Install Python packages
RUN pip install torch
RUN pip install transformers


# Create a writable cache directory in /tmp
RUN mkdir -p /tmp/cache
ENV HF_HOME=/tmp/cache

# Create output directory and set permissions
RUN mkdir -p /tmp/output && chmod -R 777 /tmp/output

# Copy the application files
COPY index.py /app/index.py
COPY trained_model.pth /app/trained_model.pth
COPY jar/* /app/jar/
COPY spark-submit-jars/* /opt/bitnami/spark/jars/

# Set the working directory
WORKDIR /app

# Ensure spark-submit is available in PATH
ENV PATH="$PATH:/opt/bitnami/spark/bin"

# Command to run your Spark job
CMD ["spark-submit", "--master", "spark://spark-master:7077", "/app/index.py"]
