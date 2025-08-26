# Buscador de Predial (Demo Local)

Este es un prototipo local con **Flask + SQLite**. Busca por "cuenta de predial" y te dice si está **VIGENTE** (adeudo <= 0) o **NO VIGENTE**.

## Requisitos
- Python 3.10 o superior (Windows/Mac/Linux)
- Pip

## Pasos rápidos (Windows / Mac / Linux)
```bash
# 1) Entrar a la carpeta del proyecto
cd predial_demo

# 2) (Opcional recomendado) Crear entorno virtual
python -m venv .venv
# Activar:
#   Windows PowerShell: .\.venv\Scripts\Activate.ps1
#   Windows CMD:        .\.venv\Scripts\activate.bat
#   Mac/Linux bash:     source .venv/bin/activate

# 3) Instalar dependencias
pip install -r requirements.txt

# 4) Ejecutar
python app.py
```

Abre http://127.0.0.1:5000 en tu navegador. Prueba cuentas del archivo `data/sample.csv` (por ejemplo `ABC-0001-2025`).

## Cargar tus propias cuentas
- Reemplaza o edita `data/sample.csv` con tus columnas:
  - `cuenta`, `propietario`, `domicilio`, `adeudo`, `fecha_actualizacion` (YYYY-MM-DD)
- Borra `data/predial.db` si quieres que se regenere con el nuevo CSV
- Ejecuta `python app.py` y se importarán los datos automáticamente si la tabla está vacía.

> **Nota**: Este demo es solo para pruebas locales. Para producción necesitarás controles de acceso, cifrado, bitácoras, sanitización de datos, y políticas de privacidad.
