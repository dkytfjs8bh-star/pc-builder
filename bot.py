import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from gigachat import GigaChat

# --- КОНФИГУРАЦИЯ ---
TELEGRAM_TOKEN = "8011928165:AAGMEjyJ93CLwI0g9zaxkjFnhu6L5Vly4Eo"
GIGACHAT_AUTH = "MDE5ZDQwYjktYzczNC03YmIzLTg2OTItNWQyODZiZThkMWE5OjI5OWE5MzdmLThkZGQtNDdmMS1iY2RjLTdiYjcwODgzZTJlNA=="

# Подключаемся к GigaChat
giga = GigaChat(
    credentials=GIGACHAT_AUTH,
    scope="GIGACHAT_API_PERS",
    verify_ssl_certs=False,
    timeout=60
)

bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

logging.basicConfig(level=logging.INFO)

# --- СОСТОЯНИЯ ---
class BuildSteps(StatesGroup):
    waiting_for_purpose = State()
    waiting_for_games = State()
    waiting_for_programs = State()
    waiting_for_budget = State()
    waiting_for_preferences = State()
    waiting_for_confirmation = State()
    waiting_for_compatibility = State()
    waiting_for_quick_budget = State()  # Новое состояние для быстрой сборки

# --- КЛАВИАТУРЫ ---
def get_main_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🛠️ ПОШАГОВАЯ СБОРКА", callback_data="step_build")],
        [InlineKeyboardButton(text="🚀 БЫСТРАЯ СБОРКА", callback_data="quick_build")],
        [InlineKeyboardButton(text="🔍 ПРОВЕРКА СОВМЕСТИМОСТИ", callback_data="check_compatibility")],
        [InlineKeyboardButton(text="📖 ИНСТРУКЦИЯ", callback_data="instruction")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_purpose_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🎮 ИГРЫ", callback_data="purpose_games")],
        [InlineKeyboardButton(text="💼 РАБОТА", callback_data="purpose_work")],
        [InlineKeyboardButton(text="🎬 МОНТАЖ/3D", callback_data="purpose_creative")],
        [InlineKeyboardButton(text="🌍 УНИВЕРСАЛЬНЫЙ", callback_data="purpose_universal")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_games_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🎮 Киберспорт", callback_data="games_esports")],
        [InlineKeyboardButton(text="🔥 Современные AAA", callback_data="games_aaa")],
        [InlineKeyboardButton(text="🎲 Инди и старые", callback_data="games_indie")],
        [InlineKeyboardButton(text="👾 ВСЕ ПОДРЯД", callback_data="games_all")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_programs_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🎬 Adobe", callback_data="prog_adobe")],
        [InlineKeyboardButton(text="🖌️ 3D", callback_data="prog_3d")],
        [InlineKeyboardButton(text="💻 Программирование", callback_data="prog_dev")],
        [InlineKeyboardButton(text="🔧 Офис", callback_data="prog_office")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_budget_keyboard():
    buttons = [
        [InlineKeyboardButton(text="💰 ДО 50 000 ₽", callback_data="budget_min")],
        [InlineKeyboardButton(text="💵 50-100 000 ₽", callback_data="budget_medium")],
        [InlineKeyboardButton(text="💎 100-200 000 ₽", callback_data="budget_high")],
        [InlineKeyboardButton(text="👑 200 000+ ₽", callback_data="budget_pro")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_preferences_keyboard():
    buttons = [
        [InlineKeyboardButton(text="💚 AMD + 🔴 AMD", callback_data="pref_amd_amd")],
        [InlineKeyboardButton(text="💚 AMD + 💙 NVIDIA", callback_data="pref_amd_nvidia")],
        [InlineKeyboardButton(text="💙 Intel + 💙 NVIDIA", callback_data="pref_intel_nvidia")],
        [InlineKeyboardButton(text="🤷 НЕТ ПРЕДПОЧТЕНИЙ", callback_data="pref_any")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_keyboard():
    buttons = [
        [InlineKeyboardButton(text="✅ ДА, СОБИРАЙ!", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="🔄 НАЧАТЬ ЗАНОВО", callback_data="confirm_restart")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_to_main():
    buttons = [[InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_compatibility_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🔄 ПРОВЕРИТЬ ДРУГУЮ СВЯЗКУ", callback_data="check_compatibility")],
        [InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- ИНСТРУКЦИЯ ---
INSTRUCTION = """
📖 КАК СОБРАТЬ ПК САМОСТОЯТЕЛЬНО

🔧 ПОДГОТОВКА
1. Купи все компоненты
2. Подготовь крестовую отвертку
3. Заземлись (прикоснись к батарее)

🔩 ПОСЛЕДОВАТЕЛЬНОСТЬ
1. Установи процессор в материнскую плату
2. Установи оперативную память (слоты 2 и 4)
3. Установи кулер (подключи к CPU_FAN)
4. Закрепи материнскую плату в корпусе
5. Установи блок питания
6. Установи SSD (M.2 или SATA)
7. Установи видеокарту (до щелчка)
8. Подключи провода: 24pin, 4/8pin CPU, переднюю панель

💻 ПЕРВЫЙ ЗАПУСК
1. Включи блок питания
2. Нажми кнопку включения
3. Установи Windows с флешки

⚠️ Если не включается: проверь кнопку Power SW и кабели питания

💡 Совет: посмотри видео "сборка ПК" на YouTube
"""

# --- ФУНКЦИЯ ДЛЯ ИЗВЛЕЧЕНИЯ БЮДЖЕТА ИЗ ЗАПРОСА ---
def extract_budget_from_query(text: str) -> tuple:
    """Извлекает бюджет из текста запроса и возвращает (бюджет_в_рублях, категория)"""
    text_lower = text.lower()
    
    # Ищем цифры с указанием бюджета
    patterns = [
        r'(\d{3,6})\s*тыс',           # 100 тыс
        r'(\d{3,6})\s*000',            # 100000
        r'до\s*(\d{3,6})',             # до 100000
        r'(\d{3,6})\s*руб',            # 100000 руб
        r'за\s*(\d{3,6})',             # за 100000
        r'бюджет\s*(\d{3,6})',         # бюджет 100000
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            amount = int(match.group(1))
            if 'тыс' in pattern or 'тыс' in text_lower:
                amount = amount * 1000
            return amount
    
    return None

def get_budget_category(amount: int) -> str:
    """Преобразует сумму в категорию бюджета"""
    if amount <= 50000:
        return "min"
    elif amount <= 100000:
        return "medium"
    elif amount <= 200000:
        return "high"
    else:
        return "pro"

# --- ГОТОВЫЕ СБОРКИ ДЛЯ РАЗНЫХ БЮДЖЕТОВ ---
def get_fixed_build(budget: int, purpose: str = "games") -> str:
    """Возвращает готовую сборку строго под указанный бюджет"""
    
    if purpose == "games":
        if budget <= 50000:
            return """🎮 **ИГРОВОЙ ПК (до 50 000 ₽)**

🔹 **Процессор:** Intel Core i3-12100F — 7 500 ₽
🔹 **Видеокарта:** GTX 1650 4GB — 15 000 ₽
🔹 **Материнская плата:** H610 — 6 000 ₽
🔹 **Оперативная память:** 16GB DDR4 3200MHz — 4 000 ₽
🔹 **SSD:** 512GB NVMe — 4 000 ₽
🔹 **Блок питания:** 500W 80+ — 3 500 ₽
🔹 **Корпус:** Aerocool Cylon — 4 000 ₽

💰 **ИТОГО:** 44 000 ₽

💡 **Совет:** Отличный вариант для 1080p в средних настройках"""
        
        elif budget <= 100000:
            return """🎮 **ИГРОВОЙ ПК (50-100 000 ₽)**

🔹 **Процессор:** Intel Core i5-12400F — 10 000 ₽
🔹 **Видеокарта:** RTX 3060 12GB — 32 000 ₽
🔹 **Материнская плата:** B660 — 8 000 ₽
🔹 **Оперативная память:** 32GB DDR4 3200MHz — 6 000 ₽
🔹 **SSD:** 1TB NVMe — 6 000 ₽
🔹 **Блок питания:** 650W Bronze — 5 000 ₽
🔹 **Корпус:** с хорошим обдувом — 5 000 ₽

💰 **ИТОГО:** 72 000 ₽

💡 **Совет:** Уверенный 1080p Ultra, заход в 1440p"""
        
        elif budget <= 200000:
            return """🎮 **ИГРОВОЙ ПК (100-200 000 ₽)**

🔹 **Процессор:** Intel i7-13700K / Ryzen 7 7800X3D — 35 000 ₽
🔹 **Видеокарта:** RTX 4070 Ti Super 16GB — 85 000 ₽
🔹 **Материнская плата:** Z790 / X670 — 18 000 ₽
🔹 **Оперативная память:** 32GB DDR5 6000MHz — 12 000 ₽
🔹 **SSD:** 2TB NVMe Gen4 — 12 000 ₽
🔹 **Блок питания:** 850W Gold — 10 000 ₽
🔹 **Корпус:** NZXT H7 Flow — 8 000 ₽

💰 **ИТОГО:** 180 000 ₽

💡 **Совет:** Отличный 1440p и 4K-гейминг"""
        
        else:
            return """🎮 **ИГРОВОЙ ПК (от 200 000 ₽)**

🔹 **Процессор:** Intel i9-14900K / Ryzen 9 7950X3D — 55 000 ₽
🔹 **Видеокарта:** RTX 4080 Super 16GB — 120 000 ₽
🔹 **Материнская плата:** Z790 / X670E — 25 000 ₽
🔹 **Оперативная память:** 64GB DDR5 6000MHz — 20 000 ₽
🔹 **SSD:** 4TB NVMe Gen5 — 25 000 ₽
🔹 **Блок питания:** 1000W Platinum — 18 000 ₽
🔹 **Корпус:** Lian Li O11 Dynamic — 12 000 ₽

💰 **ИТОГО:** 275 000 ₽

💡 **Совет:** Максимальная производительность для 4K и стриминга"""
    
    else:
        return get_fallback_build_by_budget(budget)

def get_fallback_build_by_budget(budget: int) -> str:
    if budget <= 50000:
        return """💼 **РАБОЧИЙ/УНИВЕРСАЛЬНЫЙ ПК (до 50 000 ₽)**

🔹 **Процессор:** Intel Core i3-12100 — 9 000 ₽
🔹 **Видеокарта:** Встроенная — 0 ₽
🔹 **Материнская плата:** H610 — 6 000 ₽
🔹 **Оперативная память:** 16GB DDR4 — 4 000 ₽
🔹 **SSD:** 512GB NVMe — 4 000 ₽
🔹 **Блок питания:** 450W — 3 000 ₽

💰 **ИТОГО:** 26 000 ₽

💡 **Совет:** Отличный вариант для офисных задач"""
    else:
        return """💻 **УНИВЕРСАЛЬНЫЙ ПК (оптимальный бюджет)**

🔹 **Процессор:** Intel Core i5-13400F — 12 000 ₽
🔹 **Видеокарта:** RTX 3060 12GB — 32 000 ₽
🔹 **Материнская плата:** B760 — 10 000 ₽
🔹 **Оперативная память:** 32GB DDR4 — 6 000 ₽
🔹 **SSD:** 1TB NVMe — 6 000 ₽
🔹 **Блок питания:** 650W — 5 000 ₽

💰 **ИТОГО:** 71 000 ₽

💡 **Совет:** Для работы и игр 1080p"""

# --- ФУНКЦИЯ ПРОВЕРКИ СОВМЕСТИМОСТИ ---
async def check_compatibility(cpu: str, gpu: str) -> str:
    prompt = f"""
Ты — эксперт по компьютерному железу. Проверь совместимость:

Процессор: {cpu}
Видеокарта: {gpu}

Ответь в формате:
🔍 РЕЗУЛЬТАТ: [СОВМЕСТИМЫ / НЕ СОВМЕСТИМЫ / ЕСТЬ НЮАНСЫ]
📋 ПОЯСНЕНИЕ: [кратко]
⚠️ УЗКОЕ МЕСТО: [если есть]
💡 СОВЕТ: [что лучше выбрать]
"""
    try:
        response = giga.chat(prompt)
        return response.choices[0].message.content
    except:
        return "❌ Ошибка проверки. Проверь названия компонентов."

# --- ГЕНЕРАЦИЯ СБОРКИ С ЖЕСТКИМ КОНТРОЛЕМ БЮДЖЕТА ---
async def generate_pc_build_with_budget(purpose: str, budget_amount: int, preferences: str = "") -> str:
    """Генерирует сборку строго под указанный бюджет"""
    
    purpose_names = {
        "games": "игр",
        "work": "офисной работы",
        "creative": "видеомонтажа и 3D",
        "universal": "универсальный"
    }
    
    # Если бюджет меньше 30к — сразу выдаем готовую сборку
    if budget_amount < 30000:
        return get_fixed_build(budget_amount, purpose)
    
    # Определяем категорию для промпта
    if budget_amount <= 50000:
        budget_limit = 50000
        budget_text = f"до 50 000 рублей (строго не более {budget_amount})"
    elif budget_amount <= 100000:
        budget_limit = 100000
        budget_text = f"до 100 000 рублей (строго не более {budget_amount})"
    elif budget_amount <= 200000:
        budget_limit = 200000
        budget_text = f"до 200 000 рублей (строго не более {budget_amount})"
    else:
        budget_limit = budget_amount
        budget_text = f"примерно {budget_amount} рублей"
    
    prompt = f"""
Ты — конфигуратор ПК. Собери компьютер для {purpose_names.get(purpose, purpose)}.

ЖЕСТКОЕ ОГРАНИЧЕНИЕ ПО БЮДЖЕТУ:
ИТОГОВАЯ ЦЕНА НЕ ДОЛЖНА ПРЕВЫШАТЬ {budget_limit} РУБЛЕЙ!

Предпочтения: {preferences if preferences else "нет"}

Дай список комплектующих с ценами. Каждая цена должна быть реалистичной для 2026 года.
Формат (строго):
🔹 Процессор: [модель] — [цена] ₽
🔹 Видеокарта: [модель] — [цена] ₽
🔹 Материнская плата: [модель] — [цена] ₽
🔹 Оперативная память: [объем] — [цена] ₽
🔹 SSD: [объем] — [цена] ₽
🔹 Блок питания: [мощность] — [цена] ₽
🔹 Корпус: [модель] — [цена] ₽

💰 ИТОГОВАЯ ЦЕНА: [сумма] ₽ (не более {budget_limit} ₽)

💡 СОВЕТ: [один совет]
"""
    
    try:
        response = giga.chat(prompt)
        result = response.choices[0].message.content
        
        # Проверяем итоговую цену
        price_match = re.search(r'ИТОГОВАЯ ЦЕНА.*?(\d[\d\s]*)\s*₽', result)
        if price_match:
            price_str = price_match.group(1).replace(' ', '')
            try:
                price = int(price_str)
                if price > budget_limit:
                    # Если GigaChat превысил бюджет — выдаем готовую сборку
                    return get_fixed_build(budget_limit, purpose)
            except:
                pass
        return result
    except Exception as e:
        logging.error(f"GigaChat error: {e}")
        return get_fixed_build(budget_limit, purpose)

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🖥️ ДОБРО ПОЖАЛОВАТЬ В PC BUILDER BOT!\n\n"
        "🔹 ПОШАГОВАЯ СБОРКА — задам 5 вопросов\n"
        "🔹 БЫСТРАЯ СБОРКА — напишите например: 'игровой пк за 100к'\n"
        "🔹 ПРОВЕРКА СОВМЕСТИМОСТИ — проверю связку процессор + видеокарта\n"
        "🔹 ИНСТРУКЦИЯ — как собрать ПК\n\n"
        "Выберите режим:",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data == "step_build")
async def step_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Вопрос 1 из 5: Для чего ПК?", reply_markup=get_purpose_keyboard())
    await state.set_state(BuildSteps.waiting_for_purpose)
    await callback.answer()

@dp.callback_query(F.data == "quick_build")
async def quick(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🚀 БЫСТРАЯ СБОРКА\n\n"
        "Напишите свой запрос, например:\n"
        "• 'игровой пк за 100 000 рублей'\n"
        "• 'компьютер для монтажа до 150к'\n"
        "• 'универсальный пк 80000'\n\n"
        "Введите запрос:"
    )
    await state.set_state(BuildSteps.waiting_for_quick_budget)
    await callback.answer()

@dp.callback_query(F.data == "check_compatibility")
async def check_compatibility_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🔍 ПРОВЕРКА СОВМЕСТИМОСТИ\n\n"
        "Напишите связку процессор + видеокарта:\n\n"
        "Пример: Intel i5-12400F и RTX 3060\n"
        "Пример: Ryzen 5 5600 и RX 6600 XT"
    )
    await state.set_state(BuildSteps.waiting_for_compatibility)
    await callback.answer()

@dp.callback_query(F.data == "instruction")
async def instruction(callback: CallbackQuery):
    await callback.message.answer(INSTRUCTION, reply_markup=get_back_to_main())
    await callback.answer()

# --- ПОШАГОВАЯ СБОРКА ---
@dp.callback_query(BuildSteps.waiting_for_purpose, F.data.startswith("purpose_"))
async def step_purpose(callback: CallbackQuery, state: FSMContext):
    await state.update_data(purpose=callback.data.split("_")[1])
    await callback.message.answer("Вопрос 2 из 5: В какие игры?", reply_markup=get_games_keyboard())
    await state.set_state(BuildSteps.waiting_for_games)
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_games, F.data.startswith("games_"))
async def step_games(callback: CallbackQuery, state: FSMContext):
    await state.update_data(games=callback.data.split("_")[1])
    await callback.message.answer("Вопрос 3 из 5: Какие программы?", reply_markup=get_programs_keyboard())
    await state.set_state(BuildSteps.waiting_for_programs)
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_programs, F.data.startswith("prog_"))
async def step_programs(callback: CallbackQuery, state: FSMContext):
    await state.update_data(programs=callback.data.split("_")[1])
    await callback.message.answer("Вопрос 4 из 5: Какой бюджет?", reply_markup=get_budget_keyboard())
    await state.set_state(BuildSteps.waiting_for_budget)
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_budget, F.data.startswith("budget_"))
async def step_budget(callback: CallbackQuery, state: FSMContext):
    budget_key = callback.data.split("_")[1]
    budget_amounts = {"min": 50000, "medium": 100000, "high": 200000, "pro": 300000}
    budget_amount = budget_amounts.get(budget_key, 100000)
    await state.update_data(budget=budget_key, budget_amount=budget_amount)
    await callback.message.answer("Вопрос 5 из 5: Предпочтения по производителям?", reply_markup=get_preferences_keyboard())
    await state.set_state(BuildSteps.waiting_for_preferences)
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_preferences, F.data.startswith("pref_"))
async def step_preferences(callback: CallbackQuery, state: FSMContext):
    await state.update_data(preferences=callback.data.split("_")[1])
    data = await state.get_data()
    text = f"✅ Всё верно?\n\n🎯 Назначение: {data.get('purpose')}\n🎮 Игры: {data.get('games')}\n💻 Программы: {data.get('programs')}\n💰 Бюджет: {data.get('budget_amount')} ₽\n⚙️ Предпочтения: {data.get('preferences')}"
    await callback.message.answer(text, reply_markup=get_confirm_keyboard())
    await state.set_state(BuildSteps.waiting_for_confirmation)
    await callback.answer()

@dp.callback_query(F.data == "confirm_yes")
async def confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg = await callback.message.answer("🤔 Собираю ПК под ваш бюджет...")
    
    budget_amount = data.get('budget_amount', 100000)
    purpose = data.get('purpose', 'games')
    preferences = data.get('preferences', '')
    
    build = await generate_pc_build_with_budget(purpose, budget_amount, preferences)
    await msg.delete()
    await callback.message.answer(build, reply_markup=get_back_to_main())
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "confirm_restart")
async def restart(callback: CallbackQuery, state: FSMContext):
    await step_start(callback, state)

@dp.callback_query(F.data == "main_menu")
async def menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Главное меню:", reply_markup=get_main_keyboard())
    await callback.message.delete()
    await callback.answer()

# --- БЫСТРАЯ СБОРКА (С ИЗВЛЕЧЕНИЕМ БЮДЖЕТА) ---
@dp.message(BuildSteps.waiting_for_quick_budget)
async def quick_process_with_budget(message: Message, state: FSMContext):
    user_query = message.text
    
    # Извлекаем бюджет из запроса
    budget_amount = extract_budget_from_query(user_query)
    
    if budget_amount is None:
        # Если бюджет не указан — спрашиваем
        await message.answer(
            "💰 Не указан бюджет.\n\n"
            "Напишите бюджет в формате:\n"
            "• 100 000 рублей\n"
            "• 80 тыс\n"
            "• 50000\n\n"
            "Или просто укажите сумму:"
        )
        return
    
    msg = await message.answer(f"🤔 Собираю ПК под бюджет {budget_amount} ₽...")
    
    # Определяем тип ПК из запроса
    query_lower = user_query.lower()
    if "игр" in query_lower or "game" in query_lower:
        purpose = "games"
    elif "монтаж" in query_lower or "видео" in query_lower or "3d" in query_lower:
        purpose = "creative"
    elif "работ" in query_lower or "офис" in query_lower:
        purpose = "work"
    else:
        purpose = "universal"
    
    build = await generate_pc_build_with_budget(purpose, budget_amount, "")
    await msg.delete()
    await message.answer(build, reply_markup=get_back_to_main())
    await state.clear()

# --- ПРОВЕРКА СОВМЕСТИМОСТИ ---
@dp.message(BuildSteps.waiting_for_compatibility)
async def compatibility_process(message: Message, state: FSMContext):
    components = message.text
    msg = await message.answer("🔍 Проверяю совместимость...")
    
    # Пытаемся извлечь процессор и видеокарту
    parts = components.split("и")
    if len(parts) >= 2:
        cpu = parts[0].strip()
        gpu = parts[1].strip()
    else:
        # Если нет "и", пробуем разделить по запятой
        parts = components.split(",")
        if len(parts) >= 2:
            cpu = parts[0].strip()
            gpu = parts[1].strip()
        else:
            cpu = components.strip()
            gpu = "не указана"
    
    result = await check_compatibility(cpu, gpu)
    await msg.delete()
    await message.answer(result, reply_markup=get_compatibility_keyboard())
    await state.clear()

# --- ЗАПУСК ---
async def main():
    print("🤖 PC BUILDER БОТ ЗАПУЩЕН!")
    print("✅ Используется GigaChat")
    print("✅ Жесткий контроль бюджета включен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
