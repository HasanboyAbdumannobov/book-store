import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from environs import Env
 
env = Env()
env.read_env()
TOKEN = env.str("TOKEN")

bot = Bot(TOKEN)
dp = Dispatcher()

DB_NAME = "tasks.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_task_db(user_id, text):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (user_id, text) VALUES (?, ?)", (user_id, text))
    conn.commit()
    conn.close()

def get_tasks_db(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, text FROM tasks WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_task_db(task_id, user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    conn.commit()
    conn.close()

def update_task_db(task_id, user_id, new_text):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET text = ? WHERE id = ? AND user_id = ?", (new_text, task_id, user_id))
    conn.commit()
    conn.close()

class TaskStates(StatesGroup):
    add = State()
    edit = State()

@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer(
        f"👋 Salom, {message.from_user.first_name}!\n"
        "Men sizga vazifalaringizni boshqarishda yordam beraman.\n\n"
        "📋 Buyruqlar:\n"
        "/add — Vazifa qo‘shish\n"
        "/mytasks — Vazifalarni ko‘rish\n"
        "/help — Yordam"
    )

@dp.message(Command("add"))
async def add_task_cmd(message: Message, state: FSMContext):
    await message.answer("✍️ Yangi vazifani kiriting:")
    await state.set_state(TaskStates.add)

@dp.message(TaskStates.add)
async def add_task_process(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer("⚠️ Bo‘sh matn kiritilmadi. Qayta urinib ko‘ring.")
        return
    add_task_db(message.from_user.id, text)
    await message.answer("✅ Vazifa saqlandi!")
    await state.clear()

def task_list_keyboard(tasks):
    buttons = [
        [InlineKeyboardButton(text=f"✏️ {text}", callback_data=f"edit:{task_id}"),
         InlineKeyboardButton(text="🗑 O‘chirish", callback_data=f"del:{task_id}")]
        for task_id, text in tasks
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("mytasks"))
async def show_tasks_cmd(message: Message):
    tasks = get_tasks_db(message.from_user.id)
    if not tasks:
        await message.answer("📝 Sizda vazifa yo‘q.")
        return
    text = "📋 Sizning vazifalaringiz:"
    await message.answer(text, reply_markup=task_list_keyboard(tasks))

@dp.callback_query(F.data.startswith("del:"))
async def delete_task(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    delete_task_db(task_id, callback.from_user.id)
    await callback.message.edit_text("🗑 Vazifa o‘chirildi.")
    await callback.answer("O‘chirildi!")

@dp.callback_query(F.data.startswith("edit:"))
async def edit_task_start(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    await state.update_data(task_id=task_id)
    await callback.message.answer("✍️ Yangi vazifa matnini kiriting:")
    await state.set_state(TaskStates.edit)
    await callback.answer()

@dp.message(TaskStates.edit)
async def edit_task_process(message: Message, state: FSMContext):
    data = await state.get_data()
    task_id = data.get("task_id")
    new_text = message.text.strip()
    if not new_text:
        await message.answer("⚠️ Bo‘sh matn kiritilmadi.")
        return
    update_task_db(task_id, message.from_user.id, new_text)
    await message.answer("✅ Vazifa yangilandi!")
    await state.clear()

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "🆘 Yordam:\n\n"
        "/add — Yangi vazifa qo‘shish\n"
        "/mytasks — Vazifalarni ko‘rish\n"
        "Vazifani o‘chirish yoki tahrirlash uchun tugmalardan foydalaning."
    )

async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
