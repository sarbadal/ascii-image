import argparse
import os
import subprocess
from pathlib import Path
from typing import Iterable

from google.cloud import storage


def run_cmd(command: list[str], dry_run: bool = False) -> int:
    print("Running:", " ".join(command))
    if dry_run:
        return 0
    result = subprocess.run(command, check=False)
    return result.returncode


def create_bucket_if_missing(bucket_name: str, project: str | None = None, location: str = "US") -> storage.Bucket:
    client = storage.Client(project=project) if project else storage.Client()
    bucket = client.bucket(bucket_name)
    if not bucket.exists():
        bucket = client.create_bucket(bucket, location=location)
        print(f"Created bucket: {bucket_name}")
    else:
        print(f"Bucket already exists: {bucket_name}")
    return bucket


def ensure_public_object_access(bucket_name: str, dry_run: bool = False) -> None:
    """Grant public read access to bucket objects for static hosting."""
    run_cmd(
        [
            "gcloud",
            "storage",
            "buckets",
            "add-iam-policy-binding",
            f"gs://{bucket_name}",
            "--member=allUsers",
            "--role=roles/storage.objectViewer",
        ],
        dry_run=dry_run,
    )


def upload_files(bucket: storage.Bucket, source_dir: Path, destination_prefix: str = "") -> None:
    for path in source_dir.rglob("*"):
        if path.is_file():
            relative_path = path.relative_to(source_dir).as_posix()
            blob_name = f"{destination_prefix.rstrip('/')}/{relative_path}" if destination_prefix else relative_path
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(str(path))
            blob.make_public()
            print(f"Uploaded {relative_path} -> {blob_name}")


def deploy_static(bucket_name: str, project: str, static_dir: Path, dry_run: bool = False) -> str:
    bucket = create_bucket_if_missing(bucket_name, project=project)
    ensure_public_object_access(bucket_name, dry_run=dry_run)
    upload_files(bucket, static_dir, destination_prefix="static")
    base_url = f"https://storage.googleapis.com/{bucket.name}/static"
    print(f"Static files deployed to: {base_url}")
    return base_url


def deploy_cloud_function(
    function_name: str,
    project: str,
    region: str,
    runtime: str,
    source_dir: Path,
    entry_point: str = "entry_point",
    allow_unauthenticated: bool = True,
    dry_run: bool = False,
) -> None:
    command = [
        "gcloud",
        "functions",
        "deploy",
        function_name,
        "--runtime",
        runtime,
        "--trigger-http",
        "--entry-point",
        entry_point,
        "--source",
        str(source_dir),
        "--region",
        region,
        "--project",
        project,
    ]
    if allow_unauthenticated:
        command.append("--allow-unauthenticated")

    run_cmd(command, dry_run=dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy static assets and a Flask app to Google Cloud.")
    parser.add_argument("--bucket", help="GCS bucket name for static assets")
    parser.add_argument("--project", help="GCP project ID")
    parser.add_argument("--location", default="US", help="GCS bucket location")
    parser.add_argument("--static-dir", default=str(Path(__file__).resolve().parents[0] / "webapp" / "static"), help="Local static directory to upload")
    parser.add_argument("--function-name", default="ascii-image-function", help="Cloud Function name")
    parser.add_argument("--region", default="us-central1", help="Cloud Function deploy region")
    parser.add_argument("--runtime", default="python311", help="Cloud Function runtime")
    parser.add_argument("--entry-point", default="entry_point", help="Cloud Function entry point function name")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without making changes")
    args = parser.parse_args()

    bucket_name = args.bucket or os.environ.get("GCS_STATIC_BUCKET")
    if not bucket_name:
        raise EnvironmentError("GCS_STATIC_BUCKET must be set or --bucket provided.")

    project = args.project or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise EnvironmentError("GOOGLE_CLOUD_PROJECT must be set or --project provided.")

    static_dir = Path(args.static_dir)
    if not static_dir.exists():
        raise FileNotFoundError(f"Static directory not found: {static_dir}")

    base_url = deploy_static(bucket_name, project, static_dir, dry_run=args.dry_run)
    print("Copy this URL into STATIC_BASE_URL in your Cloud Function environment.")
    print(base_url)

    source_dir = Path(__file__).resolve().parents[0]
    deploy_cloud_function(
        function_name=args.function_name,
        project=project,
        region=args.region,
        runtime=args.runtime,
        source_dir=source_dir,
        entry_point=args.entry_point,
        allow_unauthenticated=True,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
