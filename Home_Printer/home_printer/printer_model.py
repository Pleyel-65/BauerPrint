import datetime
import re
import subprocess
import time
import os
from pathlib import Path

# Weird characters
utf2pos_map = {
    b"\xc3\x87": b"\x80",
    b"\xc3\xbc": b"\x81",
    b"\xc3\xa9": b"\x82",
    b"\xc3\xa2": b"\x83",
    b"\xc3\xa4": b"\x84",
    b"\xc3\xa0": b"\x85",
    b"\xc3\xa7": b"\x87",
    b"\xc3\xaa": b"\x88",
    b"\xc3\xab": b"\x89",
    b"\xc3\xa8": b"\x8a",
    b"\xc3\xaf": b"\x8b",
    b"\xc3\xae": b"\x8c",
    b"\xc3\xac": b"\x8d",
    b"\xc3\x84": b"\x8e",
    b"\xc3\x89": b"\x90",
    b"\xc3\xa6": b"\x91",
    b"\xc3\x86": b"\x92",
    b"\xc3\xb4": b"\x93",
    b"\xc3\xb2": b"\x94",
    b"\xc3\xbf": b"\x95",
    b"\xc3\x96": b"\x96",
    b"\xc3\x9c": b"\x97",
    b"\xc3\xa1": b"\xa0",
    b"\xc3\xad": b"\xa1",
    b"\xc3\xb3": b"\xa2",
    b"\xc3\xba": b"\xa3"
}


class Printer:
    def __init__(self, check_dir=None):
        self.printer_connected = False
        self.get_output(check_dir)

    def __reset_printer(self, output_file: Path, check_dir=None):
        # Set baud rate
        subprocess.run('stty -F "' + output_file.as_posix() + '" 115200 raw -echo', shell=True)
        # Initiate printer
        with open(output_file.as_posix(), "wb") as output:
            self.set_mode(output, font_mode=0, justification=0, font_size=12)
            # Dump waiting commands if any
            if isinstance(check_dir, Path):
                self.__print_queued_commands_from_files(output, check_dir)

    def __print_queued_commands_from_files(self, output, dir_path: Path):
        if self.printer_connected:
            command_files = [f.as_posix() for f in dir_path.iterdir()]
            if len(command_files) > 0:
                for cmd_file in command_files:
                    with open(cmd_file, "rb") as cmd:
                        output.write(cmd.read())
                    os.unlink(cmd_file)

    def get_output(self, check_dir=None):
        output_file = Path("/dev/null")
        # Check for ttyUSBs
        for i in range(9):
            if Path("/dev/ttyUSB%1d" % i).is_char_device():
                output_file = Path("/dev/ttyUSB%1d" % i)
                # If reconnect
                if not self.printer_connected:
                    self.printer_connected = True
                    self.__reset_printer(output_file, check_dir)
                break
        # Redirect output to printcmd files
        if output_file.as_posix() == "/dev/null":
            self.printer_connected = False
            # Make filename
            y, m, d = str(datetime.date.today().year), str(datetime.date.today().month), str(datetime.date.today().day)
            ct = re.findall(r"\d+:\d+:\d+", time.ctime())[0].replace(":", "-")
            filename = "printcmd_" + y + "-" + m + "-" + d + "_" + ct
            # Write in file if directory is specified
            if isinstance(check_dir, Path):
                output_file = check_dir.joinpath(filename)

        return output_file

    @staticmethod
    def wrap(string: str = "", max_char: int = 30):
        lines = string.split("\n")
        for ind, line in enumerate(lines):
            words = line.split(" ")
            char_count = 0

            for i, word in enumerate(words):
                word_len = len(word) + 1
                # For very long words
                if word_len > max_char:
                    word_len = word_len - max_char
                    char_count = 0

                char_count += word_len
                if char_count > max_char and i != 0:
                    words[i - 1] += "\n"
                    char_count = word_len

            lines[ind] = " ".join(words).replace("\n ", "\n")
        return "\n".join(lines)

    @staticmethod
    def __utf_to_escpos(cmd_bytes: bytes):
        for key in utf2pos_map:
            cmd_bytes = cmd_bytes.replace(key, utf2pos_map[key])
        return cmd_bytes

    @staticmethod
    def set_mode(output, font_mode=None, justification=None, font_size=None):
        # 0: Left, 1: Centered, 2:Right
        if justification is not None:
            output.write(b"\x1b\x61" + bytes([justification]))
        # Font mode: https://reference.epson-biz.com/modules/ref_escpos/index.php?content_id=23
        if font_mode is not None:
            output.write(b"\x1b\x21" + bytes([font_mode]))
        # Font size
        if font_size is not None:
            output.write(b"\x1d\x21" + bytes([font_size]))

    @staticmethod
    def text(output, string: str):
        string = re.sub(r'[’]', "'", string)
        string = re.sub(r'[”“]', "'", string)
        output.write(Printer.__utf_to_escpos(Printer.wrap(string).encode("utf-8")))
        output.write(b"\n")

    @staticmethod
    def cut(output):
        Printer.set_mode(output, font_mode=0, justification=0, font_size=12)
        output.write(b"\n\n\n\n\n\n\n\x1b\x69\n")

    @staticmethod
    def image(output, image):
        Printer.set_mode(output, font_mode=0, justification=0, font_size=12)
        """
        Image must be a byte array with first four bytes being :
        
          xLowByte = int((img.width % 256) / 8)
          xHighByte = int(img.width / 2048)
          yLowByte = int(img.height % 256)
          yHighByte = int(img.height / 256)
          
          BEWARE ! One BIT (not byte) <=> one printer dot <=> one black or white pixel
          
          https://www.epson-biz.com/modules/ref_escpos/index.php?content_id=94
          
        """
        if not isinstance(image, bytes):
            raise TypeError("Oops... image must be byte array")
        output.write(b"\n\n")
        output.write(b"\x1d\x76\x30\x00" + image)
        output.write(b"\n\n")
