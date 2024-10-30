from flask import Flask, render_template, jsonify
from google.cloud import pubsub_v1
from pymongo import MongoClient
from google.oauth2 import service_account
import json

# Load credentials from JSON file
credentials = service_account.Credentials.from_service_account_file(
    r"c:\Users\Ewing Hunter\IsCapStone\pelagic-quanta-437214-m7-4e38c6774618.json"
)

# Initialize Pub/Sub Publisher and Subscriber Clients with credentials
publisher = pubsub_v1.PublisherClient(credentials=credentials)
subscriber = pubsub_v1.SubscriberClient(credentials=credentials)

# Set the project ID and topic ID for the current project
project_id = "pelagic-quanta-437214-m7"
topic_id = "group-5-topic"
subscription_id = "group-5-subscription"

# Create the topic and subscription paths
topic_path = publisher.topic_path(project_id, topic_id)
subscription_path = subscriber.subscription_path(project_id, subscription_id)

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')  # Adjust if using a remote MongoDB
db = client['is_capstone_5']  # Replace with your actual database name
collection = db['messages']  # Use 'messages' as the collection for storing Pub/Sub messages

# Flask App Initialization
app = Flask(__name__)

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

# Route: Insert test message into MongoDB
@app.route('/insert_test_message')
def insert_test_message():
    try:
        test_message = {
            "MessageID": "test123",
            "ItemID": "item567",
            "Location": "TestLocation",
            "Quantity": 10
        }
        result = collection.insert_one(test_message)
        return jsonify({"status": "success", "inserted_id": str(result.inserted_id)})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

# Route: Fetch messages from MongoDB and display
@app.route('/get_messages')
def get_messages():
    try:
        # Find all messages and convert them to JSON serializable format
        messages = list(collection.find({}, {"_id": 0}))  # Exclude the ObjectId for easier serialization
        return jsonify({"status": "success", "messages": messages})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    try:
        # Print received message for debugging
        print(f"Received message: {message.data.decode('utf-8')}")

        # Insert the raw message into MongoDB as a plain text entry
        message_data = message.data.decode('utf-8')
        message_dict = {"raw_message": message_data}

        # Insert the message into MongoDB
        result = collection.insert_one(message_dict)
        print(f"Inserted message with ID: {result.inserted_id}")

        # Acknowledge the message so it's not resent
        message.ack()
        print("Message acknowledged and inserted into MongoDB.")
    except Exception as e:
        print(f"Error processing message: {e}")

# Start listening for Pub/Sub messages in the background
def start_subscriber():
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}..\n")
    return streaming_pull_future

if __name__ == "__main__":
    # Start the subscriber in the background
    streaming_pull_future = start_subscriber()

    try:
        # Start Flask application
        app.run(host='0.0.0.0', port=8080)
    except KeyboardInterrupt:
        # Gracefully stop the subscriber if the Flask server is stopped
        streaming_pull_future.cancel()
        streaming_pull_future.result()

    print("Flask server and Pub/Sub subscriber stopped.")

