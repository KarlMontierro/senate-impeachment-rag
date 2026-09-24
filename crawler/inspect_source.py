import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


SOURCE_URL = "https://senate.gov.ph/services/impeachment-documents"


def inspect_source():
    print("=" * 80)
    print("PHILIPPINE SENATE IMPEACHMENT DOCUMENTS")
    print("=" * 80)
    print(f"URL: {SOURCE_URL}")
    print()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/153.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(
        SOURCE_URL,
        headers=headers,
        timeout=30,
    )

    print(f"HTTP Status: {response.status_code}")
    print(f"Content Type: {response.headers.get('content-type')}")
    print(f"Content Length: {len(response.content):,} bytes")
    print()

    if response.status_code != 200:
        print()
        print("=" * 80)
        print("SERVER RESPONSE")
        print("=" * 80)
        print(response.text)
        return

    soup = BeautifulSoup(response.text, "lxml")

    print(f"Page title: {soup.title.get_text(strip=True) if soup.title else 'N/A'}")
    print()

    # ---------------------------------------------------------
    # Links
    # ---------------------------------------------------------

    links = soup.find_all("a")

    print(f"Total links found: {len(links)}")
    print()

    print("-" * 80)
    print("ALL LINKS")
    print("-" * 80)

    for index, link in enumerate(links, start=1):
        text = link.get_text(" ", strip=True)
        href = link.get("href")

        if not href:
            continue

        absolute_url = urljoin(SOURCE_URL, href)

        print(f"[{index}]")
        print(f"Text: {text}")
        print(f"URL:  {absolute_url}")
        print()

    # ---------------------------------------------------------
    # PDF links
    # ---------------------------------------------------------

    pdf_links = []

    for link in links:
        href = link.get("href")

        if not href:
            continue

        absolute_url = urljoin(SOURCE_URL, href)

        if ".pdf" in absolute_url.lower():
            pdf_links.append(
                {
                    "text": link.get_text(" ", strip=True),
                    "url": absolute_url,
                }
            )

    print("=" * 80)
    print(f"PDF LINKS FOUND: {len(pdf_links)}")
    print("=" * 80)

    for index, pdf in enumerate(pdf_links, start=1):
        print(f"[{index}] {pdf['text']}")
        print(f"     {pdf['url']}")
        print()

    # ---------------------------------------------------------
    # Possible pagination
    # ---------------------------------------------------------

    print("=" * 80)
    print("POSSIBLE PAGINATION")
    print("=" * 80)

    pagination_keywords = [
        "next",
        "previous",
        "prev",
        "page",
        "older",
        "newer",
    ]

    for link in links:
        text = link.get_text(" ", strip=True).lower()
        href = link.get("href")

        if not href:
            continue

        if any(keyword in text for keyword in pagination_keywords):
            print(
                f"Text: {link.get_text(' ', strip=True)} | "
                f"URL: {urljoin(SOURCE_URL, href)}"
            )

    print()

    # ---------------------------------------------------------
    # Page headings
    # ---------------------------------------------------------

    print("=" * 80)
    print("HEADINGS")
    print("=" * 80)

    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text = heading.get_text(" ", strip=True)

        if text:
            print(f"{heading.name}: {text}")


if __name__ == "__main__":
    inspect_source()