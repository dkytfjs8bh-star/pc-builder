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
    waiting_for_quick = State()
    waiting_for_compatibility = State()

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

def get_budget_keyboard():
    buttons = [
        [InlineKeyboardButton(text="💰 ДО 50 000 ₽", callback_data="budget_50000")],
        [InlineKeyboardButton(text="💵 50-100 000 ₽", callback_data="budget_100000")],
        [InlineKeyboardButton(text="💎 100-200 000 ₽", callback_data="budget_200000")],
        [InlineKeyboardButton(text="👑 200 000+ ₽", callback_data="budget_300000")],
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
6. Установи SSD
7. Установи видеокарту (до щелчка)
8. Подключи провода: 24pin, 4/8pin CPU, переднюю панель

💻 ПЕРВЫЙ ЗАПУСК
1. Включи блок питания
2. Нажми кнопку включения
3. Установи Windows

💡 Совет: посмотри видео "сборка ПК" на YouTube
"""

# --- ФУНКЦИЯ ИЗВЛЕЧЕНИЯ БЮДЖЕТА (ПОДДЕРЖИВАЕТ 80к, 80 тыс, 80000) ---
def extract_budget(text: str) -> int:
    """Извлекает бюджет из текста. Понимает: 80к, 80 тыс, 80000, 80 000"""
    text = text.lower().replace(' ', '').replace(',', '')
    
    # Паттерн: число + к / тыс / тысяч / руб
    patterns = [
        (r'(\d+)к', 1000),           # 80к
        (r'(\d+)тыс', 1000),         # 80тыс
        (r'(\d+)тысяч', 1000),       # 80тысяч
        (r'(\d+)руб', 1),            # 80000руб
        (r'(\d+)₽', 1),              # 80000₽
        (r'(\d{4,6})', 1),           # 80000
    ]
    
    for pattern, multiplier in patterns:
        match = re.search(pattern, text)
        if match:
            amount = int(match.group(1))
            result = amount * multiplier
            if 20000 <= result <= 500000:
                return result
    
    # Если нашли просто число без букв
    numbers = re.findall(r'\d+', text)
    for num in numbers:
        n = int(num)
        if 20000 <= n <= 500000:
            return n
    
    return None

# --- ГОТОВЫЕ СБОРКИ ---
def get_build_by_budget(budget: int, purpose: str = "games") -> str:
    if purpose == "games":
        if budget <= 50000:
            return """🎮 **ИГРОВОЙ ПК (до 50 000 ₽)**

🔹 Процессор: Intel Core i3-12100F — 7 500 ₽
🔹 Видеокарта: GTX 1650 4GB — 15 000 ₽
🔹 Материнская плата: H610 — 6 000 ₽
🔹 Оперативная память: 16GB DDR4 — 4 000 ₽
🔹 SSD: 512GB NVMe — 4 000 ₽
🔹 Блок питания: 500W — 3 500 ₽
🔹 Корпус: Aerocool Cylon — 4 000 ₽

💰 ИТОГО: 44 000 ₽"""
        
        elif budget <= 100000:
            return """🎮 **ИГРОВОЙ ПК (50-100 000 ₽)**

🔹 Процессор: Intel Core i5-12400F — 10 000 ₽
🔹 Видеокарта: RTX 3060 12GB — 32 000 ₽
🔹 Материнская плата: B660 — 8 000 ₽
🔹 Оперативная память: 32GB DDR4 — 6 000 ₽
🔹 SSD: 1TB NVMe — 6 000 ₽
🔹 Блок питания: 650W — 5 000 ₽
🔹 Корпус: с обдувом — 5 000 ₽

💰 ИТОГО: 72 000 ₽"""
        
        elif budget <= 200000:
            return """🎮 **ИГРОВОЙ ПК (100-200 000 ₽)**

🔹 Процессор: Intel i7-13700K — 35 000 ₽
🔹 Видеокарта: RTX 4070 Ti Super — 85 000 ₽
🔹 Материнская плата: Z790 — 18 000 ₽
🔹 Оперативная память: 32GB DDR5 — 12 000 ₽
🔹 SSD: 2TB NVMe — 12 000 ₽
🔹 Блок питания: 850W Gold — 10 000 ₽
🔹 Корпус: NZXT H7 Flow — 8 000 ₽

💰 ИТОГО: 180 000 ₽"""
        
        else:
            return """🎮 **ИГРОВОЙ ПК (от 200 000 ₽)**

🔹 Процессор: Intel i9-14900K — 55 000 ₽
🔹 Видеокарта: RTX 4080 Super — 120 000 ₽
🔹 Материнская плата: Z790 — 25 000 ₽
🔹 Оперативная память: 64GB DDR5 — 20 000 ₽
🔹 SSD: 4TB NVMe — 25 000 ₽
🔹 Блок питания: 1000W Platinum — 18 000 ₽
🔹 Корпус: Lian Li O11 — 12 000 ₽

💰 ИТОГО: 275 000 ₽"""
    
    else:
        return """💻 **УНИВЕРСАЛЬНЫЙ ПК**

🔹 Процессор: Intel Core i5-13400F — 12 000 ₽
🔹 Видеокарта: RTX 3060 12GB — 32 000 ₽
🔹 Материнская плата: B760 — 10 000 ₽
🔹 Оперативная память: 32GB DDR4 — 6 000 ₽
🔹 SSD: 1TB NVMe — 6 000 ₽
🔹 Блок питания: 650W — 5 000 ₽

💰 ИТОГО: 71 000 ₽"""

# --- ПРОВЕРКА СОВМЕСТИМОСТИ ---
async def check_compatibility(cpu: str, gpu: str) -> str:
    prompt = f"""
Проверь совместимость:
Процессор: {cpu}
Видеокарта: {gpu}

Ответь кратко в формате:
🔍 РЕЗУЛЬТАТ: [Совместимы / Не совместимы / Есть нюансы]
📋 ПОЧЕМУ: [одно предложение]
⚠️ УЗКОЕ МЕСТО: [если есть]
💡 СОВЕТ: [что лучше выбрать вместо]
"""
    try:
        response = giga.chat(prompt)
        return response.choices[0].message.content
    except:
        return "❌ Ошибка. Проверь названия компонентов."

# --- ГЕНЕРАЦИЯ СБОРКИ ---
async def generate_build(purpose: str, budget: int) -> str:
    purpose_names = {"games": "игр", "work": "работы", "creative": "монтажа", "universal": "универсальный"}
    
    prompt = f"""
Собери ПК для {purpose_names.get(purpose, purpose)}.
Бюджет: {budget} рублей. Не превышать!

Формат:
🔹 Процессор: [модель] — [цена] ₽
🔹 Видеокарта: [модель] — [цена] ₽
🔹 Материнская плата: [модель] — [цена] ₽
🔹 Оперативная память: [объем] — [цена] ₽
🔹 SSD: [объем] — [цена] ₽
🔹 Блок питания: [мощность] — [цена] ₽
🔹 Корпус: [модель] — [цена] ₽

💰 ИТОГО: [сумма] ₽
"""
    try:
        response = giga.chat(prompt)
        result = response.choices[0].message.content
        price_match = re.search(r'ИТОГО.*?(\d[\d\s]*)\s*₽', result)
        if price_match:
            price_str = price_match.group(1).replace(' ', '')
            try:
                if int(price_str) > budget:
                    return get_build_by_budget(budget, purpose)
            except:
                pass
        return result
    except:
        return get_build_by_budget(budget, purpose)

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🖥️ *PC BUILDER БОТ*\n\n"
        "🔹 ПОШАГОВАЯ СБОРКА\n"
        "🔹 БЫСТРАЯ СБОРКА — напиши например: игровой пк 80к\n"
        "🔹 ПРОВЕРКА СОВМЕСТИМОСТИ\n"
        "🔹 ИНСТРУКЦИЯ\n\n"
        "Выбери:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "step_build")
async def step_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Тип ПК:", reply_markup=get_purpose_keyboard())
    await state.set_state(BuildSteps.waiting_for_quick)
    await callback.answer()

@dp.callback_query(F.data == "quick_build")
async def quick_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🚀 *БЫСТРАЯ СБОРКА*\n\n"
        "Напиши в одном сообщении:\n"
        "• тип ПК (игровой/рабочий/монтаж)\n"
        "• бюджет\n\n"
        "Примеры:\n"
        "• игровой пк 80к\n"
        "• пк для монтажа 120 тыс\n"
        "• рабочий пк 50000\n\n"
        "Или просто укажи бюджет:",
        parse_mode="Markdown"
    )
    await state.set_state(BuildSteps.waiting_for_quick)
    await callback.answer()

@dp.callback_query(F.data == "check_compatibility")
async def compatibility_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🔍 *ПРОВЕРКА СОВМЕСТИМОСТИ*\n\n"
        "Напиши связку процессор + видеокарта\n\n"
        "Пример: Intel i5-12400F и RTX 3060",
        parse_mode="Markdown"
    )
    await state.set_state(BuildSteps.waiting_for_compatibility)
    await callback.answer()

@dp.callback_query(F.data == "instruction")
async def instruction(callback: CallbackQuery):
    await callback.message.answer(INSTRUCTION, reply_markup=get_back_to_main())
    await callback.answer()

@dp.callback_query(F.data.startswith("purpose_"))
async def choose_purpose(callback: CallbackQuery, state: FSMContext):
    purpose = callback.data.split("_")[1]
    await state.update_data(purpose=purpose)
    await callback.message.answer("Бюджет:", reply_markup=get_budget_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("budget_"))
async def choose_budget(callback: CallbackQuery, state: FSMContext):
    budget = int(callback.data.split("_")[1])
    data = await state.get_data()
    purpose = data.get("purpose", "games")
    
    msg = await callback.message.answer("🤔 Собираю...")
    build = await generate_build(purpose, budget)
    await msg.delete()
    await callback.message.answer(build, reply_markup=get_back_to_main())
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Главное меню:", reply_markup=get_main_keyboard())
    await callback.message.delete()
    await callback.answer()

@dp.message(BuildSteps.waiting_for_quick)
async def handle_quick(message: Message, state: FSMContext):
    text = message.text.lower()
    
    # Извлекаем бюджет
    budget = extract_budget(text)
    
    if not budget:
        await message.answer(
            "❌ Не нашел бюджет.\n\n"
            "Напиши в формате:\n"
            "• игровой пк 80к\n"
            "• пк для монтажа 120 тыс\n"
            "• 50000\n\n"
            "Пример: игровой пк 100к"
        )
        return
    
    # Определяем тип ПК
    if "игр" in text or "game" in text:
        purpose = "games"
    elif "монтаж" in text or "видео" in text or "3d" in text:
        purpose = "creative"
    elif "работ" in text or "офис" in text:
        purpose = "work"
    else:
        purpose = "games"
    
    msg = await message.answer(f"🤔 Собираю {purpose} ПК под {budget} ₽...")
    build = await generate_build(purpose, budget)
    await msg.delete()
    await message.answer(build, reply_markup=get_back_to_main())
    await state.clear()

@dp.message(BuildSteps.waiting_for_compatibility)
async def handle_compatibility(message: Message, state: FSMContext):
    text = message.text
    parts = text.split("и")
    if len(parts) >= 2:
        cpu = parts[0].strip()
        gpu = parts[1].strip()
    else:
        await message.answer("❌ Формат: Intel i5-12400F и RTX 3060")
        return
    
    msg = await message.answer("🔍 Проверяю...")
    result = await check_compatibility(cpu, gpu)
    await msg.delete()
    await message.answer(result, reply_markup=get_compatibility_keyboard())
    await state.clear()

async def main():
    print("🤖 PC BUILDER БОТ ЗАПУЩЕН!")
    print("✅ Понимает форматы: 80к, 80 тыс, 80000")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
