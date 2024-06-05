from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, from_json
from pyspark.sql.types import StringType, FloatType, StructType, StructField, MapType
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import json

# Model name and tokenizer setup
model_name = "vinai/phobert-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Define the number of labels for your classification task
num_labels = 2

# Create an instance of the model
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=num_labels)

# Load the saved state dictionary into the model
model.load_state_dict(torch.load("trained_model.pth"))
model.eval()

# Define the prediction function with probabilities
def predict(record):
    try:
        print(f"Received record: {record}")  # Debugging line
        
        if isinstance(record, str):
            input_text = record
        else:
            raise ValueError("Invalid input format")
        
        print(f"Input text for tokenization: {input_text}")  # Debugging line
        encoded_input = tokenizer.batch_encode_plus(
            [input_text],  # Ensure input is a list of strings
            add_special_tokens=True,  # Add '[CLS]' and '[SEP]'
            padding='max_length',  # Pad to max_length
            max_length=256,  # Adjust based on your needs
            truncation=True,  # Truncate to max_length
            return_attention_mask=True,  # Include attention masks
            return_tensors='pt'  # Return PyTorch tensors
        )
        
        input_ids = encoded_input['input_ids']
        attention_mask = encoded_input['attention_mask']
        
        with torch.no_grad():
            outputs = model(input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            probabilities = torch.nn.functional.softmax(logits, dim=-1).squeeze().tolist()
            # Apply custom threshold
            threshold = 0.3  # Adjust based on your observations
            pred_label_custom_threshold = int(probabilities[1] > threshold)
        
        print(f"Logits: {logits}, Probabilities: {probabilities}, Prediction: {pred_label_custom_threshold}")  # Debugging line
        return json.dumps({"prediction": pred_label_custom_threshold, "probabilities": probabilities})
    except Exception as e:
        print(f"Error processing record: {record}, error: {e}")
        return json.dumps({"prediction": None, "probabilities": []})

# Define the schema for the output
output_schema = StructType([
    StructField("prediction", FloatType(), True),
    StructField("probabilities", StringType(), True)
])

# Register the UDF
predict_udf = udf(predict, StringType())

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("KafkaSparkML") \
    .config("spark.jars", "/Users/thangpd/Thang/DAIHOC/BIGDATA/Doan/jar/commons-pool2-2.8.0.jar,/Users/thangpd/Thang/DAIHOC/BIGDATA/Doan/jar/kafka-clients-2.6.0.jar,/Users/thangpd/Thang/DAIHOC/BIGDATA/Doan/jar/spark-sql-kafka-0-10_2.12-3.1.2.jar,/Users/thangpd/Thang/DAIHOC/BIGDATA/Doan/jar/spark-token-provider-kafka-0-10_2.12-3.1.2.jar") \
    .getOrCreate()

# Configure Kafka Consumer
kafka_brokers = "localhost:9092"
kafka_topic = "incoming-order"

# Read from Kafka
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_brokers) \
    .option("subscribe", kafka_topic) \
    .load()

# Extract the value from the Kafka message and convert to string
df = df.selectExpr("CAST(value AS STRING)")

# Apply the prediction function to each record and parse the JSON string result
predicted_df = df.withColumn("prediction_result", predict_udf(df["value"]))

# Parse the JSON result and extract fields
parsed_df = predicted_df.withColumn("parsed", from_json(col("prediction_result"), output_schema))

# Extract fields from parsed JSON
final_df = parsed_df.select(col("value"), col("parsed.prediction"), col("parsed.probabilities"))

# Start the stream and print the output to the console
query = final_df \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .option("checkpointLocation", "./output") \
    .start()

query.awaitTermination()
