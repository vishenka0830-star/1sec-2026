import os
import datetime
import subprocess
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

token = os.getenv("BOT_TOKEN")
bot = Bot(token=token)
dp = Dispatcher()

def get_user_path(user_id):
    path = f"videos/{user_id}/{datetime.datetime.now().year}"
    os.makedirs(path, exist_ok=True)
    return path

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🎥 Привет ❤️\n\n"
        "Присылай мне каждый день одно видео\n"
        "Я сохраню ровно 1 секунду\n\n"
        "/stats — сколько дней уже есть\n"
        "/render — собрать ролик прямо сейчас"
    )

@dp.message(F.video)
async def video(message: Message):
    user_id = message.from_user.id
    today = datetime.date.today().strftime("%m-%d")
    user_path = get_user_path(user_id)
    file_path = f"{user_path}/{today}.mp4"

    if os.path.exists(file_path):
        await message.answer("⚠️ За сегодня уже есть видео")
        return

    file = await bot.get_file(message.video.file_id)
    await bot.download_file(file.file_path, file_path)
    
    subprocess.run([
        "ffmpeg", "-y", "-i", file_path, "-t", "1", "-c", "copy", file_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    await message.answer("✅ 1 секунда сохранена за сегодня ❤️")

@dp.message(Command("stats"))
async def stats(message: Message):
    user_id = message.from_user.id
    user_path = get_user_path(user_id)
    count = len([f for f in os.listdir(user_path) if f.endswith(".mp4")]) if os.path.exists(user_path) else 0
    await message.answer(f"📊 Снято дней в {datetime.datetime.now().year}: {count}/365 ❤️")

@dp.message(Command("render"))
async def render(message: Message):
    user_id = message.from_user.id
    user_path = get_user_path(user_id)
    files = sorted([f for f in os.listdir(user_path) if f.endswith(".mp4")])
    
    if len(files) < 2:
        await message.answer("Пока мало видео 😔 Нужно хотя бы 2 дня")
        return

    list_file = f"{user_path}/list.txt"
    with open(list_file, "w") as f:
        for file in files:
            f.write(f"file '{user_path}/{file}'\n")

    output = f"final/{user_id}_{datetime.datetime.now().year}.mp4"
    os.makedirs("final", exist_ok=True)

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", output
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    await message.answer_video(FSInputFile(output), caption="🎬 Твой ролик готов прямо сейчас ❤️")

async def main():
    print("Бот запущен и работает 24/7 ❤️")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
