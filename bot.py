import os
import re
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

# ====================== 2D တွက်နည်းစနစ် ======================

def parse_numbers(text: str):
    """စာသားထဲက ဂဏန်း ၂လုံးတွဲတွေကို ထုတ်မယ်"""
    for ch in ['-', '*', '/', '=', ' ']:
        text = text.replace(ch, ' ')
    numbers = re.findall(r'\b(\d{2})\b', text)
    return numbers

def apply_breakdown(numbers, amount):
    """ဒဲ့ပုံစံ - ၁ကွက် × amount × ဂဏန်းအရေအတွက်"""
    return len(numbers) * amount

def apply_kip(numbers, amount):
    """ခွေ (n × (n-1)) × amount"""
    n = len(numbers)
    if n < 2:
        return 0
    return n * (n - 1) * amount

def apply_pat(numbers, amount):
    """ပတ် - ၁၉ကွက် × ဂဏန်းအရေ × amount"""
    return len(numbers) * 19 * amount

def apply_pat_pyar(numbers, amount):
    """ပတ်ပူး - ၂၀ကွက် × ဂဏန်းအရေ × amount"""
    return len(numbers) * 20 * amount

def apply_htike(amount):
    """ထိပ်စီး - ၁၀ကွက် × amount"""
    return 10 * amount

def apply_peit(amount):
    """ပိတ် - ၁၀ကွက် × amount"""
    return 10 * amount

def apply_brayte(amount):
    """ဘရိတ် - ၁၀ကွက် × amount"""
    return 10 * amount

def apply_saypyay(amount):
    """ဆယ်ပြည့် - ၁၀ကွက် × amount"""
    return 10 * amount

def main_calculation(text: str):
    """အဓိက တွက်ချက်မှု"""
    text_lower = text.lower()
    
    # Amount ရှာမယ်
    amounts = re.findall(r'\b(\d+)\b', text)
    amount = 500  # default
    if amounts:
        for a in reversed(amounts):
            if int(a) >= 10:
                amount = int(a)
                break
    
    # ဂဏန်းတွေထုတ်မယ်
    numbers = parse_numbers(text)
    if not numbers:
        return None
    
    total = 0
    matched = False
    
    # Keyword စစ်ဆေးမယ်
    if 'ခွေ' in text_lower or 'အခွေ' in text_lower or 'ခ ' in text_lower:
        total = apply_kip(numbers, amount)
        matched = True
    elif 'ပတ်' in text_lower or 'အပါ' in text_lower:
        total = apply_pat(numbers, amount)
        matched = True
    elif 'ပတ်ပူး' in text_lower or 'ပူးပို' in text_lower:
        total = apply_pat_pyar(numbers, amount)
        matched = True
    elif 'ထိပ်' in text_lower or 'ထ ' in text_lower:
        total = apply_htike(amount)
        matched = True
    elif 'ပိတ်' in text_lower or 'နောက်' in text_lower:
        total = apply_peit(amount)
        matched = True
    elif 'ဘရိတ်' in text_lower:
        total = apply_brayte(amount)
        matched = True
    elif 'ဆယ်ပြည့်' in text_lower:
        total = apply_saypyay(amount)
        matched = True
    else:
        # ဒဲ့ပုံစံ
        total = apply_breakdown(numbers, amount)
        matched = True
    
    # R ပါရင် ထပ်ထည့်
    if 'r' in text_lower and re.search(r'\br\s*\d+', text_lower):
        total = total + apply_breakdown(numbers, amount)
    
    return total

# ====================== Telegram Bot ======================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # စာတန်းကို reply မပြန်ရ
    if update.message.reply_to_message:
        return
    
    user_text = update.message.text
    if not user_text:
        return
    
    total = main_calculation(user_text)
    
    if total and total > 0:
        await update.message.reply_text(f"💰 စုစုပေါင်း: {total:,.0f} Kyats")
    else:
        # သတ်မှတ်ထားတာမပါရင် ဘာမှမပြန်ပါ
        pass

# ====================== Main ======================

if __name__ == "__main__":
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not set!")
        exit(1)
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("2D Bot is running...")
    app.run_polling()
