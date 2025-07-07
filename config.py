BOT_TOKEN = "7840639853:AAGoJ-669kVBNSfvejkgsrEM4-KNgKp4AbQ"
ADMIN_ID = "YOUR_TELEGRAM_USER_ID"  # Replace with your actual Telegram ID

# Supported countries with their languages and currencies
COUNTRIES = {
    "🇩🇪 Germany": {"lang": "de", "currency": "EUR"},
    "🇮🇹 Italy": {"lang": "it", "currency": "EUR"},
    "🇳🇱 Netherlands": {"lang": "nl", "currency": "EUR"},
    "🇷🇴 Romania": {"lang": "ro", "currency": "RON"},
    "🇹🇷 Turkey": {"lang": "tr", "currency": "TRY"},
    "🇺🇸 USA": {"lang": "en", "currency": "USD"},
    "🇫🇷 France": {"lang": "fr", "currency": "EUR"}
}

# Product categories with prices
PRODUCTS = {
    "cloned cards💳": {
        "prices": [300, 500, 1000, 5000],
        "deposit_percent": 100  # 100% payment upfront
    },
    "ID🪪": {
        "prices": [1500],
        "deposit_percent": 66.67  # €1000 deposit for €1500 item
    },
    "Drivers license🪪": {
        "prices": [1000],
        "deposit_percent": 70  # €700 deposit for €1000 item
    },
    "Bills💶": {
        "prices": [300, 500, 1000, 5000],
        "deposit_percent": 100  # 100% payment upfront
    }
}

BITCOIN_ADDRESS = "bitcoin:1EqfhYsqgcwPb8TfG4T2tm7XeRiMutsdPj"
SUPPORT_CONTACT = "@Leopold_MMM"