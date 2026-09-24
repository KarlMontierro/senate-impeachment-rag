import requests

API_URL = "https://senate.gov.ph/hq/impeachment/published"


def test_api():
    print("=" * 80)
    print("SENATE IMPEACHMENT PUBLISHED API TEST")
    print("=" * 80)
    print(f"URL: {API_URL}")
    print()

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

    print(f"HTTP Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Content Length: {len(response.content):,} bytes")
    print()

    if response.status_code != 200:
        print("REQUEST FAILED")
        print(response.text[:2000])
        return

    print("REQUEST SUCCESSFUL")
    print()

    try:
        data = response.json()
    except ValueError:
        print("Response is not valid JSON.")
        print(response.text[:2000])
        return

    print(f"Response type: {type(data).__name__}")

    if isinstance(data, dict):
        print(f"Top-level keys: {list(data.keys())}")

    elif isinstance(data, list):
        print(f"Number of records: {len(data)}")

    print()
    print("=" * 80)
    print("FIRST PART OF RESPONSE")
    print("=" * 80)

    print(response.text[:5000])


if __name__ == "__main__":
    test_api()