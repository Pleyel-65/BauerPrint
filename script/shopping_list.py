from pathlib import Path
import re
from home_printer.printer_model import Printer, Path
from flask_server import printer, LATE_COMMAND_DIR_PATH

SHOPPINGLIST_PATH= Path('.').absolute().joinpath('shopping_list.txt')
if not SHOPPINGLIST_PATH.is_file():
    open(SHOPPINGLIST_PATH, 'wb').close()

def addToList(elem):
    if not elem or elem in ('', '\n'):
        return 
    
    c_list = getShoppingList()
    elem = list(re.sub(r'^\s+', '', elem))
    elem[0] = elem[0].upper()
    elem = re.sub(r'\s+$', '', ''.join(elem))
    if any([re.match(re.compile(re.sub(r'[sx]$', '', elem)+"[sx]?$", flags=re.IGNORECASE), c) for c in c_list] + [re.match(r'^/', elem)]):
        return

    with open(SHOPPINGLIST_PATH, "a") as f:
        f.writelines(elem+"\n")

def getShoppingList():
    with open(SHOPPINGLIST_PATH, "r") as f:
        c_list = [re.sub(r'\n', '', l) for l in f.readlines()]
    return c_list

def eraseShoppingList():
    with open(SHOPPINGLIST_PATH, "w") as f:
        f.write("")

def printShoppingList(output_io):
    c_list = getShoppingList()
    if len(c_list) == 0:
        return
    printer.cut(output_io)
    printer.set_mode(output_io, font_mode=25, font_size=16, justification=1)
    printer.text(output_io, "Shopping List\n")
    printer.set_mode(output_io, font_mode=0, font_size=12, justification=0)
    for c in c_list:
        printer.text(output_io, "- {}".format(c))
    printer.set_mode(output_io, font_mode=0, font_size=9, justification=1)
    printer.text(output_io, "Merci :) !")
    printer.cut(output_io)
    
