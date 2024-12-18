import aiosqlite
from config import DATABASE_PATH

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS buttons (name TEXT PRIMARY KEY)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS hours (
            user_id INTEGER,
            date TEXT,
            hours REAL,
            details TEXT,
            PRIMARY KEY (user_id, date)
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS auto_track (
            user_id INTEGER PRIMARY KEY,
            enabled INTEGER
        )''')
        await db.commit()

async def migrate_db_schema():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("PRAGMA table_info(hours)") as cursor:
            columns = await cursor.fetchall()
            if any(col[1] == 'game' for col in columns):
                return

        await db.execute("ALTER TABLE hours RENAME TO hours_old")
        await db.execute('''CREATE TABLE hours (
            user_id INTEGER,
            date TEXT,
            game TEXT,
            hours REAL,
            details TEXT,
            PRIMARY KEY (user_id, date, game)
        )''')

        async with db.execute("SELECT user_id, date, details, hours FROM hours_old") as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                user_id, date, details, hours = row
                game, additional_info = details.split(": ", 1) if ": " in details else (details, "")
                await db.execute('''
                    INSERT INTO hours (user_id, date, game, hours, details)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, date, game.strip(), hours, additional_info.strip()))
        await db.execute("DROP TABLE hours_old")
        await db.commit()

async def add_hours_to_db(user_id: int, game: str, date: str, hours: float, additional_info: str = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        query_check = '''SELECT hours FROM hours WHERE user_id = ? AND date = ? AND game = ?'''
        async with db.execute(query_check, (user_id, date, game)) as cursor:
            existing_entry = await cursor.fetchone()

        if existing_entry:
            current_hours = existing_entry[0]
            new_hours = current_hours + hours
            query_update = '''UPDATE hours SET hours = ?, details = ? WHERE user_id = ? AND date = ? AND game = ?'''
            await db.execute(query_update, (new_hours, additional_info, user_id, date, game))
        else:
            query_insert = '''INSERT INTO hours (user_id, date, game, hours, details) VALUES (?, ?, ?, ?, ?)'''
            await db.execute(query_insert, (user_id, date, game, hours, additional_info or "No additional information"))
        await db.commit()
