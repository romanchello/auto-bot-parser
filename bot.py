import logging
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import pandas as pd
import requests
from bs4 import BeautifulSoup

# === НАСТРОЙКИ ===
BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'
SHEET_URL = 'https://docs.google.com/spreadsheets/d/1FWP1WCSzhTNPjgah7F4HEJyul_EDe0HC/export?format=csv'
HEADERS = {'User-Agent': 'Mozilla/5.0'}

bot = telebot.TeleBot(BOT_TOKEN)

# Глобальный словарь состояния пользователей
user_state = {}

def load_data():
    df = pd.read_csv(SHEET_URL)
    return df

@bot.message_handler(commands=['start'])
def start_handler(message):
    df = load_data()
    brands = df['Марка'].unique().tolist()
    markup = InlineKeyboardMarkup()
    for brand in brands:
        markup.add(InlineKeyboardButton(brand, callback_data=f"brand:{brand}"))
    bot.send_message(message.chat.id, "Выбери марку авто:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("brand:"))
def brand_handler(call):
    brand = call.data.split(":")[1]
    user_state[call.from_user.id] = {"brand": brand}
    df = load_data()
    models = df[df['Марка'] == brand]['Модель'].unique().tolist()
    markup = InlineKeyboardMarkup()
    for model in models:
        markup.add(InlineKeyboardButton(model, callback_data=f"model:{model}"))
    bot.edit_message_text("Выбери модель:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("model:"))
def model_handler(call):
    model = call.data.split(":")[1]
    user_state[call.from_user.id]["model"] = model
    df = load_data()
    entry = df[(df["Марка"] == user_state[call.from_user.id]["brand"]) & (df["Модель"] == model)].iloc[0]
    year_from = entry["Годы от"]
    year_to = entry["Годы до"]
    fuel = entry["Топливо"]
    search_query = f'{user_state[call.from_user.id]["brand"]} {model} {int(year_from)}'
    send_search_results(call.message.chat.id, search_query)

def send_search_results(chat_id, query):
    url = f"https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&sortOption.sortBy=searchNetGrossPrice&searchId=&ref=srp&damageUnrepaired=NO_DAMAGE_UNREPAIRED&ambitCountry=DE&makeModelVariant1.makeId=1900&makeModelVariant1.modelDescription={query.replace(' ', '%20')}"
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    cars = soup.select('div.cBox-body.cBox-body--resultitem')
    count = 0
    for car in cars:
        title = car.select_one('.h3.u-text-break-word')
        link = car.select_one('a')
        price = car.select_one('.price-block .h3')
        image = car.select_one('img')
        if title and link and price:
            car_title = title.get_text(strip=True)
            car_price = price.get_text(strip=True)
            car_url = "https://suchen.mobile.de" + link["href"]
            image_url = image["src"] if image else None
            caption = f"🚗 <b>{car_title}</b>"
💶 <b>{car_price}</b>"
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Открыть объявление", url=car_url))
            bot.send_photo(chat_id, image_url, caption=caption, parse_mode='HTML', reply_markup=markup)
            count += 1
        if count >= 3:
            break

bot.infinity_polling()