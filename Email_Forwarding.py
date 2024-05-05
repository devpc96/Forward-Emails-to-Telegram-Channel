import imaplib
import email
import telebot
from email.utils import parsedate_to_datetime
import os
from twilio.rest import Client

# Telegram Bot API token
TOKEN = 'xxxxxxxxxx:yyyyyyyyyyyyyyyyyyyy' # Put your Bot API token here which is obtained from bot fther
bot = telebot.TeleBot(TOKEN)

# Gmail IMAP settings
GMAIL_IMAP_SERVER = 'imap.gmail.com'
EMAIL = 'xxxxxxxxxxxx@gmail.com' # Your Email address where you receive Emails from target Mail id 
PASSWORD = 'xxxx aaaa ssss zzzz' # Create an app Password from this Link " https://myaccount.google.com/apppasswords" , This is mandatory because this bot should read the Mails in your inbox  

# Chat ID where you want to receive emails
CHAT_ID = '-100xxxxxxxxx' # Provide the chat id of the Telegram channel you want to forward Emails to

# Set to store processed email message IDs
processed_emails = set()  # this makes sure that no duplicate message will be sent again

prev_call_time = 0

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "I'm ready to receive emails!")

def extract_body(message):
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload is not None:
                    body = payload.decode()
                    return body
    else:
        payload = message.get_payload(decode=True)
        if payload is not None:
            body = payload.decode()
            return body

from datetime import datetime

def make_a_call(): # this function will make a call when an email is forwarded to the Telegram channel for Alerting purpose ( for that we need to register to twilio 
        account_sid = "xxxxxxxxxxxxxxxxxxxxxxx"
        auth_token = "ttttttttttttttttttttttt"
        client = Client(account_sid, auth_token)
    
        call = client.calls.create(
            url="http://demo.twilio.com/docs/voice.xml",
            to="+91xxxxxxxxx",
            from_="+1yyyyyyyyyyy")
    
        print(f"Call Made Successfully")
        return

def fetch_emails():
    try:
        today = datetime.today().strftime('%d-%b-%Y')  # Get today's date in the required format ( we need to avoid past emails )
        mail = imaplib.IMAP4_SSL(GMAIL_IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select('inbox') # This will make sure that our PRIMARY section in Gmail where this bot searches for new Emails 
        global prev_call_time
        status, data = mail.search(None, f'(FROM "target_email@xx.com" SINCE "{today}")') # make sure to replace target_email@xx.com with the mail id you are expecting to receive Emails from
        if status == 'OK':
            for num in data[0].split():
                status, msg_data = mail.fetch(num, '(RFC822)')
                if status == 'OK':
                    email_message = email.message_from_bytes(msg_data[0][1])
                    message_id = email_message['Message-ID']
                    # Check if this email has been processed already
                    if message_id not in processed_emails:
                        sender = email_message['From']
                        subject = email_message['Subject']
                        date_time = parsedate_to_datetime(email_message['Date'])
                        #body = extract_body(email_message)
                        # Truncate the email body if it exceeds the maximum allowed message length
                        max_length = 4000  # Since there is a limit of 4096 characters for a message in Telegram
                        truncated_body = body[:max_length] # This will split the body of the Email to 4000 charaters
                        # Send email details to Telegram
                        bot.send_message(CHAT_ID, f"New email from: {sender}\nSubject: {subject}\nDate and Time: {date_time}\nBody: {truncated_body}")
                        current_time = time.time()
                        time_diff = current_time - prev_call_time
                        print(time_diff)
                        
                        if time_diff >= 180: # This will make sure that when we have continuous emails being forwarded , we will make a call every 180 Seconds
                            print("codition is met")
                            make_a_call()
                            
                            prev_call_time = time.time()
                        
                        
                        # Mark email as read
                        mail.store(num, '+FLAGS', '\\Seen')
                        # Add message ID to processed set
                        processed_emails.add(message_id)
        mail.close()
        mail.logout()
    except Exception as e:
        print(f"Error fetching emails: {e}")

# Schedule email fetching periodically
import schedule
import time

schedule.every(10).seconds.do(fetch_emails) # we will check the Gmail server every 10 Seconds to search for any new Emails from the target Mail id

while True:
    schedule.run_pending()
    time.sleep(1)

# Run the bot
bot.polling()
