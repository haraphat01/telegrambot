import os
import requests
import openai
import time
from dotenv import load_dotenv
import pymongo
import datetime
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
os.getenv("TELEGRAM_API_KEY")
os.getenv("MONGO_DB")

now = datetime.datetime.now()
current_month = now.month



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
                current_month = datetime.datetime.now().month
                first_request_month = existing_chat.get("first_request_month")
                num_requests = existing_chat.get("num_requests", 0)
                if current_month != first_request_month or num_requests >= 30:
                    # Send message indicating that the user has exceeded their monthly limit
                    requests.post(send_message_url, json={
                        "chat_id": chat_id,
                        "text": "You have reached your monthly limit of 30 requests.\n Please try again next month. You can subscribe to premium service at $5 monthly or $50 yearly for unlimited request.\n You can currently pay with Etherum, Bnb, Busd and Usdt. Pay to this wallet address \n '0x983e746eDEa971338344D67E6DF755BbC37c8F76' \n and contact https://t.me/pencil_support to activate your account"
                    })
                    
                    return               # Update the request count and last reset time in the database
                collection.update_one({"chat_id": chat_id}, {"$inc": {"num_requests": 1}})
                if first_request_month is None:
                    collection.update_one({"chat_id": chat_id}, {"$set": {"first_request_month": current_month}})
            else:
                # Create a new entry for the user in the database with request count = 1
                collection.insert_one({
                    "chat_id": chat_id,
                    "first_request_month": datetime.datetime.now().month,
                    "num_requests": 1
                })
            if  message_text.startswith("/start") or message_text.lower() == "hello":
                message_text = "hello?"
            # Send a welcome message to the user
                requests.post(send_message_url, json={
                 "chat_id": chat_id,
                "text": "You're welcome, I can help you achieve a lot"
                })
            model = "text-davinci-003"
            temperature = 0.7
            max_tokens = 200
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
    
    
    
