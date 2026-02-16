import json
from telethon import TelegramClient, events, functions, types
from telethon.tl.custom.button import Button
from my_secret_keys import *
from PIL import Image
import io
from home_printer.printer_model import Printer, Path
from home_printer.image_raster import ThermalPrinterImage
import os
import base64
from flask_server import printer, LATE_COMMAND_DIR_PATH
from datetime import datetime, timedelta, timezone
import glob
import re
import logging
# import aiofiles
import asyncio
from menage_nyass import getMenageCandidates, printOutMenage
from inspirationnal_quote import readLastQuote, writeNextQuote
from shopping_list import *
import random
import sys

now_time = ""
now_date = ""
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('telethon')
message_limit = 20
time_limit = 5

def readUserData():
    with open("./user_data.json", "r") as f:
        u_d = json.load(f)
        return u_d
    
def writeUserData(user_data):
    with open("./user_data.json", "w") as f:
        u_d = json.dump(user_data, f)
        return u_d

def getDateTime() -> list[str]:
    now = datetime.now()
    output = ["", ""]
    global now_date
    global now_time
    if now_date != now.strftime("%d-%m-%Y"):
        now_date = now.strftime("%d-%m-%Y")
        output[0] = now_date
    if now_time != now.strftime("%H:%M"):
        now_time = now.strftime("%H:%M")
        output[1] = now_time
    return output

def inspireMe(event):
    msg = event.raw_text
    has_match = re.match(r'/inspire', msg)
    if has_match:
        asyncio.create_task(client.send_message(event.chat, readLastQuote()))
        asyncio.create_task(writeNextQuote())
    return has_match

def endPrint(output_io):
    output_io.flush()
    output_io.close()

def menageNyass(event, output_io, u_d):
    msg = event.raw_text
    sender_id = event.sender_id
    has_match = re.match(r'/menage', msg)
    is_priviliged = checkPriviliges(event, u_d)
    if has_match:
        menage_msg = getMenageCandidates()
        asyncio.create_task(client.send_message(int(sender_id), menage_msg))
        if is_priviliged:
            printOutMenage(output_io, menage_msg)
    
    return has_match

def changeAnonymous(event, user_data):
    msg = event.raw_text
    has_changed = False
    sender_id = str(event.sender_id)
    all_users = user_data["anonymous"]
    # logger.info("loaded_json : ")
    # logger.info(all_users)

    if sender_id in all_users.keys():
        is_anonymous = all_users[sender_id]
    else:
        is_anonymous = False
        all_users[sender_id] = False
    if re.match(r'/anonymous', msg):
        # try:
        #     with open('./anonymous_users.json', mode='r') as f:
        #     # f = aiofiles.open('./anonymous_users.json', 'r')
        #         all_users =  json.load(f)
        #     # f.close()
        # except (json.decoder.JSONDecodeError, FileNotFoundError):
        #     all_users = {}

        is_anonymous = not is_anonymous
        all_users[sender_id] = is_anonymous
        if is_anonymous:
            asyncio.create_task(client(functions.messages.SendReactionRequest(peer=event.chat, msg_id=event.id, reaction=[types.ReactionEmoji(emoticon='🙈')])))
        respond_message = "🙈 Sneaky mode activated 🙈" if is_anonymous else "🐵 Your name will now appear unredacted 🐵"
        asyncio.create_task(client.send_message(int(sender_id), respond_message))
        has_changed = True
    
        # logger.info(all_users)
        user_data["anonymous"] = all_users
        # writeUserData(user_data)
        # with open('./anonymous_users.json', mode='w') as f:
        # # f = open('./anonymous_users.json', 'w')
        #     f.write(json.dumps(all_users))

    return is_anonymous, has_changed, user_data

def checkPriviliges(event, user_data):
    # with open('./user_priviliges.json', mode='r') as f:
    #     priviliged_users = json.load(f)
    # logger.info(priviliged_users)
    return event.sender_id in user_data["coloc"]

def checkBan(event, user_data):
    is_banned = event.sender_id in user_data["ban"]
    if is_banned:
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=event.chat, msg_id=event.id, reaction=[types.ReactionEmoji(emoticon='👎')])))
        asyncio.create_task(client.send_message(int(event.sender_id), "Nope, sorry, you're banned"))

    # with open('./user_priviliges.json', mode='r') as f:
    #     priviliged_users = json.load(f)
    # logger.info(priviliged_users)
    return is_banned

def checkSpam(event, u_d):
    # await client.get_messages(event.chat, ids=event.reply_to.reply_to_msg_id)
    # messages = await client.get_messages(event.sender_id , offset_date=datetime.now(tz=timezone.utc) - timedelta(minutes=5), reverse=True)
    # for i, message in enumerate(messages):
    # # [print(message.sender_id, ':', message.text) for message in messages]
    #     logger.info(message.sender_id != 1641835092 and len(messages) > i)
    #     if i > 20:
    #         return True
        # i += 1
    if (str(event.sender_id) == "1641835092"):
        return False
    u_msg_hist = u_d["history"][str(event.sender_id)]
    is_spamming = len(u_msg_hist) > message_limit
    logger.info(f"{event.sender_id}:{len(u_msg_hist)}")
    if is_spamming:
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=event.chat, msg_id=event.id, reaction=[types.ReactionEmoji(emoticon='👎')])))
        asyncio.create_task(client.send_message(int(event.sender_id), f"You've exceeded' limit of {message_limit} messages per {time_limit} minutes"))
    return is_spamming

def cutTicket(event, output_io, user_data):
    msg = event.raw_text
    has_match = re.match(r'/cut', msg)
    is_priviliged = checkPriviliges(event, user_data)
    if has_match and is_priviliged:
        printer.cut(output_io)
        endPrint(output_io)
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=event.chat, msg_id=event.id, reaction=[types.ReactionEmoji(emoticon='💔')])))
    elif has_match:
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=event.chat, msg_id=event.id, reaction=[types.ReactionEmoji(emoticon='👎')])))
        asyncio.create_task(client.send_message(event.chat, "Sorry but you cannot use this command"))

    return has_match

def noAscii(event):
    event.raw_text = event.raw_text.replace('’', "'")
    event.raw_text = re.sub(r'[”“]', '"', event.raw_text)
    forbidden_char = re.findall(r'[^\x20-\xFF\r\n]', event.raw_text)
    has_matched = len(forbidden_char) > 0
    if has_matched:
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=event.chat, msg_id=event.id, reaction=[types.ReactionEmoji(emoticon='😢')])))
        asyncio.create_task(client.send_message(event.chat, "申し訳ございませんが、その「{}]の字を印刷出来ません".format(", ".join(forbidden_char))))
    return has_matched

client = TelegramClient('FACKS-bot', api_id=api_id, api_hash=api_hash)
# LATE_COMMAND_DIR_PATH = Path(".").absolute().joinpath("printcmd_queue")
# IMG_PATH = Path(".").absolute().joinpath("replace_me")
async def add_shopping_main(event, user_data):
    has_matched = re.match(r'/add_shopping', event.raw_text)
    is_priviliged = checkPriviliges(event, user_data)
    if has_matched and is_priviliged:
        elems = getShoppingList()
        shopping_list = "\n- ".join(elems)
        str_list = "Current shopping list :\n\n- {}".format(shopping_list) if len(elems) > 0 else "Shopping list is currently empty.."
        await client.send_message(event.chat, str_list)
        asyncio.create_task(event.respond("What should I add to the list ?", buttons=Button.force_reply("some_random_text")))
    elif has_matched:
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=event.chat, msg_id=event.id, reaction=[types.ReactionEmoji(emoticon='👎')])))
        asyncio.create_task(client.send_message(event.chat, "Thank you, but your input was not asked for"))

    return has_matched
    
async def add_shopping_list(event, user_data):
    if not event.reply_to:
        return False
    replied = await client.get_messages(event.chat, ids=event.reply_to.reply_to_msg_id)
    # logger.info(replied.raw_text)
    has_matched = event.reply_to and replied.raw_text == "What should I add to the list ?"
    if has_matched:
        if not checkPriviliges(event, user_data):
            asyncio.create_task(client(functions.messages.SendReactionRequest(peer=event.chat, msg_id=event.id, reaction=[types.ReactionEmoji(emoticon='🖕')])))
        else:
            asyncio.create_task(client(functions.messages.SendReactionRequest(peer=event.chat, msg_id=event.id, reaction=[types.ReactionEmoji(emoticon='✍️')])))
            elems = event.raw_text.split('\n')
            [addToList(elem) for elem in elems]
            # addToList(re.sub(r'\n', ' ', event.raw_text))
    return has_matched

def print_shopping(event, output_io, user_data):
    has_matched = re.match(r'/print_shopping', event.raw_text)
    is_priviliged = checkPriviliges(event, user_data)
    if has_matched and is_priviliged:
        if len(getShoppingList()) > 0:
            printShoppingList(output_io)
            eraseShoppingList()
            endPrint(output_io)
            asyncio.create_task(client(functions.messages.SendReactionRequest(peer=event.chat, msg_id=event.id, reaction=[types.ReactionEmoji(emoticon='👌')])))
        else:
            asyncio.create_task(client(functions.messages.SendReactionRequest(peer=event.chat, msg_id=event.id, reaction=[types.ReactionEmoji(emoticon='🤔')])))
    elif has_matched:
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=event.chat, msg_id=event.id, reaction=[types.ReactionEmoji(emoticon='👎')])))
        asyncio.create_task(client.send_message(event.chat, "Thank you for your help, but we can get on with the shopping ourselves"))
    return has_matched

def monkey(event):
    if re.match(r'(?im).*[🙊🙈🙉🦍🦧🦥]', event.raw_text):
        
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=event.chat, msg_id=event.id, reaction=[types.ReactionEmoji(emoticon='🍌')])))
        asyncio.create_task(client.send_message(event.chat, "🐒"))
    elif re.match(r'(?im).*[🍌]', event.raw_text):
        # asyncio.create_task(client(functions.messages.SendReactionRequest(peer=event.chat, msg_id=event.id, reaction=[types.ReactionEmoji(emoticon='🦍')])))
        asyncio.create_task(client.send_message(event.chat, "🦍"))
    elif re.match(r'(?im).*[🐒]', event.raw_text):
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=event.chat, msg_id=event.id, reaction=[types.ReactionEmoji(emoticon='🍌')])))
        asyncio.create_task(client.send_message(event.chat, "🦧"))
    elif re.match(r'(?im).*[🐵]', event.raw_text):
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=event.chat, msg_id=event.id, reaction=[types.ReactionEmoji(emoticon='🍌')])))
        asyncio.create_task(client.send_message(event.chat, "🙊"))

    if re.match(r'(?im)[🙊🙈🙉🐵🦍🦧🦥🍌🐒]$', event.raw_text):
        return True
    return False

def setMsgHistory(event, user_data):
    date_format = "%d-%m-%Y %H-%M-%S"
    usr_id = str(event.sender_id)
    now = datetime.now()
    if not usr_id in user_data["history"].keys():
        user_data["history"][usr_id] = [now.strftime(date_format)]
    else:
        user_data["history"][usr_id].append(now.strftime(date_format))
    user_data["history"][usr_id] = [d for d in user_data["history"][usr_id] if datetime.strptime(d, date_format) > now - timedelta(minutes=time_limit)]
    return user_data


@client.on(events.NewMessage())
#@client.on(events.NewMessage(chats = [-5259715117]))
async def handler(event):
    u_d = readUserData()
    u_d = setMsgHistory(event, u_d)
    no_print = any([re.match(r'/start', event.raw_text), 
                   checkBan(event, u_d),
                   checkSpam(event, u_d), 
                   inspireMe(event),
                   monkey(event)])
    # if no_print:
    #     return
    # if re.match(r'/start', event.raw_text):
    #     return
    # if checkBan(event, u_d):
    # if await checkSpam(event, u_d):
    # if inspireMe(event):
    #     return
    # if monkey(event):
    #     return
    add_shopping_q =  await add_shopping_main(event, u_d)
        # return
    add_shopping_a =   await add_shopping_list(event, u_d)
        # return
    is_anonymous, anonymous_has_changed, u_d = changeAnonymous(event, u_d)
    # if anonymous_has_changed:
    #     return
    no_print = any([no_print, add_shopping_q, add_shopping_a, anonymous_has_changed])
    
    output = printer.get_output(LATE_COMMAND_DIR_PATH)
    if output.is_char_device():
        output_io = open(output.as_posix(), "wb")
    else:
        output_io = open(output.as_posix(), "ab")

    no_print = any([no_print, print_shopping(event, output_io, u_d), noAscii(event), menageNyass(event, output_io, u_d), cutTicket(event, output_io, u_d)])
    # if print_shopping(event, output_io, u_d):
    #     return
    # if noAscii(event):
    #     return

    # if menageNyass(event, output_io, u_d):
    #     return
    # if cutTicket(event, output_io):
    #     return
    writeUserData(u_d)
    if no_print:
        return

    printer.set_mode(output_io, font_mode=0, font_size=8, justification=1)
    now_str = getDateTime()
    [printer.text(output_io, s) for s in now_str if s != ""]
    printer.set_mode(output_io, font_mode=136, font_size=16, justification=0)
    if is_anonymous:
        printer.text(output_io, "???????????")
    elif event.sender.first_name:
        l_name = "" if not event.sender.last_name else " " + event.sender.last_name
        output_str = event.sender.first_name + l_name
        printer.text(output_io, output_str)
    elif event.sender.username:
        printer.text(output_io, event.sender.username)
    elif event.sender.last_name:
        printer.text(output_io, event.sender.last_name)
    else:
        printer.text(output_io, str(event.sender.id))
    printer.set_mode(output_io, font_mode=0, font_size=12)
    # print(event.sender.first_name + " " + event.sender.last_name)
    # if event.photo or event.sticker:
    if event.photo:
        img_name = Path(".").absolute().joinpath("replace_me")
        img_path = Path(glob.glob(str(img_name)+".*")[0])
        if img_path.is_file():
            os.remove(img_path)
        await event.download_media(str(img_name))

        # img_path = Path(glob.glob(str(img_name)+".*")[0])
        # if event.sticker:
        #     with open(img_path, "rb") as img_file:
        #         new_img = Image.open(img_file).convert("RGB")
        #         new_img.save(str(Path(".").absolute().joinpath("replace_me.jpg")),"jpeg")
        #     os.remove(img_path)

        img_path = Path(glob.glob(str(img_name)+".*")[0])
        with open(img_path, "rb") as img_file:
            img = ThermalPrinterImage(img_file)
            printer.image(output_io, img.get_byte_image())
        # print(event.file.media)
    # print(event.raw_text)
    printer.text(output_io, event.raw_text)
    for _ in range(5):
        printer.text(output_io, "\n")
    # printer.text(output_io, event.raw_text)
    endPrint(output_io)


if __name__ == "__main__":
    client.start(bot_token=bot_token)
    logger.info("Telegram Client Started")
    try:
        client.run_until_disconnected()
    except ConnectionError:
        sys.exit(1)


