# python-context-async-perations-0x02/3-concurrent.py
import asyncio
import aiosqlite

async def async_fetch_users(db_name):
    async with aiosqlite.connect(db_name) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users") as cursor:
            results = await cursor.fetchall()
            return [dict(row) for row in results]

async def async_fetch_older_users(db_name):
    async with aiosqlite.connect(db_name) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE age > ?", (40,)) as cursor:
            results = await cursor.fetchall()
            return [dict(row) for row in results]

async def fetch_concurrently():
    db_name = "example.db"
    # Run both queries concurrently
    users, older_users = await asyncio.gather(
        async_fetch_users(db_name),
        async_fetch_older_users(db_name)
    )
    print("All users:", users)
    print("Users older than 40:", older_users)

def main():
    asyncio.run(fetch_concurrently())

if __name__ == "__main__":
    main()