import pandas as pd
from pathlib import Path
from PIL import Image
from typing import Protocol

from .gray_scale import AsciiImage


class GrayScaleVal(Protocol):
    def __call__(self, value: int | float, black_to_white: bool = True, more_levels: bool = True) -> str: 
        ...


def load_image_into_gscale(image_file: str) -> Image.Image:
    image: Image.Image = Image.open(image_file).convert('L')
    return image


class AsciiImageConverter:
    def __init__(self, image: AsciiImage, gray_scale_value: GrayScaleVal):
        self.image = image
        self.gray_scale_value = gray_scale_value

    def convert_to_array(self) -> list[list[int]]:
        width, height = self.image.image.size[0], self.image.image.size[1]
        w, h = width / self.image.columns, width / self.image.scale
        rows: int = int(height / h)

        if self.image.columns > width or rows > height:
            print("Image too small for specified cols!")
            exit(0)

        luminance = []
        for r in range(rows):
            y1: int = int(r * h)
            y2: int = height if r == rows - 1 else int((r + 1) * h)  # correct last tile

            luminance_row: list[int] = []
            for c in range(self.image.columns):
                x1: int = int(c * w)
                x2: int = width if c == self.image.columns - 1 else int((c + 1) * w)  # correct last tile
                avg = int(self.image.get_average_gscale_value(x1, y1, x2, y2))  # get average luminance
                luminance_row.append(avg)

            luminance.append(luminance_row)

        return luminance

    def to_dataframe(self) -> pd.DataFrame:
        img_array: list[list[int]] = self.convert_to_array()
        columns = list(range(len(img_array[0])))
        return pd.DataFrame.from_records(img_array, columns=columns)

    def convert_image_to_ascii(self) -> list[str]:
        img_array: list[list[int]] = self.convert_to_array()
        ascii_img: list[str] = []
        for row in img_array:
            line_chars: list[str] = []
            for col_luminance_val in row:
                gsval: str = self.gray_scale_value(
                    col_luminance_val,
                    black_to_white=self.image.black_to_white,
                    more_levels=self.image.more_levels
                )
                line_chars.append(gsval)
            ascii_img.append("".join(line_chars))

        return ascii_img

    def save_to_file(self, ascii_img: list[str], out_file: str) -> None:
        Path(out_file).parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, mode='w', encoding='utf-8') as f:
            for row in ascii_img:
                f.write(f'{row}\n')
