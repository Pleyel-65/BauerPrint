from telethon import TelegramClient, events, functions, types
from telethon.tl.custom.button import Button
from home_printer.printer_model import Printer, Path
from home_printer.image_raster import ThermalPrinterImage
from flask_server import printer, LATE_COMMAND_DIR_PATH
from datetime import datetime, timedelta, timezone
import re
import logging
# import aiofiles
import asyncio
import os

from shopping_list import *
import sys
from voicemail import Phone, NEW_MESSAGES_FOLDER, OLD_MESSAGES_FOLDER
import subprocess

from telegram_methods.telegram_utils import PrivateForwardedUser, getDateTime, readFontModes, readUserData, writeUserData, endPrint, sendToSuperUser, convertImageToJPG, disconnect
from telegram_methods.telegram_checks import checkBan, checkSpam, setMsgHistory
from telegram_methods.telegram_functionnalities import inspireMe, reboot, restart, monkey, deleteMessages, add_shopping_main, add_shopping_list, addBeer, unreadMessage, silent_voicemail, changeAnonymous, print_shopping, noAscii, menageNyass, cutTicket, printBeerTotal
from telegram_methods.my_secret_keys import *



# class AskedForReboot(Exception):
#     pass

# class AskedForRestart(Exception):
#     pass
# now_time = ""
# now_date = ""
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('telethon')

client = TelegramClient('FACKS-bot', api_id=api_id, api_hash=api_hash, catch_up=True)
is_catching_up = True
called_reboot = False


@client.on(events.CallbackQuery)
async def phoneHandler(event):
    phone = Phone()
    request = str(event.data, 'utf-8')
    logger.info(f"Got an order {request}")
    try:
        file_name = re.search(r'(?<=^(delete|unread) ).*$', request)[0]
        # logger.info(f"Working on  {file_name}")
        if re.match(r'unread', request):
            if file_name != "none":
                phone.unreadMessage(OLD_MESSAGES_FOLDER.joinpath(file_name))
            # logger.info(f"Unread {file_name}")
        elif re.match(r'delete', request):
            before = datetime.min
            after = datetime.max
            oldest = False
            youngest = False
            match int(file_name):
                case 1:
                    oldest = True
                case 2:
                    before = datetime.now() - timedelta(hours=1)
                case 3:
                    before = datetime.now() - timedelta(days=1)
                case 4:
                    before = datetime.now() - timedelta(weeks=1)
                case 5:
                    before = datetime.now() - timedelta(days=30)
                case 6:
                    after = datetime.now() - timedelta(hours=1)
                case 7:
                    after = datetime.now() - timedelta(days=1)
                case 8:
                    after = datetime.now() - timedelta(weeks=1)
                case 9:
                    after = datetime.now() - timedelta(days=30)
                case 10:
                    youngest = True
                case 11:
                    before = datetime.max
                    after = datetime.min
            phone.removeMessage(before, after, oldest, youngest)
            # logger.info(f"Deleted {file_name}")
    except Exception as e:
        raise e
    finally:
        await event.answer()
        await event.delete()
        return

    


@client.on(events.NewMessage)
async def messageEventHandler(event):
    message = event.message
    if event.sender.bot: 
        logger.info(f"Message sent from bot, skipping...")
        return
    rez = await handleMessage(message, is_catching_up)
    if rez == "reboot":
        global called_reboot
        logger.info("Disconnecting")
        print("Disconnecting")
        called_reboot = True
        await client.disconnect()
    elif rez == "restart":
        await client.disconnect()
        # return subprocess.run(["sudo", "systemctl", "restart", "facks-machine.service"])
    # TODO: make telegram client write message to file in bytes and have another worker printing them out then remove them as soon as he finds them
    # TODO: clean the fuck up
    
async def handleMessage(message, is_catching_up = False):
    u_d = readUserData()
    u_d["last_seen_message"][str(message.chat.id)] = message.id
    writeUserData(u_d)
    logger.info(f"Received message from {message.sender.id}")
    logger.info(f"Has photo : {message.photo or message.sticker}")
    logger.info(f"{message.raw_text}")
    askedReboot = reboot(message, is_catching_up)
    askedRestart = restart(message, is_catching_up)
    if askedReboot or askedRestart:
        # await client.send_message(event.chat, f"Catching up before {'reboot' if askedReboot else 'restart'}", buttons=Button.clear())
        await client.send_message(message.chat, f"Night night" if askedReboot else f"Gone for a quick nap", buttons=Button.clear())
        # await client.catch_up()
        # await client.disconnect()
        if askedReboot:
            return "reboot"
        else:
            return "restart"
            # await client.send_message(event.chat, f"Gone for a quick nap", buttons=Button.clear())

    sendToSuperUser(client, message)
    u_d = setMsgHistory(message, u_d)
    no_print = any([re.match(r'/start', message.raw_text), 
                   checkBan(client, message, u_d),
                   checkSpam(client, message, u_d), 
                   inspireMe(client, message),
                   monkey(client, message), 
                   deleteMessages(client, message, u_d)])
    # remove_message = await deleteMessages(event, u_d)
    # unread = await unreadMessage(event, u_d)
    add_shopping_q =  await add_shopping_main(client, message, u_d)
    add_shopping_a =   await add_shopping_list(client, message, u_d)
    unread =   await unreadMessage(client, message, u_d)
    is_beer, u_d = addBeer(client, message, u_d)
    silent_voicemail_changed, u_d = silent_voicemail(client, message, u_d)
    is_anonymous, anonymous_has_changed, u_d = changeAnonymous(client, message, u_d)

    if message.video:
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='👎')])))
        asyncio.create_task(client.send_message(message.chat, "I don't quite think you understand how a fax machine works...", buttons=Button.clear()))
        return

    no_print = any([no_print, add_shopping_q, add_shopping_a, anonymous_has_changed, is_beer, unread, silent_voicemail_changed])
    
    output = printer.get_output(LATE_COMMAND_DIR_PATH)
    if output.is_char_device():
        output_io = open(output.as_posix(), "wb")
    else:
        output_io = open(output.as_posix(), "ab")

    noascii = noAscii(client, message)
    no_print = any([no_print, print_shopping(client, message, output_io, u_d), 
                    menageNyass(client, message, output_io, u_d), 
                    cutTicket(client, message, output_io, u_d)])
    is_print_beer, u_d = await printBeerTotal(client, message, output_io, u_d)
    writeUserData(u_d)
    if any([no_print, is_print_beer]):
        return

    char_config = readFontModes()
    ts_cc = char_config["timestamp"]
    un_cc = char_config["user_name"]
    mb_cc = char_config["message_body"]
    space_between_messages = char_config["space_between_messages"]
    printer.set_mode(output_io, font_mode=ts_cc["mode"], font_size=ts_cc["size"], justification=ts_cc["justif"])
    now_str = getDateTime()
    [printer.text(output_io, s) for s in now_str if s != ""]
    printer.set_mode(output_io, font_mode=un_cc["mode"], font_size=un_cc["size"], justification=un_cc["justif"])
    
    # If message is forwarded by super user, print original sender user name
    if message.forward and message.sender.id == su_id:
        sender = PrivateForwardedUser(message.forward.from_name) if not message.forward.sender_id else await message.forward.get_sender()
    else:
        sender = message.sender

    # Sender name
    if is_anonymous:
        printer.text(output_io, "???????????")
    elif sender.first_name:
        l_name = "" if not sender.last_name else " " + sender.last_name
        output_str = sender.first_name + l_name
        printer.text(output_io, output_str)
    elif sender.username:
        printer.text(output_io, sender.username)
    elif sender.last_name:
        printer.text(output_io, sender.last_name)
    else:
        printer.text(output_io, str(sender.id))
    
    printer.set_mode(output_io, font_mode=mb_cc["mode"], font_size=mb_cc["size"], justification=mb_cc["justif"])
    # print(sender.first_name + " " + sender.last_name)
    if message.photo or message.sticker:
    # if event.photo:
        downloaded_fp_name = "downloaded_media"
        img_name = Path(".").absolute().joinpath(downloaded_fp_name)
        # if img_path.is_file():
        #     os.remove(img_path)

        await message.download_media(str(img_name))
        # img_path = Path(glob.glob(str(img_name)+".*")[0])
        # if event.sticker:
        #     with open(img_path, "rb") as img_file:
        #         new_img = Image.open(img_file).convert("RGB")
        #         new_img.save(str(Path(".").absolute().joinpath("replace_me.jpg")),"jpeg")
        #     os.remove(img_path)

        # while downloaded_media:
        #     try:
        conv_img_path = await convertImageToJPG(downloaded_fp_name)
        with ThermalPrinterImage(conv_img_path) as img:    
            byte_img = img.get_byte_image()
            printer.image(output_io, byte_img)
            # except FileNotFoundError:
            #     continue
            # finally:
            #     downloaded_media = [Path(f) for f in os.listdir(Path('.').absolute()) if re.search(r'downloaded_media( \(\d+\))?\..*', f)]
            #     logger.info(downloaded_media)
    # logger.info(event)
    if message.voice:
        f_name = f"{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_{message.sender.id if not is_anonymous else 0000000000}"
        if u_d["silent_voicemail"]:
            download_path = OLD_MESSAGES_FOLDER.joinpath(f_name)
        else:
            download_path = NEW_MESSAGES_FOLDER.joinpath(f_name)
        await message.download_media(str(download_path))
        message.raw_text = "New voicemail"


    printer.set_mode(output_io, font_mode=mb_cc["mode"], font_size=mb_cc["size"], justification=mb_cc["justif"])
    printer.text(output_io, message.raw_text)
    for _ in range(space_between_messages):
        printer.text(output_io, "\n")
    endPrint(output_io)
    if not noascii:
        asyncio.create_task(client(functions.messages.SendReactionRequest(peer=message.chat, msg_id=message.id, reaction=[types.ReactionEmoji(emoticon='✍️')])))

# async def sync_up():
#     u_d = readUserData()
#     if not "last_seen_message" in u_d.keys() or not isinstance(u_d["last_seen_message"], dict):
#         u_d["last_seen_message"] = {}
#         writeUserData(u_d)
#         return
#     logger.info(u_d["last_seen_message"])
#     recorded_dialogs = u_d["last_seen_message"].keys()
#     # dialogs = await client.get_dialogs(ignore_migrated=True)
#     # logger.info(dialogs)
    
#     for dialog in recorded_dialogs:
#         # logger.info(dialog.id)
#         # if not str(dialog.id) in recorded_dialogs: return
#         # logger.info("Found stuff !")
#         last_seen_id = u_d["last_seen_message"][dialog]
#         async for msg in client.iter_messages(int(dialog), min_id=last_seen_id):
#             logger.info(f"Caught up with {dialog}:{msg.id}")
#             await handleMessage(msg, True)


async def main():
    
    global is_catching_up
    disconnect_in = 60 * 60 * 3
    # await client.start(bot_token=bot_token)
    logger.info("Telegram Client Starting")
    await client.start(bot_token=bot_token)
    asyncio.create_task(disconnect(disconnect_in, client))
    # await sync_up()
    while not client.is_connected():
        await asyncio.sleep(1)
    is_catching_up = False
    logger.info("Telegram Client Running")
    await client.run_until_disconnected()
    if called_reboot:
        subprocess.run(["sudo", "reboot"])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(e)
    finally:
        sys.exit(1)

