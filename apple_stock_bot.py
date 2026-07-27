import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

PRODUCT_URL = (
    "https://www.apple.com/tr/shop/buy-iphone/"
    "iphone-17-pro/6.9-in%C3%A7-ekran-256gb-g%C3%BCm%C3%BC%C5%9F"
)

STORES = {
    "Zorlu Center": "R448",
    "Akasya": "R588",
    "Bağdat Caddesi": "R713",
}

STATE_FILE = Path("state.json")


def send_telegram(message: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode(
        {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "disable_web_page_preview": False,
        }
    ).encode()

    request = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(request, timeout=20) as response:
        response.read()


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}

    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def check_store(store_name: str, store_number: str) -> bool:
    query = urllib.parse.urlencode(
        {
            "parts.0": "MYWY3TU/A",
            "searchNearby": "true",
            "store": store_number,
        }
    )

    url = (
        "https://www.apple.com/tr/shop/fulfillment-messages?"
        + query
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            text = response.read().decode("utf-8", errors="ignore").lower()
    except Exception as exc:
        print(f"{store_name} kontrol hatası: {exc}")
        return False

    unavailable_words = [
        "unavailable",
        "stokta yok",
        "teslim alınamaz",
        "not eligible",
    ]

    available_words = [
        "available",
        "bugün",
        "pickup",
        "teslim alınabilir",
    ]

    if any(word in text for word in unavailable_words):
        return False

    return any(word in text for word in available_words)


def main() -> None:
    previous_state = load_state()
    current_state = {}

    for store_name, store_number in STORES.items():
        available = check_store(store_name, store_number)
        current_state[store_name] = available

        was_available = previous_state.get(store_name, False)

        if available and not was_available:
            send_telegram(
                "✅ Apple stok bulundu!\n\n"
                "iPhone 17 Pro Max 256 GB Gümüş\n"
                f"📍 {store_name}\n"
                "🏬 Mağazadan teslim uygun görünüyor.\n\n"
                f"🔗 {PRODUCT_URL}"
            )

    save_state(current_state)
    print(current_state)


if __name__ == "__main__":
    main()
