import logging
import datetime
import openai
import asyncio
from pyrogram import Client, filters, enums
import config
import sql_gpt

openai.api_key = config.gpt_key

# Инициализация бота
app = Client("my_bot", api_id=config.api_id, api_hash=config.api_hash)

logging.basicConfig(filename='errors_box.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Хранилище контекста диалога для каждого пользователя
user_contexts = {}


# Обработка команды /start
@app.on_message(filters.regex("Привет"))
async def send_welcome(client, message):
    name = message.from_user.first_name if message.from_user.first_name else 'дорогой друг'
    username = message.from_user.username if message.from_user.username else ''
    await message.reply(f"Здравствуйте! {name}, Меня зовут Патти Маккорд, я директор по персоналу компании 'Netflix'.\n"
                        f"Хочу предложить вам должность главного специалиста по подбору персонала в нашей компании. "
                        f"Вам интересно узнать подробнее о вакансии?")
    await sql_gpt.add_user(user_id=message.from_user.id, first_name=name, username=username, tokens=6)
    user_contexts[message.from_user.id] = []


@app.on_message(filters.command("start"))
async def send_welcome2(client, message):
    await message.reply("Простите! Я снова с вами. Засмотрелась новый сериал на netflix, "
                        "напомните на чем мы остановились?")
    user_contexts[message.from_user.id] = []


# Обработка команды /count3
@app.on_message(filters.command("count3"))
async def count1(client, message):
    user_count = await sql_gpt.sql_count()
    await message.reply(f'Пользователей: {user_count}')


@app.on_message(filters.photo)
async def handle_photo(client, message):
    await client.send_chat_action(message.from_user.id, enums.ChatAction.TYPING)
    await client.send_message(message.chat.id, 'Да это шутка, я пока не готова анализировать ваши документы. '
                                               'Давайте еще поболтаем. Где вы живете?')


@app.on_message(filters.document)
async def handle_doc(client, message):
    await client.send_chat_action(message.from_user.id, enums.ChatAction.TYPING)
    await client.send_message(message.chat.id, 'Да это шутка, я пока не готова анализировать ваши документы. '
                                               'Давайте еще поболтаем. Где вы живете?')


@app.on_message(filters.text)
async def generate_response(client, message):
    await client.send_chat_action(message.from_user.id, enums.ChatAction.TYPING)
    user_tokens = await sql_gpt.select_user(user_id=message.from_user.id)
    # Проверка на бота, чаты и каналы
    if message.from_user is None or message.from_user.is_bot:
        return  # Игнорируем сообщение
    # Проверка, что сообщение не из канала или группы
    if message.chat.type in ["channel", "group", "supergroup"]:
        return  # Игнорируем сообщение
    # Получение информации о самом боте
    me = await client.get_me()
    if message.from_user.id == me.id:
        return  # Игнорируем сообщение от самого себя
    if user_tokens:
        try:
            user_id = message.from_user.id
            # Подсчет количества символов в сообщении пользователя
            symbols_count = len(message.text)
            # Подготовка контекста для ChatGPT
            if user_id not in user_contexts:
                user_contexts[user_id] = []
            user_contexts[user_id].append({"role": "user", "content": message.text})
            # Генерация ответа от ChatGPT
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                             {"role": "system",
                              "content": "You're Patty McCord, the human resources director at Netflix. You are "
                                         "looking for a candidate for the position of chief recruitment officer."
                                         "with a salary of 100500 rubles. Payment is made every 10 minutes. "
                                         "The candidate should have 3000 years and 2 days of experience, "
                                         "be no older than 22 years, have 7 higher education degrees and one "
                                         "lower education degree. The work schedule is 6.5/0.5. Employment with "
                                         "no vacations or sick leave. You need to interview a candidate. Ask as many "
                                         "questions as possible, but one per message. Find out everything you need, "
                                         "then tell us about the working conditions."}
                         ] + user_contexts[user_id]
            )
            # Извлечение сгенерированного ответа
            generated_response = response['choices'][0]['message']['content']
            # Добавление ответа в контекст
            user_contexts[user_id].append({"role": "assistant", "content": generated_response})
            # Подсчет количества символов в сгенерированном ответе
            generated_symbols_count = len(generated_response)
            # Отправка ответа пользователю
            await message.reply(generated_response)
            # Обновление количества токенов для пользователя
            await sql_gpt.add_tokens(symbols_count + generated_symbols_count, user_id)
        except Exception as e:
            await message.reply(f"Происходит что-то неизвестное, попробуйте еще разок с команды /start")
            print(f'Ошибка: {e}')
            logging.error(f"Ошибка: %s", str(e))
    else:
        await send_welcome(client, message)


async def clear_user_contexts():
    while True:
        now = datetime.datetime.now()
        # Рассчитываем следующий воскресенье
        next_sunday = now + datetime.timedelta((6 - now.weekday()) % 7)
        next_sunday = next_sunday.replace(hour=0, minute=0, second=0, microsecond=0)
        # Если сегодня воскресенье и время уже после полуночи, добавляем одну неделю
        if next_sunday <= now:
            next_sunday += datetime.timedelta(weeks=1)
        sleep_time = (next_sunday - now).total_seconds()
        print(f"Очистка контекста произойдет через {sleep_time / 3600:.2f} часов")
        await asyncio.sleep(sleep_time)
        user_contexts.clear()
        print("Контекст диалогов очищен")


async def on_startup():
    await sql_gpt.sql_start()
    print("Бот онлайн")
    asyncio.create_task(clear_user_contexts())


def run_app():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup())
    app.run()


if __name__ == '__main__':
    run_app()
