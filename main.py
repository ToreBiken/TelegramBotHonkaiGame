import logging
import random
import sqlite3
import time
from datetime import datetime, timedelta
import pytz
import re
import threading
import html
import asyncio
import dataset
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

try:
    warp_command_count = {}
    user_state = {}

    logging.basicConfig(level=logging.INFO)
    PROXY_URL = 'http://proxy.server:3128'
    bot = Bot(token='6317450812:AAGLBdCJ-o6z6Oao9PiDVleMANus-eMgJDI',proxy=PROXY_URL)
    dp = Dispatcher(bot)

    db_connection = sqlite3.connect('genshin_inventory.db', check_same_thread=False)
    db_cursor = db_connection.cursor()
    db_lock = threading.Lock()

    db_cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        user_name TEXT,
                        item_name TEXT,
                        item_rarity TEXT,
                        item_quantity INTEGER DEFAULT 0,
                        UNIQUE (user_id, item_name, item_rarity))''')
    db_connection.commit()




    def get_astana_midnight():
        try:
            utc_now = datetime.utcnow()
            astana_tz = pytz.timezone('Asia/Almaty')
            astana_now = utc_now.replace(tzinfo=pytz.utc).astimezone(astana_tz)
            astana_midnight = astana_now.replace(hour=0, minute=0, second=0, microsecond=0)
            midnight_utc = astana_midnight.astimezone(pytz.utc)
            return midnight_utc.timestamp()
        except Exception as e:
            print("Error in get_astana_midnight:", e)


    def reset_command_count():
        while True:
            now = datetime.now(pytz.timezone('Asia/Almaty'))
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            next_midnight = midnight + timedelta(days=1)
            time_until_midnight = (next_midnight - now).total_seconds()

            time.sleep(time_until_midnight)

            warp_command_count.clear()


    threading.Thread(target=reset_command_count).start()


    @dp.message_handler(lambda message: re.match(r'^/warp', message.text, re.IGNORECASE))
    async def wish(message: types.Message):
        try:
            if message.chat.type != 'private':
                try:
                    user_id = message.from_user.id
                    user_name = message.from_user.first_name
                    if message.from_user.username:
                        user_name = "@" + message.from_user.username

                    now = datetime.now(pytz.timezone('Asia/Almaty'))
                    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

                    if user_id in warp_command_count and warp_command_count[user_id] >= 3:
                        not_allowed_more_one = await bot.send_message(message.chat.id,
                                                                      'Вы можете сделать только три прыжка в день.')
                        return

                    if user_id not in warp_command_count or warp_command_count[user_id] == 0:
                        warp_command_count[user_id] = 1
                    else:
                        warp_command_count[user_id] += 1

                    item_rarity = random.choices(['3-star', '4-star', '5-star', '6-star'], weights=[70, 22, 5, 3], k=1)[
                        0]
                    item_data = random.choice(dataset.dataset[item_rarity])
                    item_image_path = item_data["image_path"]
                    item_characteristic = item_data["characteristic"]
                    item_description = item_data["description"]
                    escaped_description = html.escape(item_description).replace("\uFFFD", "")
                    message_text = (
                        f'<b>{user_name} Вы получили</b> {item_data["name"]} \n\n'
                        f'Редкость: {get_rarity_emoji(item_rarity)} \n\n'
                        f'<strong>{item_characteristic}</strong> \n\n'
                        f'{escaped_description}'
                    )

                    if len(message_text) > 1024:
                        message_parts = [message_text[i:i + 1024] for i in range(0, len(message_text), 1024)]
                    else:
                        message_parts = [message_text]

                    with open(item_image_path, 'rb') as img_file:
                        for part in message_parts:
                            congra_win = await bot.send_photo(message.chat.id, img_file, caption=part,
                                                              parse_mode='HTML')

                    with db_lock:
                        db_cursor.execute(
                            'INSERT OR REPLACE INTO inventory (user_id, user_name, item_name, item_rarity, item_quantity) '
                            'VALUES (?, ?, ?, ?, COALESCE((SELECT item_quantity FROM inventory WHERE user_id = ? AND item_name = ? AND item_rarity = ?), 0) + 1)',
                            (user_id, user_name, item_data["name"], item_rarity, user_id, item_data["name"],
                             item_rarity))

                        db_connection.commit()
                except Exception as e:
                    print(e)
                    tex_work = await bot.send_message(message.chat.id, "ошибка, вы получили 1 прыжок")
                    warp_command_count[user_id] -= 1
                    await asyncio.sleep(1)
                    await bot.delete_message(message.chat.id, tex_work.message_id)

            else:
                not_allowed_only_private = await bot.send_message(message.chat.id,
                                                                  'Нельзя прыгать в личных сообщениях с ботом!')
        except Exception as e:
            print("Error in warp:", e)


    def get_rarity_emoji(rarity):
        try:
            if rarity == '5-star':
                return '⭐️ ⭐️ ⭐️ ⭐️ ⭐️'
            elif rarity == '4-star':
                return '⭐️ ⭐️ ⭐️ ⭐️'
            elif rarity == '3-star':
                return '⭐️ ⭐️ ⭐️'
            elif rarity == '6-star':
                return '⭐️ ⭐️ ⭐️ ⭐️ ⭐️ ⭐️'
            else:
                return ''
        except Exception as e:
            print("Error in get_rarity_emoji:", e)


    def get_item_emoji(item_rarity):
        try:
            item_emoji = {
                '6-star': '🏅',
                '5-star': '💎',
                '4-star': '⚔️',
                '3-star': '🗡',
            }
            return item_emoji.get(item_rarity, '')
        except Exception as e:
            print("Error in get_item_emoji:", e)


    rules = """Правила
    Общее

    1.1❗️Запрещено оскорбление других пользователей. Как непосредственно, так и косвенно

    1.2❗️Запрещены любые провокационные действия

    1.3❗️Запрещены любые действия, несущие негативный агитационный характер

    1.4❗️Запрещено публиковать контент, пропагандирующий случаи заболевания или членовредительство, рекламирующий заболеваемость расстройствами и т.п.

    1.5❗️Запрещается рекламировать, участвовать в продвижении или поощрении любой выявленной деятельности

    1.6❗️Запрещено разжигание межнациональной розни, выступления на политической и религиозной почве, дискриминация и т.п.

    1.7❗️Запрещено распространять контентом откровенного, сексуального содержания включая контент "гачи" с другими людьми без их согласия, а также в возрастной сфере сексуализировать несовершеннолетних

    1.8❗️Запрещено распространять изображения с жестоким обращением с животными

    1.9❗️Запрещено применение символики террористов и запрещенных организаций, призыв к насилию и экстремизму

    Размещение ссылок

    2.1❗️Запрещена публикация ссылок на донат-сайты, площадки приема платежей, спонсорской помощи, пожертвований и других сервисов похожей направленности

    2.2❗️Запрещается реклама без согласования с администрацией клуба

    Дополнение

    3.1❗️Администрация клуба по праву удаляет сообщения в сообществе без объяснения причин

    3.2❗️Администрация клуба в праве изменять/дополнять/обновлять нынешнюю редакцию правил без правил участников сообщества

    3.3❗️При нарушении правил, к нарушениям применяются меры наказания, вплоть до полного ограничения доступа к клубу.

    3.4❗️Незнание или непонимание правил не освобождает от ответственности

    3.5❗️Если вы нарушаете правила клуба, то получите предупреждение. После предупреждения мы заблокируем вам возможность общаться (выдаем мут) сроком на 24 часа. Последующие нарушения повлекут за собой более продолжительные ограничения. (запрет)

    3.6❗️Пользователи, неоднократно нарушающие, будут занесены в черный список.

    Черный список
    Черный список это список лиц, которые по какой-либо причине были забанены или исключены из клуба. Эти лица могли нарушать правила клуба или кодекс поведения, или они могли вести себя неприемлемым или вредным для клуба или его членов."""


    @dp.message_handler(commands=['rules'])
    async def send_rules(message: types.Message):
        await message.answer(rules, parse_mode='HTML')


    @dp.message_handler(commands=['report'])
    async def report(message: types.Message):
        try:
            report_text = message.text.replace('/report', '', 1).strip()

            if report_text:
                await bot.send_message(1047995825, f'{message.from_user.username} отправил жалобу:\n\n{report_text}')

                await message.reply('Ваша жалоба была отправлена администратору')

            else:
                await message.reply('Укажите текст жалобы после команды /report')
        except Exception as e:
            print("Error in report:", e)


    @dp.message_handler(commands=['chats'])
    async def send_chats(message: types.Message):
        try:
            chat_info = """Действующие ссылки на чаты:

    DISCORD
    https://discord.gg/amzSYQ4XRg

    Дисциплины

    Большие ( > 200 участников)

    CS:GO
    Админ: @XeRReRa_WWS
    Чат: https://t.me/aitucsgo

    DOTA 2
    Админ: @Cvrsxdcrovvn
    Чат: https://t.me/+UYBeAiTl7kExNGIy

    VALORANT
    Админ: @plutoodo
    Чат: https://t.me/+dYNShF5OSn02ZmU6

    Minecraft
    Админ: @airsmiann
    Чат: https://t.me/+FWkWQFDofAI2Njli

    Средние (50 - 200 участников)

    Genshin
    Админ: @ToreBiken
    Чат: https://t.me/AITUHoyoCLUB (This chat)

    MLBB
    Админ: @feeldraft
    Чат: https://t.me/+LpsgQ4jqTMc0MmM6

    FIFA
    Админ: @alish_back
    Чат: https://t.me/+b09BBUdQ339iNGUy

    Маленькие (< 50 участников)

    Overwatch 2
    Чат: https://t.me/+iwtR6LSb_S8wOWNi

    Tetris
    Админ: @uismuis
    Чат: https://t.me/+i8tUXxuuysA5YzFi

    Hearthstone
    Админ: @4ry1337
    Чат: https://t.me/+Wnw4R_erBaQyM2Ni

    PUBG / PUBGM
    Админ: @PELLUCCI
    Чат: https://t.me/+DdQr4unqPE0yMjAy

    APEX
    Админ: @s0mebodhi
    Чат: https://t.me/+9xsglBw6kCJhMWYy

    Supercell
    Чат: https://t.me/+5kn947qf1gEzZWI6

    AITU GIRLS GAMING
    Админ: @RyUwUv
    Чат: доступен по форме https://forms.office.com/r/Tq50ChmN22

    NBA 2023
    Админ: @nuralchik0303
    Чат: https://t.me/+pq5jM0ZUiL05MTdi"""
            escaped_chat_info = html.escape(chat_info)
            await message.answer(escaped_chat_info, parse_mode='HTML')

        except Exception as e:
            print("Error in send_chats:", e)


    @dp.message_handler(commands=['inventory', 'inv'])
    async def show_inventory(message: types.Message):
        try:
            user_id = message.from_user.id
            user_name = message.from_user.first_name

            with db_lock:
                db_cursor.execute(
                    'SELECT item_rarity, item_name, SUM(item_quantity) FROM inventory WHERE user_id = ? GROUP BY '
                    'item_rarity, item_name ORDER BY item_rarity DESC',
                    (user_id,))
                result = db_cursor.fetchall()

            if result:
                inventory_text = f'Инвентарь игрока {user_name} :\n\n'
                items_by_rarity = {}

                for item_rarity, item_name, item_quantity in result:
                    if item_rarity not in items_by_rarity:
                        items_by_rarity[item_rarity] = []
                    items_by_rarity[item_rarity].append(f'{get_item_emoji(item_rarity)}{item_name} x{item_quantity}')

                for item_rarity, items_list in items_by_rarity.items():
                    inventory_text += f'{get_rarity_emoji(item_rarity)}:\n'
                    inventory_text += ', '.join(items_list) + '\n\n'

                markup = types.InlineKeyboardMarkup(row_width=1)
                hide_button = types.InlineKeyboardButton("Скрыть инвентарь", callback_data="hide_inventory")
                markup.add(hide_button)
                inv_user_to_del = await message.answer(inventory_text, reply_markup=markup)
            else:
                empty_inv = await message.answer(f'{user_name}, ваш инвентарь пуст!')

        except Exception as e:
            tex_work = await message.answer("Тех работы")
            await asyncio.sleep(1)
            await bot.delete_message(message.chat.id, tex_work.message_id)


    @dp.callback_query_handler(lambda call: call.data == "hide_inventory")
    async def hide_inventory_callback(call: types.CallbackQuery):
        try:
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        text=f'Инвентарь скрыт игроком - {call.from_user.first_name}.',
                                        reply_markup=None)
        except Exception as e:
            print("Error in hide_inventory_callback:", e)


    if __name__ == '__main__':
        from aiogram import executor
        executor.start_polling(dp, skip_updates=True)

except Exception as e:
    print(e)