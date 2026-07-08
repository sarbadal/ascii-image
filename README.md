<p align="center"> <img src="src/logo/ascii-image-logo-transparent.png" alt="ascii-image logo" width="200" /> 
</p>

# ascii-image

Convert images into clean ASCII art from the command line.

ascii-image is a Python package and CLI that transforms JPG, PNG, and other common image formats into grayscale ASCII text.  
It can export both:
- ASCII art as `.txt`
- Luminance grid data as `.csv`

Built with Pillow and pandas, it is useful for terminal art, creative coding, and image-data experiments.

## Features

- Convert any supported image (JPG, PNG, etc.) to grayscale ASCII text.
- Export ASCII output to a text file.
- Export tile luminance values to CSV for analysis.
- Control width (`cols`) and output density (`scale`) from the CLI.

## Install

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

After install, the CLI command is available as `ascii-image`.

## CLI Usage

```bash
ascii-image -MF <input_image_path> -C <columns> -S <scale> -OF <output_txt_path> [-BW <true|false>]
```

### CLI Arguments

- `-MF`, `--imagefile` (required): Path to input image.
- `-C`, `--cols` (required): Number of columns in ASCII output.
- `-S`, `--scale` (required): Scale value used to calculate row height.
- `-OF`, `--outfile` (required): Path to output text file.
- `-BW`, `--blacktowhite` (optional): Invert grayscale mapping.
  Accepted truthy values include `true`, `1`, `yes`, `y`.

## Examples

### 1. Basic conversion

```bash
ascii-image \
  -MF images/imports/saturn.jpg \
  -C 80 \
  -S 35 \
  -OF images/exports/saturn.jpg.txt
```

### 2. Inverted grayscale mapping

```bash
ascii-image \
  -MF images/imports/saturn.jpg \
  -C 80 \
  -S 35 \
  -OF images/exports/saturn_invert.jpg.txt \
  -BW y
```

## Output Files

For `-OF images/exports/saturn.jpg.txt`, the CLI generates:

- `images/exports/saturn.jpg.txt` (ASCII text art)
- `images/exports/saturn.jpg.txt.csv` (numeric luminance matrix)

## Programmatic Usage

```python
from ascii_image.gray_scale import AsciiImage
from ascii_image.ascii_img_generator import AsciiImageConverter, load_image_into_gscale

image = load_image_into_gscale("images/imports/saturn.jpg")
ascii_img_info = AsciiImage(
    image=image,
    columns=80,
    scale=35,
    more_levels=True,
    black_to_white=True,
)

converter = AsciiImageConverter(
    image=ascii_img_info,
    gray_scale_value=ascii_img_info.convert_to_ascii,
)

ascii_lines = converter.convert_image_to_ascii()
converter.save_to_file(ascii_lines, "images/exports/saturn_programmatic.txt")
converter.to_dataframe().to_csv("images/exports/saturn_programmatic.txt.csv", index=False, header=False)
```
## Flask Web App

A lightweight Flask frontend is included under `webapp/`.

Run it locally with:

```bash
python webapp/app.py
```

Then open `http://127.0.0.1:5000` to upload an image and generate ASCII art in your browser.

## Deployment

A deploy helper is included in `deployment.py` for Google Cloud deployment.

You can pass bucket and project values directly on the command line, or use environment variables.

```bash
python deployment.py \
  --bucket my-bucket \
  --project my-gcp-project \
  --location US \
  --dry-run
```

Or with environment variables:

```bash
export GOOGLE_CLOUD_PROJECT=your-gcp-project
export GCS_STATIC_BUCKET=your-static-bucket-name
python deployment.py --dry-run
```

Available CLI options:

- `--bucket` — GCS bucket name for static assets
- `--project` — GCP project ID
- `--location` — bucket location (default: `US`)
- `--static-dir` — local directory containing static files (default: `webapp/static`)
- `--function-name` — Cloud Function name (default: `ascii-image-function`)
- `--region` — Cloud Function deploy region (default: `us-central1`)
- `--runtime` — Cloud Function runtime (default: `python311`)
- `--entry-point` — Cloud Function entry point function name (default: `entry_point`)
- `--dry-run` — print commands without making changes

This script will:

- create the bucket if it does not exist
- grant public object read access for static hosting
- upload `webapp/static/` to the bucket
- deploy the Flask app to Google Cloud Functions
- print the public static base URL for `STATIC_BASE_URL`

Cloud Function details:

- default function name: `ascii-image-function`
- entrypoint function: `entry_point` (exposed from `main.py`)
- deploy region default: `us-central1`
- runtime default: `python311`

In production, set `STATIC_BASE_URL` to the URL printed by `deployment.py`.

## Notes

- If `cols` is too large for the input image, conversion will stop with: `Image too small for specified cols!`.
- The CLI creates parent directories for output paths automatically.