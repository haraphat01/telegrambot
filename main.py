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

PAI_TOKEN = "\n \n Any donations you can make are greatly appreciated and will help us keep our "
Telegram = "\n \n Kindly join our telegram group https://t.me/pencilAI"

# Connect to MongoDB to save userid
client = pymongo.MongoClient(format(os.getenv("MONGO_DB")))
db = client["abekeapo"]
collection = db["Cluster0"]


update_url = "https://api.telegram.org/bot{}/getUpdates".format(os.getenv("TELEGRAM_API_KEY"))
send_message_url = "https://api.telegram.org/bot{}/sendMessage".format(os.getenv("TELEGRAM_API_KEY"))
client = openai.OpenAI(
    api_key=os.environ.get("TOGETHER_API_KEY"),
    base_url='https://api.together.xyz',
)

# Set to keep track of unique users
last_update_id = 0
# Function to handle incoming messages
def handle_message(update):
    if "message" in update:
        message = update["message"]
        if "text" in message:
            message_text = message["text"]
            chat_id = message["chat"]["id"]
            bot_name = "@TajiriBot"
            if bot_name in message_text:
                # Extract the user's question
                question = message_text.split(bot_name)[0].strip()
                print("User's question:", question) 
                # Send the user's question to OpenAI for a response
                # response = openai.Completion.create(
                #     model="your-openai-model",
                #     prompt=question,
                # )
                model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
                chat_completion = client.chat.completions.create(
                    messages=[
                {
                    "role": "user",
                    "content": question,
                }
                            ],
                    model= model
                )
                # Tag the user and send the response back to the Telegram group
                response_text = f"@{message['from']['username']} {chat_completion.choices[0].message.content.strip()}"
                requests.post(send_message_url, json={
                    "chat_id": chat_id,
                    "text": response_text
                })
                
            existing_chat = collection.find_one({"chat_id": chat_id})
            current_month = time.strftime("%m") # get the current month
            if existing_chat and existing_chat.get("month") == current_month and existing_chat.get("requests") >= 60:
                requests.post(send_message_url, json={
                    "chat_id": chat_id,
                    "text": "You have reached your monthly limit of 30 requests"
                })
                return True # add return statement here
            if existing_chat:
                # If it's a new month, reset the request count
                if existing_chat.get("month") != current_month:
                    collection.update_one({"chat_id": chat_id}, {"$set": {"month": current_month, "requests": 1}})
                else:
                    collection.update_one({"chat_id": chat_id}, {"$inc": {"requests": 1}})
                
            else:
                # Add the user to the database for the first time
                collection.insert_one({
                "chat_id": chat_id, 
                "month": current_month,
                "requests": 1
                })
            if  message_text.startswith("/start") or message_text.lower() == "hello":
                message_text = "hello?"
            # Send a welcome message to the user
                requests.post(send_message_url, json={
                 "chat_id": chat_id,
                "text": "This is PencilAI, may I know how I can help you?"
                })
          
            try:
                # response = openai.Completion.create(
                #     model=model,
                #     prompt=message_text,
                #     temperature=temperature,
                #     max_tokens=max_tokens
                # )
                chat_completion = client.chat.completions.create(
                    messages=[
                {
                    "role": "user",
                    "content": message_text,
                }
                            ],
                    model= model
                )
                # send the response back to Telegram
                requests.post(send_message_url, json={
                    "chat_id": chat_id,
                    "text": chat_completion.choices[0].message.content.strip()
                })
            except:
                requests.post(send_message_url, json={
                    "chat_id": chat_id,
                    "text": "I'm sorry, there was an error processing your request from our third party service providers. Please try again later."
                })  
            global last_update_id
            last_update_id = update["update_id"]
        else:
            print("No text in the message")
    else:
        print("No message in update")
        print("User's question:", question) 
while True:
     response = requests.get(update_url, params={"offset": last_update_id+1})
     if "result" in response.json():
        updates = response.json()["result"]
        for update in updates:
            handle_message_result = handle_message(update)
            if handle_message_result == "break":
                break
     time.sleep(5)
print("User's question:") 