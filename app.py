from flask import Flask, render_template, request, jsonify
import sqlite3, os, csv, datetime

app = Flask(__name__)

DB_PATH = os.path.join("data", "predial.db")
CSV_SEED = os.path.join("data", "sample.csv")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cuentas (
            cuenta TEXT PRIMARY KEY,
            propietario TEXT,
            adeudo REAL DEFAULT 0,
            fecha_vigencia TEXT,
            gdrive_id TEXT
        )
    """)
    # Revisar si está vacío
    cur.execute("SELECT COUNT(*) AS c FROM cuentas")
    count = cur.fetchone()["c"]
    if count == 0 and os.path.exists(CSV_SEED):
        with open(CSV_SEED, newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = [
                (
                    r["CUENTA PREDIAL"].strip().upper(),
                    r.get("NOMBRE DEL TITULAR","").strip(),
                    float(r.get("ADEUDO", 0) or 0),
                    r.get("FECHA VIGENCIA","").strip() or datetime.date.today().isoformat(),
                    r.get("GDRIVE_ID","").strip()
                )
                for r in reader
            ]
        cur.executemany("""
            INSERT OR IGNORE INTO cuentas 
            (cuenta, propietario, adeudo, fecha_vigencia, gdrive_id) 
            VALUES (?, ?, ?, ?, ?)
        """, rows)
        conn.commit()
    conn.close()

def get_status(adeudo):
    try:
        adeudo = float(adeudo)
    except:
        adeudo = 0.0
    return "VIGENTE" if adeudo <= 0 else "NO VIGENTE"

@app.route("/", methods=["GET"])
def index():
    q = (request.args.get("q") or "").strip()
    result = None
    if q:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM cuentas WHERE cuenta = ?", (q.upper(),))
        row = cur.fetchone()
        conn.close()
        if row:
            result = dict(row)
            result["status"] = get_status(result["adeudo"])
            if result.get("gdrive_id"):
                result["gdrive_url"] = f"https://drive.google.com/uc?export=download&id={result['gdrive_id']}"
        else:
            result = None
    return render_template("index.html", q=q, result=result)

@app.route("/api/consulta")
def api_consulta():
    cuenta = (request.args.get("cuenta") or "").strip().upper()
    if not cuenta:
        return jsonify({"ok": False, "error": "Falta el parámetro 'cuenta'"}), 400
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cuentas WHERE cuenta = ?", (cuenta,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"ok": True, "found": False, "cuenta": cuenta})
    d = dict(row)
    d["status"] = get_status(d["adeudo"])
    if d.get("gdrive_id"):
        d["gdrive_url"] = f"https://drive.google.com/uc?export=download&id={d['gdrive_id']}"
    return jsonify({"ok": True, "found": True, "data": d})

# Ejecutar init_db siempre que arranque la app (en Render o local)
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

