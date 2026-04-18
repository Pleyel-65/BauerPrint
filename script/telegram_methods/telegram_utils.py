from datetime import datetime
from pathlib import Path
import json
import asyncio
from telegram_methods.my_secret_keys import su_id
import os
import re
import logging

logger = logging.getLogger(__name__)

async def disconnect(delay: int, client):
    logger.info(f"Telegram Client will disconnect in {delay} seconds")
    await asyncio.sleep(delay)
    await client.disconnect()


def getDateTime() -> list[str]:
    now = datetime.now()
    output = ["", ""]
    if not Path("./now_dates.json").is_file():
        with open("./now_dates.json", "w") as f:
            json.dump({"now_date": "", "now_time": ""}, f)
        now_date = ""
        now_time = ""
    else:
        with open("./now_dates.json", "r") as f:
            data = json.load(f)
            now_date = data["now_date"]
            now_time = data["now_time"]
    # global now_date
    # global now_time
    if now_date != now.strftime("%d-%m-%Y"):
        now_date = now.strftime("%d-%m-%Y")
        output[0] = now_date
    if now_time != now.strftime("%H:%M"):
        now_time = now.strftime("%H:%M")
        output[1] = now_time
    if any([d != "" for d in output]):
        with open("./now_dates.json", "w") as f:
            json.dump({"now_date": now_date, "now_time": now_time}, f)
    return output

class PrivateForwardedUser():
    def __init__(self, name):
        self.first_name = name
        self.last_name = None

def readFontModes():
    with open("./message_char_config.json", "r") as f:
        c_c = json.load(f)
        return c_c

def readUserData():
    with open("./user_data.json", "r") as f:
        u_d = json.load(f)
        return u_d
    
def writeUserData(user_data):
    with open("./user_data.json", "w") as f:
        u_d = json.dump(user_data, f)
        return u_d

def endPrint(output_io):
    output_io.flush()
    output_io.close()

def sendToSuperUser(client, msg):
    if msg.sender.id != su_id:
        logger.info(f'Forwarding to {su_id}')
        asyncio.create_task(client.forward_messages(su_id, msg))

multiple_image_lock = asyncio.Lock()
async def convertImageToJPG(dwnld_file_name: Path):
    async with multiple_image_lock:
        downloaded_media = [Path(f) for f in os.listdir(Path('.').absolute()) if re.search(re.compile(f'{dwnld_file_name}( \\(\\d+\\))?\\..*'), f)]
        fp = Path(downloaded_media[0])
        new_file_name = "replace_me.jpeg"
        if os.path.isfile(f"./{new_file_name}"):
            os.remove(new_file_name)

        if not fp.suffix in [".jpg", ".jpeg"]:
            os.system(f'''ffmpeg -i '{fp}' -vf "format=yuva444p,geq='if(lte(alpha(X,Y),1),255,p(X,Y))':'if(lte(alpha(X,Y),1),128,p(X,Y))':'if(lte(alpha(X,Y),1),128,p(X,Y))'" {new_file_name}''')
            # os.remove(fp)
        else:
            os.system(f'''ffmpeg -i '{fp}' -pix_fmt yuv444p {new_file_name}''')
            # fp.rename(new_file_name)
        os.remove(fp)


    return Path(".").absolute().joinpath(new_file_name)



# def printImageToFile(byte_img: bytes):
#     c_ind = len(os.listdir("../byte_imgs"))
#     with open(f"../byte_imgs/byte_img_{str(c_ind).zfill(3)}", "wb") as f:
#         f.write(byte_img)
