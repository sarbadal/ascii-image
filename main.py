from PIL import Image
from webapp.app import app

from ascii_image.gray_scale import AsciiImage
from ascii_image.ascii_img_generator import AsciiImageConverter, load_image_into_gscale
from ascii_image.to_csv import DataFrameLoader

def main() -> None:
    out_file: str = "images/exports/saturn2.jpg.txt"
    image: Image.Image = load_image_into_gscale(image_file="images/imports/saturn.jpg")
    ascii_img_info = AsciiImage(
        image=image,
        columns=80,
        scale=35,
        more_levels=True,
        black_to_white=True
    )

    converter = AsciiImageConverter(
        image=ascii_img_info, 
        gray_scale_value=ascii_img_info.convert_to_ascii
    )
    ascii_img: list[str] = converter.convert_image_to_ascii()
    converter.save_to_file(ascii_img, out_file)

    df_loader = DataFrameLoader(file=out_file)
    df = df_loader.to_dataframe()
    print(df.head(n=30))


if __name__ == "__main__":
    # ascii-image -MF images/imports/saturn.jpg -C 80 -S 35 -OF images/exports/saturn.jpg.txt -BW y
    main()