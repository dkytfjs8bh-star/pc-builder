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

# --- КОНФИГУРАЦИЯ (токены вставлены) ---
TELEGRAM_TOKEN = "8011928165:AAGMEjyJ93CLwI0g9zaxkjFnhu6L5Vly4Eo"
GIGACHAT_AUTH = "MDE5ZDQwYjktYzczNC03YmIzLTg2OTItNWQyODZiZThkMWE5OjI5OWE5MzdmLThkZGQtNDdmMS1iY2RjLTdiYjcwODgzZTJlNA=="

# Подключаемся к GigaChat
giga = GigaChat(
    credentials=GIGACHAT_AUTH,
    scope="GIGACHAT_API_PERS",
    verify_ssl_certs=False,
    timeout=60
)

# Подключаем бота
bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

logging.basicConfig(level=logging.INFO)

# --- ВСТРОЕННАЯ ИНСТРУКЦИЯ ---
INSTRUCTION_TEXT = """📖 **КАК СОБРАТЬ КОМПЬЮТЕР САМОСТОЯТЕЛЬНО**

🔧 **ПОДГОТОВКА**
• Купите все компоненты согласно сборке
• Подготовьте стол, хорошее освещение
• Заземлитесь (прикоснитесь к батарее)
• Подготовьте крестовую отвертку

🔩 **УСТАНОВКА ПРОЦЕССОРА**
1. Откройте защелку на материнской плате
2. Вставьте процессор (ориентир — золотой треугольник)
3. Закройте защелку

🔩 **УСТАНОВКА ОЗУ**
1. Откройте защелки на слотах
2. Вставьте планки до щелчка (слоты 2 и 4)

🔩 **УСТАНОВКА КУЛЕРА**
1. Нанесите термопасту (если не нанесена)
2. Закрепите кулер на плате
3. Подключите к CPU_FAN

🔩 **МАТЕРИНСКАЯ ПЛАТА В КОРПУС**
1. Вкрутите стойки в корпус
2. Закрепите плату винтами

🔩 **БЛОК ПИТАНИЯ**
1. Закрепите БП в корпусе
2. Проложите кабели через заднюю стенку

🔩 **УСТАНОВКА SSD**
• M.2 SSD: вставьте под углом, закрепите винтом
• SATA SSD: закрепите, подключите кабель и питание

🔩 **ВИДЕОКАРТА**
1. Выломайте заглушки на корпусе (2 шт)
2. Откройте защелку на PCI-E слоте
3. Вставьте карту до щелчка
4. Закрепите винтами
5. Подключите питание (6 или 8 pin)

🔩 **ПОДКЛЮЧЕНИЕ ПРОВОДОВ**
• 24 pin — питание материнской платы
• 4/8 pin — питание процессора
• Передняя панель: Power SW, Reset SW, HDD LED, Power LED
• USB 3.0, USB 2.0, аудио

🔩 **КАБЕЛЬ-МЕНЕДЖМЕНТ**
• Соберите провода сзади
• Затяните стяжками

💻 **ПЕРВЫЙ ЗАПУСК**
1. Включите БП тумблером (I)
2. Нажмите кнопку включения
3. Установите Windows с флешки
4. Установите драйвера

⚠️ **Если не включается:** проверьте БП, кнопку Power SW, кабели питания

💡 **Совет:** при неуверенности — обратитесь в сервисный центр (2000-3000₽)"""

# --- СОСТОЯНИЯ FSM ---
class BuildSteps(StatesGroup):
    waiting_for_purpose = State()
    waiting_for_games = State()
    waiting_for_programs = State()
    waiting_for_budget = State()
    waiting_for_preferences = State()
    waiting_for_confirmation = State()

# --- КЛАВИАТУРЫ ---
def get_main_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🛠️ ПОШАГОВАЯ СБОРКА", callback_data="step_build")],
        [InlineKeyboardButton(text="🚀 БЫСТРАЯ СБОРКА", callback_data="quick_build")],
        [InlineKeyboardButton(text="📖 ИНСТРУКЦИЯ ПО СБОРКЕ", callback_data="instruction")],
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
        [InlineKeyboardButton(text="🎮 Киберспорт (CS2, Valorant)", callback_data="games_esports")],
        [InlineKeyboardButton(text="🔥 Современные AAA (Cyberpunk, GTA)", callback_data="games_aaa")],
        [InlineKeyboardButton(text="🎲 Инди и старые игры", callback_data="games_indie")],
        [InlineKeyboardButton(text="👾 ВСЕ ПОДРЯД", callback_data="games_all")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_programs_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🎬 Adobe (Premiere, Photoshop)", callback_data="prog_adobe")],
        [InlineKeyboardButton(text="🖌️ 3D (Blender, 3ds Max)", callback_data="prog_3d")],
        [InlineKeyboardButton(text="💻 Программирование", callback_data="prog_dev")],
        [InlineKeyboardButton(text="🔧 Офис и браузер", callback_data="prog_office")],
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

# --- FALLBACK СБОРКИ (на случай ошибки GigaChat) ---
def get_fallback_build(data: dict) -> str:
    """Готовая сборка на случай ошибки или превышения бюджета"""
    
    purpose = data.get('purpose', 'games')
    budget = data.get('budget', 'medium')
    
    if purpose == 'games':
        if budget == 'min':
            return """🎮 **ИГРОВОЙ ПК (до 50 000 ₽)**

🔹 **Процессор:** Intel Core i3-12100F — 7 500 ₽
🔹 **Видеокарта:** GTX 1650 4GB — 15 000 ₽
🔹 **Материнская плата:** H610 — 6 000 ₽
🔹 **Оперативная память:** 16GB DDR4 3200MHz — 4 000 ₽
🔹 **SSD:** 512GB NVMe — 4 000 ₽
🔹 **Блок питания:** 500W 80+ — 3 500 ₽
🔹 **Корпус:** Aerocool Cylon — 4 000 ₽

💰 **ИТОГО:** 44 000 ₽

💡 **Совет:** Отличный бюджетный вариант для 1080p в средних настройках"""
        
        elif budget == 'medium':
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
        
        elif budget == 'high':
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
            return """🎮 **ИГРОВОЙ ПК (200 000+ ₽)**

🔹 **Процессор:** Intel i9-14900K / Ryzen 9 7950X3D — 55 000 ₽
🔹 **Видеокарта:** RTX 4080 Super 16GB — 120 000 ₽
🔹 **Материнская плата:** Z790 / X670E — 25 000 ₽
🔹 **Оперативная память:** 64GB DDR5 6000MHz — 20 000 ₽
🔹 **SSD:** 4TB NVMe Gen5 — 25 000 ₽
🔹 **Блок питания:** 1000W Platinum — 18 000 ₽
🔹 **Корпус:** Lian Li O11 Dynamic — 12 000 ₽

💰 **ИТОГО:** 275 000 ₽

💡 **Совет:** Максимальная производительность для 4K и стриминга"""
    
    elif purpose == 'creative':
        if budget == 'min':
            return """🎬 **ПК ДЛЯ МОНТАЖА (до 50 000 ₽)**

🔹 **Процессор:** Intel Core i3-12100F — 7 500 ₽
🔹 **Видеокарта:** GTX 1650 4GB — 15 000 ₽
🔹 **Материнская плата:** H610 — 6 000 ₽
🔹 **Оперативная память:** 16GB DDR4 — 4 000 ₽
🔹 **SSD:** 512GB NVMe — 4 000 ₽
🔹 **Блок питания:** 500W — 3 500 ₽

💰 **ИТОГО:** 40 000 ₽

💡 **Совет:** Базовый уровень для легкого монтажа 1080p"""
        
        elif budget == 'medium':
            return """🎬 **ПК ДЛЯ МОНТАЖА (50-100 000 ₽)**

🔹 **Процессор:** Intel Core i5-13500 — 18 000 ₽
🔹 **Видеокарта:** RTX 3060 12GB — 32 000 ₽
🔹 **Материнская плата:** B760 — 10 000 ₽
🔹 **Оперативная память:** 32GB DDR4 — 6 000 ₽
🔹 **SSD:** 1TB NVMe + 1TB HDD — 8 000 ₽
🔹 **Блок питания:** 650W — 5 000 ₽

💰 **ИТОГО:** 79 000 ₽

💡 **Совет:** Хорош для Premiere, After Effects, Blender"""
        
        else:
            return """🎬 **ПК ДЛЯ МОНТАЖА (100 000+ ₽)**

🔹 **Процессор:** Intel Core i7-13700K — 35 000 ₽
🔹 **Видеокарта:** RTX 4070 12GB — 65 000 ₽
🔹 **Материнская плата:** Z790 — 18 000 ₽
🔹 **Оперативная память:** 64GB DDR5 — 18 000 ₽
🔹 **SSD:** 2TB NVMe Gen4 — 12 000 ₽
🔹 **Блок питания:** 750W Gold — 8 000 ₽

💰 **ИТОГО:** 156 000 ₽

💡 **Совет:** Для 4K-монтажа и сложной 3D-графики"""
    
    elif purpose == 'work':
        return """💼 **РАБОЧИЙ ПК (офис, браузер, 1С)**

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

# --- ГЕНЕРАЦИЯ СБОРКИ ЧЕРЕЗ GIGACHAT (С ПРОВЕРКОЙ БЮДЖЕТА) ---
async def generate_pc_build(data: dict) -> str:
    purpose_names = {
        "games": "игр",
        "work": "офисной работы",
        "creative": "видеомонтажа и 3D",
        "universal": "универсальный"
    }
    
    budget_names = {
        "min": "до 50 000 рублей (строго не более 50 000)",
        "medium": "от 50 000 до 100 000 рублей (строго не более 100 000)",
        "high": "от 100 000 до 200 000 рублей (строго не более 200 000)",
        "pro": "от 200 000 рублей (бюджет не ограничен)"
    }
    
    # Получаем бюджет для проверки
    budget_key = data.get('budget', 'medium')
    budget_limit = {
        "min": 50000,
        "medium": 100000,
        "high": 200000,
        "pro": 9999999
    }.get(budget_key, 100000)
    
    games_names = {
        "esports": "киберспорт (CS2, Valorant, Dota) — важна высокая частота кадров",
        "aaa": "современные AAA-игры (Cyberpunk, GTA, Starfield) — важна мощная видеокарта",
        "indie": "инди и старые игры — требования к железу минимальны",
        "all": "любые игры — баланс между процессором и видеокартой"
    }
    
    programs_names = {
        "adobe": "Adobe Creative Cloud (Premiere, After Effects, Photoshop) — важны процессор и ОЗУ",
        "3d": "3D-пакеты (Blender, 3ds Max, Maya) — важны видеокарта и ОЗУ",
        "dev": "программирование (IDE, Docker) — важны процессор и ОЗУ",
        "office": "офисные программы (Word, Excel, браузер) — требования минимальны"
    }
    
    # Для быстрой сборки (текстовый запрос)
    if data.get('purpose') == 'quick':
        prompt = f"""
Ты — профессиональный конфигуратор ПК. Пользователь хочет собрать компьютер.

ЗАПРОС ПОЛЬЗОВАТЕЛЯ: {data.get('quick_request', '')}

Подбери оптимальную сборку ПК под этот запрос. Укажи все компоненты с примерными ценами в рублях.
Формат ответа:

🎯 **СБОРКА ПК**

🔹 **Процессор:** [модель] — [цена] ₽
🔹 **Видеокарта:** [модель] — [цена] ₽
🔹 **Материнская плата:** [модель] — [цена] ₽
🔹 **Оперативная память:** [объем] — [цена] ₽
🔹 **SSD:** [объем] — [цена] ₽
🔹 **Блок питания:** [мощность] — [цена] ₽
🔹 **Система охлаждения:** [тип] — [цена] ₽
🔹 **Корпус:** [модель] — [цена] ₽

💰 **ИТОГОВАЯ ЦЕНА:** [сумма] ₽

💡 **СОВЕТ:** [важный совет]
"""
    else:
        prompt = f"""
Ты — профессиональный конфигуратор ПК. Твоя задача — подобрать сборку строго в рамках указанного бюджета.

ПАРАМЕТРЫ ПОЛЬЗОВАТЕЛЯ:
- НАЗНАЧЕНИЕ: {purpose_names.get(data.get('purpose', ''), 'не указано')}
- ИГРЫ: {games_names.get(data.get('games', ''), data.get('games', 'не указаны')) if data.get('games') else 'не указаны'}
- ПРОГРАММЫ: {programs_names.get(data.get('programs', ''), data.get('programs', 'не указаны')) if data.get('programs') else 'не указаны'}
- БЮДЖЕТ: {budget_names.get(data.get('budget', ''), 'любой')}
- ПРЕДПОЧТЕНИЯ: {data.get('preferences', 'нет предпочтений')}

ВАЖНОЕ ПРАВИЛО:
1. ИТОГОВАЯ ЦЕНА СБОРКИ НЕ ДОЛЖНА ПРЕВЫШАТЬ УКАЗАННЫЙ БЮДЖЕТ!
2. Если бюджет до 50 000 — итоговая цена должна быть 45 000-50 000
3. Если бюджет 50-100 000 — итоговая цена должна быть 70 000-95 000
4. Если бюджет 100-200 000 — итоговая цена должна быть 130 000-180 000
5. Если бюджет от 200 000 — цена может быть выше

Формат ответа (строго соблюдай):

🎯 **СБОРКА ПК (строго в рамках бюджета {budget_names.get(data.get('budget', ''), '')})**

🔹 **Процессор:** [модель] — [цена в рублях] — [почему]
🔹 **Видеокарта:** [модель] — [цена в рублях] — [почему]
🔹 **Материнская плата:** [модель] — [цена в рублях] — [почему]
🔹 **Оперативная память:** [объем и тип] — [цена в рублях] — [почему]
🔹 **SSD:** [объем и тип] — [цена в рублях] — [почему]
🔹 **Блок питания:** [мощность] — [цена в рублях] — [почему]
🔹 **Система охлаждения:** [тип] — [цена в рублях] — [почему]
🔹 **Корпус:** [модель] — [цена в рублях] — [почему]

💰 **ИТОГОВАЯ ЦЕНА:** [сумма] рублей (не превышает {budget_limit} ₽)

💡 **СОВЕТ:** [один важный совет]
"""
    
    try:
        response = giga.chat(prompt)
        result = response.choices[0].message.content
        
        # Проверяем, что цена в ответе не превышает бюджет (только для пошаговой сборки)
        if data.get('purpose') != 'quick':
            price_match = re.search(r'ИТОГОВАЯ ЦЕНА.*?(\d[\d\s]*)\s*руб', result)
            if price_match:
                price_str = price_match.group(1).replace(' ', '').replace('₽', '').replace('руб', '')
                try:
                    price = int(price_str)
                    if price > budget_limit and budget_limit < 9999999:
                        # Если цена превышает бюджет — используем готовую сборку
                        return get_fallback_build(data)
                except:
                    pass
        
        return result
        
    except Exception as e:
        logging.error(f"GigaChat error: {e}")
        return get_fallback_build(data)

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🖥️ *ДОБРО ПОЖАЛОВАТЬ В PC BUILDER BOT!*\n\n"
        "Я использую GigaChat от Сбера для подбора сборок ПК.\n\n"
        "🔹 *ПОШАГОВАЯ СБОРКА* — я задам 5 вопросов и подберу конфигурацию\n"
        "🔹 *БЫСТРАЯ СБОРКА* — просто опишите свой запрос\n"
        "🔹 *ИНСТРУКЦИЯ ПО СБОРКЕ* — пошаговое руководство как собрать ПК\n\n"
        "Выберите режим:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "step_build")
async def step_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "🛠️ *ПОШАГОВАЯ СБОРКА*\n\n"
        "**Вопрос 1 из 5:**\n"
        "Для каких задач вам нужен компьютер?",
        reply_markup=get_purpose_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(BuildSteps.waiting_for_purpose)
    await callback.answer()

@dp.callback_query(F.data == "quick_build")
async def quick(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🚀 *БЫСТРАЯ СБОРКА*\n\n"
        "Опишите, какой компьютер вам нужен.\n\n"
        "Примеры:\n"
        "• «Игровой ПК для Cyberpunk 2077, бюджет 100 000 рублей»\n"
        "• «Компьютер для монтажа видео в Premiere Pro, до 150 000»\n\n"
        "Напишите свой запрос:",
        parse_mode="Markdown"
    )
    await state.set_state(BuildSteps.waiting_for_purpose)
    await callback.answer()

@dp.callback_query(F.data == "instruction")
async def instruction(callback: CallbackQuery):
    """Отправляет встроенную инструкцию"""
    await callback.message.answer(
        INSTRUCTION_TEXT,
        reply_markup=get_back_to_main(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_purpose, F.data.startswith("purpose_"))
async def step_purpose(callback: CallbackQuery, state: FSMContext):
    purpose = callback.data.split("_")[1]
    await state.update_data(purpose=purpose)
    
    await callback.message.answer(
        "**Вопрос 2 из 5:**\n"
        "В какие игры планируете играть?",
        reply_markup=get_games_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(BuildSteps.waiting_for_games)
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_games, F.data.startswith("games_"))
async def step_games(callback: CallbackQuery, state: FSMContext):
    games = callback.data.split("_")[1]
    await state.update_data(games=games)
    
    await callback.message.answer(
        "**Вопрос 3 из 5:**\n"
        "Какие программы будете использовать?",
        reply_markup=get_programs_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(BuildSteps.waiting_for_programs)
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_programs, F.data.startswith("prog_"))
async def step_programs(callback: CallbackQuery, state: FSMContext):
    programs = callback.data.split("_")[1]
    await state.update_data(programs=programs)
    
    await callback.message.answer(
        "**Вопрос 4 из 5:**\n"
        "Какой у вас бюджет?",
        reply_markup=get_budget_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(BuildSteps.waiting_for_budget)
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_budget, F.data.startswith("budget_"))
async def step_budget(callback: CallbackQuery, state: FSMContext):
    budget = callback.data.split("_")[1]
    await state.update_data(budget=budget)
    
    await callback.message.answer(
        "**Вопрос 5 из 5:**\n"
        "Есть ли предпочтения по производителям?\n"
        "(можно выбрать 'нет предпочтений')",
        reply_markup=get_preferences_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(BuildSteps.waiting_for_preferences)
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_preferences, F.data.startswith("pref_"))
async def step_preferences(callback: CallbackQuery, state: FSMContext):
    preferences = callback.data.split("_")[1]
    await state.update_data(preferences=preferences)
    
    data = await state.get_data()
    
    summary = (
        "📋 *Вот что вы выбрали:*\n\n"
        f"🎯 Назначение: {data.get('purpose', '-')}\n"
        f"🎮 Игры: {data.get('games', '-')}\n"
        f"💻 Программы: {data.get('programs', '-')}\n"
        f"💰 Бюджет: {data.get('budget', '-')}\n"
        f"⚙️ Предпочтения: {data.get('preferences', '-')}\n\n"
        "✅ Всё верно? Могу собрать ПК под эти параметры."
    )
    
    await callback.message.answer(
        summary,
        reply_markup=get_confirm_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(BuildSteps.waiting_for_confirmation)
    await callback.answer()

@dp.callback_query(F.data == "confirm_yes")
async def confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    loading_msg = await callback.message.answer(
        "🤖 *Анализирую и подбираю оптимальную конфигурацию...*\n\n"
        "⏳ Обычно это занимает 15-30 секунд...",
        parse_mode="Markdown"
    )
    
    build = await generate_pc_build(data)
    
    await loading_msg.delete()
    await callback.message.answer(
        build,
        reply_markup=get_back_to_main(),
        parse_mode="Markdown"
    )
    
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "confirm_restart")
async def restart(callback: CallbackQuery, state: FSMContext):
    await step_start(callback, state)

@dp.callback_query(F.data == "main_menu")
async def menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "🖥️ *ГЛАВНОЕ МЕНЮ*\n\nВыберите режим:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )
    await callback.message.delete()
    await callback.answer()

@dp.message(BuildSteps.waiting_for_purpose)
async def quick_process(message: Message, state: FSMContext):
    msg = await message.answer("🤔 Думаю...")
    data = {"purpose": "quick", "quick_request": message.text}
    build = await generate_pc_build(data)
    await msg.delete()
    await message.answer(build, reply_markup=get_back_to_main(), parse_mode="Markdown")
    await state.clear()

# --- ЗАПУСК ---
async def main():
    print("🤖 PC BUILDER БОТ ЗАПУЩЕН!")
    print("✅ Используется GigaChat")
    print("✅ Инструкция встроена в код (без загрузки с GitHub)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
