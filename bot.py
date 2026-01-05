import os
import datetime
import subprocess
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
import asyncio
from config import BOT_TOKEN, VIDEOS_DIR, FINAL_DIR

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def user_year_path(user_id: int, year: int):
    path = os.path.join(VIDEOS_DIR, f"user_{user_id}", str(year))
    os.makedirs(path, exist_ok=True)
    return path

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🎥 Привет!\n\n"
        "Каждый день присылай мне одно видео (1-3 сек)\n"
        "Я обрежу до 1 секунды и сохраню ❤️\n\n"
        "В конце года соберу твой фильм!\n\n"
        "Команды:\n"
        "/render — собрать видео сейчас\n"
        "/stats — сколько дней уже есть"
    )

@dp.message(F.video)
async def handle_video(message: Message):
    user_id = message.from_user.id
    today = datetime.date.today()
    year = today.year
    user_path = user_year_path(user_id, year)
    filename = f"{today.strftime('%m-%d')}.mp4"
    file_path = os.path.join(user_path, filename)

    if os.path.exists(file_path):
        await message.answer("⚠️ За сегодня уже есть видео. Можно переснять завтра или использовать /render")
        return

    video = message.video
    temp_path = file_path.replace(".mp4", "_temp.mp4")
    await bot.download(video.file_id, temp_path)

    # Обрезаем до 1 секунды
    subprocess.run([
        "ffmpeg", "-y", "-i", temp_path, "-t", "1", "-c:v", "libx264", "-preset", "ultrafast", file_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    os.remove(temp_path)
    await message.answer("✅ 1 секунда сохранена!")

@dp.message(Command("render"))
async def render(message: Message):
    user_id = message.from_user.id
    year = datetime.date.today().year
    user_path = user_year_path(user_id, year)

    files = sorted([f for f in os.listdir(user_path) if f.endswith(".mp4")])
    if not files:
        await message.answer("Нет видео за этот год 😔")
        return

    list_file = os.path.join(user_path, "list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for file in files:
            f.write(f"file '{os.path.join(user_path, file)}'\n")

    os.makedirs(FINAL_DIR, exist_ok=True)
    output = os.path.join(FINAL_DIR, f"{user_id}_{year}_final.mp4")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", output
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    await message.answer_video(open(output, "rb"), caption="🎉 Твой фильм 2025 года готов!")

@dp.message(Command("stats"))
async def stats(message: Message):
    user_id = message.from_user.id
    year = datetime.date.today().year
    user_path = user_year_path(user_id, year)
    count = len([f for f in os.listdir(user_path) if f.endswith(".mp4")]) if os.path.exists(user_path) else 0
    await message.answer(f"Снято дней в {year} году: {count}/365 📅")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())