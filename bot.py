import asyncio
import logging
import os
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

# Ссылка на файл с инструкцией на GitHub (RAW)
INSTRUCTION_URL = "https://raw.githubusercontent.com/dkytfjs8bh-star/pc-builder/main/instruction.txt"

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

# --- ФУНКЦИЯ ПОЛУЧЕНИЯ ИНСТРУКЦИИ С GITHUB ---
async def get_instruction_from_github() -> str:
    """Скачивает инструкцию с GitHub"""
    try:
        response = requests.get(INSTRUCTION_URL, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            return "❌ Не удалось загрузить инструкцию. Попробуйте позже."
    except Exception as e:
        return f"❌ Ошибка загрузки: {e}"

# --- ГЕНЕРАЦИЯ СБОРКИ ---
async def generate_pc_build(data: dict) -> str:
    purpose_names = {
        "games": "игр",
        "work": "офисной работы",
        "creative": "видеомонтажа и 3D",
        "universal": "универсальный"
    }
    
    budget_names = {
        "min": "до 50 000",
        "medium": "50 000 - 100 000",
        "high": "100 000 - 200 000",
        "pro": "от 200 000"
    }
    
    games_names = {
        "esports": "киберспорт (CS2, Valorant, Dota)",
        "aaa": "современные AAA-игры (Cyberpunk, GTA, Starfield)",
        "indie": "инди и старые игры",
        "all": "любые игры"
    }
    
    programs_names = {
        "adobe": "Adobe Creative Cloud (Premiere, After Effects, Photoshop)",
        "3d": "3D-пакеты (Blender, 3ds Max, Maya, Cinema 4D)",
        "dev": "программирование (IDE, Docker)",
        "office": "офисные программы (Word, Excel, браузер)"
    }
    
    prompt = f"""
Ты — профессиональный конфигуратор ПК с 10-летним опытом.

Пользователь хочет собрать компьютер для следующих задач:

1. НАЗНАЧЕНИЕ: {purpose_names.get(data.get('purpose', ''), 'не указано')}
2. ИГРЫ: {games_names.get(data.get('games', ''), data.get('games', 'не указаны')) if data.get('games') else 'не указаны'}
3. ПРОГРАММЫ: {programs_names.get(data.get('programs', ''), data.get('programs', 'не указаны')) if data.get('programs') else 'не указаны'}
4. БЮДЖЕТ: {budget_names.get(data.get('budget', ''), 'любой')} рублей
5. ПРЕДПОЧТЕНИЯ: {data.get('preferences', 'нет предпочтений')}

Дай сборку с комплектующими и ценами. Формат с эмодзи.
"""
    
    try:
        response = giga.chat(prompt)
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"GigaChat error: {e}")
        return f"❌ Ошибка: {e}"

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🖥️ *ДОБРО ПОЖАЛОВАТЬ В PC BUILDER BOT!*\n\n"
        "Я использую GigaChat от Сбера для подбора сборок ПК.\n\n"
        "🔹 *ПОШАГОВАЯ СБОРКА* — я задам 5 вопросов\n"
        "🔹 *БЫСТРАЯ СБОРКА* — опишите свой запрос\n"
        "🔹 *ИНСТРУКЦИЯ ПО СБОРКЕ* — как собрать ПК\n\n"
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
        "Напишите свой запрос (например: 'Игровой ПК за 100к для Cyberpunk')",
        parse_mode="Markdown"
    )
    await state.set_state(BuildSteps.waiting_for_purpose)
    await callback.answer()

@dp.callback_query(F.data == "instruction")
async def instruction(callback: CallbackQuery):
    """Отправляет инструкцию из файла на GitHub"""
    await callback.message.answer("📖 *Загружаю инструкцию...*", parse_mode="Markdown")
    
    instruction_text = await get_instruction_from_github()
    
    await callback.message.answer(
        instruction_text,
        reply_markup=get_back_to_main(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_purpose, F.data.startswith("purpose_"))
async def step_purpose(callback: CallbackQuery, state: FSMContext):
    purpose = callback.data.split("_")[1]
    await state.update_data(purpose=purpose)
    await callback.message.answer("Вопрос 2: В какие игры?", reply_markup=get_games_keyboard())
    await state.set_state(BuildSteps.waiting_for_games)
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_games, F.data.startswith("games_"))
async def step_games(callback: CallbackQuery, state: FSMContext):
    games = callback.data.split("_")[1]
    await state.update_data(games=games)
    await callback.message.answer("Вопрос 3: Какие программы?", reply_markup=get_programs_keyboard())
    await state.set_state(BuildSteps.waiting_for_programs)
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_programs, F.data.startswith("prog_"))
async def step_programs(callback: CallbackQuery, state: FSMContext):
    programs = callback.data.split("_")[1]
    await state.update_data(programs=programs)
    await callback.message.answer("Вопрос 4: Какой бюджет?", reply_markup=get_budget_keyboard())
    await state.set_state(BuildSteps.waiting_for_budget)
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_budget, F.data.startswith("budget_"))
async def step_budget(callback: CallbackQuery, state: FSMContext):
    budget = callback.data.split("_")[1]
    await state.update_data(budget=budget)
    await callback.message.answer("Вопрос 5: Предпочтения?", reply_markup=get_preferences_keyboard())
    await state.set_state(BuildSteps.waiting_for_preferences)
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_preferences, F.data.startswith("pref_"))
async def step_preferences(callback: CallbackQuery, state: FSMContext):
    preferences = callback.data.split("_")[1]
    await state.update_data(preferences=preferences)
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
    await callback.message.answer("🖥️ Главное меню:", reply_markup=get_main_keyboard())
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
