import hashlib
import os
from pathlib import Path

import pymupdf
import psycopg
import pytesseract
from dotenv import load_dotenv
from PIL import Image


# ============================================================
# Configuration
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "documents"

load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in .env")


# ============================================================
# Failed documents
# ============================================================

FAILED_DOCUMENTS = [
    {
        "filename": "06. ANNEXES KKKKKKKK to DDDDDDDDD_edited.pdf",
        "category": "Prosecution",
        "category_slug": "prosecution",
    },
    {
        "filename": "Annex 1 - Petition for Certiorari and Prohibition dtd March 30, 2026.pdf",
        "category": "Defense",
        "category_slug": "defense",
    },
]


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


def sanitize_text(text: str) -> str:
    """
    Remove NUL bytes that PostgreSQL TEXT fields cannot store.
    """

    if not text:
        return ""

    return text.replace("\x00", "")


# ============================================================
# Text extraction
# ============================================================

def text_quality_is_good(text: str) -> bool:
    """
    Determine whether normal PDF extraction produced
    enough usable text.
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


def extract_page_text(page) -> str:
    """Extract selectable text from a PDF page."""

    text = page.get_text("text")

    return sanitize_text(text.strip())


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

    return sanitize_text(text.strip())


def extract_pages(file_path: Path):
    """
    Extract every page from a PDF.

    Normal text extraction is attempted first.
    OCR is used only when extracted text is poor.
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

            text = sanitize_text(text)

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

def find_document(
    conn,
    filename,
):
    """
    Find an existing document using its title.

    The two failed documents may already have records
    in the documents table from the previous ingestion run.
    """

    with conn.cursor() as cur:

        cur.execute(
            """
            SELECT
                id,
                source_url,
                status
            FROM documents
            WHERE title = %s
            ORDER BY id
            LIMIT 1
            """,
            (filename,),
        )

        return cur.fetchone()


def upsert_document(
    conn,
    metadata,
    file_path,
    file_hash,
    file_size,
):
    """Insert or update the document record."""

    existing = find_document(
        conn,
        metadata["filename"],
    )

    with conn.cursor() as cur:

        if existing:

            document_id = existing[0]

            cur.execute(
                """
                UPDATE documents
                SET
                    category = %s,
                    file_path = %s,
                    file_hash = %s,
                    file_size = %s,
                    status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    metadata["category"],
                    safe_relative_path(file_path),
                    file_hash,
                    file_size,
                    "processing",
                    document_id,
                ),
            )

            return document_id

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
            RETURNING id
            """,
            (
                metadata["filename"],
                metadata["category"],
                None,
                f"retry://{metadata['filename']}",
                safe_relative_path(file_path),
                file_hash,
                file_size,
                "processing",
            ),
        )

        return cur.fetchone()[0]


def delete_existing_pages(
    conn,
    document_id,
):
    """
    Remove any partially inserted pages from the previous
    failed ingestion attempt.

    This ensures the retry starts with a clean page set.
    """

    with conn.cursor() as cur:

        cur.execute(
            """
            DELETE FROM pages
            WHERE document_id = %s
            """,
            (document_id,),
        )


def insert_pages(
    conn,
    document_id,
    pages,
):
    """Insert page-level text."""

    with conn.cursor() as cur:

        for page in pages:

            clean_text = sanitize_text(
                page["text"]
            )

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
                """,
                (
                    document_id,
                    page["page_number"],
                    clean_text,
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
# Process one failed document
# ============================================================

def process_document(
    conn,
    metadata,
):
    """Retry processing one failed PDF."""

    filename = metadata["filename"]
    category_slug = metadata["category_slug"]

    file_path = (
        DATA_DIR
        / category_slug
        / filename
    )

    print()
    print("=" * 70)
    print(f"Document: {filename}")
    print(f"Category: {metadata['category']}")
    print(f"Path:     {file_path}")
    print("=" * 70)

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

        print(
            f"Database ID: {document_id}"
        )

        print("Removing any previous partial pages...")

        delete_existing_pages(
            conn,
            document_id,
        )

        print("Inserting page text...")

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

        print()
        print("STATUS: PROCESSED")

        return {
            "status": "processed",
            "filename": filename,
            "document_id": document_id,
            "pages": len(pages),
            "ocr_pages": ocr_count,
        }

    except Exception as error:

        conn.rollback()

        print()
        print("STATUS: FAILED")
        print(
            f"ERROR: {error}"
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
    print("Senate Impeachment RAG - Retry Failed Documents")
    print("=" * 70)

    print()
    print("Documents to retry:")
    
    for document in FAILED_DOCUMENTS:
        print(
            f"  - {document['filename']}"
        )

    print()
    print(
        f"Total documents to retry: "
        f"{len(FAILED_DOCUMENTS)}"
    )

    print()
    print("Connecting to PostgreSQL...")

    results = []

    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        for index, metadata in enumerate(
            FAILED_DOCUMENTS,
            start=1,
        ):

            print()
            print(
                f"[{index}/{len(FAILED_DOCUMENTS)}]"
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
    print("RETRY SUMMARY")
    print("=" * 70)

    print(
        f"Documents retried: {len(FAILED_DOCUMENTS)}"
    )

    print(
        f"Processed:         {processed}"
    )

    print(
        f"Missing:           {missing}"
    )

    print(
        f"Failed:            {failed}"
    )

    print("=" * 70)

    if failed:

        print()
        print("Still failed:")

        for result in results:

            if result["status"] == "failed":

                print(
                    f"  - {result['filename']}: "
                    f"{result['error']}"
                )


if __name__ == "__main__":
    main()