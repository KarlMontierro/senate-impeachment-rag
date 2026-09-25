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
    "Referer": (
        "https://senate.gov.ph/services/impeachment-documents"
    ),
}


def build_download_url(file_url):
    """Convert the manifest URL to the /hq/ browser-accessible URL."""

    parsed = urlparse(file_url)
    path = parsed.path

    if path.startswith("/uploads/"):
        path = "/hq" + path

    return f"{BASE_URL}{path}"


def calculate_sha256(file_path):
    """Calculate SHA-256 hash of a file."""

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def is_valid_pdf(file_path):
    """Check whether the file begins with the PDF file signature."""

    try:
        with open(file_path, "rb") as f:
            return f.read(5) == b"%PDF-"
    except OSError:
        return False


def download_file(record):
    """Download one PDF from the manifest."""

    download_url = build_download_url(
        record["file_url"]
    )

    filename = record["filename"]

    category_dir = (
        OUTPUT_DIR / record["category_slug"]
    )

    category_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = category_dir / filename

    print()
    print("=" * 70)
    print(f"ID:       {record['id']}")
    print(f"Label:    {record['label']}")
    print(f"Category: {record['category']}")
    print(f"Filename: {filename}")
    print(f"URL:      {download_url}")
    print("=" * 70)

    if output_path.exists():

        if is_valid_pdf(output_path):

            file_size = output_path.stat().st_size
            sha256 = calculate_sha256(output_path)

            print(
                f"Already downloaded. "
                f"Skipping ({file_size:,} bytes)."
            )

            return {
                "status": "already_exists",
                "file_path": str(output_path),
                "file_size": file_size,
                "sha256": sha256,
            }

        print("Existing file is invalid. Removing it.")

        output_path.unlink()

    print("Downloading...")

    response = requests.get(
        download_url,
        headers=HEADERS,
        stream=True,
        timeout=120,
    )

    status_code = response.status_code
    content_type = response.headers.get(
        "content-type",
        "",
    )

    print(f"HTTP Status: {status_code}")
    print(f"Content-Type: {content_type}")

    response.raise_for_status()

    if "application/pdf" not in content_type.lower():

        raise RuntimeError(
            f"Expected a PDF but received: {content_type}"
        )

    temporary_path = output_path.with_suffix(
        output_path.suffix + ".part"
    )

    total_size = 0

    try:

        with open(temporary_path, "wb") as f:

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):

                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)

        if not is_valid_pdf(temporary_path):
            raise RuntimeError(
                "Downloaded file is not a valid PDF."
            )

        temporary_path.replace(output_path)

    except Exception:

        if temporary_path.exists():
            temporary_path.unlink()

        raise

    sha256 = calculate_sha256(output_path)

    print(f"Downloaded: {total_size:,} bytes")
    print(f"SHA-256:    {sha256}")
    print(f"Saved to:   {output_path}")

    return {
        "status": "downloaded",
        "file_path": str(output_path),
        "file_size": total_size,
        "sha256": sha256,
    }


def main():

    print("=" * 70)
    print("Senate Impeachment RAG - PDF Downloader")
    print("=" * 70)

    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Manifest not found: {MANIFEST_PATH}"
        )

    with open(
        MANIFEST_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        manifest = json.load(f)

    pdf_records = [
        record
        for record in manifest["documents"]
        if record.get("file_type") == "pdf"
    ]

    print(
        f"PDFs in manifest: {len(pdf_records)}"
    )

    print(
        f"Output directory: {OUTPUT_DIR}"
    )

    results = []

    for index, record in enumerate(
        pdf_records,
        start=1,
    ):

        print()
        print(
            f"[{index}/{len(pdf_records)}]"
        )

        try:

            result = download_file(record)

            result["filename"] = record["filename"]

            results.append(result)

        except Exception as error:

            print(
                f"DOWNLOAD FAILED: {error}"
            )

            results.append(
                {
                    "status": "failed",
                    "filename": record["filename"],
                    "error": str(error),
                }
            )

    downloaded = sum(
        result["status"] == "downloaded"
        for result in results
    )

    already_exists = sum(
        result["status"] == "already_exists"
        for result in results
    )

    failed = sum(
        result["status"] == "failed"
        for result in results
    )

    print()
    print("=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)

    print(f"Manifest PDFs:   {len(pdf_records)}")
    print(f"Downloaded:      {downloaded}")
    print(f"Already existed: {already_exists}")
    print(f"Failed:          {failed}")

    print("=" * 70)

    if failed:

        print()
        print("Failed downloads:")

        for result in results:

            if result["status"] == "failed":

                print(
                    f"  - {result['filename']}"
                )

                print(
                    f"    {result['error']}"
                )


if __name__ == "__main__":
    main()