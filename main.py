import os
import time
import psycopg2
from flask import Flask, request

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "carpet_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")

def get_db_connection():
    while True:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            return conn
        except psycopg2.OperationalError:
            time.sleep(1)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            customer VARCHAR(100),
            mat_type VARCHAR(100),
            dimensions VARCHAR(50),
            pattern VARCHAR(20),
            cut VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Фабрика грязезащитных ковриков</title>
    <style>
        body { font-family: Arial, sans-serif; background: #eef2f5; padding: 30px; }
        .card { max-width: 500px; margin: auto; background: #fff; padding: 25px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        h2 { margin-top: 0; color: #1a202c; }
        label { display: block; margin-top: 15px; font-weight: bold; color: #4a5568; }
        select, input[type="text"] { width: 100%; padding: 8px; margin-top: 6px; box-sizing: border-box; border: 1px solid #cbd5e0; border-radius: 4px; }
        .options { margin-top: 15px; background: #f7fafc; padding: 12px; border-radius: 4px; border: 1px solid #edf2f7; }
        .options label { font-weight: normal; margin-top: 8px; }
        button { margin-top: 20px; width: 100%; padding: 10px; background: #2b6cb0; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }
        .link { display: block; margin-top: 15px; text-align: center; color: #2b6cb0; text-decoration: none; font-size: 14px; }
    </style>
</head>
<body>
<div class="card">
    <h2>Заказ ковриков с фабрики</h2>
    <form method="POST" action="/order">
        <label>Заказчик (ФИО или компания):</label>
        <input type="text" name="customer" required placeholder="Например, ООО 'Офис-Центр'">

        <label>Тип покрытия:</label>
        <select name="mat_type">
            <option value="Ворсовый придверный (влаговпитывающий)">Ворсовый придверный (влаговпитывающий)</option>
            <option value="Щетинистый (грязезащитный)">Щетинистый (грязезащитный)</option>
            <option value="Ячеистый (резиновый/сотовый)">Ячеистый (резиновый/сотовый)</option>
        </select>

        <label>Размеры (Длина x Ширина в см):</label>
        <input type="text" name="dimensions" placeholder="150x90">

        <div class="options">
            <label><input type="checkbox" name="custom_pattern"> Индивидуальный узор / логотип (+доплата)</label>
            <label><input type="checkbox" name="custom_cut"> Нестандартный раскрой под порог (+доплата)</label>
        </div>

        <button type="submit">Передать в цех</button>
    </form>
    <a class="link" href="/orders">Посмотреть журнал заказов в БД →</a>
</div>
</body>
</html>
"""

@app.route('/')
def home():
    return HTML_FORM

@app.route('/order', methods=['POST'])
def order():
    customer = request.form.get('customer')
    mat_type = request.form.get('mat_type')
    dimensions = request.form.get('dimensions') or "Стандартный размер"
    pattern = "Требуется" if request.form.get('custom_pattern') else "Нет"
    cut = "Требуется" if request.form.get('custom_cut') else "Нет"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (customer, mat_type, dimensions, pattern, cut) VALUES (%s, %s, %s, %s, %s);",
        (customer, mat_type, dimensions, pattern, cut)
    )
    conn.commit()
    cur.close()
    conn.close()

    return f"""
    <div style="font-family: Arial, sans-serif; padding: 40px; text-align: center;">
        <h2 style="color: #2b6cb0;">Заказ записан в PostgreSQL!</h2>
        <p><b>Клиент:</b> {customer}</p>
        <p><b>Покрытие:</b> {mat_type}</p>
        <p><b>Размер:</b> {dimensions}</p>
        <br>
        <a href="/">Оформить ещё</a> | <a href="/orders">Все заказы цеха</a>
    </div>
    """

@app.route('/orders')
def list_orders():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, customer, mat_type, dimensions, pattern, cut, created_at FROM orders ORDER BY id DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    items = "".join([f"<tr><td style='padding:8px; border:1px solid #ccc;'>{r[0]}</td><td style='padding:8px; border:1px solid #ccc;'>{r[1]}</td><td style='padding:8px; border:1px solid #ccc;'>{r[2]}</td><td style='padding:8px; border:1px solid #ccc;'>{r[3]}</td><td style='padding:8px; border:1px solid #ccc;'>{r[4]}</td><td style='padding:8px; border:1px solid #ccc;'>{r[5]}</td><td style='padding:8px; border:1px solid #ccc;'>{r[6]}</td></tr>" for r in rows])

    return f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Журнал заказов фабрики (данные из базы)</h2>
        <table style="border-collapse: collapse; width: 100%;">
            <tr style="background: #2b6cb0; color: white;">
                <th style="padding: 8px;">ID</th><th>Заказчик</th><th>Покрытие</th><th>Размер</th><th>Узор</th><th>Раскрой</th><th>Дата</th>
            </tr>
            {items}
        </table>
        <br><a href="/">← Вернуться к форме</a>
    </div>
    """

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
