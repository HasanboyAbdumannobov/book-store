import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from environs import Env

env = Env()
env.read_env()
TOKEN = env.str("TOKEN")

bot = Bot(TOKEN)
dp = Dispatcher()

DB_PATH = "books.db"

class SearchState(StatesGroup):
    query = State()
    selecting = State()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            genre TEXT NOT NULL,
            description TEXT NOT NULL,
            price TEXT NOT NULL
        )
    """)
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM books")
    count = cur.fetchone()[0]
    if count == 0:
        sample = [
            ("Sariq devni minib", "Xudoyberdi To‘xtaboyev", "Sarguzasht", "Bolalar uchun sarguzashtlarga boy, quvnoq va o‘qilishi oson asar.", "45000"),
            ("O‘tkan kunlar", "Abdulla Qodiriy", "Tarixiy drama", "O‘zbekiston tarixidagi eng mashhur sevgi va sadoqat haqidagi roman.", "60000"),
            ("Shum bola", "G‘afur G‘ulom", "Sarguzasht", "Qiziqarli va kulgili bolalik sarguzashtlarini hikoya qiluvchi asar.", "40000"),
            ("Jinlar bazmi", "Tahir Malik", "Detektiv", "Sirli jinoyatlar va ularga qarshi kurashuvchi jasur qahramon haqida.", "50000"),
            ("Dunyoning ishlari", "O‘tkir Hoshimov", "Drama", "Hayotning achchiq haqiqatlarini ochib beruvchi asar.", "45000"),
            ('Sariq devni minib', 'Xudoyberdi To‘xtaboyev', 'Sarguzasht', 'Bolalar uchun sarguzashtlarga boy, quvnoq va o‘qilishi oson asar.', "45000"),
            ('O‘tkan kunlar', 'Abdulla Qodiriy', 'Tarixiy drama', 'O‘zbekiston tarixidagi eng mashhur sevgi va sadoqat haqidagi roman.', "60000"),
            ('Kecha va kunduz', 'Cho‘lpon', 'Realistik', 'Jamiyat va inson orzulari haqidagi chuqur falsafiy asar.', "55000"),
            ('Shum bola', 'G‘afur G‘ulom', 'Sarguzasht', 'Qiziqarli va kulgili bolalik sarguzashtlarini hikoya qiluvchi asar.', "40000"),
            ('Jinlar bazmi', 'Tahir Malik', 'Detektiv', 'Sirli jinoyatlar va ularga qarshi kurashuvchi jasur qahramon haqida.', "50000"),
            ('Dunyoning ishlari', 'O‘tkir Hoshimov', 'Drama', 'Hayotning achchiq haqiqatlarini ochib beruvchi asar.', "45000"),
            ('Odam bo‘lish qiyin', 'O‘tkir Hoshimov', 'Falsafiy', 'Insoniylik, vijdon va mehr haqida yozilgan chuqur ma’naviy roman.', "48000"),
            ('Jimjitlik', 'Erkin A’zam', 'Psixologik', 'Ichki kechinmalar, yolg‘izlik va hayot ma’nosi haqida hikoya.', "42000"),
            ('Ikki eshik orasi', 'O‘tkir Hoshimov', 'Drama', 'Yurakni ezuvchi, oilaviy hayotdagi murakkab voqealar haqida.', "47000"),
            ('Qo‘rqinchli tun', 'Tahir Malik', 'Detektiv', 'Sirli qotilliklar ortida yashiringan jinoyat dunyosining ochilishi.', "53000"),
            ('Alvido bolalik', 'Xudoyberdi To‘xtaboyev', 'Sarguzasht', 'Bolalikdan yoshlikka o‘tish davrini o‘ziga xos tarzda aks ettirgan.', "40000"),
            ('Noma’lum qotil', 'Tahir Malik', 'Detektiv', 'Qotilni topish uchun aql va sabr kerak bo‘lgan murakkab voqea.', "55000"),
            ('Hayot abadiy emas', 'O‘tkir Hoshimov', 'Drama', 'Yaxshilik va yomonlik, muhabbat va nafrat to‘qnashuvi.', "48000"),
            ('Ona yurt', 'Abdulla Qahhor', 'Realistik', 'O‘zbekiston xalqining hayotini aks ettiruvchi hikoyalar to‘plami.', "40000"),
            ('Ko‘zgu', 'Erkin Vohidov', 'She’riyat', 'Fikr va tuyg‘ularni go‘zal ifoda etgan she’rlar to‘plami.', "30000"),
            ('Yulduzli tunlar', 'Pirimqul Qodirov', 'Tarixiy', 'Bobur hayoti va davri haqida tarixiy asar.', "60000"),
            ('Tushda kechgan umrlar', 'O‘tkir Hoshimov', 'Psixologik', 'Inson hayotidagi o‘tgan davrlar xotirasi bilan bog‘liq hikoya.', "46000"),
            ('Aql va yurak', 'Erkin Vohidov', 'She’riyat', 'Yurak va aql o‘rtasidagi ziddiyatni ifoda etuvchi go‘zal she’rlar.', "32000"),
            ('Sadoqat', 'Tog‘ay Murod', 'Drama', 'Inson sadoqati, or-nomusi va muhabbati haqida ta’sirli asar.', "50000"),
            ('Bu dunyoda o‘lib bo‘lmaydi', 'O‘tkir Hoshimov', 'Falsafiy', 'Insonning hayotga bo‘lgan muhabbati va sabr haqida asar.', "49000"),
            ('Qutlug‘ qon', 'Oybek', 'Tarixiy', 'Milliy uyg‘onish davrida xalq ozodligi uchun kurash haqidagi roman.', "55000"),
            ('Sarob', 'Cho‘lpon', 'Realistik', 'Inson orzulari va ularning puchligi haqida yozilgan asar.', "46000"),
            ('Shaytanat I', 'Tahir Malik', 'Detektiv', 'O‘zbekiston adabiyotidagi eng mashhur jinoyat romanlaridan biri.', "65000"),
            ('Shaytanat II', 'Tahir Malik', 'Detektiv', 'Jinoyat olamining davom etayotgan kurashi va sirlar ochilishi.', "70000"),
            ('Yangi zamon odamlari', 'Abdulla Qahhor', 'Satira', 'Jamiyatdagi kulgili va achchiq haqiqatlarni ko‘rsatgan asar.', "40000"),
            ('Baxt izlab', 'Tohir Malik', 'Sarguzasht', 'Baxt izlab yo‘lga chiqqan insonning hayotiy sinovlari haqida.', "43000"),
            ('Qorako‘z Majnun', 'Tog‘ay Murod', 'Drama', 'Chin muhabbat va fojiali taqdir haqidagi roman.', "51000"),
            ('Dilxiroj', 'Erkin A’zam', 'Psixologik', 'Sevgi, hasrat va inson qalbining nozik tomonlarini ko‘rsatadi.', "44000"),
            ('Muhabbat', 'Oybek', 'Romantik', 'Chin muhabbat va fidoyilik haqida yozilgan klassik asar.', "47000"),
            ('Bahor qaytmaydi', 'Saida Zunnunova', 'Lirik', 'Ayol qalbining dardi va orzulari haqida yozilgan ta’sirli asar.', "45000")
        ]
        cur.executemany("INSERT INTO books (title, author, genre, description, price) VALUES (?, ?, ?, ?, ?)", sample)
        conn.commit()
    conn.close()

def get_all_books():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM books ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows

def search_books_by_query(query):
    q = f"%{query}%"
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, title, author, genre, description, price FROM books WHERE title LIKE ? OR author LIKE ? OR genre LIKE ?", (q, q, q))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_book_by_id(book_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, title, author, genre, description, price FROM books WHERE id = ?", (book_id,))
    row = cur.fetchone()
    conn.close()
    return row

def main_menu_inline():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Barcha kitoblar", callback_data="all_books"),
            InlineKeyboardButton(text="🔎 Qidiruv", callback_data="search_start")
        ],
        [
            InlineKeyboardButton(text="ℹ️ About", callback_data="about"),
            InlineKeyboardButton(text="📞 Bog'lanish", callback_data="contact")
        ]
    ])

def books_inline_keyboard(list_of_ids_titles, page=0, per_page=10):
    start = page * per_page
    end = start + per_page
    current_page_books = list_of_ids_titles[start:end]

    kb = []
    row = []
    for idx, title in current_page_books:
        row.append(InlineKeyboardButton(text=title[:25] + "..." if len(title) > 25 else title, callback_data=f"choose:{idx}"))
        if len(row) == 2:
            kb.append(row)
            row = []

    if row:
        kb.append(row)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"page:{page-1}"))
    if end < len(list_of_ids_titles):
        nav_buttons.append(InlineKeyboardButton(text="➡️ Keyingi", callback_data=f"page:{page+1}"))
    if nav_buttons:
        kb.append(nav_buttons)

    kb.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")])

    return InlineKeyboardMarkup(inline_keyboard=kb)


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(
        f"👋 Assalomu alaykum, {message.from_user.first_name}!\n📚 Online Kitob Do‘koniga xush kelibsiz!",
        reply_markup=main_menu_inline()
    )
    await state.clear()

@dp.callback_query(F.data == "search_start")
async def search_start_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🔎 Qidiruvni boshlaymiz!\nKitob nomi, muallif yoki janrni yozing:")
    await state.set_state(SearchState.query)
    await callback.answer()

@dp.message(StateFilter(SearchState.query))
async def process_search(message: Message, state: FSMContext):
    q = message.text.strip()
    rows = search_books_by_query(q)
    if not rows:
        await message.answer("❌ Hech narsa topilmadi. Qayta urinib ko‘ring.", reply_markup=main_menu_inline())
        await state.clear()
        return
    list_ids_titles = [(r[0], r[1]) for r in rows]
    await state.update_data(selected=[], search_results=list_ids_titles)
    kb = books_inline_keyboard(list_ids_titles)
    await message.answer("🔎 Natijalar — tanlang kitob(lar):", reply_markup=kb)
    await state.set_state(SearchState.selecting)

@dp.callback_query(StateFilter(SearchState.selecting), F.data.startswith("choose:"))
async def choose_book(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    book_id = int(callback.data.split(":")[1])
    selected = data.get("selected", [])
    search_results = data.get("search_results", [])
    if book_id in selected:
        selected.remove(book_id)
        await callback.answer("❌ Tanlovdan olib tashlandi")
    else:
        selected.append(book_id)
        await callback.answer("✅ Tanlandi")
    await state.update_data(selected=selected)
    kb = books_inline_keyboard(search_results)
    await callback.message.edit_reply_markup(reply_markup=kb)

@dp.callback_query(StateFilter(SearchState.selecting), F.data == "next_selected")
async def show_selected(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected", [])
    if not selected:
        await callback.answer("Hech narsa tanlanmadi ⚠️", show_alert=True)
        return
    text = "📚 Siz tanlagan kitoblar:\n\n"
    for bid in selected:
        book = get_book_by_id(bid)
        if book:
            _, title, author, genre, desc, price = book
            text += f"📘 <b>{title}</b>\n👤 {author}\n💰 {price}\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await state.clear()

@dp.callback_query(F.data == "main_menu")
async def main_menu_cb(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🏠 Asosiy menyu:", reply_markup=main_menu_inline())
    await state.clear()
    await callback.answer()

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

ADMINS = [776560887] 

class AddBookState(StatesGroup):
    title = State()
    author = State()
    genre = State()
    description = State()
    price = State()

@dp.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id in ADMINS:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="➕ Add")],
                [KeyboardButton(text="📚 All")],
                [KeyboardButton(text="⬅️ Back")]
            ],
            resize_keyboard=True
        )
        await message.answer(
            "👑 <b>Admin paneliga xush kelibsiz!</b>\n\n"
            "Siz yangi kitob qo‘shishingiz yoki barcha kitoblarni ko‘rishingiz mumkin.",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await state.clear()
    else:
        await message.answer("🚫 Siz admin emassiz.")

@dp.message(F.text == "📚 All")
async def show_all_books_admin(message: Message):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT title, author, genre, price FROM books")
    books = cur.fetchall()
    conn.close()

    if not books:
        await message.answer("📭 Bazada hozircha kitob yo‘q.")
        return

    text = "📚 <b>Barcha kitoblar:</b>\n\n"
    for title, author, genre, price in books:
        text += f"📘 <b>{title}</b>\n👤 {author}\n🏷️ {genre}\n💰 {price} so‘m\n\n"

    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "➕ Add")
async def add_book_start(message: Message, state: FSMContext):
    await message.answer("📘 Yangi kitob nomini kiriting:")
    await state.set_state(AddBookState.title)

@dp.message(AddBookState.title)
async def add_book_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("👤 Muallif nomini kiriting:")
    await state.set_state(AddBookState.author)

@dp.message(AddBookState.author)
async def add_book_author(message: Message, state: FSMContext):
    await state.update_data(author=message.text)
    await message.answer("🏷️ Kitob janrini kiriting:")
    await state.set_state(AddBookState.genre)

@dp.message(AddBookState.genre)
async def add_book_genre(message: Message, state: FSMContext):
    await state.update_data(genre=message.text)
    await message.answer("📝 Kitob haqida qisqacha tavsif yozing:")
    await state.set_state(AddBookState.description)

@dp.message(AddBookState.description)
async def add_book_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("💰 Narxini kiriting (faqat raqam):")
    await state.set_state(AddBookState.price)

@dp.message(AddBookState.price)
async def add_book_price(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data["title"]
    author = data["author"]
    genre = data["genre"]
    description = data["description"]
    price = message.text

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO books (title, author, genre, description, price) VALUES (?, ?, ?, ?, ?)",
        (title, author, genre, description, price)
    )
    conn.commit()
    conn.close()

    await message.answer(f"✅ <b>{title}</b> kitobi muvaffaqiyatli qo‘shildi!", parse_mode="HTML")

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Add")],
            [KeyboardButton(text="📚 All")],
            [KeyboardButton(text="⬅️ Back")]
        ],
        resize_keyboard=True
    )
    await message.answer("🔙 Admin menyuga qaytdingiz.", reply_markup=keyboard)
    await state.clear()

@dp.message(F.text == "⬅️ Back")
async def back_to_main(message: Message, state: FSMContext):
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=None)
    await message.answer("🏠 Asosiy menyu:", reply_markup=main_menu_inline())
    await state.clear()

@dp.callback_query(F.data == "all_books")
async def all_books_cb(callback: CallbackQuery):
    books = get_all_books()
    if not books:
        await callback.message.edit_text("📭 Bazada hozircha kitob yo‘q.", reply_markup=main_menu_inline())
        await callback.answer()
        return

    kb = books_inline_keyboard(books)
    await callback.message.edit_text("📚 Barcha kitoblar ro‘yxati:", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data == "about")
async def about_cb(callback: CallbackQuery):
    text = (
        "ℹ️ <b>Biz haqimizda</b>\n\n"
        "Bu bot orqali siz o‘zbek adabiyotining eng mashhur kitoblarini "
        "ko‘rishingiz va ularning mualliflari haqida ma’lumot olishingiz mumkin.\n\n"
        "📚 Maqsadimiz — o‘qish madaniyatini rivojlantirish!"
    )
    await callback.message.edit_text(text, reply_markup=main_menu_inline(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "contact")
async def contact_cb(callback: CallbackQuery): 
    text = (
        "📞 <b>Biz bilan bog‘lanish:</b>\n\n"
        "Telegram: @abdumannobov_x7\n"
        "Manzil: Namangan Mingbuloq\n"
        "Telefon: +998 77 444 68 21"
    )
    await callback.message.edit_text(text, reply_markup=main_menu_inline(), parse_mode="HTML")
    await callback.answer()


async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
