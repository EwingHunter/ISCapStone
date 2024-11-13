import os
from google.cloud import pubsub_v1
import certifi
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import json

# Set the environment variable to authenticate with Google Cloud
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/ewinghunter/ISCapStone/pelagic-quanta-437214-m7-4e38c6774618.json"


# MongoDB connection setup
mongo_connection_string = "mongodb+srv://ewinghunter:Hannah94@iscapstonecluster.5btls.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(
    mongo_connection_string,
    server_api=ServerApi('1'),
    tlsCAFile=certifi.where()
)

try:
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except Exception as e:
    print("MongoDB Connection Error:", e)
    exit(1)

db = client['iscapstone']
collection = db['messages']

# Google Pub/Sub setup
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path('pelagic-quanta-437214-m7', 'group-5-subscription')

def callback(message):
    print(f"Received message: {message.data.decode('utf-8')}")
    # Parse the message data
    try:
        message_data = json.loads(message.data.decode('utf-8'))
        
        # Insert the parsed message into MongoDB
        collection.insert_one(message_data)

        # Acknowledge the message after processing
        message.ack()
        print("Message processed and inserted into MongoDB.")
    except Exception as e:
        print(f"Error inserting message into MongoDB: {e}")

# Subscribe to the Pub/Sub topic
subscriber.subscribe(subscription_path, callback=callback)

print(f"Listening for messages on {subscription_path}...")

# Keep the main thread alive so the subscriber can keep receiving messages
import time
while True:
    time.sleep(60)
