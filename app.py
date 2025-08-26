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
            domicilio TEXT,
            adeudo REAL DEFAULT 0,
            fecha_actualizacion TEXT
        )
    """)
    # Seed with CSV if table is empty
    cur.execute("SELECT COUNT(*) AS c FROM cuentas")
    count = cur.fetchone()["c"]
    if count == 0 and os.path.exists(CSV_SEED):
        with open(CSV_SEED, newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = [(r["cuenta"].strip().upper(),
                     r.get("propietario","").strip(),
                     r.get("domicilio","").strip(),
                     float(r.get("adeudo", 0) or 0),
                     r.get("fecha_actualizacion","").strip() or datetime.date.today().isoformat()
                    ) for r in reader]
        cur.executemany("INSERT OR IGNORE INTO cuentas (cuenta, propietario, domicilio, adeudo, fecha_actualizacion) VALUES (?, ?, ?, ?, ?)", rows)
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
    return jsonify({"ok": True, "found": True, "data": d})

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
