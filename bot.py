import os
import requests
import time
from datetime import datetime

# ==========================================
# READ ENVIRONMENT VARIABLES
# ==========================================
API_TOKEN = os.getenv("COOE_API_TOKEN")
COOKIE_STR = os.getenv("COOE_COOKIE")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not API_TOKEN or not COOKIE_STR:
    raise Exception("Missing COOE_API_TOKEN or COOE_COOKIE")

# ==========================================
# CONSTANTS
# ==========================================
today_period = datetime.now().strftime("%Y%m%d")
headers = {
    "accept": "application/json, text/plain, */*",
    "authorization": f"Token {API_TOKEN}",
    "cookie": f"csrftoken={COOKIE_STR}",
    "referer": "https://cooegame.com/",
    "user-agent": "Mozilla/5.0"
}
categories = ["P", "S", "B", "E"]
selected_endings = [
    "003","006","009","033","036","039",
    "123","126","129","153","156","159",
    "213","216","219","243","246","249",
    "303","306","309","333","336","339",
    "423","426","429","453","456"
]
table_groups = [
    ["003","123","213","303","423"],
    ["006","126","216","306","426"],
    ["009","129","219","309","429"],
    ["033","153","243","333","453"],
    ["036","156","246","336","456"],
    ["039","159","249","339"]
]

all_data = {}

print("\n" + "="*80)
print("🚀 CAPTURE STARTED (e=red/o, o=green, v=violet)")
print("="*80)

# ==========================================
# CAPTURE LOOP
# ==========================================
for category in categories:
    print(f"\n📡 CATEGORY {category}")
    cat_results = {}
    stop = False

    for page in range(1, 50):
        if stop:
            break
        timestamp = int(time.time() * 1000)
        url = f"https://cooegame.com/win/guesses?t={timestamp}&category={category}&p={page}&p_size=10"
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code != 200:
                break
            data = resp.json()
            if "queryset" not in data or not data["queryset"]:
                break
            for item in data["queryset"]:
                period_str = str(item.get("period"))
                if not period_str.startswith(today_period):
                    continue
                ending = period_str[-3:]
                if ending == "003":
                    stop = True
                if ending in selected_endings:
                    is_red = item.get("is_red")
                    is_green = item.get("is_green")
                    is_violet = item.get("is_violet")
                    if is_red or (is_red and is_violet):
                        color = "e"
                    elif is_green or (is_green and is_violet):
                        color = "o"
                    elif is_violet:
                        color = "v"
                    else:
                        color = "?"
                    cat_results[ending] = color
                    print(f"   {ending} → {color}")
            time.sleep(0.15)
        except Exception as e:
            print(f"Error: {e}")
            break
    all_data[category] = cat_results

# ==========================================
# SAVE TO FILE (WITHOUT DUPLICATE HEADERS)
# ==========================================
txt_file = "capture_results.txt"
with open(txt_file, "w", encoding="utf-8") as f:
    for category in categories:
        # Ek baar header print aur write
        header = f"\n{'#'*75}\n        {category} CATEGORY PERIOD RESULTS\n{'#'*75}\n"
        print(header)
        f.write(header)

        data = all_data.get(category, {})
        for row in table_groups:
            line = ""
            for period in row:
                result = data.get(period, "--")
                line += f"{period} {result}".ljust(18)
            print(line)
            f.write(line + "\n")
        print()  # extra blank line
        f.write("\n")

print(f"\n✅ Saved to {txt_file}")

# ==========================================
# SEND TO TELEGRAM
# ==========================================
if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    with open(txt_file, "rb") as doc:
        files = {"document": doc}
        caption = f"📊 Results {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        r = requests.post(url, files=files, data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption})
        if r.status_code == 200:
            print("✅ Telegram sent")
        else:
            print("❌ Telegram failed")
