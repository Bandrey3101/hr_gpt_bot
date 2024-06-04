import sqlite3 as sq
# from create_bot import dp, bot


async def sql_start():
    global base, cur
    base = sq.connect('gpt.db')
    cur = base.cursor()
    if base:
        print('Data base connected')
    base.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER UNIQUE, '
                 'first_name TEXT, username TEXT, tokens INTEGER)')
    # base.execute('CREATE UNIQUE INDEX IF NOT EXISTS name_product ON basket (user_id, name)')
    # base.execute('CREATE TABLE IF NOT EXISTS users(user_id PRIMARY KEY, firstname, username,'
    #              ' phone_number, delivery_address, pay)')
    # base.execute('CREATE TABLE IF NOT EXISTS ids(user_id PRIMARY KEY)')
    base.commit()
    print('таблицы добавлены')


async def add_user(user_id, first_name, username, tokens):
    cur.execute("INSERT OR IGNORE INTO users (user_id, first_name, username, tokens) VALUES (?, ?, ?, ?)",
                (user_id, first_name, username, tokens))
    base.commit()


async def select_user(user_id):
    cur.execute("SELECT tokens FROM users WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    return result


async def add_tokens(symbols, user_id):
    cur.execute("UPDATE users SET tokens = tokens + ? WHERE user_id = ?", (symbols, user_id))
    base.commit()


async def reset_tokens():
    cur.execute("UPDATE users SET tokens = 0")
    base.commit()


async def sql_count():
    cur.execute("SELECT COUNT(*) FROM users")
    result = cur.fetchone()[0]
    return result
