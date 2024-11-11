from flask import Flask, render_template, jsonify, request
from google.cloud import pubsub_v1
from pymongo import MongoClient
from google.oauth2 import service_account
import json
import threading
import datetime
import time

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
            "Quantity": 10,
            "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        result = collection.insert_one(test_message)
        return jsonify({"status": "success", "inserted_id": str(result.inserted_id)})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

# Route: Fetch messages from MongoDB and display
@app.route('/get_messages', methods=['GET'])
def get_messages():
    try:
        # Apply filters if provided
        filters = {}
        if request.args:
            for key, value in request.args.items():
                filters[key] = value

        # Find messages and convert them to JSON serializable format
        messages = list(collection.find(filters, {"_id": 0}))
        return jsonify({"status": "success", "messages": messages})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

# Route: Export Messages to JSON or CSV
@app.route('/export_messages', methods=['GET'])
def export_messages():
    try:
        export_format = request.args.get('format', 'json')
        messages = list(collection.find({}, {"_id": 0}))
        if export_format == 'csv':
            # Convert to CSV format
            import csv
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=messages[0].keys())
            writer.writeheader()
            writer.writerows(messages)
            return output.getvalue(), 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=messages.csv'}
        else:
            # Return JSON by default
            return jsonify({"status": "success", "messages": messages})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

# Route: Real-time Updates using Long Polling
@app.route('/real_time_updates')
def real_time_updates():
    try:
        # Fetch new messages added in the last 10 seconds
        ten_seconds_ago = datetime.datetime.now() - datetime.timedelta(seconds=10)
        new_messages = list(collection.find({"Timestamp": {"$gte": ten_seconds_ago.strftime("%Y-%m-%d %H:%M:%S")}}, {"_id": 0}))
        return jsonify({"status": "success", "new_messages": new_messages})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

# Route: Delete a Message from MongoDB
@app.route('/delete_message', methods=['POST'])
def delete_message():
    try:
        message_id = request.form.get('MessageID')
        result = collection.delete_one({"MessageID": message_id})
        if result.deleted_count > 0:
            return jsonify({"status": "success", "message": "Message deleted"})
        else:
            return jsonify({"status": "error", "message": "Message not found"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

# Route: User Settings - Toggle Dark Mode
@app.route('/toggle_dark_mode', methods=['POST'])
def toggle_dark_mode():
    try:
        # Assuming user settings are stored in MongoDB
        user_id = request.form.get('user_id', 'default_user')
        dark_mode = request.form.get('dark_mode', 'off') == 'on'
        db['user_settings'].update_one(
            {"user_id": user_id},
            {"$set": {"dark_mode": dark_mode}},
            upsert=True
        )
        return jsonify({"status": "success", "dark_mode": dark_mode})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

# Callback for Pub/Sub subscriber
def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    try:
        # Print received message for debugging
        print(f"Received message: {message.data.decode('utf-8')}")

        # Decode message
        message_data = message.data.decode('utf-8')

        # Attempt to parse as JSON if possible
        try:
            message_dict = json.loads(message_data)
        except json.JSONDecodeError:
            # If message is not JSON, just log it as is
            message_dict = {"message": message_data}

        # Insert the message into MongoDB
        message_dict['Timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        # Stop the subscriber if the Flask server is stopped
        streaming_pull_future.cancel()
        streaming_pull_future.result()

    print("Flask server and Pub/Sub subscriber stopped.")

