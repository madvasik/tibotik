import aiosqlite
import json

async def init_db():
    async with aiosqlite.connect('users.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                token TEXT,
                history TEXT
            )
        ''')
        await db.commit()

async def add_user(user_id, token):
    history = {
        'sell_dates': [],
        'sell_prices': [],
        'buy_dates': [],
        'buy_prices': [],
        'capital': 100_000,
        'position': 0
    }
    history_json = json.dumps(history)

    async with aiosqlite.connect('users.db') as db:
        await db.execute('INSERT OR REPLACE INTO users (user_id, token, history) VALUES (?, ?, ?)', 
                        (user_id, token, history_json))
        await db.commit()

async def get_users():
    async with aiosqlite.connect('users.db') as db:
        async with db.execute('SELECT user_id, token, history FROM users') as cursor:
            rows = await cursor.fetchall()
            user_ids = []
            tokens = []
            histories = []
            if rows:
                for row in rows:
                    user_id, token, history_json = row
                    user_ids.append(user_id)
                    tokens.append(token)
                    histories.append(json.loads(history_json))
            return user_ids, tokens, histories
        
async def update_user(user_id, history):
    async with aiosqlite.connect('users.db') as db:
        await db.execute('UPDATE users SET history = ? WHERE user_id = ?', (json.dumps(history), user_id))
        await db.commit()