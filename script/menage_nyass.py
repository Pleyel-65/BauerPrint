import urllib.request
import json
import re
from home_printer.printer_model import Printer
from home_printer.image_raster import ThermalPrinterImage
import random
from flask_server import printer, LATE_COMMAND_DIR_PATH
from os import listdir
from pathlib import Path
# LATE_COMMAND_DIR_PATH = Path(".").absolute().joinpath("printcmd_queue")
MEME_PATH = Path(".").absolute().joinpath("menage_memes")
download_url = "https://docs.google.com/spreadsheets/d/10UsPaxLbLbiy-aKpmRMlXdIA7Xc7cipuH9ekh-PKstc/gviz/tq?tqx=out:json&sheet=MAIN"
def getMenageCandidates():
    urllib.request.urlretrieve(download_url, "./menage.txt")
    f = open("./menage.txt", "r")
    l = f.readlines()[1]
    # print(re.findall(r'{.*}', f))
    candidates = [v[0] for v in sorted([[v['v'] for v in r['c'][8:] if v] for r in json.loads(re.findall(r'{.*}', l)[0])["table"]["rows"] if r['c'][8] and r['c'][10] and not r['c'][10]['v']], key=lambda x : x[4])[-2:]]
    # print([r[0]['v'] for r in rows])
    f.close()
    possible_responses = ["Merci à {} & {} de faire le ménage", "C'est au tour de {} & {}", "{} & {} sont de corvée !", "A priori c'est {} & {} qui s'y collent", "{} & {} se sont porté.e.s volontaires", "{} & {} vont bien nous laver tout ça"]
    output_str = possible_responses[random.randint(1, len(possible_responses)) - 1].format(*candidates)
    return output_str

def printOutMenage(output_io, msg):
    possible_titles = ["Menage, menage", "Ma neige, mais nage", "Ménage Manège", "N-Mage Men Age", "M'ai je n'a mets Jeanne"]
    printer.set_mode(output_io, font_mode=25, font_size=20, justification=0)
    printer.text(output_io, possible_titles[random.randint(1, len(possible_titles)) - 1])
    img_files = listdir(MEME_PATH)
    img_path = MEME_PATH.joinpath(img_files[random.randint(1, len(img_files)) - 1])
    # with open(img_path, "rb") as img_file:
    with ThermalPrinterImage(img_path) as img:
        printer.image(output_io, img.get_byte_image())
    printer.set_mode(output_io, font_mode=0, font_size=12, justification=0)
    printer.text(output_io, msg)
    for _ in range(5):
        printer.text(output_io, "\n")

def endPrint(output_io):
    output_io.flush()
    output_io.close()

if __name__ == '__main__':
    output = printer.get_output(LATE_COMMAND_DIR_PATH)
    if output.is_char_device():
        output_io = open(output.as_posix(), "wb")
    else:
        output_io = open(output.as_posix(), "ab")
    printOutMenage(output_io, getMenageCandidates())
    endPrint(output_io)
    # MEME_PATH = Path("C:\\Users\\landr\\Downloads\\").absolute().joinpath("menage_memes")
    