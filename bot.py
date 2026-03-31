import asyncio
import logging
import re
import random
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
    waiting_for_purpose = State()
    waiting_for_budget = State()

# --- КЛАВИАТУРЫ ---
def get_main_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🛠️ ПОШАГОВАЯ СБОРКА", callback_data="step_build")],
        [InlineKeyboardButton(text="🚀 БЫСТРАЯ СБОРКА", callback_data="quick_build")],
        [InlineKeyboardButton(text="🔍 ПРОВЕРКА СОВМЕСТИМОСТИ", callback_data="check_compatibility")],
        [InlineKeyboardButton(text="📖 ИНСТРУКЦИЯ", callback_data="instruction_start")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_instruction_nav_keyboard(current_part: int):
    """Клавиатура навигации для инструкции"""
    buttons = []
    
    nav_buttons = []
    if current_part > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️ НАЗАД", callback_data=f"inst_part_{current_part-1}"))
    if current_part < 3:
        nav_buttons.append(InlineKeyboardButton(text="ДАЛЕЕ ▶️", callback_data=f"inst_part_{current_part+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")])
    
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

def get_step_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🎲 ДРУГУЮ СБОРКУ", callback_data="another_build")],
        [InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_compatibility_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🔄 ПРОВЕРИТЬ ДРУГУЮ СВЯЗКУ", callback_data="check_compatibility")],
        [InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- ИНСТРУКЦИЯ (ПРОСТОЙ ТЕКСТ, БЕЗ MARKDOWN) ---
INSTRUCTION_PART1 = """🔧 СБОРКА ПК — ЧАСТЬ 1/3: ПОДГОТОВКА И ПРОЦЕССОР

🔧 ЧТО НУЖНО:
• Крестовая отвертка PH2
• Термопаста
• Антистатический браслет (желательно)
• Все компоненты

⚡ ПОДГОТОВКА:
1. Заземлись — коснись батареи или корпуса выключенного ПК
2. Распакуй все детали на чистый стол
3. Проверь, что всё на месте

🔩 ШАГ 1: УСТАНОВКА ПРОЦЕССОРА
1. На материнской плате найди сокет (квадратный разъем)
2. Подними металлическую защелку
3. Найди золотой треугольник на процессоре и такой же на сокете
4. Совмести их и аккуратно положи процессор (он должен лечь без усилий!)
5. Опусти защелку

🔩 ШАГ 2: УСТАНОВКА ОПЕРАТИВНОЙ ПАМЯТИ
1. Открой защелки по краям слотов RAM
2. Для двух планок используй слоты 2 и 4 (считая от процессора)
3. Вставь планку до щелчка — защелки закроются сами

🔩 ШАГ 3: УСТАНОВКА КУЛЕРА
1. Если на кулере нет термопасты — нанеси тонкий слой на центр процессора (размером с горошину)
2. Установи кулер на процессор
3. Закрепи кулер (обычно прикручивается)
4. Подключи провод кулера к разъему CPU_FAN на материнской плате"""

INSTRUCTION_PART2 = """🖥️ СБОРКА ПК — ЧАСТЬ 2/3: КОРПУС, ПИТАНИЕ, НАКОПИТЕЛЬ

🔩 ШАГ 4: ПОДГОТОВКА КОРПУСА
1. Сними обе боковые крышки корпуса
2. Проверь, что в корпусе есть медные стойки для материнской платы
3. Если нет — вкрути их в отмеченные отверстия

🔩 ШАГ 5: МАТЕРИНСКАЯ ПЛАТА В КОРПУС
1. Вставь заглушку портов (идет с мат. платой) в заднюю панель корпуса
2. Аккуратно опусти плату на стойки
3. Закрути винты (не перетягивай!)

🔩 ШАГ 6: БЛОК ПИТАНИЯ
1. Установи БП в отведенное место (обычно снизу или сверху сзади)
2. Закрепи 4 винтами
3. Проложи кабели питания через отверстия на заднюю сторону корпуса

🔩 ШАГ 7: УСТАНОВКА SSD
• M.2 SSD: вставь в слот под углом 30°, прижми, закрепи винтом
• SATA SSD: закрепи в отсеке, подключи SATA-кабель и питание"""

INSTRUCTION_PART3 = """💻 СБОРКА ПК — ЧАСТЬ 3/3: ВИДЕОКАРТА, ПРОВОДА, ЗАПУСК

🔩 ШАГ 8: ВИДЕОКАРТА
1. Выломай металлические заглушки на задней панели корпуса (2-3 шт)
2. Открой защелку на PCI-E слоте материнской платы
3. Аккуратно вставь видеокарту до щелчка
4. Закрепи винтами к корпусу
5. Подключи кабели питания от БП (6 или 8 pin)

🔩 ШАГ 9: ПОДКЛЮЧЕНИЕ ПРОВОДОВ

Основные кабели:
• 24-pin — питание материнской платы (самый широкий)
• 4/8-pin CPU — питание процессора (вверху слева)

Передняя панель (смотри схему на мат. плате!):
• POWER SW — кнопка включения
• RESET SW — перезагрузка
• HDD LED — индикатор диска
• POWER LED — индикатор питания

Дополнительно:
• USB 3.0 (синий), USB 2.0 (черный), AUDIO

🔩 ШАГ 10: КАБЕЛЬ-МЕНЕДЖМЕНТ
1. Собери провода на задней стороне корпуса
2. Затяни стяжками, чтобы не мешали воздуху
3. Закрой заднюю крышку

💻 ПЕРВЫЙ ЗАПУСК
1. Подключи кабель питания к БП
2. Включи тумблер на БП (положение I)
3. Подключи монитор к видеокарте!
4. Нажми кнопку включения
5. Если всё работает — установи Windows с флешки
6. Установи драйвера (сначала чипсет, потом видеокарту)

⚠️ НЕ ВКЛЮЧАЕТСЯ?
• Проверь тумблер на БП
• Проверь кнопку POWER SW
• Проверь кабель питания
• Если вентиляторы крутятся, но нет картинки — монитор подключен к видеокарте?

📹 ВИДЕО: на YouTube набери "сборка ПК" — Ремонтяш, PRO Hi-Tech

💡 СОВЕТ: Если не уверен — обратись в сервисный центр (2000-3000₽)"""

# --- ХРАНИЛИЩЕ ---
last_build_data = {}

# --- ФУНКЦИЯ ИЗВЛЕЧЕНИЯ БЮДЖЕТА ---
def extract_budget(text: str) -> int:
    text = text.lower().replace(' ', '').replace(',', '')
    
    patterns = [
        (r'(\d+)к', 1000),
        (r'(\d+)тыс', 1000),
        (r'(\d+)тысяч', 1000),
        (r'(\d+)руб', 1),
        (r'(\d+)₽', 1),
        (r'(\d{4,6})', 1),
    ]
    
    for pattern, multiplier in patterns:
        match = re.search(pattern, text)
        if match:
            amount = int(match.group(1))
            result = amount * multiplier
            if 20000 <= result <= 500000:
                return result
    
    numbers = re.findall(r'\d+', text)
    for num in numbers:
        n = int(num)
        if 20000 <= n <= 500000:
            return n
    
    return None

# --- РАНДОМНАЯ ГЕНЕРАЦИЯ СБОРКИ ---
async def generate_random_build(purpose: str, budget: int) -> str:
    purpose_names = {
        "games": "игр. Важно: мощная видеокарта",
        "work": "офисной работы. Важен SSD и ОЗУ",
        "creative": "видеомонтажа и 3D. Важны: процессор, ОЗУ",
        "universal": "универсального использования"
    }
    
    random_style = random.choice([
        "сбалансированную", "максимально производительную", 
        "экономичную", "с запасом на апгрейд"
    ])
    
    prompt = f"""
Собери {random_style} сборку ПК для {purpose_names.get(purpose, purpose)}.
Бюджет: {budget} рублей. НЕ ПРЕВЫШАТЬ!

Формат:
🎯 СБОРКА ПК

🔹 Процессор: [модель] — [цена] ₽
🔹 Видеокарта: [модель] — [цена] ₽
🔹 Материнская плата: [модель] — [цена] ₽
🔹 Оперативная память: [объем] — [цена] ₽
🔹 SSD: [объем] — [цена] ₽
🔹 Блок питания: [мощность] — [цена] ₽
🔹 Корпус: [модель] — [цена] ₽

💰 ИТОГО: [сумма] ₽ (не более {budget} ₽)

💡 СОВЕТ: [один совет]
"""
    try:
        response = giga.chat(prompt)
        result = response.choices[0].message.content
        
        price_match = re.search(r'ИТОГО.*?(\d[\d\s]*)\s*₽', result)
        if price_match:
            price_str = price_match.group(1).replace(' ', '')
            try:
                if int(price_str) > budget:
                    return f"🎮 ИГРОВОЙ ПК (до {budget} ₽)\n\n🔹 Процессор: Intel i5-12400F — 10 000 ₽\n🔹 Видеокарта: RTX 3060 — 32 000 ₽\n🔹 Материнская плата: B660 — 8 000 ₽\n🔹 ОЗУ: 32GB DDR4 — 6 000 ₽\n🔹 SSD: 1TB NVMe — 6 000 ₽\n🔹 БП: 650W — 5 000 ₽\n🔹 Корпус: с обдувом — 5 000 ₽\n\n💰 ИТОГО: 72 000 ₽"
            except:
                pass
        return result
    except:
        return f"🎮 ИГРОВОЙ ПК (до {budget} ₽)\n\n🔹 Процессор: Intel i5-12400F — 10 000 ₽\n🔹 Видеокарта: RTX 3060 — 32 000 ₽\n🔹 Материнская плата: B660 — 8 000 ₽\n🔹 ОЗУ: 32GB DDR4 — 6 000 ₽\n🔹 SSD: 1TB NVMe — 6 000 ₽\n🔹 БП: 650W — 5 000 ₽\n🔹 Корпус: с обдувом — 5 000 ₽\n\n💰 ИТОГО: 72 000 ₽"

# --- ПРОВЕРКА СОВМЕСТИМОСТИ ---
async def check_compatibility(cpu: str, gpu: str) -> str:
    prompt = f"""
Проверь совместимость:
Процессор: {cpu}
Видеокарта: {gpu}

Ответь:
🔍 РЕЗУЛЬТАТ: [Совместимы / Не совместимы]
📋 ПОЧЕМУ: [одно предложение]
⚠️ УЗКОЕ МЕСТО: [если есть]
💡 СОВЕТ: [что лучше]
"""
    try:
        response = giga.chat(prompt)
        return response.choices[0].message.content
    except:
        return "❌ Ошибка. Проверь названия компонентов."

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🖥️ PC BUILDER БОТ\n\n"
        "🔹 ПОШАГОВАЯ СБОРКА\n"
        "🔹 БЫСТРАЯ СБОРКА — напиши: игровой пк 80к\n"
        "🔹 ПРОВЕРКА СОВМЕСТИМОСТИ\n"
        "🔹 ИНСТРУКЦИЯ — пошаговый гайд\n\n"
        "Выбери:",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data == "step_build")
async def step_build_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Выбери тип ПК:", reply_markup=get_purpose_keyboard())
    await state.set_state(BuildSteps.waiting_for_purpose)
    await callback.answer()

@dp.callback_query(F.data == "quick_build")
async def quick_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🚀 БЫСТРАЯ СБОРКА\n\nНапиши: игровой пк 80к"
    )
    await state.set_state(BuildSteps.waiting_for_quick)
    await callback.answer()

@dp.callback_query(F.data == "check_compatibility")
async def compatibility_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🔍 ПРОВЕРКА СОВМЕСТИМОСТИ\n\nНапиши: Intel i5-12400F и RTX 3060"
    )
    await state.set_state(BuildSteps.waiting_for_compatibility)
    await callback.answer()

@dp.callback_query(F.data == "instruction_start")
async def instruction_start(callback: CallbackQuery):
    """Начинает инструкцию с 1 части"""
    await callback.message.answer(
        INSTRUCTION_PART1,
        reply_markup=get_instruction_nav_keyboard(1)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("inst_part_"))
async def instruction_navigate(callback: CallbackQuery):
    """Навигация по инструкции"""
    part_num = int(callback.data.split("_")[2])
    
    if part_num == 1:
        text = INSTRUCTION_PART1
    elif part_num == 2:
        text = INSTRUCTION_PART2
    else:
        text = INSTRUCTION_PART3
    
    await callback.message.edit_text(
        text,
        reply_markup=get_instruction_nav_keyboard(part_num)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("purpose_"))
async def choose_purpose(callback: CallbackQuery, state: FSMContext):
    purpose = callback.data.split("_")[1]
    await state.update_data(purpose=purpose)
    await callback.message.answer("Выбери бюджет:", reply_markup=get_budget_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("budget_"))
async def choose_budget(callback: CallbackQuery, state: FSMContext):
    budget = int(callback.data.split("_")[1])
    data = await state.get_data()
    purpose = data.get("purpose", "games")
    
    msg = await callback.message.answer(f"🤔 Генерирую сборку под {budget} ₽...")
    
    last_build_data[callback.from_user.id] = {
        "purpose": purpose,
        "budget": budget
    }
    
    build = await generate_random_build(purpose, budget)
    await msg.delete()
    await callback.message.answer(build, reply_markup=get_step_keyboard())
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "another_build")
async def another_build(callback: CallbackQuery):
    user_id = callback.from_user.id
    data = last_build_data.get(user_id)
    
    if not data:
        await callback.message.answer(
            "❌ Не найдены параметры. Выбери сборку заново.",
            reply_markup=get_back_to_main()
        )
        await callback.answer()
        return
    
    purpose = data["purpose"]
    budget = data["budget"]
    
    msg = await callback.message.answer(f"🎲 Генерирую другую сборку под {budget} ₽...")
    build = await generate_random_build(purpose, budget)
    await msg.delete()
    await callback.message.answer(build, reply_markup=get_step_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "🏠 Главное меню:",
        reply_markup=get_main_keyboard()
    )
    await callback.message.delete()
    await callback.answer()

@dp.message(BuildSteps.waiting_for_quick)
async def handle_quick(message: Message, state: FSMContext):
    text = message.text.lower()
    budget = extract_budget(text)
    
    if not budget:
        await message.answer("❌ Не нашел бюджет. Пример: игровой пк 80к")
        return
    
    if "игр" in text:
        purpose = "games"
    elif "монтаж" in text or "видео" in text:
        purpose = "creative"
    else:
        purpose = "games"
    
    msg = await message.answer(f"🤔 Генерирую {purpose} ПК под {budget} ₽...")
    
    last_build_data[message.from_user.id] = {
        "purpose": purpose,
        "budget": budget
    }
    
    build = await generate_random_build(purpose, budget)
    await msg.delete()
    await message.answer(build, reply_markup=get_step_keyboard())
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
    print("✅ Инструкция с кнопками ДАЛЕЕ/НАЗАД (без Markdown)")
    print("✅ Рандомная генерация сборок")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
