import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from config import BOT_TOKEN, COUNTRIES, PRODUCTS, BITCOIN_ADDRESS, SUPPORT_CONTACT, ADMIN_ID

# File to store user data
DATA_FILE = "data.json"

# Load user data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# Save user data
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Currency conversion rates (simplified - in a real app, use an API)
CURRENCY_RATES = {
    "EUR": 1,
    "USD": 1.18,
    "TRY": 10.5,
    "RON": 4.92
}

def convert_currency(amount, from_currency, to_currency):
    if from_currency == to_currency:
        return amount
    eur_amount = amount / CURRENCY_RATES.get(from_currency, 1)
    return round(eur_amount * CURRENCY_RATES.get(to_currency, 1), 2)

# Start command
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    data = load_data()
    
    if str(user_id) in data:
        send_main_menu(update, context, user_id)
        return
    
    # Ask for country
    keyboard = [
        [InlineKeyboardButton(country, callback_data=f"country_{country}")]
        for country in COUNTRIES.keys()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "Please select your country / Bitte wählen Sie Ihr Land / "
        "Seleziona il tuo paese / Selecteer uw land / "
        "Vă rugăm să selectați țara dumneavoastră / "
        "Lütfen ülkenizi seçiniz / Veuillez sélectionner votre pays:",
        reply_markup=reply_markup
    )

def country_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    country = query.data.split("_")[1]
    
    data = load_data()
    data[str(user_id)] = {
        "country": country,
        "lang": COUNTRIES[country]["lang"],
        "currency": COUNTRIES[country]["currency"],
        "step": "country_selected"
    }
    save_data(data)
    
    send_main_menu(update, context, user_id)

def send_main_menu(update, context, user_id):
    data = load_data()
    user_data = data.get(str(user_id), {})
    lang = user_data.get("lang", "en")
    
    # Simple language responses (expand this in a real app)
    responses = {
        "en": {
            "main_menu": "What would you like to do?",
            "shop": "🛍️ Shop",
            "support": "🆘 Contact Support"
        },
        "de": {
            "main_menu": "Was möchten Sie tun?",
            "shop": "🛍️ Einkaufen",
            "support": "🆘 Support kontaktieren"
        },
        # Add other languages...
    }
    
    # Default to English if language not implemented
    lang_responses = responses.get(lang, responses["en"])
    
    keyboard = [
        [InlineKeyboardButton(lang_responses["shop"], callback_data="shop")],
        [InlineKeyboardButton(lang_responses["support"], callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(update, 'message'):
        update.message.reply_text(lang_responses["main_menu"], reply_markup=reply_markup)
    else:
        update.callback_query.edit_message_text(lang_responses["main_menu"], reply_markup=reply_markup)

def shop(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    data = load_data()
    user_data = data.get(str(user_id), {})
    lang = user_data.get("lang", "en")
    
    responses = {
        "en": "What would you like to shop?",
        "de": "Was möchten Sie kaufen?",
        # Add other languages...
    }
    
    keyboard = [
        [InlineKeyboardButton(product, callback_data=f"product_{product}")]
        for product in PRODUCTS.keys()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        responses.get(lang, responses["en"]),
        reply_markup=reply_markup
    )

def product_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    product = query.data.split("_")[1]
    
    data = load_data()
    user_data = data.get(str(user_id), {})
    lang = user_data.get("lang", "en")
    currency = user_data.get("currency", "EUR")
    
    responses = {
        "en": {
            "select_quantity": f"Please select quantity for {product}",
            "prices": "Prices:"
        },
        "de": {
            "select_quantity": f"Bitte wählen Sie die Menge für {product}",
            "prices": "Preise:"
        },
        # Add other languages...
    }
    
    # Get prices in user's currency
    prices_in_currency = [
        convert_currency(price, "EUR", currency)
        for price in PRODUCTS[product]["prices"]
    ]
    
    # Create price text
    price_text = "\n".join([
        f"{i+1}. {price} {currency}" 
        for i, price in enumerate(prices_in_currency)
    ])
    
    # First ask for quantity
    context.user_data["current_product"] = product
    query.edit_message_text(
        f"{responses.get(lang, responses['en'])['select_quantity']}\n\n"
        f"{responses.get(lang, responses['en'])['prices']}\n"
        f"{price_text}\n\n"
        "Please send me the quantity (1, 2, 3, etc.):"
    )

def handle_quantity(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    quantity = update.message.text
    
    if not quantity.isdigit() or int(quantity) < 1:
        update.message.reply_text("Please enter a valid quantity (1, 2, 3, etc.)")
        return
    
    data = load_data()
    user_data = data.get(str(user_id), {})
    product = context.user_data.get("current_product")
    
    if not product:
        update.message.reply_text("Please start over.")
        return
    
    # Store the selected quantity
    user_data["current_order"] = {
        "product": product,
        "quantity": int(quantity),
        "step": "quantity_selected"
    }
    data[str(user_id)] = user_data
    save_data(data)
    
    # Ask for price selection if there are multiple prices
    if len(PRODUCTS[product]["prices"]) > 1:
        ask_for_price(update, context, user_id, product)
    else:
        # Only one price, proceed to payment
        prepare_payment(update, context, user_id, product, PRODUCTS[product]["prices"][0], int(quantity))

def ask_for_price(update: Update, context: CallbackContext, user_id, product):
    data = load_data()
    user_data = data.get(str(user_id), {})
    currency = user_data.get("currency", "EUR")
    
    prices_in_currency = [
        convert_currency(price, "EUR", currency)
        for price in PRODUCTS[product]["prices"]
    ]
    
    keyboard = [
        [InlineKeyboardButton(f"{price} {currency}", callback_data=f"price_{i}")]
        for i, price in enumerate(prices_in_currency)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "Please select the price option:",
        reply_markup=reply_markup
    )

def price_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    price_index = int(query.data.split("_")[1])
    
    data = load_data()
    user_data = data.get(str(user_id), {})
    product = user_data.get("current_order", {}).get("product")
    quantity = user_data.get("current_order", {}).get("quantity", 1)
    
    if not product:
        query.edit_message_text("Please start over.")
        return
    
    price = PRODUCTS[product]["prices"][price_index]
    prepare_payment(update, context, user_id, product, price, quantity)

def prepare_payment(update: Update, context: CallbackContext, user_id, product, price, quantity):
    data = load_data()
    user_data = data.get(str(user_id), {})
    currency = user_data.get("currency", "EUR")
    lang = user_data.get("lang", "en")
    
    responses = {
        "en": {
            "order_summary": "Order Summary",
            "product": "Product",
            "quantity": "Quantity",
            "price_per_item": "Price per item",
            "total_amount": "Total amount",
            "deposit_required": "Deposit required now",
            "balance_on_delivery": "Balance on delivery",
            "payment_instructions": f"Please send the deposit to our Bitcoin address:\n\n{BITCOIN_ADDRESS}\n\nAfter payment, please send a screenshot as proof.",
            "provide_address": "Please provide your shipping address:"
        },
        "de": {
            "order_summary": "Bestellübersicht",
            "product": "Produkt",
            "quantity": "Menge",
            "price_per_item": "Preis pro Stück",
            "total_amount": "Gesamtbetrag",
            "deposit_required": "Anzahlung jetzt erforderlich",
            "balance_on_delivery": "Restzahlung bei Lieferung",
            "payment_instructions": f"Bitte senden Sie die Anzahlung an unsere Bitcoin-Adresse:\n\n{BITCOIN_ADDRESS}\n\nNach der Zahlung senden Sie bitte einen Screenshot als Nachweis.",
            "provide_address": "Bitte geben Sie Ihre Lieferadresse an:"
        },
        # Add other languages...
    }
    
    price_in_currency = convert_currency(price, "EUR", currency)
    total_amount = price_in_currency * quantity
    deposit_percent = PRODUCTS[product]["deposit_percent"]
    deposit_amount = total_amount * (deposit_percent / 100)
    balance_amount = total_amount - deposit_amount
    
    # Store order details
    user_data["current_order"]["price_per_item"] = price
    user_data["current_order"]["total_amount"] = total_amount
    user_data["current_order"]["deposit_amount"] = deposit_amount
    user_data["current_order"]["balance_amount"] = balance_amount
    user_data["current_order"]["step"] = "awaiting_payment"
    data[str(user_id)] = user_data
    save_data(data)
    
    lang_responses = responses.get(lang, responses["en"])
    
    message = (
        f"{lang_responses['order_summary']}:\n\n"
        f"{lang_responses['product']}: {product}\n"
        f"{lang_responses['quantity']}: {quantity}\n"
        f"{lang_responses['price_per_item']}: {price_in_currency} {currency}\n"
        f"{lang_responses['total_amount']}: {total_amount} {currency}\n"
    )
    
    if deposit_percent < 100:
        message += (
            f"\n{lang_responses['deposit_required']}: {deposit_amount} {currency}\n"
            f"{lang_responses['balance_on_delivery']}: {balance_amount} {currency}\n"
        )
    
    message += f"\n{lang_responses['payment_instructions']}"
    
    if hasattr(update, 'message'):
        update.message.reply_text(message)
    else:
        query = update.callback_query
        query.edit_message_text(message)
    
    # Ask for shipping address after payment
    context.user_data["awaiting_address"] = True

def handle_address(update: Update, context: CallbackContext):
    if not context.user_data.get("awaiting_address"):
        return
    
    user_id = update.effective_user.id
    address = update.message.text
    
    data = load_data()
    user_data = data.get(str(user_id), {})
    
    if "current_order" not in user_data:
        update.message.reply_text("Please start over.")
        return
    
    user_data["current_order"]["address"] = address
    user_data["current_order"]["step"] = "completed"
    data[str(user_id)] = user_data
    save_data(data)
    
    # Notify admin
    notify_admin(update, context, user_id, user_data)
    
    update.message.reply_text(
        "Thank you for your order! Our support will contact you soon. "
        f"If you have any questions, please contact {SUPPORT_CONTACT}."
    )
    
    del context.user_data["awaiting_address"]

def notify_admin(update: Update, context: CallbackContext, user_id, user_data):
    order = user_data.get("current_order", {})
    user = update.effective_user
    
    message = (
        "📦 New Order Received!\n\n"
        f"User: {user.full_name} (@{user.username or 'N/A'})\n"
        f"User ID: {user_id}\n"
        f"Product: {order.get('product')}\n"
        f"Quantity: {order.get('quantity')}\n"
        f"Price per item: {order.get('price_per_item')} EUR\n"
        f"Total amount: {order.get('total_amount')} {user_data.get('currency')}\n"
        f"Deposit paid: {order.get('deposit_amount')} {user_data.get('currency')}\n"
        f"Balance on delivery: {order.get('balance_amount')} {user_data.get('currency')}\n"
        f"Shipping address: {order.get('address')}\n\n"
        f"User's language: {user_data.get('lang')}"
    )
    
    context.bot.send_message(chat_id=ADMIN_ID, text=message)

def handle_payment_proof(update: Update, context: CallbackContext):
    # Check if user has sent a photo (payment proof)
    if update.message.photo:
        user_id = update.effective_user.id
        data = load_data()
        user_data = data.get(str(user_id), {})
        
        if user_data.get("current_order", {}).get("step") == "awaiting_payment":
            # Store the photo file_id
            photo_id = update.message.photo[-1].file_id
            user_data["current_order"]["payment_proof"] = photo_id
            data[str(user_id)] = user_data
            save_data(data)
            
            # Ask for shipping address
            lang = user_data.get("lang", "en")
            responses = {
                "en": "Thank you for the payment proof. Please provide your shipping address:",
                "de": "Vielen Dank für den Zahlungsnachweis. Bitte geben Sie Ihre Lieferadresse an:",
                # Add other languages...
            }
            
            update.message.reply_text(responses.get(lang, responses["en"]))
            context.user_data["awaiting_address"] = True

def support(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    data = load_data()
    user_data = data.get(str(user_id), {})
    lang = user_data.get("lang", "en")
    
    responses = {
        "en": f"For any issues, please contact our support team: {SUPPORT_CONTACT}",
        "de": f"Bei Problemen wenden Sie sich bitte an unser Support-Team: {SUPPORT_CONTACT}",
        # Add other languages...
    }
    
    query.edit_message_text(responses.get(lang, responses["en"]))

def admin_commands(update: Update, context: CallbackContext):
    if str(update.effective_user.id) != ADMIN_ID:
        return
    
    command = update.message.text.split()[0]
    
    if command == "/users":
        data = load_data()
        update.message.reply_text(f"Total users: {len(data)}")
    
    elif command == "/orders":
        data = load_data()
        orders = [user for user in data.values() if "current_order" in user]
        update.message.reply_text(f"Total orders: {len(orders)}")

def error_handler(update: Update, context: CallbackContext):
    print(f"Update {update} caused error {context.error}")
    
    if update.effective_user:
        update.effective_user.send_message(
            "Sorry, something went wrong. Please try again or contact support."
        )

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    
    # Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(country_selected, pattern="^country_"))
    dp.add_handler(CallbackQueryHandler(shop, pattern="^shop$"))
    dp.add_handler(CallbackQueryHandler(product_selected, pattern="^product_"))
    dp.add_handler(CallbackQueryHandler(price_selected, pattern="^price_"))
    dp.add_handler(CallbackQueryHandler(support, pattern="^support$"))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    dp.add_handler(MessageHandler(Filters.photo, handle_payment_proof))
    dp.add_handler(CommandHandler("users", admin_commands))
    dp.add_handler(CommandHandler("orders", admin_commands))
    dp.add_error_handler(error_handler)
    
    updater.start_polling()
    updater.idle()

def handle_text(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    data = load_data()
    user_data = data.get(str(user_id), {})
    
    if context.user_data.get("awaiting_address"):
        handle_address(update, context)
    elif "current_order" in user_data and user_data["current_order"].get("step") == "quantity_selected":
        handle_quantity(update, context)

if __name__ == '__main__':
    main()