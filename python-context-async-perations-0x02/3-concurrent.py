import asyncio
import aiosqlite

# 🔹 Function to fetch all users
async def async_fetch_users():
    async with aiosqlite.connect('users.db') as db:
        async with db.execute("SELECT * FROM users") as cursor:
            result = await cursor.fetchall()
            print("All Users:", result)
            return result

# 🔹 Function to fetch users older than 40
async def async_fetch_older_users():
    async with aiosqlite.connect('users.db') as db:
        async with db.execute("SELECT * FROM users WHERE age > 40") as cursor:
            result = await cursor.fetchall()
            print("Users older than 40:", result)
            return result

# 🔹 Function to run both fetches concurrently
async def fetch_concurrently():
    results = await asyncio.gather(
        async_fetch_users(),
        async_fetch_older_users()
    )
    return results

# 🔹 Execute the concurrent fetch using asyncio.run
if __name__ == "__main__":
    asyncio.run(fetch_concurrently())
