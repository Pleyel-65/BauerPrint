from PIL import Image
import base64
import io


class ThermalPrinterImage:
    def __init__(self, file):
        self.image = Image.open(file)

        self.__choose_rotate()
        self.__resize()
        self.__black_white()

    def get_byte_image(self):
        byte = 0
        dot_image = []
        # True is dot for printer
        for i, bit in enumerate(list(self.image.getdata())):
            byte <<= 1
            if bit == 0:
                byte |= 1
            if i % 8 == 7:
                dot_image.append(byte)
                byte = 0

        xl = int((self.image.width / 8) % 256)
        xh = int(self.image.width / 2048)
        yl = int(self.image.height % 256)
        yh = int(self.image.height / 256)

        # Conform to [GS, v, 0, xl, xh, yl, yh, d0, d1 ... dk] command in ESC/POS
        return bytes([xl, xh, yl, yh]) + bytes(dot_image)

    def __choose_rotate(self):
        if self.image.width > self.image.height:
            self.image = self.image.rotate(angle=90, expand=1)

    def __resize(self):
        if self.image.width != 392:
            ratio = 392 / self.image.width
            self.image = self.image.resize((392, int(self.image.height * ratio)))

    def __black_white(self):
        self.image = self.image.convert(mode="1")

    @staticmethod
    def from_html_base64(html_base64):
        html_base64 = html_base64[html_base64.find("base64") + len("base64,"):]
        html_base64 = base64.b64decode(html_base64)
        buf = io.BytesIO(html_base64)
        return ThermalPrinterImage(buf)
