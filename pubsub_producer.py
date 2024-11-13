import os
from google.cloud import pubsub_v1
import json

# Set the environment variable to authenticate with Google Cloud
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "pelagic-quanta-437214-m7-4e38c6774618.json"

# Google Pub/Sub setup
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('pelagic-quanta-437214-m7', 'group-5-topic')

# JSON messages (direct JSON versions of your messages)
messages = [
    {
        "TransactionNumber": "f14243cb-e953-4aa7-a8cc-33489fdcd22c",
        "TransactionDateTime": "2024-01-03T06:07:09.967",
        "ItemId": "609827617635",
        "Location": "003",
        "Quantity": 8,
        "Status": "AVAILABLE",
        "NextAvailabilityDate": None,
        "TotalIncludingSubstituteItems": 1273.0,
        "SubstituteItemsAvailable": False,
        "SubstitutionDetails": None,
        "FirstAvailableFutureQuantity": None,
        "FirstAvailableFutureDate": None
    },
    {
        "TransactionNumber": "a16373ef-e953-4aa7-a8cc-33489fdcd22c",
        "TransactionDateTime": "2023-09-12T09:45:37.865",
        "ItemId": "005860917635",
        "Location": "002",
        "Quantity": 45,
        "Status": "AVAILABLE",
        "NextAvailabilityDate": None,
        "TotalIncludingSubstituteItems": 1273.0,
        "SubstituteItemsAvailable": False,
        "SubstitutionDetails": None,
        "FirstAvailableFutureQuantity": None,
        "FirstAvailableFutureDate": None
    },
    {
        "TransactionNumber": "d72313ef-e953-4aa7-a8cc-33489fdcd22c",
        "TransactionDateTime": "2023-05-03T06:21:25.472",
        "ItemId": "008763419206",
        "Location": "001",
        "Quantity": 1273,
        "Status": "AVAILABLE",
        "NextAvailabilityDate": None,
        "TotalIncludingSubstituteItems": 1273.0,
        "SubstituteItemsAvailable": False,
        "SubstitutionDetails": None,
        "FirstAvailableFutureQuantity": None,
        "FirstAvailableFutureDate": None
    },
    {
        "TransactionNumber": "d72313ef-e953-4aa7-a8cc-33489fdcd22c",
        "TransactionDateTime": "2023-05-03T06:21:25.472",
        "ItemId": "008763419206",
        "Location": "001",
        "Quantity": 1273,
        "Status": "AVAILABLE",
        "NextAvailabilityDate": None,
        "TotalIncludingSubstituteItems": 1273.0,
        "SubstituteItemsAvailable": False,
        "SubstitutionDetails": None,
        "FirstAvailableFutureQuantity": None,
        "FirstAvailableFutureDate": None
    }
]

# Publish each message
for message_data in messages:
    try:
        # Convert message to JSON string for publishing
        message_str = json.dumps(message_data)

        # Encode message to bytes and publish
        future = publisher.publish(topic_path, message_str.encode('utf-8'))
        print(f"Published message: {future.result()}")
    except Exception as e:
        print(f"Error publishing message: {e}")


