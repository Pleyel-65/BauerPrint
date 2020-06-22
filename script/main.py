from home_printer.printer_model import *
from home_printer.image_raster import *
from flask import Flask, request, render_template, jsonify
from urllib.parse import unquote
import json

LATE_COMMAND_DIR_PATH = Path(".").absolute().parent.joinpath("printcmd_queue")

app = Flask(__name__)
printer = Printer(LATE_COMMAND_DIR_PATH)


def parse_request(req):
    # Parses application/json request body data into a Python dictionary
    payload = req.get_data().decode("utf-8")
    payload = unquote(payload)
    payload = json.loads(payload)

    return payload


@app.route("/", methods=['GET'])
def index():
    return render_template("index.html")


@app.route("/print", methods=['POST'])
def print_thermal():
    payload = parse_request(request)
    output = printer.get_output(LATE_COMMAND_DIR_PATH)

    if output.is_char_device():
        output_io = open(output.as_posix(), "wb")
    else:
        output_io = open(output.as_posix(), "ab")

    if "set" in payload.keys():
        if "font_mode" in payload["set"].keys():
            printer.set_mode(output_io, font_mode=payload["set"]["font_mode"])
        if "justification" in payload["set"].keys():
            printer.set_mode(output_io, justification=payload["set"]["justification"])
        if "font_size" in payload["set"].keys():
            printer.set_mode(output_io, font_size=payload["set"]["font_size"])

    if "image" in payload.keys():
        img = ThermalPrinterImage.from_html_base64(payload["image"])
        printer.image(output_io, img.get_byte_image())

    if "text" in payload.keys():
        printer.text(output_io, payload["text"])

    if "cut" in payload.keys() and payload["cut"]:
        printer.cut(output_io)

    output_io.flush()
    output_io.close()
    return jsonify({"success": True})


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True, host="0.0.0.0")
