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

def get_instruction_nav_keyboard(current_part: int):
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

# --- ИНСТРУКЦИЯ (3 ЧАСТИ) ---
INSTRUCTION_PART1 = """🔧 *СБОРКА ПК — ЧАСТЬ 1/3: ПОДГОТОВКА И ПРОЦЕССОР*

🔧 *ЧТО НУЖНО:*
• Крестовая отвертка PH2
• Термопаста
• Антистатический браслет
• Все компоненты

⚡ *ПОДГОТОВКА:*
1. Заземлись — коснись батареи
2. Распакуй детали на чистый стол

🔩 *ШАГ 1: ПРОЦЕССОР*
1. Подними защелку на сокете
2. Найди золотой треугольник на CPU
3. Положи процессор (без усилий)
4. Опусти защелку

🔩 *ШАГ 2: ОПЕРАТИВНАЯ ПАМЯТЬ*
1. Открой защелки на слотах
2. Для 2 планок — слоты 2 и 4
3. Вставь до щелчка

🔩 *ШАГ 3: КУЛЕР*
1. Нанеси термопасту (горошина)
2. Установи кулер
3. Подключи к CPU_FAN"""

INSTRUCTION_PART2 = """🖥️ *СБОРКА ПК — ЧАСТЬ 2/3: КОРПУС, ПИТАНИЕ, SSD*

🔩 *ШАГ 4: КОРПУС*
1. Сними обе боковые крышки
2. Вкрути стойки для мат. платы
3. Вставь заглушку портов

🔩 *ШАГ 5: МАТЕРИНСКАЯ ПЛАТА*
1. Опусти плату на стойки
2. Закрути винты

🔩 *ШАГ 6: БЛОК ПИТАНИЯ*
1. Установи БП в корпус
2. Закрепи винтами
3. Проложи кабели сзади

🔩 *ШАГ 7: SSD*
• M.2 SSD: вставь под углом, закрепи винтом
• SATA SSD: закрепи, подключи кабель и питание"""

INSTRUCTION_PART3 = """💻 *СБОРКА ПК — ЧАСТЬ 3/3: ВИДЕОКАРТА, ПРОВОДА, ЗАПУСК*

🔩 *ШАГ 8: ВИДЕОКАРТА*
1. Выломай заглушки на корпусе
2. Открой защелку на PCI-E слоте
3. Вставь карту до щелчка
4. Закрепи винтами
5. Подключи питание (6 или 8 pin)

🔩 *ШАГ 9: ПРОВОДА*
• 24-pin — питание мат. платы
• 4/8-pin CPU — питание процессора
• POWER SW — кнопка включения
• RESET SW — перезагрузка
• USB, AUDIO

🔩 *ШАГ 10: КАБЕЛИ*
1. Собери провода сзади
2. Затяни стяжками

💻 *ПЕРВЫЙ ЗАПУСК*
1. Включи БП (тумблер I)
2. Нажми кнопку включения
3. Установи Windows
4. Драйвера: чипсет → видеокарта

⚠️ *НЕ ВКЛЮЧАЕТСЯ?*
• Проверь тумблер БП
• Проверь POWER SW
• Проверь питание CPU

💡 *СОВЕТ:* Если не уверен — обратись в сервисный центр (2000-3000₽)"""

# --- ХРАНИЛИЩЕ ---
last_build_data = {}

# --- ФУНКЦИЯ ИЗВЛЕЧЕНИЯ БЮДЖЕТА (С УЧЕТОМ "ДО" И "ЗА") ---
def extract_budget(text: str) -> tuple:
    """
    Возвращает (бюджет, is_max_budget)
    is_max_budget = True если есть слова "до", "не более" (бюджет — максимальный)
    is_max_budget = False если есть "за", "около" (бюджет — ориентир)
    """
    text = text.lower().replace(' ', '').replace(',', '')
    
    # Проверяем наличие слов "до" или "за"
    is_max = "до" in text or "неболее" in text or "меньше" in text
    is_approx = "за" in text or "около" in text or "примерно" in text
    
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
                return result, is_max
    
    numbers = re.findall(r'\d+', text)
    for num in numbers:
        n = int(num)
        if 20000 <= n <= 500000:
            return n, is_max
    
    return None, None

# --- РАНДОМНАЯ ГЕНЕРАЦИЯ СБОРКИ (ПОЛНОСТЬЮ ЧЕРЕЗ GIGACHAT) ---
async def generate_random_build(purpose: str, budget: int, is_max: bool = True) -> str:
    """Генерирует полностью рандомную сборку через GigaChat"""
    
    purpose_names = {
        "games": "игр. Важно: мощная видеокарта, процессор среднего уровня",
        "work": "офисной работы (Word, Excel, браузер, 1С). Важны: быстрый SSD, 16-32GB ОЗУ, встроенная графика или слабая видеокарта",
        "creative": "видеомонтажа и 3D-моделирования. Важны: мощный процессор, 32-64GB ОЗУ, быстрый SSD",
        "universal": "универсального использования (и игры, и работа). Нужен баланс между CPU и GPU"
    }
    
    # Случайный стиль сборки
    random_style = random.choice([
        "сбалансированную", 
        "максимально производительную", 
        "экономичную", 
        "с запасом на будущий апгрейд",
        "тихую",
        "компактную"
    ])
    
    # Формулировка ограничения бюджета
    if is_max:
        budget_constraint = f"ЖЕСТКО: итоговая цена НЕ ДОЛЖНА ПРЕВЫШАТЬ {budget} рублей!"
    else:
        budget_constraint = f"ЖЕЛАТЕЛЬНО уложиться в {budget} рублей, но допустимо немного выше, если оправдано производительностью."
    
    prompt = f"""
Ты — профессиональный конфигуратор ПК. Собери {random_style} сборку для {purpose_names.get(purpose, purpose)}.

{budget_constraint}

Рекомендации для разнообразия:
- Рассмотри разные бренды (Intel/AMD для CPU, NVIDIA/AMD для GPU)
- Разные форм-факторы (ATX, mATX)
- Разные стили сборки

Дай список КОНКРЕТНЫХ моделей с ценами.
Каждая цена должна быть реалистичной для рынка 2026 года.

Формат ответа (строго соблюдай, используй эмодзи):

🎯 **СБОРКА ПК** ({random_style})

🔹 **Процессор:** [модель] — [цена] ₽
🔹 **Видеокарта:** [модель] — [цена] ₽
🔹 **Материнская плата:** [модель] — [цена] ₽
🔹 **Оперативная память:** [объем] [тип] — [цена] ₽
🔹 **SSD (накопитель):** [объем] [тип] — [цена] ₽
🔹 **Блок питания:** [мощность] [сертификат] — [цена] ₽
🔹 **Корпус:** [модель] — [цена] ₽

💰 **ИТОГОВАЯ ЦЕНА:** [сумма] ₽

💡 **СОВЕТ:** [один важный совет по сборке или выбору компонентов]

⚠️ *Цены примерные, актуальны на 2026 год.*
"""
    
    try:
        response = giga.chat(prompt)
        result = response.choices[0].message.content
        
        # Проверяем, что цена в пределах бюджета (если is_max)
        if is_max:
            price_match = re.search(r'ИТОГОВАЯ ЦЕНА.*?(\d[\d\s]*)\s*₽', result)
            if price_match:
                price_str = price_match.group(1).replace(' ', '')
                try:
                    price = int(price_str)
                    if price > budget:
                        # Если превысил — генерируем еще раз с усиленным требованием
                        return await generate_random_build_strict(purpose, budget)
                except:
                    pass
        return result
        
    except Exception as e:
        logging.error(f"GigaChat error: {e}")
        return await generate_random_build_strict(purpose, budget)

async def generate_random_build_strict(purpose: str, budget: int) -> str:
    """Строгая генерация с повторным промптом если бюджет превышен"""
    
    purpose_names = {
        "games": "игр",
        "work": "офисной работы",
        "creative": "видеомонтажа и 3D",
        "universal": "универсального использования"
    }
    
    prompt = f"""
Собери сборку ПК для {purpose_names.get(purpose, purpose)}.
Бюджет: {budget} рублей. КАТЕГОРИЧЕСКИ НЕ ПРЕВЫШАТЬ!
Сделай итоговую цену на 5-10% ниже бюджета для запаса.

Формат:
🎯 **СБОРКА ПК**

🔹 **Процессор:** [модель] — [цена] ₽
🔹 **Видеокарта:** [модель] — [цена] ₽
🔹 **Материнская плата:** [модель] — [цена] ₽
🔹 **Оперативная память:** [объем] — [цена] ₽
🔹 **SSD:** [объем] — [цена] ₽
🔹 **Блок питания:** [мощность] — [цена] ₽
🔹 **Корпус:** [модель] — [цена] ₽

💰 **ИТОГО:** [сумма] ₽ (не более {budget} ₽)

💡 **СОВЕТ:** [один совет]
"""
    try:
        response = giga.chat(prompt)
        return response.choices[0].message.content
    except:
        return f"❌ Ошибка генерации. Попробуйте другой бюджет."

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
💡 СОВЕТ: [что лучше выбрать]
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
        "🖥️ *PC BUILDER БОТ*\n\n"
        "🔹 ПОШАГОВАЯ СБОРКА\n"
        "🔹 БЫСТРАЯ СБОРКА — напиши: рабочий пк до 80к\n"
        "🔹 ПРОВЕРКА СОВМЕСТИМОСТИ\n"
        "🔹 ИНСТРУКЦИЯ — пошаговый гайд\n\n"
        "Выбери:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
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
        "🚀 *БЫСТРАЯ СБОРКА*\n\n"
        "Напиши в формате:\n"
        "• рабочий пк до 80к\n"
        "• игровой пк за 100к\n"
        "• пк для монтажа 120 тысяч\n\n"
        "Или просто: 50000",
        parse_mode="Markdown"
    )
    await state.set_state(BuildSteps.waiting_for_quick)
    await callback.answer()

@dp.callback_query(F.data == "check_compatibility")
async def compatibility_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🔍 *ПРОВЕРКА СОВМЕСТИМОСТИ*\n\nНапиши: Intel i5-12400F и RTX 3060",
        parse_mode="Markdown"
    )
    await state.set_state(BuildSteps.waiting_for_compatibility)
    await callback.answer()

@dp.callback_query(F.data == "instruction_start")
async def instruction_start(callback: CallbackQuery):
    msg = await callback.message.answer(
        INSTRUCTION_PART1,
        reply_markup=get_instruction_nav_keyboard(1),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("inst_part_"))
async def instruction_navigate(callback: CallbackQuery):
    part_num = int(callback.data.split("_")[2])
    if part_num == 1:
        text = INSTRUCTION_PART1
    elif part_num == 2:
        text = INSTRUCTION_PART2
    else:
        text = INSTRUCTION_PART3
    await callback.message.edit_text(
        text,
        reply_markup=get_instruction_nav_keyboard(part_num),
        parse_mode="Markdown"
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
    
    msg = await callback.message.answer(f"🤔 Генерирую {purpose} ПК под {budget} ₽...")
    
    last_build_data[callback.from_user.id] = {
        "purpose": purpose,
        "budget": budget
    }
    
    build = await generate_random_build(purpose, budget, is_max=True)
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
    build = await generate_random_build(purpose, budget, is_max=True)
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
    
    # Извлекаем бюджет с учетом "до" и "за"
    budget, is_max = extract_budget(text)
    
    if not budget:
        await message.answer("❌ Не нашел бюджет. Пример: рабочий пк до 80к")
        return
    
    # Определяем тип ПК (ВАЖНО: для "рабочий" не должно быть "games"!)
    if "игр" in text or "game" in text:
        purpose = "games"
    elif "рабоч" in text or "офис" in text or "work" in text:
        purpose = "work"
    elif "монтаж" in text or "видео" in text or "3d" in text or "creative" in text:
        purpose = "creative"
    elif "универс" in text or "всё" in text:
        purpose = "universal"
    else:
        purpose = "games"  # по умолчанию
    
    msg = await message.answer(f"🤔 Генерирую {purpose} ПК под {budget} ₽...")
    
    last_build_data[message.from_user.id] = {
        "purpose": purpose,
        "budget": budget
    }
    
    build = await generate_random_build(purpose, budget, is_max)
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
    print("✅ Полная рандомизация сборок через GigaChat")
    print("✅ Учет слов 'до' и 'за' для бюджета")
    print("✅ Правильное определение типа ПК")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
