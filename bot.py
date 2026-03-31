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
        [InlineKeyboardButton(text="📖 ИНСТРУКЦИЯ", callback_data="instruction")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_purpose_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🎮 ИГРЫ", callback_data="purpose_games")],
        [InlineKeyboardButton(text="💼 РАБОТА (офис, браузер, 1С)", callback_data="purpose_work")],
        [InlineKeyboardButton(text="🎬 МОНТАЖ/3D (видео, Blender)", callback_data="purpose_creative")],
        [InlineKeyboardButton(text="🌍 УНИВЕРСАЛЬНЫЙ (всё вместе)", callback_data="purpose_universal")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_budget_keyboard():
    buttons = [
        [InlineKeyboardButton(text="💰 ДО 50 000 ₽ (начальный)", callback_data="budget_50000")],
        [InlineKeyboardButton(text="💵 50-100 000 ₽ (средний)", callback_data="budget_100000")],
        [InlineKeyboardButton(text="💎 100-200 000 ₽ (хороший)", callback_data="budget_200000")],
        [InlineKeyboardButton(text="👑 200 000+ ₽ (топовый)", callback_data="budget_300000")],
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

# --- ХРАНИЛИЩЕ ПОСЛЕДНИХ ПАРАМЕТРОВ ---
last_build_data = {}

# --- ФУНКЦИЯ ИЗВЛЕЧЕНИЯ БЮДЖЕТА ---
def extract_budget(text: str) -> int:
    """Извлекает бюджет из текста. Понимает: 80к, 80 тыс, 80000"""
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

def budget_to_key(budget: int) -> str:
    if budget <= 50000:
        return "50000"
    elif budget <= 100000:
        return "100000"
    elif budget <= 200000:
        return "200000"
    else:
        return "300000"

def get_budget_range(budget: int) -> str:
    if budget <= 50000:
        return "до 50 000 рублей"
    elif budget <= 100000:
        return "от 50 000 до 100 000 рублей"
    elif budget <= 200000:
        return "от 100 000 до 200 000 рублей"
    else:
        return "от 200 000 рублей"

# --- РАНДОМНАЯ ГЕНЕРАЦИЯ СБОРКИ ЧЕРЕЗ GIGACHAT ---
async def generate_random_build(purpose: str, budget: int) -> str:
    """Генерирует полностью рандомную сборку через GigaChat"""
    
    purpose_names = {
        "games": "игр. Важно: мощная видеокарта, процессор среднего уровня",
        "work": "офисной работы (Word, Excel, браузер, 1С). Графика не важна, важен быстрый SSD и 16-32GB ОЗУ",
        "creative": "видеомонтажа и 3D-моделирования. Важны: мощный процессор, 32-64GB ОЗУ, быстрый SSD",
        "universal": "универсального использования (и игры, и работа). Нужен баланс"
    }
    
    # Случайные параметры для разнообразия
    cpu_brands = ["Intel Core", "AMD Ryzen"]
    gpu_brands = ["NVIDIA GeForce", "AMD Radeon"]
    ram_options = ["16GB", "32GB", "64GB"]
    ssd_options = ["512GB", "1TB", "2TB"]
    
    random_style = random.choice([
        "сбалансированную", 
        "максимально производительную", 
        "экономичную", 
        "с запасом на будущий апгрейд",
        "тихую",
        "компактную"
    ])
    
    random_cpu_brand = random.choice(cpu_brands)
    random_gpu_brand = random.choice(gpu_brands)
    random_ram = random.choice(ram_options)
    random_ssd = random.choice(ssd_options)
    
    prompt = f"""
Ты — профессиональный конфигуратор ПК. Собери {random_style} сборку для {purpose_names.get(purpose, purpose)}.

ЖЕСТКОЕ УСЛОВИЕ: ИТОГОВАЯ ЦЕНА НЕ ДОЛЖНА ПРЕВЫШАТЬ {budget} РУБЛЕЙ!

Рекомендации для разнообразия:
- Рассмотри вариант с {random_cpu_brand} процессором
- Рассмотри вариант с {random_gpu_brand} видеокартой
- ОЗУ: {random_ram}
- SSD: {random_ssd}

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
🔹 **Система охлаждения:** [тип] — [цена] ₽
🔹 **Корпус:** [модель] — [цена] ₽

💰 **ИТОГОВАЯ ЦЕНА:** [сумма] ₽ (не превышает {budget} ₽)

💡 **СОВЕТ:** [один важный совет по сборке или выбору компонентов]

⚠️ *Цены примерные, актуальны на 2026 год.*
"""
    
    try:
        response = giga.chat(prompt)
        result = response.choices[0].message.content
        
        # Проверяем, что цена в пределах бюджета
        price_match = re.search(r'ИТОГОВАЯ ЦЕНА.*?(\d[\d\s]*)\s*₽', result)
        if price_match:
            price_str = price_match.group(1).replace(' ', '')
            try:
                price = int(price_str)
                if price > budget:
                    # Если GigaChat превысил бюджет — генерируем еще раз с другим промптом
                    return await generate_random_build_fallback(purpose, budget)
            except:
                pass
        return result
        
    except Exception as e:
        logging.error(f"GigaChat error: {e}")
        return await generate_random_build_fallback(purpose, budget)

async def generate_random_build_fallback(purpose: str, budget: int) -> str:
    """Запасной вариант генерации, если основной не сработал"""
    
    purpose_names = {
        "games": "игр",
        "work": "работы",
        "creative": "монтажа",
        "universal": "универсального использования"
    }
    
    prompt = f"""
Собери ПК для {purpose_names.get(purpose, purpose)}.
Бюджет: {budget} рублей. Не превышать!

Дай список комплектующих с ценами. Итоговая цена должна быть в пределах бюджета.
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
        return response.choices[0].message.content
    except:
        return f"❌ Ошибка генерации. Попробуйте другой бюджет или выберите другую сборку."

# --- ПРОВЕРКА СОВМЕСТИМОСТИ ---
async def check_compatibility(cpu: str, gpu: str) -> str:
    prompt = f"""
Проверь совместимость:
Процессор: {cpu}
Видеокарта: {gpu}

Ответь в формате:
🔍 РЕЗУЛЬТАТ: [Совместимы / Не совместимы / Есть нюансы]
📋 ПОЧЕМУ: [одно предложение]
⚠️ УЗКОЕ МЕСТО: [если есть]
💡 СОВЕТ: [что лучше выбрать вместо этого]
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
        "Я помогаю собрать компьютер под ваши задачи и бюджет.\n\n"
        "🔹 *ПОШАГОВАЯ СБОРКА* — выберите тип и бюджет\n"
        "🔹 *БЫСТРАЯ СБОРКА* — напишите например: игровой пк 80к\n"
        "🔹 *ПРОВЕРКА СОВМЕСТИМОСТИ* — проверю связку процессор + видеокарта\n"
        "🔹 *ИНСТРУКЦИЯ* — как собрать ПК своими руками\n\n"
        "Выберите режим:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "step_build")
async def step_build_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "🛠️ *ПОШАГОВАЯ СБОРКА*\n\n"
        "Сначала выберите, для чего нужен компьютер:",
        reply_markup=get_purpose_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(BuildSteps.waiting_for_purpose)
    await callback.answer()

@dp.callback_query(F.data == "quick_build")
async def quick_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🚀 *БЫСТРАЯ СБОРКА*\n\n"
        "Напишите в одном сообщении:\n"
        "• тип ПК (игровой/рабочий/монтаж)\n"
        "• бюджет\n\n"
        "📝 *Примеры:*\n"
        "• игровой пк 80к\n"
        "• пк для монтажа 120 тыс\n"
        "• рабочий пк 50000\n"
        "• 100000\n\n"
        "Просто напишите свой запрос:",
        parse_mode="Markdown"
    )
    await state.set_state(BuildSteps.waiting_for_quick)
    await callback.answer()

@dp.callback_query(F.data == "check_compatibility")
async def compatibility_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🔍 *ПРОВЕРКА СОВМЕСТИМОСТИ*\n\n"
        "Напишите связку процессор + видеокарта\n\n"
        "📝 *Примеры:*\n"
        "• Intel i5-12400F и RTX 3060\n"
        "• Ryzen 5 5600 и RX 6600 XT\n"
        "• Intel i7-13700K, RTX 4070 Ti\n\n"
        "Введите компоненты:",
        parse_mode="Markdown"
    )
    await state.set_state(BuildSteps.waiting_for_compatibility)
    await callback.answer()

@dp.callback_query(F.data == "instruction")
async def instruction(callback: CallbackQuery):
    await callback.message.answer(get_instruction(), reply_markup=get_back_to_main())
    await callback.answer()

@dp.callback_query(F.data.startswith("purpose_"))
async def choose_purpose(callback: CallbackQuery, state: FSMContext):
    purpose = callback.data.split("_")[1]
    await state.update_data(purpose=purpose)
    await callback.message.answer(
        "💰 Теперь выберите бюджет:",
        reply_markup=get_budget_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("budget_"))
async def choose_budget(callback: CallbackQuery, state: FSMContext):
    budget = int(callback.data.split("_")[1])
    data = await state.get_data()
    purpose = data.get("purpose", "games")
    
    msg = await callback.message.answer(f"🤔 Генерирую случайную сборку под {budget} ₽...")
    
    # Сохраняем параметры для кнопки "Другую сборку"
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
    """Генерирует другую сборку с теми же параметрами"""
    user_id = callback.from_user.id
    data = last_build_data.get(user_id)
    
    if not data:
        await callback.message.answer(
            "❌ Не найдены предыдущие параметры.\n"
            "Выберите сборку заново в главном меню.",
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
        "🏠 *Главное меню*\n\nВыберите режим работы:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )
    await callback.message.delete()
    await callback.answer()

@dp.message(BuildSteps.waiting_for_quick)
async def handle_quick(message: Message, state: FSMContext):
    text = message.text.lower()
    budget = extract_budget(text)
    
    if not budget:
        await message.answer(
            "❌ Не удалось определить бюджет.\n\n"
            "Напишите в формате:\n"
            "• игровой пк 80к\n"
            "• 50000\n"
            "• 120 тыс\n\n"
            "Пример: игровой пк 100к"
        )
        return
    
    if "игр" in text:
        purpose = "games"
    elif "монтаж" in text or "видео" in text or "3d" in text:
        purpose = "creative"
    elif "работ" in text or "офис" in text:
        purpose = "work"
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
        parts = text.split(",")
        if len(parts) >= 2:
            cpu = parts[0].strip()
            gpu = parts[1].strip()
        else:
            await message.answer(
                "❌ Неправильный формат.\n\n"
                "Используйте:\n"
                "• Intel i5-12400F и RTX 3060\n"
                "• Ryzen 5 5600, RX 6600 XT"
            )
            return
    
    msg = await message.answer("🔍 Проверяю совместимость...")
    result = await check_compatibility(cpu, gpu)
    await msg.delete()
    await message.answer(result, reply_markup=get_compatibility_keyboard())
    await state.clear()

def get_instruction() -> str:
    """Возвращает подробную инструкцию по сборке ПК"""
    return """
📖 *ПОДРОБНАЯ ИНСТРУКЦИЯ ПО СБОРКЕ ПК СВОИМИ РУКАМИ*

---

🔧 *ЧТО ВАМ ПОНАДОБИТСЯ*

**Инструменты:**
• Крестовая отвертка (Phillips PH2) — самая важная
• Пластиковые стяжки для кабелей
• Термопаста (если не нанесена на кулер)
• Антистатический браслет (желательно, но можно заземлиться)

**Компоненты:**
• Материнская плата
• Процессор (CPU)
• Оперативная память (RAM)
• Видеокарта (GPU)
• Накопитель (SSD)
• Блок питания (PSU)
• Корпус (Case)
• Кулер для процессора

---

⚡ *ВАЖНО: ПОДГОТОВКА*

1. **Заземлитесь!** Прикоснитесь к батарее отопления или металлическому корпусу выключенного ПК. Это защитит компоненты от статического электричества.

2. **Подготовьте рабочее место** — чистый стол, хорошее освещение, свободное пространство.

3. **Распакуйте компоненты** и разложите их так, чтобы было удобно брать.

---

🔩 *ШАГ 1: УСТАНОВКА ПРОЦЕССОРА*

1. Найдите сокет (квадратный разъем) на материнской плате.
2. Поднимите металлическую защелку.
3. Аккуратно достаньте процессор из коробки (держите за края, не трогайте контакты).
4. Найдите золотой треугольник на процессоре и такой же на сокете — совместите их.
5. Положите процессор в сокет (он должен лечь без усилий!).
6. Опустите защелку и зафиксируйте.

---

🔩 *ШАГ 2: УСТАНОВКА ОПЕРАТИВНОЙ ПАМЯТИ*

1. Найдите слоты RAM (обычно 4 штуки).
2. Откройте защелки по краям слотов.
3. Для двух планок используйте слоты 2 и 4 (считая от процессора).
4. Вставьте планку до характерного щелчка — защелки должны закрыться сами.

---

🔩 *ШАГ 3: УСТАНОВКА КУЛЕРА*

1. Если на кулере нет термопасты — нанесите тонкий слой на центр процессора (размером с горошину).
2. Установите кулер на процессор согласно инструкции к нему.
3. Закрепите кулер — обычно нужно прикрутить его к материнской плате.
4. Подключите провод кулера к разъему CPU_FAN на материнской плате.

---

🔩 *ШАГ 4: ПОДГОТОВКА КОРПУСА*

1. Снимите обе боковые крышки корпуса.
2. Проверьте, что в корпусе установлены стойки для материнской платы (медные штырьки).
3. Если стоек нет — вкрутите их в отмеченные отверстия под вашу материнскую плату.

---

🔩 *ШАГ 5: УСТАНОВКА МАТЕРИНСКОЙ ПЛАТЫ В КОРПУС*

1. Вставьте заглушку портов (поставляется с материнской платой) в заднюю панель корпуса.
2. Аккуратно опустите материнскую плату на стойки.
3. Закрутите винты (не перетягивайте!).

---

🔩 *ШАГ 6: УСТАНОВКА БЛОКА ПИТАНИЯ*

1. Установите блок питания в отведенное место (обычно снизу или сверху сзади).
2. Закрепите его 4 винтами.
3. Проложите кабели питания через отверстия в корпусе на заднюю сторону.

---

🔩 *ШАГ 7: УСТАНОВКА SSD*

**Для M.2 SSD:**
1. Найдите слот M.2 на материнской плате.
2. Вставьте SSD под углом 30 градусов.
3. Прижмите и закрепите маленьким винтом.

**Для SATA SSD:**
1. Закрепите SSD в отсеке корпуса.
2. Подключите кабель SATA к материнской плате и к SSD.
3. Подключите питание от блока питания.

---

🔩 *ШАГ 8: УСТАНОВКА ВИДЕОКАРТЫ*

1. Выломайте металлические заглушки на задней панели корпуса (обычно 2-3 штуки).
2. Откройте защелку на PCI-E слоте материнской платы.
3. Аккуратно вставьте видеокарту до щелчка.
4. Закрепите видеокарту винтами к корпусу.
5. Подключите кабели питания от блока питания (6 или 8 pin).

---

🔩 *ШАГ 9: ПОДКЛЮЧЕНИЕ ПРОВОДОВ*

**Основные кабели питания:**
• 24-pin — самый широкий, питание материнской платы
• 4/8-pin CPU — питание процессора (обычно вверху слева)

**Передняя панель корпуса (самое сложное!):**
• POWER SW — кнопка включения
• RESET SW — кнопка перезагрузки
• HDD LED — индикатор работы диска
• POWER LED — индикатор питания

*Смотрите схему в инструкции к материнской плате!*

**Дополнительные кабели:**
• USB 3.0 — синий разъем
• USB 2.0 — черный разъем
• AUDIO — разъем для наушников и микрофона

---

🔩 *ШАГ 10: КАБЕЛЬ-МЕНЕДЖМЕНТ*

1. Соберите все лишние провода на задней стороне корпуса.
2. Затяните пластиковыми стяжками, чтобы они не мешали потоку воздуха.
3. Закройте заднюю крышку корпуса.

---

💻 *ПЕРВЫЙ ЗАПУСК*

1. Подключите кабель питания к блоку питания.
2. Включите тумблер на блоке питания (должен быть в положении I).
3. Подключите монитор к видеокарте (не к материнской плате!).
4. Нажмите кнопку включения на корпусе.
5. Если всё работает — установите Windows с флешки.
6. Установите драйвера: сначала чипсет материнской платы, потом видеокарту.

---

⚠️ *ЕСЛИ КОМПЬЮТЕР НЕ ВКЛЮЧАЕТСЯ*

1. **Нет реакции на кнопку включения:**
   - Проверьте, что блок питания включен тумблером
   - Проверьте подключение кнопки POWER SW
   - Проверьте кабель питания

2. **Вентиляторы крутятся, но нет изображения:**
   - Проверьте, что монитор подключен к видеокарте (а не к материнской плате)
   - Переставьте видеокарту в другой слот
   - Проверьте, что оперативная память защелкнулась

3. **Постоянно перезагружается:**
   - Проверьте питание процессора (4/8 pin)
   - Проверьте, что кулер правильно установлен

---

📹 *ПОЛЕЗНЫЕ ВИДЕО*

На YouTube наберите:
• "Сборка ПК своими руками" — Ремонтяш
• "Как собрать компьютер" — PRO Hi-Tech
• "PC build guide" — Linus Tech Tips

---

💡 *ПОСЛЕДНИЙ СОВЕТ*

Если не уверены в своих силах — обратитесь в сервисный центр. Сборка ПК обычно стоит 2000-3000 рублей, зато вы будете спокойны за сохранность компонентов.
"""

async def main():
    print("🤖 PC BUILDER БОТ ЗАПУЩЕН!")
    print("✅ Рандомная генерация сборок через GigaChat")
    print("✅ Каждая сборка уникальна")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
