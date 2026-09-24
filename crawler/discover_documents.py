import json
from pathlib import Path
from urllib.parse import urljoin

import requests


API_URL = "https://senate.gov.ph/hq/impeachment/published"
BASE_URL = "https://senate.gov.ph"


def fetch_impeachment_data():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/153.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://senate.gov.ph/services/impeachment-documents",
    }

    response = requests.get(
        API_URL,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def extract_documents(data):
    documents = []

    for party in data.get("parties", []):
        category = party.get("label")
        category_slug = party.get("slug")

        for section in party.get("sections", []):
            section_id = section.get("id")
            section_title = section.get("title")

            for document in section.get("documents", []):
                relative_url = document.get("url")
                filename = document.get("filename")
                label = document.get("label")

                if not relative_url:
                    continue

                file_url = urljoin(BASE_URL, relative_url)

                extension = Path(filename or relative_url).suffix.lower()

                if extension == ".pdf":
                    file_type = "pdf"
                elif extension in {".mp4", ".mov", ".avi", ".mkv"}:
                    file_type = "video"
                else:
                    file_type = "other"

                documents.append(
                    {
                        "id": document.get("id"),
                        "label": label,
                        "filename": filename,
                        "category": category,
                        "category_slug": category_slug,
                        "section_id": section_id,
                        "section_title": section_title,
                        "file_type": file_type,
                        "source_url": API_URL,
                        "file_url": file_url,
                    }
                )

    return documents


def save_manifest(data, documents):
    output_dir = Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "document_manifest.json"

    manifest = {
        "case_number": data.get("case_number"),
        "title": data.get("title"),
        "source_url": API_URL,
        "document_count": len(documents),
        "pdf_count": sum(
            1 for document in documents
            if document["file_type"] == "pdf"
        ),
        "video_count": sum(
            1 for document in documents
            if document["file_type"] == "video"
        ),
        "documents": documents,
    }

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            manifest,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return output_path


def print_summary(data, documents):
    print("=" * 80)
    print("PHILIPPINE SENATE IMPEACHMENT DOCUMENT DISCOVERY")
    print("=" * 80)

    print(f"Case Number: {data.get('case_number')}")
    print(f"Title:       {data.get('title')}")
    print()

    print(f"Total records: {len(documents)}")

    pdf_count = sum(
        1 for document in documents
        if document["file_type"] == "pdf"
    )

    video_count = sum(
        1 for document in documents
        if document["file_type"] == "video"
    )

    other_count = len(documents) - pdf_count - video_count

    print(f"PDF files:    {pdf_count}")
    print(f"Video files:  {video_count}")
    print(f"Other files:  {other_count}")
    print()

    print("-" * 80)
    print("DOCUMENTS BY CATEGORY")
    print("-" * 80)

    categories = {}

    for document in documents:
        category = document["category"]

        if category not in categories:
            categories[category] = {
                "pdf": 0,
                "video": 0,
                "other": 0,
            }

        categories[category][document["file_type"]] += 1

    for category, counts in categories.items():
        print(
            f"{category}: "
            f"{counts['pdf']} PDF, "
            f"{counts['video']} video, "
            f"{counts['other']} other"
        )

    print()

    print("-" * 80)
    print("SAMPLE DOCUMENTS")
    print("-" * 80)

    for document in documents[:10]:
        print(f"[{document['file_type'].upper()}]")
        print(f"Category: {document['category']}")
        print(f"Section:  {document['section_title']}")
        print(f"Label:    {document['label']}")
        print(f"Filename: {document['filename']}")
        print(f"URL:      {document['file_url']}")
        print()


def main():
    print("Fetching Senate impeachment document data...")
    print()

    data = fetch_impeachment_data()

    documents = extract_documents(data)

    output_path = save_manifest(data, documents)

    print_summary(data, documents)

    print("=" * 80)
    print(f"MANIFEST SAVED: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()