FROM bitnami/spark:latest

# Install dependencies
RUN pip install torch transformers

# Copy the application files
COPY index.py /app/index.py
COPY trained_model.pth /app/trained_model.pth

# Set the working directory
WORKDIR /app

# Command to run your Spark job
CMD ["spark-submit", "--master", "spark://spark-master:7077", "/app/index.py"]
