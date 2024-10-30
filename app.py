from flask import Flask, render_template, jsonify
from google.cloud import pubsub_v1
from pymongo import MongoClient
from google.oauth2 import service_account
from google.cloud import pubsub_v1

# Load credentials from JSON file
credentials = service_account.Credentials.from_service_account_file(
    r"c:\Users\Ewing Hunter\IsCapStone\pelagic-quanta-437214-m7-4e38c6774618.json"
)

# Initialize the Publisher Client with the credentials
publisher = pubsub_v1.PublisherClient(credentials=credentials)

# Set the project ID and topic ID for the current project
project_id = "pelagic-quanta-437214-m7"
topic_id = "group-5-topic"

# Create the topic path
topic_path = publisher.topic_path(project_id, topic_id)

# Publish a test message
message_data = "Hello, this is a test message from pelagic-quanta!".encode("utf-8")  # Convert message to bytes
future = publisher.publish(topic_path, message_data)

# Add callback to handle the result of the future
def callback(message_future):
    if message_future.exception(timeout=30):
        print('Publishing message on {} threw an Exception: {}'.format(
            topic_path, message_future.exception()))
    else:
        print(f'Message published: {message_future.result()}')

future.add_done_callback(callback)


app = Flask(__name__)

# Initialize Pub/Sub client
project_id = "pelagic-quanta-437214-m7"
topic_id = "group-5-topic"
subscription_id = "group-5-subscription"
publisher = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()
topic_path = publisher.topic_path(project_id, topic_id)

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')  # Replace with your MongoDB connection string
db = client['your_db_name']
collection = db['messages']

# Route: Home Page
@app.route('/')
def home():
    return render_template('index.html')

# Route: Test Pub/Sub Connectivity
@app.route('/test_pubsub')
def test_pubsub():
    try:
        message = "Test Message for Pub/Sub Connectivity"
        future = publisher.publish(topic_path, message.encode('utf-8'))
        message_id = future.result()  # Wait for the result
        return jsonify({"status": "success", "message_id": message_id})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

# Route: Insert message into MongoDB
@app.route('/test_database')
def test_database():
    try:
        message = {
            "MessageID": "12345",
            "ItemID": "54321",
            "Location": "Warehouse",
            "Quantity": 100
        }
        collection.insert_one(message)  # Insert into MongoDB
        return jsonify({"status": "success", "message": "Message inserted into MongoDB"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

# Route: Fetch messages from MongoDB and display
@app.route('/get_messages')
def get_messages():
    try:
        messages = list(collection.find())
        return jsonify({"status": "success", "messages": messages})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
