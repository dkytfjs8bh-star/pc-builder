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
    waiting_for_compatibility = State()  # Новое состояние для проверки совместимости

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

# --- ФУНКЦИЯ ПРОВЕРКИ СОВМЕСТИМОСТИ ---
async def check_compatibility(cpu: str, gpu: str) -> str:
    """Проверяет совместимость процессора и видеокарты через GigaChat"""
    
    prompt = f"""
Ты — эксперт по компьютерному железу. Проверь совместимость следующих компонентов:

Процессор: {cpu}
Видеокарта: {gpu}

Ответь в формате:
🔍 РЕЗУЛЬТАТ ПРОВЕРКИ: [СОВМЕСТИМЫ / НЕ СОВМЕСТИМЫ / ЕСТЬ НЮАНСЫ]

📋 ПОЯСНЕНИЕ:
[Краткое объяснение, почему они совместимы или нет]

⚠️ БУТЫЛОЧНОЕ ГОРЛЫШКО:
[Если есть узкое место — какой компонент будет тормозить]

💡 СОВЕТ:
[Что лучше выбрать для оптимальной работы]
"""
    
    try:
        response = giga.chat(prompt)
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Ошибка проверки: {e}\n\nПопробуй переформулировать названия компонентов."

# --- FALLBACK СБОРКИ ---
def get_fallback_build(budget: str) -> str:
    if budget == "min":
        return """🎮 ИГРОВОЙ ПК (до 50 000 ₽)

🔹 Процессор: Intel Core i3-12100F — 7 500 ₽
🔹 Видеокарта: GTX 1650 4GB — 15 000 ₽
🔹 Материнская плата: H610 — 6 000 ₽
🔹 Оперативная память: 16GB DDR4 — 4 000 ₽
🔹 SSD: 512GB NVMe — 4 000 ₽
🔹 Блок питания: 500W — 3 500 ₽
🔹 Корпус: Aerocool Cylon — 4 000 ₽

💰 ИТОГО: 44 000 ₽

💡 Совет: Отличный бюджетный вариант для 1080p"""
    
    elif budget == "high":
        return """🎮 ИГРОВОЙ ПК (100-200 000 ₽)

🔹 Процессор: Intel i7-13700K — 35 000 ₽
🔹 Видеокарта: RTX 4070 Ti Super — 85 000 ₽
🔹 Материнская плата: Z790 — 18 000 ₽
🔹 Оперативная память: 32GB DDR5 — 12 000 ₽
🔹 SSD: 2TB NVMe — 12 000 ₽
🔹 Блок питания: 850W Gold — 10 000 ₽
🔹 Корпус: NZXT H7 Flow — 8 000 ₽

💰 ИТОГО: 180 000 ₽

💡 Совет: Отличный 1440p и 4K-гейминг"""
    
    else:
        return """🎮 ИГРОВОЙ ПК (50-100 000 ₽)

🔹 Процессор: Intel Core i5-12400F — 10 000 ₽
🔹 Видеокарта: RTX 3060 12GB — 32 000 ₽
🔹 Материнская плата: B660 — 8 000 ₽
🔹 Оперативная память: 32GB DDR4 — 6 000 ₽
🔹 SSD: 1TB NVMe — 6 000 ₽
🔹 Блок питания: 650W Bronze — 5 000 ₽
🔹 Корпус: с хорошим обдувом — 5 000 ₽

💰 ИТОГО: 72 000 ₽

💡 Совет: Уверенный 1080p Ultra, заход в 1440p"""

# --- ГЕНЕРАЦИЯ СБОРКИ ---
async def generate_pc_build(data: dict) -> str:
    purpose = data.get('purpose', 'games')
    budget = data.get('budget', 'medium')
    
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
    
    games = data.get('games', 'не указаны')
    programs = data.get('programs', 'не указаны')
    
    prompt = f"""
Собери ПК для {purpose_names.get(purpose, purpose)}.
Бюджет: {budget_names.get(budget, budget)} рублей.
Игры: {games}
Программы: {programs}

Дай список комплектующих с ценами. Итоговая цена не должна превышать бюджет.
Формат:
🔹 Процессор: [модель] — [цена]
🔹 Видеокарта: [модель] — [цена]
🔹 Материнская плата: [модель] — [цена]
🔹 Оперативная память: [объем] — [цена]
🔹 SSD: [объем] — [цена]
🔹 Блок питания: [мощность] — [цена]

💰 ИТОГО: [сумма] рублей
"""
    
    try:
        response = giga.chat(prompt)
        result = response.choices[0].message.content
        
        # Проверка цены
        price_match = re.search(r'ИТОГО.*?(\d[\d\s]*)\s*руб', result)
        if price_match:
            price_str = price_match.group(1).replace(' ', '')
            try:
                price = int(price_str)
                budget_limit = {"min": 50000, "medium": 100000, "high": 200000, "pro": 9999999}.get(budget, 100000)
                if price > budget_limit and budget_limit < 9999999:
                    return get_fallback_build(budget)
            except:
                pass
        return result
    except Exception as e:
        logging.error(f"GigaChat error: {e}")
        return get_fallback_build(budget)

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🖥️ ДОБРО ПОЖАЛОВАТЬ В PC BUILDER BOT!\n\n"
        "🔹 ПОШАГОВАЯ СБОРКА — я задам 5 вопросов\n"
        "🔹 БЫСТРАЯ СБОРКА — опишите свой запрос\n"
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
    await callback.message.answer("🚀 Напишите свой запрос (например: 'Игровой ПК за 100к для Cyberpunk')")
    await state.set_state(BuildSteps.waiting_for_purpose)
    await callback.answer()

@dp.callback_query(F.data == "check_compatibility")
async def check_compatibility_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🔍 ПРОВЕРКА СОВМЕСТИМОСТИ\n\n"
        "Напишите связку процессор + видеокарта в формате:\n\n"
        "Пример 1: Intel i5-12400F и RTX 3060\n"
        "Пример 2: Ryzen 5 5600 и RX 6600 XT\n"
        "Пример 3: Intel i7-13700K и RTX 4070 Ti\n\n"
        "Введите компоненты:"
    )
    await state.set_state(BuildSteps.waiting_for_compatibility)
    await callback.answer()

@dp.callback_query(F.data == "instruction")
async def instruction(callback: CallbackQuery):
    await callback.message.answer(INSTRUCTION, reply_markup=get_back_to_main())
    await callback.answer()

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
    await state.update_data(budget=callback.data.split("_")[1])
    await callback.message.answer("Вопрос 5 из 5: Предпочтения по производителям?", reply_markup=get_preferences_keyboard())
    await state.set_state(BuildSteps.waiting_for_preferences)
    await callback.answer()

@dp.callback_query(BuildSteps.waiting_for_preferences, F.data.startswith("pref_"))
async def step_preferences(callback: CallbackQuery, state: FSMContext):
    await state.update_data(preferences=callback.data.split("_")[1])
    data = await state.get_data()
    text = f"✅ Всё верно?\n\n🎯 Назначение: {data.get('purpose')}\n🎮 Игры: {data.get('games')}\n💻 Программы: {data.get('programs')}\n💰 Бюджет: {data.get('budget')}\n⚙️ Предпочтения: {data.get('preferences')}\n\n✅ Всё верно? Могу собрать ПК."
    await callback.message.answer(text, reply_markup=get_confirm_keyboard())
    await state.set_state(BuildSteps.waiting_for_confirmation)
    await callback.answer()

@dp.callback_query(F.data == "confirm_yes")
async def confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg = await callback.message.answer("🤔 Думаю... (15-30 секунд)")
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
    data = {"purpose": "quick", "quick_request": message.text, "budget": "medium"}
    build = await generate_pc_build(data)
    await msg.delete()
    await message.answer(build, reply_markup=get_back_to_main())
    await state.clear()

@dp.message(BuildSteps.waiting_for_compatibility)
async def compatibility_process(message: Message, state: FSMContext):
    """Обработка запроса на проверку совместимости"""
    components = message.text
    
    msg = await message.answer("🔍 Проверяю совместимость... (15-20 секунд)")
    
    result = await check_compatibility(components, "")
    
    await msg.delete()
    await message.answer(result, reply_markup=get_compatibility_keyboard())
    await state.clear()

# --- ЗАПУСК ---
async def main():
    print("🤖 PC BUILDER БОТ ЗАПУЩЕН!")
    print("✅ Используется GigaChat")
    print("✅ Доступные функции: сборка ПК + проверка совместимости")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
