import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

import requests


BASE_URL = "https://senate.gov.ph"

MANIFEST_PATH = Path("data/document_manifest.json")
OUTPUT_DIR = Path("data/documents")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    ),
    "Referer": "https://senate.gov.ph/services/impeachment-documents",
}


def build_download_url(file_url):
    """
    Convert the API URL:

        /uploads/...

    into the browser-accessible URL:

        /hq/uploads/...
    """

    parsed = urlparse(file_url)

    path = parsed.path

    if path.startswith("/uploads/"):
        path = "/hq" + path

    return f"{BASE_URL}{path}"


def calculate_sha256(file_path):
    """Calculate SHA-256 hash of a downloaded file."""

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def download_file(record):
    """Download one PDF from the manifest."""

    original_url = record["file_url"]
    download_url = build_download_url(original_url)

    document_id = record["id"]
    label = record["label"]
    filename = record["filename"]
    category = record["category"]
    section_title = record["section_title"]

    category_dir = OUTPUT_DIR / record["category_slug"]
    category_dir.mkdir(parents=True, exist_ok=True)

    output_path = category_dir / filename

    print()
    print("=" * 70)
    print(f"ID:       {document_id}")
    print(f"Label:    {label}")
    print(f"Category: {category}")
    print(f"Section:  {section_title}")
    print(f"Filename: {filename}")
    print(f"URL:      {download_url}")
    print("=" * 70)

    if output_path.exists():
        print("Already downloaded. Skipping.")

        sha256 = calculate_sha256(output_path)

        return {
            "status": "already_exists",
            "file_path": str(output_path),
            "file_size": output_path.stat().st_size,
            "sha256": sha256,
            "download_url": download_url,
        }

    print("Downloading...")

    response = requests.get(
        download_url,
        headers=HEADERS,
        stream=True,
        timeout=120,
    )

    print(f"HTTP Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")

    response.raise_for_status()

    content_type = response.headers.get("content-type", "")

    if "application/pdf" not in content_type.lower():
        raise RuntimeError(
            f"Expected a PDF but received: {content_type}"
        )

    total_size = 0

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):

            if chunk:
                f.write(chunk)
                total_size += len(chunk)

    sha256 = calculate_sha256(output_path)

    print(f"Downloaded: {total_size:,} bytes")
    print(f"SHA-256:    {sha256}")
    print(f"Saved to:   {output_path}")

    return {
        "status": "downloaded",
        "file_path": str(output_path),
        "file_size": total_size,
        "sha256": sha256,
        "download_url": download_url,
    }


def main():

    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Manifest not found: {MANIFEST_PATH}"
        )

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    pdf_records = [
        record
        for record in manifest["documents"]
        if record["file_type"] == "pdf"
    ]

    print(f"PDFs in manifest: {len(pdf_records)}")
    print(f"Output directory: {OUTPUT_DIR}")

    # Test only the first PDF for now.
    record = pdf_records[0]

    result = download_file(record)

    print()
    print("Result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()