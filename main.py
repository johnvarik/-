import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import List

from telegram import Bot, Update
from telegram.error import TelegramError
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# --- НАСТРОЙКИ (заполни своими данными) ---
BOT_TOKEN = "8791185504:AAEYIE7wWFQmruIVUrLTbNJ6-g5QtuhVZbM"
CHAT_ID = -1003007922511
# Диапазон времени отправки (часы, минуты)
START_HOUR = 8
END_HOUR = 23
# ------------------------------------------

# Логирование в консоль
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# База фраз (только с ТАКСОН и САБЛИН)
PHRASES = [
    # ТАКСОН
    "ТАКСОН ПИДОХАС",
    "ТАКСОН ХУЙЛО",
    "ТАКСОН ПИДОР",
    "ТАКСОН ГАВНО",
    "ТАКСОН УЁБОК",
    "ТАКСОН ЧМО",
    "ТАКСОН МРАЗЬ",
    "ТАКСОН ДОЛБОЁБ",
    "ТАКСОН КОЗЁЛ",
    "ТАКСОН ПЁС",
    "ТАКСОН ШАКАЛ",
    "ТАКСОН ГНИДА",
    "ТАКСОН СКОТИНА",
    "ТАКСОН ТУПОЙ",
    "ТАКСОН БЕЗМОЗГЛЫЙ",
    "ТАКСОН ДЕБИЛ",
    "ТАКСОН ИДИОТ",
    "ТАКСОН ОБОСРАНЕЦ",
    "ТАКСОН ЧЕРТ",
    "ТАКСОН БЕС",
    "ТАКСОН ВЫБЛЯДОК",
    "ТАКСОН ПРОСТИТУТКА",
    "ТАКСОН ШЛЮХА",
    "ТАКСОН ПЕТУХ",
    "ТАКСОН ПОДЗАБОРНЫЙ",
    "ТАКСОН ПОМОЙНЫЙ",
    "ТАКСОН КАНАЛИЗАЦИОННЫЙ",
    "ТАКСОН ПАРШИВЫЙ",
    "ТАКСОН ЧЕСОТОЧНЫЙ",
    "ТАКСОН КОРОСТАВЫЙ",
    "ТАКСОН ТУХЛЫЙ",
    "ТАКСОН ГНИЛОЙ",
    "ТАКСОН ВОНЮЧИЙ",
    "ТАКСОН СМЕРДЯЩИЙ",
    "ТАКСОН ЗЛОВОННЫЙ",
    "ТАКСОН СОБАКА",
    "ТАКСОН ЦЕПНОЙ",
    "ТАКСОН ДВОРОВЫЙ",
    "ТАКСОН БЕШЕНЫЙ",
    "ТАКСОН ШЕЛУДИВЫЙ",
    "ТАКСОН КУСАЧИЙ",
    "ТАКСОН БРЕХЛИВЫЙ",
    "ТАКСОН БЕСХВОСТЫЙ",
    "ТАКСОН КРИВОЛАПЫЙ",
    "ТАКСОН КОСОГЛАЗЫЙ",
    "ТАКСОН КРИВОРОЖИЙ",
    "ТАКСОН КОСОРУКИЙ",
    "ТАКСОН ГОРБАТЫЙ",
    "ТАКСОН КРИВОЙ",
    "ТАКСОН ХРОМОЙ",
    
    # САБЛИН
    "САБЛИН ХУЙ КОНЧЕННЫЙ",
    "САБЛИН ПИДОХАС",
    "САБЛИН ПИДОР",
    "САБЛИН ГАВНО",
    "САБЛИН УЁБОК",
    "САБЛИН ЧМО",
    "САБЛИН МРАЗЬ",
    "САБЛИН ДОЛБОЁБ",
    "САБЛИН КОЗЁЛ",
    "САБЛИН ПЁС",
    "САБЛИН ШАКАЛ",
    "САБЛИН ГНИДА",
    "САБЛИН СКОТИНА",
    "САБЛИН ТУПОЙ",
    "САБЛИН БЕЗМОЗГЛЫЙ",
    "САБЛИН ДЕБИЛ",
    "САБЛИН ИДИОТ",
    "САБЛИН ОБОСРАНЕЦ",
    "САБЛИН ЧЕРТ",
    "САБЛИН БЕС",
    "САБЛИН ВЫБЛЯДОК",
    "САБЛИН ПРОСТИТУТКА",
    "САБЛИН ШЛЮХА",
    "САБЛИН ПЕТУХ",
    "САБЛИН ПОДЗАБОРНЫЙ",
    "САБЛИН ПОМОЙНЫЙ",
    "САБЛИН КАНАЛИЗАЦИОННЫЙ",
    "САБЛИН ПАРШИВЫЙ",
    "САБЛИН ЧЕСОТОЧНЫЙ",
    "САБЛИН КОРОСТАВЫЙ",
    "САБЛИН ТУХЛЫЙ",
    "САБЛИН ГНИЛОЙ",
    "САБЛИН ВОНЮЧИЙ",
    "САБЛИН СМЕРДЯЩИЙ",
    "САБЛИН ЗЛОВОННЫЙ",
    "САБЛИН СОБАКА",
    "САБЛИН ЦЕПНОЙ",
    "САБЛИН ДВОРОВЫЙ",
    "САБЛИН БЕШЕНЫЙ",
    "САБЛИН ШЕЛУДИВЫЙ",
    "САБЛИН КУСАЧИЙ",
    "САБЛИН БРЕХЛИВЫЙ",
    "САБЛИН БЕСХВОСТЫЙ",
    "САБЛИН КРИВОЛАПЫЙ",
    "САБЛИН КОСОГЛАЗЫЙ",
    "САБЛИН КРИВОРОЖИЙ",
    "САБЛИН КОСОРУКИЙ",
    "САБЛИН ГОРБАТЫЙ",
    "САБЛИН КРИВОЙ",
    "САБЛИН ХРОМОЙ",
    "САБЛИН ОДНОНОГИЙ",
    "САБЛИН БЕЗРУКИЙ",
    "САБЛИН БЕЗГЛАЗЫЙ",
    "САБЛИН БЕЗУХИЙ",
    "САБЛИН БЕЗНОСЫЙ",
    "САБЛИН БЕЗРОТЫЙ",
    "САБЛИН БЕЗЪЯЗЫЙ",
    "САБЛИН КОНЧЕНЫЙ",
    "САБЛИН ОТБРОС",
    "САБЛИН ОТВЕРГНУТЫЙ",
    "САБЛИН НИЧТОЖЕСТВО",
    "САБЛИН НИКЧЕМНЫЙ",
    "САБЛИН БЕСПОЛЕЗНЫЙ"
]

# Отдельные базы для ответов на триггеры
TAKSON_PHRASES = [p for p in PHRASES if p.startswith("ТАКСОН")]
SABLIN_PHRASES = [p for p in PHRASES if p.startswith("САБЛИН")]

# Для избежания повторов подряд
used_phrases = []
last_trigger_response = {}  # Словарь для отслеживания последних ответов на триггеры
daily_task_running = False

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает входящие сообщения и отвечает на триггеры."""
    message_text = update.message.text.strip().lower()
    chat_id = update.effective_chat.id
    
    # Проверяем, что сообщение из нужного чата (опционально)
    if chat_id != CHAT_ID:
        return
    
    # Проверяем триггеры (теперь реагируем на упоминания слов)
    response = None
    
    # Просто "таксон" или "саблин" в любом контексте
    if "таксон" in message_text:
        # Выбираем случайную фразу про ТАКСОНА
        available = [p for p in TAKSON_PHRASES if p not in last_trigger_response.get('takson', [])]
        if not available:
            last_trigger_response['takson'] = []
            available = TAKSON_PHRASES
        
        response = random.choice(available)
        last_trigger_response.setdefault('takson', []).append(response)
        
    elif "саблин" in message_text:
        # Выбираем случайную фразу про САБЛИНА
        available = [p for p in SABLIN_PHRASES if p not in last_trigger_response.get('sablin', [])]
        if not available:
            last_trigger_response['sablin'] = []
            available = SABLIN_PHRASES
        
        response = random.choice(available)
        last_trigger_response.setdefault('sablin', []).append(response)
    
    # Если есть ответ - отправляем
    if response:
        try:
            await update.message.reply_text(response)
            logger.info(f"Ответ на упоминание в чате {chat_id}: {response}")
        except TelegramError as e:
            logger.error(f"Ошибка отправки ответа: {e}")

async def send_random_insult(context: ContextTypes.DEFAULT_TYPE):
    """Отправляет случайное оскорбление в чат."""
    chat_id = CHAT_ID
    
    # Выбираем фразу
    available = [p for p in PHRASES if p not in used_phrases]
    if not available:
        # Если все фразы использованы - сбрасываем список
        used_phrases.clear()
        available = PHRASES
    
    phrase = random.choice(available)
    used_phrases.append(phrase)
    
    try:
        await context.bot.send_message(chat_id=chat_id, text=phrase)
        logger.info(f"Отправлено сообщение в чат {chat_id}: {phrase}")
    except TelegramError as e:
        logger.error(f"Ошибка отправки: {e}")

async def daily_scheduler(app: Application):
    """Планировщик ежедневных сообщений."""
    global daily_task_running
    if daily_task_running:
        return
    daily_task_running = True
    
    while True:
        try:
            # Вычисляем случайное время для следующей отправки
            now = datetime.now()
            
            # Случайный час и минута
            random_hour = random.randint(START_HOUR, END_HOUR)
            random_minute = random.randint(0, 59)
            
            # Создаем время для сегодня
            target_time = now.replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)
            
            # Если время уже прошло сегодня - переносим на завтра
            if target_time <= now:
                target_time += timedelta(days=1)
            
            # Ждем до нужного времени
            wait_seconds = (target_time - now).total_seconds()
            logger.info(f"Следующая отправка запланирована на {target_time} (через {wait_seconds/3600:.1f} часов)")
            
            await asyncio.sleep(wait_seconds)
            
            # Отправляем сообщение
            await send_random_insult(ContextTypes.DEFAULT_TYPE(app=app, bot=app.bot))
            
        except Exception as e:
            logger.error(f"Ошибка в планировщике: {e}")
            await asyncio.sleep(60)  # Подождать минуту при ошибке

async def post_init(app: Application):
    """Действия после инициализации бота."""
    # Запускаем планировщик в фоне
    asyncio.create_task(daily_scheduler(app))
    logger.info("Планировщик ежедневных сообщений запущен")

def main():
    """Точка входа."""
    # Проверка токена
    if BOT_TOKEN == "ТОКЕН_БОТА_СЮДА" or CHAT_ID == -123456789:
        logger.error("Не заполнены TOKEN или CHAT_ID!")
        return
    
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Добавляем обработчик сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    logger.info("Бот запущен...")
    app.run_polling(allowed_updates=[])

if __name__ == "__main__":
    main()
