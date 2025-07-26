import requests  
import time  
import json  
import os  
import re  
import telebot  
from keep_alive import keep_alive

TOKEN = "7905547591:AAEivoneinmUDRtg7hvBkGPEPPAegMC36uc"  
CHAT_ID = "5292727929"  
bot = telebot.TeleBot(TOKEN)

SEARCH_INTERVAL = 60  
URLS = [  
    "https://www.avito.ru/mahachkala/telefony/iphone-ASgBAgICAUSwwQ2I_Dc?cd=1",  
    "https://www.avito.ru/kaspiysk/telefony/iphone-ASgBAgICAUSwwQ2I_Dc?cd=1"  
]

SEEN_ADS_FILE = "seen_ads.json"  
if os.path.exists(SEEN_ADS_FILE):  
    with open(SEEN_ADS_FILE, "r", encoding="utf-8") as f:  
        seen_ads = json.load(f)  
else:  
    seen_ads = []

price_limits = {  
    "iphone x 64": 5000,  
    "iphone x 128": 6000,  
    "iphone x 256": 6000,  
    "iphone xs 64": 6000,  
    "iphone xs 256": 7000,  
    "iphone 11 64": 9000,  
    "iphone 11 128": 13000,  
    "iphone 11 256": 16000,  
    "iphone 11 pro 64": 11000,  
    "iphone 11 pro 256": 15000,  
    "iphone 11 pro max 128": 17000,  
    "iphone 11 pro max 256": 19000,  
    "iphone 12 128": 15000,  
    "iphone 12 256": 17000,  
    "iphone 12 pro 128": 18000,  
    "iphone 12 pro max 128": 20000,  
    "iphone 12 pro max 256": 25000,  
    "iphone 13 128": 21000  
}

good_keywords = ["идеал", "в отличном состоянии", "100% акб", "экран без царапин", "вскрытый", "70%", "80%", "95%", "мелкие царапины", "акб", "аккумулятор", "батарея"]  
bad_keywords = ["перекуп", "проблем", "восстанов", "реф"]

def normalize_title(title):  
    return re.sub(r"\s+", " ", title.lower())

def is_good_ad(title, description, price):  
    full_text = f"{title} {description}".lower()  
    # Filter out disallowed keywords (e.g., reseller, refurbished, problems)  
    if any(bad in full_text for bad in bad_keywords):  
        return False  
    # Check for broken screen indicators  
    broken_keywords = ["разбит", "трещ", "битый"]  
    broken = any(bk in full_text for bk in broken_keywords)  
    # For non-broken items, require at least one "good" keyword indicating good condition or battery info  
    if not broken:  
        if not any(good in full_text for good in good_keywords):  
            return False  
    # Check if any target iPhone model is mentioned and if price is within the acceptable limit  
    for model, limit in price_limits.items():  
        if model in normalize_title(full_text):  
            if broken:  
                if price <= limit - 1000:  
                    return True  
            else:  
                if price <= limit:  
                    return True  
    return False

def get_ads():  
    headers = { "User-Agent": "Mozilla/5.0" }  
    found = []  
    for url in URLS:  
        try:  
            response = requests.get(url, headers=headers, timeout=10)  
        except Exception as e:  
            continue  # skip this URL on error and move to next  
        if not response.ok:  
            continue  
        text = response.text  
        # Find ad JSON objects in the page content  
        matches = re.findall(r'{"id":\d+.*?}', text)  
        for match in matches:  
            try:  
                ad = json.loads(match)  
            except json.JSONDecodeError:  
                continue  
            ad_id = str(ad.get("id"))  
            if ad_id in seen_ads:  
                continue  # already seen this ad  
            title = ad.get("title", "")  
            desc = ad.get("description", "")  
            price = int(ad.get("price", 0))  
            link = f"https://www.avito.ru{ad.get('url', '')}"  
            if is_good_ad(title, desc, price):  
                seen_ads.append(ad_id)  
                found.append({  
                    "title": title,  
                    "desc": desc,  
                    "price": price,  
                    "link": link  
                })  
    return found

def send_ad(ad):  
    message = f"📱 {ad['title']}\n💰 Цена: {ad['price']}₽\n🔗 {ad['link']}"  
    bot.send_message(CHAT_ID, message)

def save_seen():  
    with open(SEEN_ADS_FILE, "w", encoding="utf-8") as f:  
        json.dump(seen_ads, f, ensure_ascii=False)

@bot.message_handler(commands=["start"])  
def start_message(message):  
    bot.send_message(message.chat.id, "Бот запущен.")

def run_search():  
    while True:  
        ads = get_ads()  
        for ad in ads:  
            send_ad(ad)  
        save_seen()  
        time.sleep(SEARCH_INTERVAL)

if __name__ == "__main__":  
    import threading  
    threading.Thread(target=run_search, daemon=True).start()  
    keep_alive()  
    bot.polling(none_stop=True)
