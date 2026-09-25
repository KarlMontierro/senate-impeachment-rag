import hashlib
import json
import os
from pathlib import Path
from datetime import date

import pymupdf
import psycopg
import pytesseract
from dotenv import load_dotenv
from PIL import Image


# ============================================================
# Configuration
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "data" / "document_manifest.json"
DATA_DIR = PROJECT_ROOT / "data" / "documents"

load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in .env")


# ============================================================
# File helpers
# ============================================================

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""

    sha256 = hashlib.sha256()

    with file_path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            sha256.update(chunk)

    return sha256.hexdigest()


def safe_relative_path(file_path: Path) -> str:
    """Return a project-relative path for database storage."""

    return str(file_path.relative_to(PROJECT_ROOT))


# ============================================================
# Text extraction
# ============================================================

def extract_page_text(page) -> str:
    """Extract selectable text from a PDF page."""

    return page.get_text("text").strip()


def text_quality_is_good(text: str) -> bool:
    """
    Determine whether normal PDF extraction produced
    enough usable text.

    Poor or nearly empty pages are sent to OCR.
    """

    cleaned = " ".join(text.split())

    if len(cleaned) < 50:
        return False

    alphanumeric = sum(
        character.isalnum()
        for character in cleaned
    )

    if alphanumeric < 30:
        return False

    return True


def ocr_page(page) -> str:
    """Render a PDF page and run Tesseract OCR."""

    matrix = pymupdf.Matrix(
        200 / 72,
        200 / 72,
    )

    pixmap = page.get_pixmap(
        matrix=matrix,
        colorspace=pymupdf.csRGB,
        alpha=False,
    )

    image = Image.frombytes(
        "RGB",
        [pixmap.width, pixmap.height],
        pixmap.samples,
    )

    text = pytesseract.image_to_string(
        image,
        config="--psm 6",
    )

    return text.strip()


def extract_pages(file_path: Path):
    """
    Extract every page from a PDF.

    Normal text extraction is attempted first.
    OCR is used only for pages with poor extracted text.
    """

    document = pymupdf.open(file_path)

    pages = []
    ocr_count = 0

    try:

        total_pages = len(document)

        for page_number, page in enumerate(
            document,
            start=1,
        ):

            text = extract_page_text(page)

            used_ocr = False

            if not text_quality_is_good(text):

                text = ocr_page(page)

                used_ocr = True
                ocr_count += 1

            pages.append(
                {
                    "page_number": page_number,
                    "text": text,
                    "used_ocr": used_ocr,
                }
            )

            extraction_type = (
                "OCR"
                if used_ocr
                else "TEXT"
            )

            print(
                f"    Page {page_number}/{total_pages} "
                f"| {extraction_type:<4} "
                f"| {len(text):,} characters"
            )

    finally:
        document.close()

    return pages, ocr_count


# ============================================================
# Database
# ============================================================

def upsert_document(
    conn,
    metadata,
    file_path,
    file_hash,
    file_size,
):
    """Insert or update a document record."""

    with conn.cursor() as cur:

        cur.execute(
            """
            INSERT INTO documents (
                title,
                category,
                document_date,
                source_url,
                file_path,
                file_hash,
                file_size,
                status,
                updated_at
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                CURRENT_TIMESTAMP
            )

            ON CONFLICT (source_url)
            DO UPDATE SET
                title = EXCLUDED.title,
                category = EXCLUDED.category,
                document_date = EXCLUDED.document_date,
                file_path = EXCLUDED.file_path,
                file_hash = EXCLUDED.file_hash,
                file_size = EXCLUDED.file_size,
                status = EXCLUDED.status,
                updated_at = CURRENT_TIMESTAMP

            RETURNING id
            """,
            (
                metadata.get("filename"),
                metadata.get("category"),
                None,
                metadata.get("file_url"),
                safe_relative_path(file_path),
                file_hash,
                file_size,
                "processing",
            ),
        )

        return cur.fetchone()[0]


def insert_pages(
    conn,
    document_id,
    pages,
):
    """Insert or update page-level text."""

    with conn.cursor() as cur:

        for page in pages:

            cur.execute(
                """
                INSERT INTO pages (
                    document_id,
                    page_number,
                    text
                )
                VALUES (
                    %s,
                    %s,
                    %s
                )

                ON CONFLICT (
                    document_id,
                    page_number
                )

                DO UPDATE SET
                    text = EXCLUDED.text
                """,
                (
                    document_id,
                    page["page_number"],
                    page["text"],
                ),
            )


def update_document_status(
    conn,
    document_id,
    status,
):
    """Update document processing status."""

    with conn.cursor() as cur:

        cur.execute(
            """
            UPDATE documents
            SET
                status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (
                status,
                document_id,
            ),
        )


# ============================================================
# Process one document
# ============================================================

def process_document(
    conn,
    metadata,
):
    """Process one locally available PDF."""

    filename = metadata["filename"]
    category_slug = metadata["category_slug"]

    file_path = (
        DATA_DIR
        / category_slug
        / filename
    )

    print()
    print("-" * 70)
    print(f"Document: {filename}")
    print(f"Category: {metadata['category']}")
    print(f"Path:     {file_path}")

    if not file_path.exists():

        print("STATUS: MISSING LOCAL FILE")

        return {
            "status": "missing",
            "filename": filename,
        }

    try:

        file_size = file_path.stat().st_size

        print(
            f"Size:     {file_size:,} bytes"
        )

        print("SHA-256:  calculating...")

        file_hash = calculate_sha256(
            file_path
        )

        print(
            f"SHA-256:  {file_hash}"
        )

        print("Extracting pages...")

        pages, ocr_count = extract_pages(
            file_path
        )

        print(
            f"Pages:    {len(pages)}"
        )

        print(
            f"OCR:      {ocr_count} pages"
        )

        document_id = upsert_document(
            conn,
            metadata,
            file_path,
            file_hash,
            file_size,
        )

        insert_pages(
            conn,
            document_id,
            pages,
        )

        update_document_status(
            conn,
            document_id,
            "processed",
        )

        conn.commit()

        print(
            f"STATUS:   PROCESSED "
            f"(database ID {document_id})"
        )

        return {
            "status": "processed",
            "filename": filename,
            "document_id": document_id,
            "pages": len(pages),
            "ocr_pages": ocr_count,
        }

    except Exception as error:

        conn.rollback()

        print(
            f"STATUS:   FAILED"
        )

        print(
            f"ERROR:    {error}"
        )

        return {
            "status": "failed",
            "filename": filename,
            "error": str(error),
        }


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 70)
    print("Senate Impeachment RAG - Day 2 Document Ingestion")
    print("=" * 70)

    # --------------------------------------------------------
    # Load manifest
    # --------------------------------------------------------

    print("\nLoading manifest...")

    with MANIFEST_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:

        manifest = json.load(f)

    documents = [
        document
        for document in manifest["documents"]
        if document.get("file_type") == "pdf"
    ]

    print(
        f"PDF records in manifest: {len(documents)}"
    )

    # --------------------------------------------------------
    # Database connection
    # --------------------------------------------------------

    print("\nConnecting to PostgreSQL...")

    results = []

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        # ----------------------------------------------------
        # Process every PDF
        # ----------------------------------------------------

        for index, metadata in enumerate(
            documents,
            start=1,
        ):

            print()
            print(
                f"[{index}/{len(documents)}]"
            )

            result = process_document(
                conn,
                metadata,
            )

            results.append(result)

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    processed = sum(
        result["status"] == "processed"
        for result in results
    )

    missing = sum(
        result["status"] == "missing"
        for result in results
    )

    failed = sum(
        result["status"] == "failed"
        for result in results
    )

    print()
    print("=" * 70)
    print("DAY 2 INGESTION SUMMARY")
    print("=" * 70)

    print(
        f"Manifest PDFs: {len(documents)}"
    )

    print(
        f"Processed:     {processed}"
    )

    print(
        f"Missing:       {missing}"
    )

    print(
        f"Failed:        {failed}"
    )

    print("=" * 70)

    if missing:

        print()
        print("Missing local PDFs:")

        for result in results:

            if result["status"] == "missing":

                print(
                    f"  - {result['filename']}"
                )

    if failed:

        print()
        print("Failed PDFs:")

        for result in results:

            if result["status"] == "failed":

                print(
                    f"  - {result['filename']}: "
                    f"{result['error']}"
                )


if __name__ == "__main__":
    main()
