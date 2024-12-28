import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import pytz
from flask import Flask
from threading import Thread

# Configuración básica del servidor Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "¡El bot está corriendo correctamente!"

def run_server():
    port = int(os.environ.get("PORT", 5000))  # Render asigna dinámicamente este puerto
    app.run(host="0.0.0.0", port=port)

# Ejecutar Flask en un hilo secundario
Thread(target=run_server).start()

# Configuración de logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Lista de IDs de usuarios autorizadoqs
USUARIOS_AUTORIZADOS = [7142146578, 7400707912, 5475503020]  # Sustituye con los IDs reales

# Configuración de rutas de plantillas y salidas
FONT_PATH = "fuente.ttf"  # Asegúrate de que la ruta sea correcta
FONT_MOVIMIENTOS_PATH = "fuente.ttf"  # Asegúrate de que la ruta sea correcta
COMPROBANTES = {
    "comprobante1": {
        "template": "plantilla1.jpeg",
        "output": "comprobante1_generado.png",
        "styles": {
            "nombre": {"size": 42, "color": "#1b0b19", "pos": (90, 492)},
            "telefono": {"size": 46, "color": "#1b0b19", "pos": (90, 816)},
            "valor1": {"size": 42, "color": "#1b0b19", "pos": (90, 1148)},
            "fecha": {"size": 42, "color": "#1b0b19", "pos": (90, 983)},
        },
    },
    "comprobante2": {
        "template": "plantilla2.jpg",
        "output": "comprobante2_generado.png",
        "styles": {
            "nombre": {"size": 43, "color": "#1b0b19", "pos": (86, 1060)},
            "telefono": {"size": 43, "color": "#1b0b19", "pos": (86, 1375)},
            "valor1": {"size": 43, "color": "#1b0b19", "pos": (86, 1220)},
            "fecha": {"size": 43, "color": "#1b0b19", "pos": (86, 1535)},
        },
    },
    "comprobante3": {
        "template": "plantilla3.jpg",
        "output": "comprobante3_generado.png",
        "styles": {
            "nombre": {"size": 22, "color": "#1b0b19", "pos": (62, 285)},
            "telefono": {"size": 22, "color": "#1b0b19", "pos": (62, 365)},
            "valor1": {"size": 22, "color": "#1b0b19", "pos": (62, 445)},
            "fecha": {"size": 22, "color": "#1b0b19", "pos": (62, 522)},
        },
    },
    "movimientos": {
        "template": "movimientos.jpg",
        "output": "movimiento_generado.png",
        "styles": {
            "nombre": {"size": 40, "color": "#1b0b19", "pos": (155 ,465)},
            "valor1": {"size": 40, "color": "#007500", "pos": (800, 465)},
        },
    },
}

# Validar archivo
def validar_archivo(path: str) -> bool:
    if not os.path.exists(path):
        logging.error(f"Archivo no encontrado: {path}")
        return False
    return True

## Obtener fecha para comprobante1
def obtener_fecha_comprobante1() -> str:
    utc_now = datetime.now(pytz.utc)
    colombia_tz = pytz.timezone("America/Bogota")
    hora_colombiana = utc_now.astimezone(colombia_tz)
    dia = f"{hora_colombiana.day:02d}"
    
    # Diccionario de los meses en español
    meses = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
        7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }
    mes = meses[hora_colombiana.month]  # Utilizamos el mes en español
    anio = hora_colombiana.year
    hora = hora_colombiana.strftime("%I:%M %p").lower()
    hora = hora.replace("am", "a.m.").replace("pm", "p.m.")
    
    return f"{dia} de {mes} de {anio}, {hora}"

# Obtener fecha para comprobante2 y comprobante3
def obtener_fecha_comprobante2y3() -> str:
    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    utc_now = datetime.now(pytz.utc)
    colombia_tz = pytz.timezone("America/Bogota")
    hora_colombiana = utc_now.astimezone(colombia_tz)
    dia = f"{hora_colombiana.day:02d}"
    mes = meses[hora_colombiana.month - 1]
    anio = hora_colombiana.year
    hora = hora_colombiana.strftime("%I:%M %p").lower()
    hora = hora.replace("am", "a.m.").replace("pm", "p.m.")
    return f"{dia} de {mes} de {anio} a las {hora}"

# Formatear nombre
def formatear_nombre(nombre: str, comprobante: str) -> str:
    if comprobante == "comprobante1":
        return nombre.upper()
    elif comprobante == "comprobante2" or comprobante == "comprobante3":
        return nombre.title()
    return nombre

# Formatear teléfono
# Formatear teléfono
def formatear_telefono(telefono: str, comprobante: str) -> str:
    if comprobante == "comprobante1" or comprobante == "comprobante3":
        return telefono  # 10 dígitos seguidos, sin espacios
    elif comprobante == "comprobante2":
        return f"{telefono[:3]} {telefono[3:6]} {telefono[6:]}"  # XXX XXX XXXX
    return telefono

# Formatear valor
def formatear_valor(valor: int) -> str:
    return f"$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Generar comprobante dinámico
def generar_comprobante(nombre: str, telefono: str, valor: int, config: dict) -> str:
    template_path = config["template"]
    output_path = config["output"]
    styles = config["styles"]
    
    if not validar_archivo(template_path) or not validar_archivo(FONT_PATH):
        raise FileNotFoundError("Archivo de plantilla o fuente no encontrado")
    
    escala = 3  # Resolución alta
    img = Image.open(template_path)
    img = img.resize((img.width * escala, img.height * escala), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    
    if config["output"] == "comprobante1_generado.png":
        fecha_actual = obtener_fecha_comprobante1()
    else:
        fecha_actual = obtener_fecha_comprobante2y3()
    
    valor_formato = formatear_valor(valor)

    for key, style in styles.items():
        font = ImageFont.truetype(FONT_PATH, size=style["size"] * escala) if key != "movimientos" else ImageFont.truetype(FONT_MOVIMIENTOS_PATH, size=style["size"] * escala)
        if key == "nombre":
            nombre_formateado = formatear_nombre(nombre, config["output"].split("_")[0])
            draw.text(
                (style["pos"][0] * escala, style["pos"][1] * escala),
                nombre_formateado,
                font=font,
                fill=style["color"]
            )
        elif key == "telefono":
            telefono_formateado = formatear_telefono(telefono, config["output"].split("_")[0])
            draw.text(
                (style["pos"][0] * escala, style["pos"][1] * escala),
                telefono_formateado,
                font=font,
                fill=style["color"]
            )
        elif key == "valor1":
            draw.text(
                (style["pos"][0] * escala, style["pos"][1] * escala),
                valor_formato,
                font=font,
                fill=style["color"]
            )
        elif key == "fecha":
            draw.text(
                (style["pos"][0] * escala, style["pos"][1] * escala),
                fecha_actual,
                font=font,
                fill=style["color"]
            )
    img.save(output_path, quality=99)
    return output_path

# Verificar acceso de usuario
async def verificar_acceso(update: Update) -> bool:
    user_id = update.effective_user.id
    if user_id not in USUARIOS_AUTORIZADOS:
        await update.message.reply_text("Acceso denegado. No estás autorizado para usar este bot.")
        return False
    return True

# Manejar comprobante
async def manejar_comprobante(update: Update, context: ContextTypes.DEFAULT_TYPE, comprobante_key: str) -> None:
    if not await verificar_acceso(update):
        return
    try:
        if comprobante_key not in COMPROBANTES:
            await update.message.reply_text("Comprobante no configurado.")
            return
        
        datos = update.message.text.replace(f"/{comprobante_key}", "").strip()
        if datos.count(",") != 2:
            await update.message.reply_text("Formato incorrecto. Usa el formato: Nombre, Teléfono, Valor")
            return
        
        nombre, telefono, valor = [x.strip() for x in datos.split(",")]
        if not valor.isdigit():
            await update.message.reply_text("El valor debe ser un número. Inténtalo de nuevo.")
            return
        
        config = COMPROBANTES[comprobante_key]
        comprobante_path = generar_comprobante(nombre, telefono, int(valor), config)
        
        with open(comprobante_path, "rb") as comprobante:
            await update.message.reply_photo(comprobante, caption="Aquí está tu comprobante")
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("Hubo un error al procesar tus datos.")

# Comando /comprobante1
async def comprobante1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await manejar_comprobante(update, context, "comprobante1")

# Comando /comprobante2
async def comprobante2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await manejar_comprobante(update, context, "comprobante2")

# Comando /comprobante3
async def comprobante3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await manejar_comprobante(update, context, "comprobante3")

# Comando /movimientos
async def movimientos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await verificar_acceso(update):
        return
    try:
        datos = update.message.text.replace(f"/movimientos", "").strip()
        if datos.count(",") != 1:
            await update.message.reply_text("Formato incorrecto. Usa el formato: Nombre, Valor")
            return

        nombre, valor = [x.strip() for x in datos.split(",")]
        if not valor.isdigit():
            await update.message.reply_text("El valor debe ser un número. Inténtalo de nuevo.")
            return

        config = COMPROBANTES["movimientos"]
        comprobante_path = generar_comprobante(nombre, "", int(valor), config)
        
        with open(comprobante_path, "rb") as comprobante:
            await update.message.reply_photo(comprobante, caption="Aquí está tu movimiento")
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("Hubo un error al procesar tus datos.")

# Comando de inicio
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "¡Hola! Soy tu bot de comprobantes. Estos son los comandos que puedes usar:\n\n"
        "/comprobante1 [Nombre], [Teléfono], [Valor] - Generar el primer comprobante.\n"
        "/comprobante2 [Nombre], [Teléfono], [Valor] - Generar el segundo comprobante.\n"
        "/comprobante3 [Nombre], [Teléfono], [Valor] - Generar el tercer comprobante.\n"
        "/movimientos [Nombre], [Valor] - Generar un movimiento.\n\n"
        "Nota: Asegúrate de escribir correctamente el formato."
    )

# Función principal para inicializar el bot
def main() -> None:
    TOKEN = "7219648330:AAEvqKRRPzfE9N4Ym_ErWx9BfWNkifwY8xM"  # Sustituye por el token real de tu bot

    # Crear la aplicación del bot
    application = Application.builder().token(TOKEN).build()

    # Asignar comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("comprobante1", comprobante1))
    application.add_handler(CommandHandler("comprobante2", comprobante2))
    application.add_handler(CommandHandler("comprobante3", comprobante3))
    application.add_handler(CommandHandler("movimientos", movimientos))

    # Ejecutar el bot
    application.run_polling()

# Ejecutar si el script es llamado directamente
if __name__ == "__main__":
    main()
