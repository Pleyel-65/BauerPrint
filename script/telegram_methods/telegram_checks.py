import asyncio
from telethon import functions, Button, types
from logging import getLogger
from telegram_methods.my_secret_keys import su_id
from datetime import timedelta, datetime

logger = getLogger(__name__)
message_limit = 20
time_limit = 5

def checkPriviliges(msg, user_data):
    return msg.sender.id in user_data["coloc"]

def checkBan(client, msg, user_data):
    is_banned = msg.sender.id in user_data["ban"]
    if is_banned:
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=msg.chat, msg_id=msg.id, reaction=[types.ReactionEmoji(emoticon='👎')])))
        asyncio.create_task(client.send_message(int(msg.sender.id), "Nope, sorry, you're banned", buttons=Button.clear()))
    return is_banned

def checkSpam(client, msg, u_d):
    if (str(msg.sender.id) == str(su_id)):
        return False
    u_msg_hist = u_d["history"][str(msg.sender.id)]
    is_spamming = len(u_msg_hist) > message_limit
    logger.info(f"{msg.sender.id}:{len(u_msg_hist)}")
    if is_spamming:
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=msg.chat, msg_id=msg.id, reaction=[types.ReactionEmoji(emoticon='👎')])))
        asyncio.create_task(client.send_message(int(msg.sender.id), f"You've exceeded' limit of {message_limit} messages per {time_limit} minutes", buttons=Button.clear()))
    return is_spamming

def setMsgHistory(message, user_data):
    date_format = "%d-%m-%Y %H-%M-%S"
    usr_id = str(message.sender_id)
    now = datetime.now()
    if not usr_id in user_data["history"].keys():
        user_data["history"][usr_id] = [now.strftime(date_format)]
    else:
        user_data["history"][usr_id].append(now.strftime(date_format))
    user_data["history"][usr_id] = [d for d in user_data["history"][usr_id] if datetime.strptime(d, date_format) > now - timedelta(minutes=time_limit)]
    return user_data

