import numpy as np
from PIL import Image, ImageOps, ImageEnhance
import base64
import io
from functools import partial

class ThermalPrinterImage:
    def __init__(self, file):
        # self.file = open(file, "rb")
        self.image = Image.open(file)

        self.__choose_rotate()
        self.__resize()
        self.__black_white()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.image.close()
        # self.file.close()
        return True

    def get_byte_image(self):
        byte = 0
        dot_image = []
        # True is dot for printer
        # print(list(self.image.getdata()))
        for i, bit in enumerate(list(self.image.getdata())):
            byte <<= 1
            if bit == 0:
                byte |= 1
            if i % 8 == 7:
                dot_image.append(byte)
                byte = 0

        
        xl = int((self.image.width // 8) % 256)
        xh = int(self.image.width // 2048)
        yl = int(self.image.height % 256)
        yh = int(self.image.height // 256)


        # print((xh * 256 * 8 + xl)*(yh * 256 + yl))
        # Conform to [GS, v, 0, xl, xh, yl, yh, d0, d1 ... dk] command in ESC/POS
        return bytes([xl, xh, yl, yh]) + bytes(dot_image[:(xh * 256 * 8 + xl)*(yh * 256 + yl)])#.replace(b'\x1b\x53', b'\x00\x53')

    def __choose_rotate(self):
        if self.image.width > self.image.height:
            self.image = self.image.rotate(angle=90, expand=1)

    def __resize(self):
        if self.image.width != 392:
            ratio = 392 / self.image.width
            self.image = self.image.resize((392, int(self.image.height * ratio)))

    @staticmethod
    def __operate_on_image(v, mean_val):
        plus = 255 - v
        # print(f'pls: {plus}     mean: {mean_val}  v: {v}')
        mean_val = min(180, mean_val)
        # print(f'pls: {plus}     mean: {mean_val}  v: {v}')
        brighten = 180/mean_val
        # print(f'pls: {plus}     mean: {mean_val}  bright: {brighten} v: {v}')
        v = (pow(1-v/255, 10) * plus * 0.1 + v)*brighten
        # print(f'pls: {plus}     mean: {mean_val}  bright: {brighten} v: {v}')
        return max(0, min(255, int(v)))

    def __black_white(self):
        self.image = self.image.convert(mode="L")
        sharpness = ImageEnhance.Sharpness(self.image)
        self.image = sharpness.enhance(10)
        self.image = ImageOps.autocontrast(self.image, (0,5))
        operate = partial(ThermalPrinterImage.__operate_on_image, mean_val=np.average(np.array(self.image)))
        self.image = self.image.point(operate)
        self.image = self.image.convert(mode="1")


    @staticmethod
    def from_html_base64(html_base64):
        html_base64 = html_base64[html_base64.find("base64") + len("base64,"):]
        return ThermalPrinterImage.from_base64(html_base64)

    @staticmethod
    def from_base64(base_64):
        base_64 = base64.b64decode(base_64)
        buf = io.BytesIO(base_64)
        return ThermalPrinterImage(buf)
    
if __name__ == "__main__":
    with ThermalPrinterImage("./replace_me.jpeg") as img:
        img.image.save("./replaced.jpeg")
        # with open("replace.jpg", "wb") as n_img:
        #     n_img.write()
        