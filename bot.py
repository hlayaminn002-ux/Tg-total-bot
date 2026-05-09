import os
import re
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ======================= 2D LOTTERY ENGINE =======================

def parse_numbers(text: str):
    """ဂဏန်းတွေကို space / - / * / / / = စတဲ့ ပုံစံကနေ ထုတ်ယူမယ်"""
    # သင်္ကေတတွေကို space အဖြစ်ပြောင်း
    for ch in ['-', '*', '/', '=']:
        text = text.replace(ch, ' ')
    # ဂဏန်း ၂လုံးတွဲတွေကို ရှာမယ် (00-99)
    numbers = re.findall(r'\b(\d{2})\b', text)
    return numbers

def generate_two_digit_combinations(digits):
    """ဂဏန်းတွေကနေ 2D ကွက်တွေထုတ်မယ်"""
    if not digits:
        return []
    return [f"{int(d):02d}" for d in digits]

def apply_r_permutation(numbers):
    """R ပါရင် ဂဏန်းတွေကို ပြောင်းပြန်ထည့်မယ် (12 -> 21)"""
    result = []
    for num in numbers:
        result.append(num)
        rev = num[1] + num[0]
        if rev != num:
            result.append(rev)
    return result

def apply_breaked(numbers, amount):
    """ဒဲ့ ( - ) ပုံစံ = 1 ကွက် × amount"""
    return len(numbers) * amount

def apply_kip(numbers, amount):
    """ခွေ (အပူးမပါ) n×(n-1)×amount"""
    n = len(numbers)
    if n < 2:
        return 0
    return n * (n - 1) * amount

def apply_kip_pyar(numbers, amount):
    """ခွေပူး (အပူးပါ) n×n×amount"""
    n = len(numbers)
    return (n * n) * amount

def apply_pat(numbers, amount):
    """ပတ် = 19 ကွက် × ဂဏန်းအရေ × amount"""
    return len(numbers) * 19 * amount

def apply_pat_pyar(numbers, amount):
    """ပတ်ပူး = 20 ကွက် × ဂဏန်းအရေ × amount"""
    return len(numbers) * 20 * amount

def apply_htike(amount):
    """ထိပ်စီး = 10 × amount"""
    return 10 * amount

def apply_peit(amount):
    """ပိတ် = 10 × amount"""
    return 10 * amount

def apply_brayte(amount):
    """ဘရိတ် = 10 × amount"""
    return 10 * amount

def apply_sone_brayte(amount):
    """စုံဘရိတ် = 50 × amount"""
    return 50 * amount

def apply_sone_ma(numbers, amount, has_r=False):
    """စုံမ = 25 × amount (Rပါရင် 50)"""
    base = 25 * amount
    if has_r:
        return base * 2
    return base

def apply_kat(numbers1, numbers2, amount, has_r=False):
    """ကပ် = a×b×amount (Rပါရင်×2)"""
    a = len(numbers1)
    b = len(numbers2)
    if a == 0 or b == 0:
        return 0
    base = a * b * amount
    if has_r:
        return base * 2
    return base

def apply_saypyay(amount):
    """ဆယ်ပြည့် = 10 × amount"""
    return 10 * amount

def apply_apyar(amount):
    """အပူးစုံ = 10 × amount"""
    return 10 * amount

def apply_sa_apyar(amount):
    """စပူး = 5 × amount"""
    return 5 * amount

def apply_pawar(amount):
    """ပါဝါ = 10 × amount"""
    return 10 * amount

def apply_nakhat(amount):
    """နက္ခတ် = 10 × amount"""
    return 10 * amount

def apply_nyiko(amount):
    """ညီကို = 20 × amount"""
    return 20 * amount

def detect_city_brand(text: str):
    """မြို့အမည် (Du, Me, Maxi, Glo, Landon, Lao, Mm) ကို ရှာမယ်"""
    text_lower = text.lower()
    brands = {
        'du': 'Dubai', 'dubai': 'Dubai', 'ဒူ': 'Dubai', 'ဒူဘိုင်း': 'Dubai',
        'me': 'Mega', 'mega': 'Mega', 'မီ': 'Mega', 'မီဂါ': 'Mega',
        'maxi': 'Maxi', 'max': 'Maxi', 'မက်ဆီ': 'Maxi', 'မက်စီ': 'Maxi', 'စီစီ': 'Maxi',
        'glo': 'Global', 'global': 'Global', 'ဂလို': 'Global',
        'landon': 'London', 'london': 'London', 'လန်လန်': 'London', 'လန်ဒန်': 'London', 'ld': 'London',
        'lao': 'Lao', 'loa': 'Lao', 'laodon': 'Lao', 'လာအို': 'Lao', 'လာလာ': 'Lao',
        'mm': 'Mm'
    }
    for key, val in brands.items():
        if key in text_lower:
            return val
    return None

def calculate_2d(message_text: str):
    """အဓိက တွက်ချက်မှု"""
    text = message_text.lower()
    total = 0
    details = []
    
    # 1. R ပါသလား? (နောက်ဆုံး r ကို စစ်မယ်)
    has_r = bool(re.search(r'\br\s*\d+', text))
    
    # 2. ဂဏန်းတွေထုတ်မယ်
    raw_numbers = parse_numbers(message_text)
    if not raw_numbers:
        return None, None, None
    
    # 3. Amount ရှာမယ် (နောက်ဆုံးမှာပါတဲ့ နံပါတ်)
    amount_matches = re.findall(r'\b(\d+)\b', message_text)
    amount = None
    if amount_matches:
        # နောက်ဆုံးဂဏန်းကြီးကို amount လို့ယူ
        for am in reversed(amount_matches):
            if int(am) >= 10:
                amount = int(am)
                break
    if amount is None:
        amount = 0
    
    # 4. Keyword အလိုက် detect လုပ်မယ်
    keywords = {
        'ဒဲ့': ('basic', apply_breaked),
        'ပတ်': ('pat', apply_pat),
        'ပါ': ('pat', apply_pat),
        'ch': ('pat', apply_pat),
        'ပတ်ပူး': ('pat_pyar', apply_pat_pyar),
        'ပူးပို': ('pat_pyar', apply_pat_pyar),
        'ခွေ': ('kip', apply_kip),
        'အခွေ': ('kip', apply_kip),
        'ခ': ('kip', apply_kip),
        'ပူး': ('kip_pyar', apply_kip_pyar),
        'ခွေပူး': ('kip_pyar', apply_kip_pyar),
        'ထိပ်': ('htike', apply_htike),
        'ထ': ('htike', apply_htike),
        'top': ('htike', apply_htike),
        'ပိတ်': ('peit', apply_peit),
        'နောက်': ('peit', apply_peit),
        'န': ('peit', apply_peit),
        'ဘရိတ်': ('brayte', apply_brayte),
        'bk': ('brayte', apply_brayte),
        'စုံဘရိတ်': ('sone_brayte', apply_sone_brayte),
        'ဆယ်ပြည့်': ('saypyay', apply_saypyay),
        'အပူးစုံ': ('apyar', apply_apyar),
        'စပူး': ('sa_apyar', apply_sa_apyar),
        'စုံမ': ('sone_ma', apply_sone_ma),
        'စမ': ('sone_ma', apply_sone_ma),
        'ပါဝါ': ('pawar', apply_pawar),
        'pw': ('pawar', apply_pawar),
        'power': ('pawar', apply_pawar),
        'နက္ခတ်': ('nakhat', apply_nakhat),
        'nk': ('nakhat', apply_nakhat),
        'ညီကို': ('nyiko', apply_nyiko),
    }
    
    matched_keyword = None
    calc_func = None
    
    for kw, (name, func) in keywords.items():
        if kw in text:
            matched_keyword = kw
            calc_func = func
            break
    
    if calc_func is not None:
        if matched_keyword in ['ခွေ', 'အခွေ', 'ခ']:
            total = calc_func(raw_numbers, amount)
        elif matched_keyword in ['ပူး', 'ခွေပူး']:
            total = calc_func(raw_numbers, amount)
        elif matched_keyword in ['ပတ်', 'ပါ', 'ch', 'ပတ်ပူး', 'ပူးပို']:
            total = calc_func(raw_numbers, amount)
        elif matched_keyword in ['ထိပ်','ထ','top','ပိတ်','နောက်','န']:
            total = calc_func(amount)
        elif matched_keyword in ['ဘရိတ်','bk','စုံဘရိတ်']:
            total = calc_func(amount)
        elif matched_keyword in ['ဆယ်ပြည့်','အပူးစုံ','စပူး','ပါဝါ','pw','power','နက္ခတ်','nk','ညီကို']:
            total = calc_func(amount)
        elif matched_keyword in ['စုံမ','စမ']:
            total = calc_func(raw_numbers, amount, has_r)
        details.append(f"Keyword: {matched_keyword} → {total} Kyats")
    else:
        # basic ဒဲ့
        total = apply_breaked(raw_numbers, amount)
        details.append(f"Basic (ဒဲ့): {total} Kyats")
    
    # 5. R ပါရင် ဒဲ့ဘက်အတိုင်း ထပ်ထည့်
    if has_r and calc_func not in ['sone_ma']:
        r_total = apply_breaked(raw_numbers, amount)
        total += r_total
        details.append(f"R added: +{r_total} = {total} Kyats")
    
    # 6. မြို့အမည် attach
    city = detect_city_brand(message_text)
    
    return total, city, "\n".join(details)

# ======================= TELEGRAM BOT =======================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # စာတန်းကို reply လုပ်တာကို လုံးဝမဖြေရ
    if update.message.reply_to_message:
        return
    
    user_text = update.message.text
    if not user_text:
        return
    
    total, city, details = calculate_2d(user_text)
    
    if total is not None and total > 0:
        reply = f"💰 **စုစုပေါင်း: {total:,.0f} Kyats**"
        if city:
            reply = f"📍 {city}\n" + reply
        reply += f"\n\n📝 {details}"
        await update.message.reply_text(reply)
        logging.info(f"Calculated: {total}")
    else:
        # ဘာမှမတွက်ရင် တိတ်နေမယ်
        logging.info(f"No match: {user_text}")

if __name__ == "__main__":
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not set!")
        exit(1)
    
    app = ApplicationBuilder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🎲 2D Lottery Bot is running on Railway 24/7...")
    app.run_polling()
