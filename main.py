import os
import requests
import openai
import time
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
os.getenv("TELEGRAM_API_KEY")


update_url = "https://api.telegram.org/bot{}/getUpdates".format(os.getenv("TELEGRAM_API_KEY"))
send_message_url = "https://api.telegram.org/bot{}/sendMessage".format(os.getenv("TELEGRAM_API_KEY"))


last_update_id = 0
# Function to handle incoming messages
def handle_message(update):
    if "message" in update:
        message = update["message"]
        if "text" in message:
            message_text = message["text"]
            chat_id = message["chat"]["id"]
            model = "text-davinci-003"
            temperature = 0.7
            max_tokens = 256
            top_p = 1
            frequency_penalty = 0
            presence_penalty = 0
            response = openai.Completion.create(
                model=model,
                prompt=message_text,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty
            )
            # send the response back to Telegram
            requests.post(send_message_url, json={
                "chat_id": chat_id,
                "text": response["choices"][0]["text"]
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
