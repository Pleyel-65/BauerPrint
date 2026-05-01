import re
from telethon import Button, functions, types
import asyncio
from menage_nyass import getMenageCandidates, printOutMenage
from inspirationnal_quote import readLastQuote, writeNextQuote
from home_printer.printer_model import Printer, Path
from home_printer.image_raster import ThermalPrinterImage
from flask_server import printer
from datetime import timedelta, datetime
from logging import getLogger
from voicemail import OLD_MESSAGES_FOLDER
import os
from shopping_list import getShoppingList, addToList, printShoppingList, eraseShoppingList

from telegram_methods.telegram_checks import checkPriviliges
from telegram_methods.telegram_utils import endPrint
from telegram_methods.my_secret_keys import su_id
logger = getLogger(__name__)

def inspireMe(client, message):
    msg = message.raw_text
    has_match = re.match(r'/inspire', msg)
    if has_match:
        asyncio.create_task(client.send_message(message.chat, readLastQuote(), buttons=Button.clear()))
        asyncio.create_task(writeNextQuote())
    return has_match


def menageNyass(client, message, output_io, u_d):
    msg = message.raw_text
    sender_id = message.sender.id
    has_match = re.match(r'/menage', msg)
    is_priviliged = checkPriviliges(message, u_d)
    if has_match:
        menage_msg = getMenageCandidates()
        asyncio.create_task(client.send_message(int(sender_id), menage_msg, buttons=Button.clear()))
        if is_priviliged:
            printOutMenage(output_io, menage_msg)
    
    return has_match

def changeAnonymous(client, message, user_data):
    msg = message.raw_text
    has_changed = False
    sender_id = str(message.sender_id)
    all_users = user_data["anonymous"]

    if sender_id in all_users.keys():
        is_anonymous = all_users[sender_id]
    else:
        is_anonymous = False
        all_users[sender_id] = False
    if re.match(r'/anonymous', msg):
        is_anonymous = not is_anonymous
        all_users[sender_id] = is_anonymous
        if is_anonymous:
            asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='🙈')])))
        respond_message = "🙈 Sneaky mode activated 🙈" if is_anonymous else "🐵 Your name will now appear unredacted 🐵"
        asyncio.create_task(client.send_message(int(sender_id), respond_message, buttons=Button.clear()))
        has_changed = True
    
        user_data["anonymous"] = all_users

    return is_anonymous, has_changed, user_data

def cutTicket(client, message, output_io, user_data):
    msg = message.raw_text
    has_match = re.match(r'/cut', msg)
    is_priviliged = checkPriviliges(message, user_data)
    if has_match and is_priviliged:
        printer.cut(output_io)
        endPrint(output_io)
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='💔')])))
    elif has_match:
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='👎')])))
        asyncio.create_task(client.send_message(message.chat, "Sorry but you cannot use this command", buttons=Button.clear()))

    return has_match

def noAscii(client, message):
    message.raw_text = message.raw_text.replace('’', "'")
    message.raw_text = re.sub(r'[”“]', '"', message.raw_text)
    forbidden_char = re.findall(r'[^\x20-\xFF\r\n]', message.raw_text)
    has_matched = len(forbidden_char) > 0
    if has_matched:
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='😢')])))
        asyncio.create_task(client.send_message(message.chat, "申し訳ございませんが、その「{}」の字を印刷出来ません".format(", ".join(forbidden_char)), buttons=Button.clear()))
    message.raw_text = re.sub(r'[^\x20-\xFF\r\n]', '', message.raw_text)
    return has_matched


async def add_shopping_main(client, message, user_data):
    has_matched = re.match(r'/add_shopping', message.raw_text)
    is_priviliged = checkPriviliges(message, user_data)
    if has_matched and is_priviliged:
        elems = getShoppingList()
        shopping_list = "\n- ".join(elems)
        str_list = "Current shopping list :\n\n- {}".format(shopping_list) if len(elems) > 0 else "Shopping list is currently empty.."
        await client.send_message(message.chat, str_list, buttons=Button.clear())
        but = Button.force_reply("some_random_text")
        await message.respond("What should I add to the list ?", buttons=but)
    elif has_matched:
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='👎')])))
        asyncio.create_task(client.send_message(message.chat, "Thank you, but your input was not asked for", buttons=Button.clear()))

    return has_matched
    
async def add_shopping_list(client, message, user_data):
    if not message.reply_to:
        return False
    replied = await client.get_messages(message.chat, ids=message.reply_to.reply_to_msg_id)
    # logger.info(replied.raw_text)
    has_matched = message.reply_to and replied.raw_text == "What should I add to the list ?"

    if has_matched:
        if not checkPriviliges(message, user_data):
            asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='🖕')])))
            asyncio.create_task(client.send_message(message.chat,'Smart-arse',buttons=Button.clear()))
        else:
            asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='✍️')])))
            elems = message.raw_text.split('\n')
            [addToList(elem) for elem in elems]
            asyncio.create_task(client.send_message(message.chat,'Noice, please use /print_shopping to print list',buttons=Button.clear()))
    
    return has_matched

def print_shopping(client, message, output_io, user_data):
    has_matched = re.match(r'/print_shopping', message.raw_text)
    is_priviliged = checkPriviliges(message, user_data)
    if has_matched and is_priviliged:
        if len(getShoppingList()) > 0:
            printShoppingList(output_io)
            eraseShoppingList()
            endPrint(output_io)
            asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='👌')])))
            asyncio.create_task(client.send_message(message.chat, "Thank you for your service 🫡", buttons=Button.clear()))
        else:
            asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='🤔')])))
            asyncio.create_task(client.send_message(message.chat, "Are you trying to waste some paper on an empty list", buttons=Button.clear()))
    elif has_matched:
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='👎')])))
        asyncio.create_task(client.send_message(message.chat, "Thank you for your help, but we can get on with the shopping ourselves", buttons=Button.clear()))
    return has_matched

def monkey(client, message):
    if re.match(r'(?im).*[🙊🙈🙉🦍🦧🦥]', message.raw_text):
        
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='🍌')])))
        asyncio.create_task(client.send_message(message.chat, "🐒",buttons=Button.clear()))
    elif re.match(r'(?im).*[🍌]', message.raw_text):
        # asyncio.create_task(client(functions.messages.SendReactionRequest(peer=event.chat, msg_id=event.id, reaction=[types.ReactionEmoji(emoticon='🦍')])))
        asyncio.create_task(client.send_message(message.chat, "🦍", buttons=Button.clear()))
    elif re.match(r'(?im).*[🐒]', message.raw_text):
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='🍌')])))
        asyncio.create_task(client.send_message(message.chat, "🦧", buttons=Button.clear()))
    elif re.match(r'(?im).*[🐵]', message.raw_text):
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='🍌')])))
        asyncio.create_task(client.send_message(message.chat, "🙊", buttons=Button.clear()))

    if re.match(r'(?im)[🙊🙈🙉🐵🦍🦧🦥🍌🐒]$', message.raw_text):
        return True
    return False



def reboot(message, is_catching_up):
    # su_id = 1641835092
    logger.info(is_catching_up)
    has_matched = re.match(r'/reboot', message.raw_text)
    do_thing = has_matched and message.sender_id == su_id and not is_catching_up
    return do_thing

def restart(message, is_catching_up):
    logger.info(is_catching_up)
    # su_id = 1641835092
    has_matched = re.match(r'/restart', message.raw_text)
    do_thing = has_matched and message.sender_id == su_id and not is_catching_up
    return do_thing
        

def addBeer(client, message, user_data):
    has_matched = re.match(r'/add_beer', message.raw_text)
    if not has_matched:
        return has_matched, user_data
    
    beer_data = user_data["beers"]
    if not str(message.sender_id) in beer_data:
        beer_data[str(message.sender_id)] = 0
    beer_data[str(message.sender_id)] += 1

    match beer_data[str(message.sender_id)]:
        case 1:
            suffix = "st"
        case 2:
            suffix = "nd"
        case 3:
            suffix = "rd"
        case _:
            suffix = "th"
    if beer_data[str(message.sender_id)] < 20:
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='🍾')])))
    else:
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='🤮')])))
    asyncio.create_task(client.send_message(message.chat, f"Enjoy your {beer_data[str(message.sender_id)]}{suffix} beer !", buttons=Button.clear()))

    user_data["beers"] = beer_data
    return has_matched, user_data

async def printBeerTotal(client, message, output_io, user_data):
    has_matched = re.match(r'/print_beer', message.raw_text)
    if has_matched and not checkPriviliges(message, user_data):
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='👎')])))
        asyncio.create_task(client.send_message(message.chat, "Functionality reserved to members of sharehouse", buttons=Button.clear()))
        return has_matched, user_data

    if not has_matched or len(user_data["beers"].keys()) == 0:
        return has_matched, user_data
    
    printer.cut(output_io)
    printer.set_mode(output_io, font_mode=25, font_size=20, justification=0)
    printer.text(output_io, "Concours de Pochtron")
    printer.set_mode(output_io, font_mode=0, font_size=12)
    printer.text(output_io, "\n")
    for id, beer_count in user_data["beers"].items():
        user = await client.get_entity(int(id))
        if user.first_name:
            l_name = "" if not user.last_name else " " + user.last_name
            user_name = user.first_name + l_name
        elif user.username:
            user_name = user.username
        elif user.last_name:
            user_name = user.last_name
        else:
            user_name = str(id)
        printer.text(output_io, f"{user_name}: {beer_count}")
    printer.text(output_io, "\n")
    printer.cut(output_io)
    endPrint(output_io)

    asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='🤝')])))
    user_data["beers"] = {}
    return has_matched, user_data

def silent_voicemail(client, message, user_data):
    has_matched = re.match(r'/silent_voicemail', message.raw_text)
    if has_matched:
        if not checkPriviliges(message, user_data):
            asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='👎')])))
            asyncio.create_task(client.send_message(message.chat, "You are not concerned by the noise that the voicemail makes", buttons=Button.clear()))
            return has_matched, user_data
        mode = not user_data["silent_voicemail"]
        user_data["silent_voicemail"] = mode
        if mode:
            asyncio.create_task(client.send_message(message.chat, "☎️ No more getting woken up on the couch ☎️", buttons=Button.clear()))
        else:
            asyncio.create_task(client.send_message(message.chat, "📞 Loud mode activated ! 📞", buttons=Button.clear()))
    return has_matched, user_data




async def unreadMessage(client, message, user_data):
    has_matched = re.match(r'/unread_voicemail', message.raw_text)
    if has_matched:
        if not checkPriviliges(message, user_data):
            asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='👎')])))
            asyncio.create_task(client.send_message(message.chat, "Functionality reserved to members of sharehouse", buttons=Button.clear()))
            return has_matched  
        msgs = os.listdir(OLD_MESSAGES_FOLDER)
        if not msgs:
            asyncio.create_task(client.send_message(message.chat, "No voicemail...", buttons=Button.clear()))
            return has_matched  
        msg_buttons = []
        for m in msgs:
            receive_date = datetime.strptime(re.search(r'\d{4}([_|-]\d{2}){5}', Path(m).stem).group(0), "%Y-%m-%d_%H-%M-%S")
            id = re.search(r'\d+(?=(.mp3|.oga)?$)', m).group(0)
            logger.info(id)
            if id != "0":
                user = await client.get_entity(int(id))
                if user.first_name:
                    l_name = "" if not user.last_name else " " + user.last_name
                    user_name = user.first_name + l_name
                elif user.username:
                    user_name = user.username
                elif user.last_name:
                    user_name = user.last_name
                else:
                    user_name = str(id)
            else: 
                user_name = "???"
            msg_buttons.append(f"{user_name} {receive_date.strftime("%d/%m/%y %H:%M:%S")}")


        asyncio.create_task(client.send_message(message.sender_id, "What message do you whish to unread ?", buttons=[[Button.inline(msg, f'unread {msgs[i]}')] for i, msg in enumerate(msg_buttons)]+[[Button.inline("Cancel", "unread none")]]))

    return has_matched

def deleteMessages(client, message, user_data):
    has_matched = re.match(r'/delete_voicemail', message.raw_text)
    if has_matched:
        if not checkPriviliges(message, user_data):
            asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='👎')])))
            asyncio.create_task(client.send_message(message.chat, "Functionality reserved to members of sharehouse", buttons=Button.clear()))
            return has_matched
        if not os.listdir(OLD_MESSAGES_FOLDER):
            asyncio.create_task(client.send_message(message.chat, "No voicemail...", buttons=Button.clear()))
            return has_matched
        counts = [0] * 12
        counts[1], counts[-2] = 1, 1
        now = datetime.now()
        lim_dates = [now - timedelta(hours=1), now - timedelta(days=1), now - timedelta(weeks=1), now - timedelta(days=31)]
        for msg_name in os.listdir(OLD_MESSAGES_FOLDER):
            counts[-1] += 1
            for i, lim in enumerate(lim_dates):
                receive_date = datetime.strptime(re.search(r'\d{4}([_|-]\d{2}){5}', msg_name).group(0), "%Y-%m-%d_%H-%M-%S")  
                if receive_date <= lim:
                    counts[i+2] += 1
                if receive_date >= lim:
                    counts[i+6] += 1


        msg_buttons = ["none", "oldest", "older than an hour", "older than a day", "older than a week", "older than a month", "younger than an hour", "younger than a day", "younger than a week", "younger than a month", "youngest", "all"]
        asyncio.create_task(client.send_message(message.sender_id, "What messages do you wish to delete ?", buttons=[[Button.inline(f"{msg} ({counts[i]})",  f'delete {i}')] for i, msg in enumerate(msg_buttons)]))
    return has_matched