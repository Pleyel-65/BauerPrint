from home_printer.printer_model import Printer, Path
from home_printer.image_raster import ThermalPrinterImage
from flask_server import printer, LATE_COMMAND_DIR_PATH


output = printer.get_output(LATE_COMMAND_DIR_PATH)
if output.is_char_device():
    output_io = open(output.as_posix(), "wb")
else:
    output_io = open(output.as_posix(), "ab")

printer.set_mode(output_io, font_mode=136, font_size=16, justification=0)
printer.text(output_io, "Hello")
printer.flush()