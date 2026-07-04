import psycopg2
import os

def test_connection():
    try:
        conn = psycopg2.connect(
            host="db.eiulinywwfkmfnmjwwyn.supabase.co",
            database="postgres",
            user="postgres",
            password=os.environ.get('DB_PASSWORD'),
            port="5432"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        print("Connection successful! Current database time:", result)
        cursor.close()
        conn.close()
    except Exception as e:
        print("Connection failed!")
        print("Error:", e)

if __name__ == "__main__":
    test_connection()