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
            existing_chat = collection.find_one({"chat_id": chat_id})
            if existing_chat:
                collection.update_one({"chat_id": chat_id}, {"$set": {"chat_id": chat_id}})
                
            else:
                collection.insert_one({
                "chat_id": chat_id, 
                })
            if message_text == "/start":
            # Send a welcome message to the user
                requests.post(send_message_url, json={
                 "chat_id": chat_id,
                "text": "Welcome to the bot! How can I help you today?"
                })
            model = "text-davinci-003"
            temperature = 0.85
            max_tokens = 1250
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
    