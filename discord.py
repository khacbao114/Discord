import json
import time
import shareithub
import os
import random
import requests
from dotenv import load_dotenv
from datetime import datetime
from shareithub import shareithub

shareithub()
load_dotenv()

discord_token = os.getenv('DISCORD_TOKEN')
google_api_key = os.getenv('GOOGLE_API_KEY')

last_message_id = None
bot_user_id = None
last_ai_response = None  # Stores the last AI response

def log_message(message):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")

def generate_reply(prompt, use_google_ai=True, use_file_reply=False, language="id"):
    """Generates a reply, avoiding duplication if using Google Gemini AI"""

    global last_ai_response  # Use global variable for session-wide access

    if use_file_reply:
        log_message("💬 Using messages from a file as replies.")
        return {"candidates": [{"content": {"parts": [{"text": get_random_message()}]}}]}

    if use_google_ai:
        # Language choice
        if language == "en":
            ai_prompt = f"{prompt}\n\nRespond with only one sentence in casual urban English, like a natural conversation, and do not use symbols."
        else:
            ai_prompt = f"{prompt}\n\nProvide only one sentence in Jakarta's slang language, like a casual conversation, and do not use any symbols."

        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={google_api_key}'
        headers = {'Content-Type': 'application/json'}
        data = {'contents': [{'parts': [{'text': ai_prompt}]}]}

        for attempt in range(3):  # Retry up to 3 times if AI repeats the same response
            try:
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                ai_response = response.json()

                # Extract text from AI response
                response_text = ai_response['candidates'][0]['content']['parts'][0]['text']

                # Check if AI response is the same as the last one
                if response_text == last_ai_response:
                    log_message("⚠️ AI gave the same response, retrying...")
                    continue  # Retry with a new request
                
                last_ai_response = response_text  # Save the latest response
                return ai_response

            except requests.exceptions.RequestException as e:
                log_message(f"⚠️ Request failed: {e}")
                return None

        log_message("⚠️ AI keeps giving the same response, using the last available response.")
        return {"candidates": [{"content": {"parts": [{"text": last_ai_response or 'Sorry, unable to reply.'}]}}]}

    else:
        return {"candidates": [{"content": {"parts": [{"text": get_random_message()}]}}]}

def get_random_message():
    """Retrieving a random message from pesan.txt file"""
    try:
        with open('pesan.txt', 'r') as file:
            lines = file.readlines()
            if lines:
                return random.choice(lines).strip()
            else:
                log_message("The pesan.txt file is empty.")
                return "No messages available."
    except FileNotFoundError:
        log_message("The pesan.txt file was not found.")
        return "The pesan.txt file was not found."

def send_message(channel_id, message_text, reply_to=None, reply_mode=True):
    """Sending a message to Discord, with or without a reply"""
    headers = {
        'Authorization': f'{discord_token}',
        'Content-Type': 'application/json'
    }

    payload = {'content': message_text}

    # Only add a reply if reply_mode is enabled
    if reply_mode and reply_to:
        payload['message_reference'] = {'message_id': reply_to}

    try:
        response = requests.post(f"https://discord.com/api/v9/channels/{channel_id}/messages", json=payload, headers=headers)
        response.raise_for_status()

        if response.status_code == 201:
            log_message(f"✅ Sent message: {message_text}")
        else:
            log_message(f"⚠️ Failed to send message: {response.status_code}")
    except requests.exceptions.RequestException as e:
        log_message(f"⚠️ Request error: {e}")

def auto_reply(channel_id, read_delay, reply_delay, use_google_ai, use_file_reply, language, reply_mode):
    """Function for auto-reply on Discord while avoiding AI duplication"""
    global last_message_id, bot_user_id

    headers = {'Authorization': f'{discord_token}'}

    try:
        bot_info_response = requests.get('https://discord.com/api/v9/users/@me', headers=headers)
        bot_info_response.raise_for_status()
        bot_user_id = bot_info_response.json().get('id')
    except requests.exceptions.RequestException as e:
        log_message(f"⚠️ Failed to retrieve bot information: {e}")
        return

    while True:
        try:
            response = requests.get(f'https://discord.com/api/v9/channels/{channel_id}/messages', headers=headers)
            response.raise_for_status()

            if response.status_code == 200:
                messages = response.json()
                if len(messages) > 0:
                    most_recent_message = messages[0]
                    message_id = most_recent_message.get('id')
                    author_id = most_recent_message.get('author', {}).get('id')
                    message_type = most_recent_message.get('type', '')

                    if (last_message_id is None or int(message_id) > int(last_message_id)) and author_id != bot_user_id and message_type != 8:
                        user_message = most_recent_message.get('content', '')
                        log_message(f"💬 Received message: {user_message}")

                        result = generate_reply(user_message, use_google_ai, use_file_reply, language)
                        response_text = result['candidates'][0]['content']['parts'][0]['text'] if result else "Sorry, unable to reply."

                        log_message(f"⏳ Waiting {reply_delay} seconds before replying...")
                        time.sleep(reply_delay)
                        send_message(channel_id, response_text, reply_to=message_id if reply_mode else None, reply_mode=reply_mode)
                        last_message_id = message_id

            log_message(f"⏳ Waiting {read_delay} seconds before checking for new messages...")
            time.sleep(read_delay)
        except requests.exceptions.RequestException as e:
            log_message(f"⚠️ Request error: {e}")
            time.sleep(read_delay)
