from flask import Flask, render_template, request, jsonify, send_file
import sqlite3, os, csv, datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)

# Ruta a la base de datos y al archivo CSV
DB_PATH = os.path.join("data", "predial.db")
CSV_SEED = os.path.join("data", "sample.csv")

# Conexión a la base de datos
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Inicializa la base de datos y carga datos del CSV si está vacío
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cuentas (
            "CUENTA PREDIAL" TEXT PRIMARY KEY,
            "NOMBRE DEL TITULAR" TEXT,
            "ADEUDO" REAL DEFAULT 0,
            "FECHA VIGENCIA" TEXT
        )
    """)
    cur.execute("SELECT COUNT(*) AS c FROM cuentas")
    count = cur.fetchone()["c"]

    if count == 0 and os.path.exists(CSV_SEED):
        with open(CSV_SEED, newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = [(r["CUENTA PREDIAL"].strip().upper(),
                     r.get("NOMBRE DEL TITULAR","").strip(),
                     float(r.get("ADEUDO", 0) or 0),
                     r.get("FECHA VIGENCIA","").strip() or datetime.date.today().isoformat()
                    ) for r in reader]

        cur.executemany('''
            INSERT OR IGNORE INTO cuentas ("CUENTA PREDIAL", "NOMBRE DEL TITULAR", "ADEUDO", "FECHA VIGENCIA")
            VALUES (?, ?, ?, ?)
        ''', rows)
        conn.commit()
    conn.close()

# Determinar el estado de la cuenta
def get_status(adeudo):
    try:
        adeudo = float(adeudo)
    except:
        adeudo = 0.0
    return "VIGENTE" if adeudo <= 0 else "NO VIGENTE"

# Página principal con el formulario de búsqueda y resultados
@app.route("/", methods=["GET"])
def index():
    q = (request.args.get("q") or "").strip()
    result = None
    if q:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('SELECT * FROM cuentas WHERE "CUENTA PREDIAL" = ?', (q.upper(),))
        row = cur.fetchone()
        conn.close()
        if row:
            result = {
                "CUENTA_PREDIAL": row["CUENTA PREDIAL"],
                "NOMBRE_TITULAR": row["NOMBRE DEL TITULAR"],
                "ADEUDO": row["ADEUDO"],
                "FECHA_VIGENCIA": row["FECHA VIGENCIA"],
                "status": get_status(row["ADEUDO"])
            }
    return render_template("index.html", q=q, result=result)

# Generar y descargar el certificado en PDF
@app.route("/descargar/<cuenta>")
def descargar_pdf(cuenta):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM cuentas WHERE "CUENTA PREDIAL" = ?', (cuenta,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return "Cuenta no encontrada", 404

    # Crear PDF en memoria
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(140, 750, "CERTIFICADO DE MEMBRESÍA FUNERARIA")

    p.setFont("Helvetica", 12)
    p.drawString(50, 700, f"Cuenta: {row['CUENTA PREDIAL']}")
    p.drawString(50, 680, f"Nombre del titular: {row['NOMBRE DEL TITULAR']}")
    p.drawString(50, 660, f"Adeudo: ${row['ADEUDO']}")
    p.drawString(50, 640, f"Fecha vigencia: {row['FECHA VIGENCIA']}")
    p.drawString(50, 620, f"Estado: {get_status(row['ADEUDO'])}")

    p.showPage()
    p.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"certificado_{cuenta}.pdf",
        mimetype="application/pdf"
    )

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
