import os
import secrets
import sys
from io import BytesIO
from pathlib import Path
from typing import Any

from flask import Flask, Response, render_template, request, url_for
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ascii_image.ascii_img_generator import AsciiImageConverter
from ascii_image.gray_scale import AsciiImage

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}
IMAGE_STORE: dict[str, bytes] = {}

app = Flask(__name__, static_folder="static", template_folder="templates")
STATIC_BASE_URL = os.getenv("STATIC_BASE_URL", "").rstrip("/")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def build_ascii_text(image: Image.Image, columns: int, scale: int, black_to_white: bool, more_levels: bool = True) -> str:
    if columns < 1:
        raise ValueError("Columns must be a positive number.")
    if scale < 1:
        raise ValueError("Scale must be a positive number.")

    image = image.convert("L")
    width, height = image.size

    if columns > width:
        raise ValueError("Columns value is too large for the selected image.")

    row_height = width / scale
    if row_height <= 0:
        raise ValueError("Scale must be greater than zero.")

    rows = int(height / row_height)
    if rows < 1 or rows > height:
        raise ValueError("Scale value is too large for the selected image height.")

    ascii_image = AsciiImage(
        image=image,
        columns=columns,
        scale=scale,
        more_levels=more_levels,
        black_to_white=black_to_white,
    )

    converter = AsciiImageConverter(
        image=ascii_image,
        gray_scale_value=ascii_image.convert_to_ascii,
    )
    lines = converter.convert_image_to_ascii()
    return "\n".join(lines)


@app.route("/", methods=["GET", "POST"])
def index() -> Any:
    ascii_text = None
    error = None
    columns = 90
    scale = 35
    black_to_white = True
    more_levels = True
    image_token = ""
    image_name = ""

    if request.method == "POST":
        image_file = request.files.get("imagefile")
        image_token = request.form.get("image_token", "")
        image_name = request.form.get("image_name", "uploaded_image")

        try:
            columns = int(request.form.get("columns", columns))
            scale = int(request.form.get("scale", scale))
        except ValueError:
            error = "Columns and scale must be whole numbers."

        black_to_white = request.form.get("blacktowhite") == "on"
        more_levels = request.form.get("morelevels") == "on"

        if image_file and image_file.filename:
            if not allowed_file(image_file.filename):
                error = "Supported image types are PNG, JPG, GIF, BMP, and WEBP."
            else:
                try:
                    image_bytes = image_file.stream.read()
                    image = Image.open(BytesIO(image_bytes))
                    ascii_text = build_ascii_text(
                        image=image,
                        columns=columns,
                        scale=scale,
                        black_to_white=black_to_white,
                        more_levels=more_levels,
                    )
                    image_token = secrets.token_urlsafe(16)
                    IMAGE_STORE[image_token] = image_bytes
                    image_name = image_file.filename
                except Exception as exc:
                    error = str(exc)
        elif image_token and image_token in IMAGE_STORE:
            try:
                image_bytes = IMAGE_STORE[image_token]
                image = Image.open(BytesIO(image_bytes))
                ascii_text = build_ascii_text(
                    image=image,
                    columns=columns,
                    scale=scale,
                    black_to_white=black_to_white,
                    more_levels=more_levels,
                )
            except Exception as exc:
                error = str(exc)
        else:
            error = "Please upload an image file."

    return render_template(
        "index.html",
        ascii_text=ascii_text,
        error=error,
        columns=columns,
        scale=scale,
        black_to_white=black_to_white,
        more_levels=more_levels,
        image_token=image_token,
        image_name=image_name,
    )


@app.context_processor
def utility_processor() -> dict[str, Any]:
    def static_url(filename: str) -> str:
        if STATIC_BASE_URL:
            return f"{STATIC_BASE_URL}/{filename}"
        return url_for("static", filename=filename)

    return {"static_url": static_url}


@app.route("/preview/<token>")
def preview(token: str) -> Response:
    image_bytes = IMAGE_STORE.get(token)
    if not image_bytes:
        return Response("Image not found", status=404, mimetype="text/plain")

    try:
        image = Image.open(BytesIO(image_bytes))
        mimetype = Image.MIME.get(image.format, "image/png")
    except Exception:
        mimetype = "image/png"

    return Response(image_bytes, mimetype=mimetype)


@app.route("/download", methods=["POST"])
def download() -> Response:
    ascii_text = request.form.get("ascii_text", "")
    if not ascii_text:
        return Response("No ASCII art available to download.", status=400, mimetype="text/plain")

    return Response(
        ascii_text,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=ascii-image.txt"},
    )


# functions-framework --target=entry_point --debug
def func_entry_point(request):
    """Entry point for Google Cloud Function"""
    return app


if __name__ == "__main__":
    app.run(debug=True, port=5000)
