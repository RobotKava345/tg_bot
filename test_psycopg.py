import psycopg
from config import DATABASE_URL


print("Connecting to PostgreSQL...")

conn = psycopg.connect(
    DATABASE_URL,
    sslmode="require",
    connect_timeout=15,
)

print("Connected successfully!")

with conn.cursor() as cursor:
    cursor.execute("SELECT version();")
    print(cursor.fetchone()[0])

conn.close()