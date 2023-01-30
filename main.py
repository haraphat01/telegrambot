import os
import requests
import openai
import time
from dotenv import load_dotenv
import pymongo

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
os.getenv("TELEGRAM_API_KEY")
os.getenv("MONGO_DB")



# Connect to MongoDB to save userid
client = pymongo.MongoClient(format(os.getenv("MONGO_DB")))
db = client["abekeapo"]
collection = db["Cluster0"]


update_url = "https://api.telegram.org/bot{}/getUpdates".format(os.getenv("TELEGRAM_API_KEY"))
send_message_url = "https://api.telegram.org/bot{}/sendMessage".format(os.getenv("TELEGRAM_API_KEY"))


# Set to keep track of unique users
unique_users = set()
last_update_id = 0
# Function to handle incoming messages
def handle_message(update):
    if "message" in update:
        message = update["message"]
        if "text" in message:
            message_text = message["text"]
            chat_id = message["chat"]["id"]
            existing_user = collection.find_one({"chat_id": chat_id})
            # Check if user already exists in the database
            if existing_user:
                # Check if user's subscription has expired
                current_time = time.time()
                if existing_user['subscription_end_time'] and existing_user['subscription_end_time'] < current_time:
                    # If expired, update user's subscription status
                    collection.update_one({"chat_id": chat_id}, {"$set": {"subscription_status": "expired"}})
                    # Update user's last interaction time
                    collection.update_one({"chat_id": chat_id}, {"$set": {"last_interaction_time": current_time}})
                else:
                        # Insert new user into the database with default values
                    collection.insert_one({
                        "chat_id": chat_id,
                        "request_count": 0,
                        "subscription_status": "free",
                        "last_interaction_time": time.time(),
                        "subscription_end_time": None
                    })   
            user = collection.find_one({"chat_id": chat_id})
        if user["subscription_status"] == "free":
            if user["request_count"] >= 20:
                # If user has reached the monthly limit, send a message to upgrade to a paid subscription
                requests.post(send_message_url, json={
                    "chat_id": chat_id,
                    "text": "You have reached the monthly limit of 20 requests. Upgrade to a paid subscription for unlimited requests."
                })
            else:
                # Increment user's request count
                collection.update_one({"chat_id": chat_id}, {"$inc": {"request_count": 1}})
                
                # If user's subscription is still valid, process the message
                if  message_text.startswith("/start") or message_text.lower() == "hello":
                    message_text = "hello?"
                # Send a welcome message to the user
                requests.post(send_message_url, json={
                 "chat_id": chat_id,
                "text": "You're welcome, I can help you achieve a lot"
                })
            model = "text-davinci-003"
            temperature = 0.7
            max_tokens = 256
            try:
                response = openai.Completion.create(
                    model=model,
                    prompt=message_text,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                # send the response back to Telegram
                requests.post(send_message_url, json={
                    "chat_id": chat_id,
                    "text": response["choices"][0]["text"].strip()
                })
                requests.post(send_message_url, json={
                    "chat_id": chat_id,
                    "text": response["choices"][0]["text"].strip()
                })
            except:
                requests.post(send_message_url, json={
                    "chat_id": chat_id,
                    "text": "I'm sorry, there was an error processing your request. Please try again later."
                })  
            global last_update_id
            last_update_id = update["update_id"]
        else:
            print("No text in the message")
        
    else:
        print("No message in update")
        

while True:
    response = requests.get(update_url, params={"offset": last_update_id+1})
    if "result" in response.json():
        updates = response.json()["result"]
        for update in updates:
            handle_message(update)
    else:
        print("No updates to retrieve.")
    time.sleep(5)
    