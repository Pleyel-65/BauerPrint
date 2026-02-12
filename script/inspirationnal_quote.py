import time
import requests
import random
import re
from functools import partial
from home_printer.printer_model import Printer
from home_printer.image_raster import ThermalPrinterImage
from flask_server import printer, LATE_COMMAND_DIR_PATH
from datetime import datetime
# LATE_COMMAND_DIR_PATH = Path(".").absolute().joinpath("printcmd_queue")
def keepCase(match, word='som'):
    word = list(word)
    for i, c in enumerate(word):            
        if i == 0 or (re.match(r'[a-z]', c) and re.match(r'[A-Z]', match.group(0)[min(i, len(match.group(0))-1)])):
            word[i] = str.upper(c)
        if match.group(0) == "I" and i != 0:
            return "".join(word)
    return "".join(word)
def getQuote():
    website = "https://randomwordgenerator.com/json/inspirational-quote.json"
    # with urllib.request.urlopen(website) as quotes:
    data = requests.get(website).json()
    words_to_som = "|".join(["I(’|')m", "I am", "you are"])
    change_to_som = re.compile("(?i)\\b({})\\b".format(words_to_som))
    quote = re.sub(change_to_som, "Som is", re.sub(r'<[^<>]*>', '', data['data'][random.randint(1, len(data['data'])) - 1]["inspirational_quote"]))

    words_to_som = "|".join(["Man", "woman", "som", "girl", "boy", "person", "you", "I", "me", "she", "he", "yourself", "human", "god", "myself"])
    change_to_som = re.compile("(?i)\\b({})\\b".format(words_to_som))
    quote = re.sub(change_to_som, "Som", quote)

    quote = re.sub(r'(?i)\byour\b', "Som's", quote)
    return quote

def printOutQuote(output_io, msg):
    printer.set_mode(output_io, font_mode=25, font_size=16, justification=1)
    printer.text(output_io, "Som quote of the day")    
    printer.set_mode(output_io, font_mode=1, font_size=12, justification=1)
    printer.text(output_io, datetime.now().strftime("%d-%m-%Y"))
    printer.set_mode(output_io, font_mode=0, font_size=12, justification=0)
    printer.text(output_io, msg)
    for _ in range(5):
        printer.text(output_io, "\n")

def endPrint(output_io):
    output_io.flush()
    output_io.close()

if __name__ == '__main__':
    time_to_sleep = random.randint(0, 10800)
    print("Printing quote in {} seconds".format(time_to_sleep))
    time.sleep(time_to_sleep)
    output = printer.get_output(LATE_COMMAND_DIR_PATH)
    if output.is_char_device():
        output_io = open(output.as_posix(), "wb")
    else:
        output_io = open(output.as_posix(), "ab")
    printOutQuote(output_io, getQuote())
    endPrint(output_io)
