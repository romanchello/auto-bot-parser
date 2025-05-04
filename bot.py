
import logging
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os

# === НАСТРОЙКИ ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHROMEDRIVER_PATH = "/opt/homebrew/bin/chromedriver"

# Настройки Selenium
def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)

# Поиск машин
def search_cars():
    driver = create_driver()
    search_url = "https://suchen.mobile.de/fahrzeuge/search.html?vc=Car&dam=false&fr=2022%3A&ms=25200%3B%3B&sb=rel&searchId=&ref=quickSearch"
    driver.get(search_url)
    time.sleep(3)

    ads = driver.find_elements(By.CSS_SELECTOR, "a[href*='/fahrzeuge/details.html']")
    urls = list(set([ad.get_attribute("href") for ad in ads]))[:3]
    results = []

    for url in urls:
        driver.get(url)
        time.sleep(2)

        def get_text(by, value):
            try:
                return driver.find_element(by, value).text
            except:
                return "—"

        results.append({
            "Название": get_text(By.CSS_SELECTOR, "h1 span"),
            "Цена": get_text(By.CSS_SELECTOR, '[data-testid="prime-price"]'),
            "Нетто": get_text(By.XPATH, '//div[contains(text(), "Netto")]'),
            "Пробег": get_text(By.XPATH, '//li[contains(text(), "km")]'),
            "Мощность": get_text(By.XPATH, '//li[contains(text(), "kW")]'),
            "Коробка": get_text(By.XPATH, '//li[contains(text(), "Automatik") or contains(text(), "Schaltgetriebe")]'),
            "Регистрация": get_text(By.XPATH, '//li[contains(text(), "Erstzulassung")]'),
            "Ссылка": url
        })

    driver.quit()
    return results

# Бот
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "Привет! Введи запрос, например: Volkswagen ID.4 2022 дизель")

@bot.message_handler(func=lambda msg: True)
def handle_query(message):
    bot.send_message(message.chat.id, "Ищу авто, подожди немного...")
    results = search_cars()
    for car in results:
        text = f"<b>{car['Название']}</b>\n💶 {car['Цена']} (Netto: {car['Нетто']})\n🚗 {car['Пробег']}\n⚡ {car['Мощность']}\n🔁 {car['Коробка']}\n📅 {car['Регистрация']}\n🔗 {car['Ссылка']}"
        bot.send_message(message.chat.id, text, parse_mode="HTML")

bot.infinity_polling()
