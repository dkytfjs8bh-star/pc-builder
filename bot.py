import asyncio
import logging
import os
import re
import requests
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

# Подключаем бота
bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

logging.basicConfig(level=logging.INFO)

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

# --- ИНСТРУКЦИЯ ---
INSTRUCTION_TEXT = """📖 *КАК СОБРАТЬ КОМПЬЮТЕР САМОСТОЯТЕЛЬНО*

🔧 **ПОДГОТОВКА**
• Купите все компоненты
• Подготовьте стол и отвертку
• Заземлитесь (прикоснитесь к батарее)

🔩 **УСТАНОВКА ПРОЦЕССОРА**
1. Откройте защелку на материнской плате
2. Вставьте процессор (ориентир — золотой треугольник)
3. Закройте защелку

🔩 **УСТАНОВКА ОЗУ**
1. Откройте защелки на слотах
2. Вставьте планки до щелчка (слоты 2 и 4)

🔩 **УСТАНОВКА КУЛЕРА**
1. Нанесите термопасту
2. Закрепите кулер на плате
3. Подключите к CPU_FAN

🔩 **МАТЕРИНСКАЯ ПЛАТА В КОРПУС**
1. Вкрутите стойки в корпус
2. Закрепите плату винтами

🔩 **БЛОК ПИТАНИЯ**
1. Закрепите БП в корпусе
2. Проложите кабели

🔩 **УСТАНОВКА SSD**
• M.2 SSD: вставьте под углом, закрепите винтом

🔩 **ВИДЕОКАРТА**
1. Выломайте заглушки
2. Вставьте карту до щелчка
3. Подключите питание

🔩 **ПОДКЛЮЧЕНИЕ ПРОВОДОВ**
• 24 pin — питание платы
• 4/8 pin — питание процессора
• Передняя панель: Power SW, Reset SW

💻 **ПЕРВЫЙ ЗАПУСК**
1. Включите БП
2. Нажмите кнопку включения
3. Установите Windows

💡 *Совет: при неуверенности — обратитесь в сервисный центр*"""

# --- FALLBACK СБОРКИ ---
def get_fallback_build(data: dict) -> str:
    purpose = data.get('purpose', 'games')
    budget = data.get('budget', 'medium')
    
    if purpose == 'games' and budget == 'medium':
        return """🎮 **ИГРОВОЙ ПК (50-100 000 ₽)**

🔹 **Процессор:** Intel Core i5-12400F — 10 000 ₽
🔹 **Видеокарта:** RTX 3060 12GB — 32 000 ₽
🔹 **Материнская плата:** B660 — 8 000 ₽
🔹 **Оперативная память:** 32GB DDR4 — 6 000 ₽
🔹 **SSD:** 1TB NVMe — 6 000 ₽
🔹 **Блок питания:** 650W Bronze — 5 000 ₽
🔹 **Корпус:** с обдувом — 5 000 ₽

💰 **ИТОГО:** 72 000 ₽

💡 **Совет:** Уверенный 1080p Ultra"""
    
    elif purpose == 'games' and budget == 'min':
        return """🎮 **ИГРОВОЙ ПК (до 50 000 ₽)**

🔹 **Процессор:** Intel Core i3-12100F — 7 500 ₽
🔹 **Видеокарта:** GTX 1650 4GB — 15 000 ₽
🔹 **Материнская плата:** H610 — 6 000 ₽
🔹 **Оперативная память:** 16GB DDR4 — 4 000 ₽
🔹 **SSD:** 512GB NVMe — 4 000 ₽
🔹 **Блок питания:** 500W — 3 500 ₽
🔹 **Корпус:** Aerocool Cylon — 4 000 ₽

💰 **ИТОГО:** 44 000 ₽"""
    
    elif purpose == 'creative':
        return """🎬 **ПК ДЛЯ МОНТАЖА (50-100 000 ₽)**

🔹 **Процессор:** Intel Core i5-13500 — 18 000 ₽
🔹 **Видеокарта:** RTX 3060 12GB — 32 000 ₽
🔹 **Материнская плата:** B760 — 10 000 ₽
🔹 **Оперативная память:** 32GB DDR4 — 6 000 ₽
🔹 **SSD:** 1TB NVMe + 1TB HDD — 8 000 ₽
🔹 **Блок питания:** 650W — 5 000 ₽

💰 **ИТОГО:** 79 000 ₽"""
    
    else:
        return """💻 **УНИВЕРСАЛЬНЫЙ ПК (50-100 000 ₽)**

🔹 **Процессор:** Intel Core i5-13400F — 12 000 ₽
🔹 **Видеокарта:** RTX 3060 12GB — 32 000 ₽
🔹 **Материнская плата:** B760 — 10 000 ₽
🔹 **Оперативная память:** 32GB DDR4 — 6 000 ₽
🔹 **SSD:** 1TB NVMe — 6 000 ₽
🔹 **Блок питания:** 650W — 5 000 ₽

💰 **ИТОГО:** 71 000 ₽"""

# --- ГЕНЕРАЦИЯ СБОРКИ ---
async def generate_pc_build(data: dict) -> str:
    purpose_names = {
        "games": "игр",
        "work": "офисной работы",
        "creative": "видеомонтажа и 3D",
        "universal": "универсальный"
    }
    
    budget_names = {
        "min": "до 50 000 рублей",
        "medium": "50 000 - 100 000 рублей",
        "high": "100 000 - 200 000 рублей",
        "pro": "от 200 000 рублей"
    }
    
    budget_key = data.get('budget', 'medium')
    budget_limit = {"min": 50000, "medium": 100000, "high": 200000, "pro": 9999999}.get(budget_key, 100000)
    
    prompt = f"""
Ты — конфигуратор ПК. Собери ПК строго в рамках бюджета.

Параметры:
- Назначение: {purpose_names.get(data.get('purpose', ''), 'не указано')}
- Игры: {data.get('games', 'не указаны')}
- Программы: {data.get('programs', 'не указаны')}
- Бюджет: {budget_names.get(budget_key, 'любой')}
- Предпочтения: {data.get('preferences', 'нет')}

ВАЖНО: итоговая цена НЕ должна превышать {budget_limit} рублей!

Формат ответа:
🎯 **СБОРКА ПК**

🔹 **Процессор:** [модель] — [цена] — [почему]
🔹 **Видеокарта:** [модель] — [цена] — [почему]
🔹 **Материнская плата:** [модель] — [цена] — [почему]
🔹 **Оперативная память:** [объем] — [цена] — [почему]
🔹 **SSD:** [объем] — [цена] — [почему]
🔹 **Блок питания:** [мощность] — [цена] — [почему]

💰 **ИТОГОВАЯ ЦЕНА:** [сумма] рублей

💡 **СОВЕТ:** [один совет]
"""
    
    try:
        response = giga.chat(prompt)
        result = response.choices[0].message.content
        
        # Проверка цены
        price_match = re.search(r'ИТОГОВАЯ ЦЕНА.*?(\d[\d\s]*)\s*руб', result)
        if price_match:
            price_str = price_match.group(1).replace(' ', '')
            try:
                price = int(price_str)
                if price > budget_limit and budget_limit < 9999999:
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
        "🔹 *ПОШАГОВАЯ СБОРКА* — задам 5 вопросов\n"
        "🔹 *БЫСТРАЯ СБОРКА* — опишите запрос\n"
        "🔹 *ИНСТРУКЦИЯ* — как собрать ПК\n\n"
        "Выберите режим:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "step_build")
async def step_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Вопрос 1: Для чего ПК?", reply_markup=get_purpose_keyboard())
    await state.set_state(BuildSteps.waiting_for_purpose)
    await callback.answer()

@dp.callback_query(F.data == "quick_build")
async def quick(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🚀 Напишите свой запрос (например: 'Игровой ПК за 100к')")
    await state.set_state(BuildSteps.waiting_for_purpose)
    await callback.answer()

@dp.callback_query(F.data == "instruction")
async def instruction(callback: CallbackQuery):
    await callback.message.answer(INSTRUCTION_TEXT, reply_markup=get_back_to_main(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_purpose, F.data.startswith("purpose_"))
async def step_purpose(callback: CallbackQuery, state: FSMContext):
    await state.update_data(purpose=callback.data.split("_")[1])
    await callback.message.answer("Вопрос 2: В какие игры?", reply_markup=get_games_keyboard())
    await state.set_state(BuildSteps.waiting_for_games)
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_games, F.data.startswith("games_"))
async def step_games(callback: CallbackQuery, state: FSMContext):
    await state.update_data(games=callback.data.split("_")[1])
    await callback.message.answer("Вопрос 3: Какие программы?", reply_markup=get_programs_keyboard())
    await state.set_state(BuildSteps.waiting_for_programs)
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_programs, F.data.startswith("prog_"))
async def step_programs(callback: CallbackQuery, state: FSMContext):
    await state.update_data(programs=callback.data.split("_")[1])
    await callback.message.answer("Вопрос 4: Какой бюджет?", reply_markup=get_budget_keyboard())
    await state.set_state(BuildSteps.waiting_for_budget)
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_budget, F.data.startswith("budget_"))
async def step_budget(callback: CallbackQuery, state: FSMContext):
    await state.update_data(budget=callback.data.split("_")[1])
    await callback.message.answer("Вопрос 5: Предпочтения?", reply_markup=get_preferences_keyboard())
    await state.set_state(BuildSteps.waiting_for_preferences)
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_preferences, F.data.startswith("pref_"))
async def step_preferences(callback: CallbackQuery, state: FSMContext):
    await state.update_data(preferences=callback.data.split("_")[1])
    data = await state.get_data()
    text = f"✅ Всё верно?\n\n🎯 {data.get('purpose')}\n🎮 {data.get('games')}\n💻 {data.get('programs')}\n💰 {data.get('budget')}\n⚙️ {data.get('preferences')}"
    await callback.message.answer(text, reply_markup=get_confirm_keyboard())
    await state.set_state(BuildSteps.waiting_for_confirmation)
    await callback.answer()

@dp.callback_query(F.data == "confirm_yes")
async def confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg = await callback.message.answer("🤔 Думаю...")
    build = await generate_pc_build(data)
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

@dp.message(BuildSteps.waiting_for_purpose)
async def quick_process(message: Message, state: FSMContext):
    msg = await message.answer("🤔 Думаю...")
    data = {"purpose": "quick", "quick_request": message.text}
    build = await generate_pc_build(data)
    await msg.delete()
    await message.answer(build, reply_markup=get_back_to_main())
    await state.clear()

# --- ЗАПУСК ---
async def main():
    print("🤖 PC BUILDER БОТ ЗАПУЩЕН!")
    print("✅ Используется GigaChat")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
