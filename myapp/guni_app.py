from flask import Flask, request, render_template, jsonify
import mariadb
from datetime import datetime, date

# ----------------------------
# Flask app (Gunicorn will import this)
# ----------------------------
app = Flask(__name__)

# ----------------------------
# DB settings
# ----------------------------
DB_HOST = "192.168.52.239"
DB_PORT = 3306
DB_USER = "052user"
DB_PASSWORD = "password"
DB_NAME = "sensordb"

TABLE_NAME = "iot_log"

# ----------------------------
def connect_mariadb():
    conn = mariadb.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    return conn

# ----------------------------
def init_table():
    conn = None
    try:
        conn = connect_mariadb()
        cur = conn.cursor()

        sql = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            device VARCHAR(20) NOT NULL,
            temp DECIMAL(6,2) NULL,
            light INT NULL,
            device_time VARCHAR(25) NULL,
            seq INT NULL,
            recv_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
        cur.execute(sql)
        conn.commit()
    finally:
        if conn is not None:
            conn.close()

# ----------------------------
def safe_to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None

def safe_to_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None

# ----------------------------
# URL prefix: /gn
# ----------------------------
@app.route("/gn/")
def gn_index():
    return "<h1>GN Server OK</h1>"

# ----------------------------
# Gateway -> Server (LoRa record insert)
# Example:
# requests.post("http://PI2:8000/gn/ingest", data={
#   "device": "device1",
#   "temp": "23.40",
#   "light": "456",
#   "time": "2025/12/18 15:10:00",
#   "seq": "123"
# })
# ----------------------------
@app.route("/gn/ingest", methods=["POST"])
def ingest():
    device = request.form.get("device")
    temp_str = request.form.get("temp")
    light_str = request.form.get("light")
    time_str = request.form.get("time")
    seq_str = request.form.get("seq")

    if device is None or device.strip() == "":
        return "Missing device", 400

    temp_val = safe_to_float(temp_str)
    light_val = safe_to_int(light_str)
    seq_val = safe_to_int(seq_str)

    conn = None
    try:
        conn = connect_mariadb()
        cur = conn.cursor()

        # mariadb-python prefers ? placeholders
        sql = f"""
        INSERT INTO {TABLE_NAME} (device, temp, light, device_time, seq)
        VALUES (?, ?, ?, ?, ?)
        """
        cur.execute(sql, (device, temp_val, light_val, time_str, seq_val))
        conn.commit()

        return "OK", 200
    except mariadb.Error as e:
        if conn is not None:
            conn.rollback()
        return f"DBError: {e}", 500
    finally:
        if conn is not None:
            conn.close()

# ----------------------------
# HTML list page
# ----------------------------
@app.route("/gn/datalist", methods=["GET"])
def datalist():
    conn = None
    try:
        conn = connect_mariadb()
        cur = conn.cursor()

        sql = f"SELECT id, device, temp, light, device_time, seq, recv_time FROM {TABLE_NAME} ORDER BY id DESC LIMIT 200"
        cur.execute(sql)
        rows = cur.fetchall()

        columns = [desc[0] for desc in cur.description]
        return render_template("list.html", columns=columns, rows=rows, tablename=TABLE_NAME)
    except mariadb.Error as e:
        return f"DBError: {e}", 500
    finally:
        if conn is not None:
            conn.close()

# ----------------------------
# Query form (optional, replaces the old /home html)
# ----------------------------
@app.route("/gn/query", methods=["GET"])
def query_form():
    return render_template("query.html")

# ----------------------------
# JSON API (date range + devno list)
# This imitates your old /datajson style.
# POST fields:
#   sdate1, sdate2 (optional)
#   devno=... (checkbox multiple)
# Here: we filter by device_time string prefix date (rough but OK for class)
# ----------------------------
@app.route("/gn/datajson", methods=["POST"])
def datajson():
    sdate1 = request.form.get("sdate1")
    sdate2 = request.form.get("sdate2")
    devno_list = request.form.getlist("devno")

    # Build WHERE safely
    where_clauses = []
    params = []

    # If your device_time is "YYYY/MM/DD HH:MM:SS", date part is first 10 chars
    # For class work: we filter by string range using REPLACE to "YYYY-MM-DD"
    if sdate1 is not None and sdate1 != "":
        where_clauses.append("REPLACE(SUBSTRING(device_time, 1, 10), '/', '-') >= ?")
        params.append(sdate1)

    if sdate2 is not None and sdate2 != "":
        where_clauses.append("REPLACE(SUBSTRING(device_time, 1, 10), '/', '-') <= ?")
        params.append(sdate2)

    if devno_list is not None and len(devno_list) > 0:
        # Your checkboxes are "1","2","3" etc. If you use "device1", adjust here.
        # We assume DB device field is like "device1"
        dev_devices = []
        for d in devno_list:
            dev_devices.append(f"device{d}")

        placeholders = ", ".join(["?"] * len(dev_devices))
        where_clauses.append(f"device IN ({placeholders})")
        for item in dev_devices:
            params.append(item)

    where_sql = ""
    if len(where_clauses) > 0:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    conn = None
    try:
        conn = connect_mariadb()
        cur = conn.cursor()

        sql = f"""
        SELECT id, device, temp, light, device_time, seq, recv_time
        FROM {TABLE_NAME}
        {where_sql}
        ORDER BY id DESC
        LIMIT 500
        """
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()

        keys = ["id", "device", "temp", "light", "device_time", "seq", "recv_time"]
        results = []
        for row in rows:
            values = []
            for item in row:
                if isinstance(item, (datetime, date)):
                    values.append(str(item))
                else:
                    values.append(item)
            results.append(dict(zip(keys, values)))

        return jsonify({"sensorData": results})
    except mariadb.Error as e:
        return f"DBError: {e}", 500
    finally:
        if conn is not None:
            conn.close()

# ----------------------------
# Initialize table once at import time
# ----------------------------
init_table()
