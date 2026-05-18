import streamlit as st
from datetime import datetime
import gspread
from google.oauth2 import service_account
import re
import pytz

# ---------------------------
# CONFIG GOOGLE SHEETS (SECRETS)
# ---------------------------

google_secrets = dict(st.secrets["google"])
google_secrets["private_key"] = (
    google_secrets["private_key"]
    .replace("\\n", "\n")
    .replace("\r\n", "\n")
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = service_account.Credentials.from_service_account_info(
    google_secrets, scopes=SCOPES)
client = gspread.authorize(creds)

SHEET_ID = "1RFsEMgRx-nfnVxKLTGt_hzB_BmLspqJb9GIRusd8dKM"
sheet = client.open_by_key(SHEET_ID).get_worksheet(0)

# ---------------------------
# CONFIG UI
# ---------------------------

st.set_page_config(page_title="Carga de Novedades", layout="centered")

st.markdown("""
    <style>
        header[data-testid="stHeader"] { display: none !important; }
        footer { display: none !important; }
        #MainMenu { display: none !important; }
        [data-testid="stBottomBlockContainer"] { display: none !important; }
        [class*="_profileContainer"] { display: none !important; }
        [class*="_profilePreview"] { display: none !important; }
        [class*="_viewerBadge"] { display: none !important; }
        [class*="_imageMove"] { display: none !important; }
        [data-testid="appCreatorAvatar"] { display: none !important; }
    </style>
    <script>
        function ocultarBadge() {
            document.querySelectorAll('[class*="_profilePreview"]').forEach(el => {
                el.style.setProperty('display', 'none', 'important');
            });
            document.querySelectorAll('a[href*="streamlit.io"]').forEach(a => {
                let parent = a;
                for (let i = 0; i < 6; i++) {
                    if (parent.parentElement) parent = parent.parentElement;
                }
                parent.style.setProperty('display', 'none', 'important');
            });
        }
        ocultarBadge();
        setInterval(ocultarBadge, 300);
    </script>
""", unsafe_allow_html=True)

# ---------------------------
# HEADER
# ---------------------------

col_logo, col_titulo = st.columns([1, 6])

with col_logo:
    st.image("logo_izquierda.png", width=70)

with col_titulo:
    st.markdown(
        """
        <div style="text-align:center; padding-top:10px;">
            <h1 style="color:#0d9488; margin-bottom:5px;">Carga de Novedades</h1>
            <p style="color:gray; margin-top:0;">Sistema de monitoreo</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")

# ---------------------------
# CONFIG DATOS
# ---------------------------

categorias = {
    "Robo": ["Moto", "Auto", "Via pública", "Finca", "Comercio", "Tentativa"],
    "Hurto": ["Moto", "Auto", "Via pública", "Finca", "Comercio", "Escuela", "Tentativa"],
    "Accidente de tránsito": ["Daños materiales", "Con lesiones"],
    "Conflicto": ["Vecinal", "Familiar", "Pareja"],
    "Violencia": ["Violencia de Género", "Maltrato animal", "Violencia Infantil", "Violencia Familia"],
    "Heridos": ["Arma de fuego", "Arma blanca"],
    "Persecución": ["Con aprendido", "Fugo"],
    "Obito": ["Homicidio", "Natural", "Suicidio"],
    "Incendios": ["Via pública", "Comercio", "Automotor", "Finca", "Escuela"],
    "Otros": []
}

comisarias = [
    "Cria 1ra", "Cria 2da", "Cria 3ra", "Cria 4ta", "Cria 5ta",
    "Cria 6ta", "Cria 7ma", "Cria 8va", "Cria 9na", "Cria 10ma",
    "Dto Turdera", "Dto Banfield", "Dto Villa Rita"
]

# ---------------------------
# SESSION STATE
# ---------------------------

if "form_key" not in st.session_state:
    st.session_state.form_key = 0
if "success_msg" not in st.session_state:
    st.session_state.success_msg = None
if "error_msg" not in st.session_state:
    st.session_state.error_msg = None

# ---------------------------
# MENSAJES DE ESTADO
# ---------------------------

if st.session_state.success_msg:
    st.success(st.session_state.success_msg)
    st.session_state.success_msg = None

if st.session_state.error_msg:
    st.error(st.session_state.error_msg)
    st.session_state.error_msg = None

# ---------------------------
# CATEGORÍA Y SUBCATEGORÍA — fuera del form para que sean reactivas
# ---------------------------

fk = st.session_state.form_key

categoria = st.selectbox(
    "Categoría",
    options=["Seleccione una opción"] + list(categorias.keys()),
    index=0,
    key=f"categoria_{fk}"
)

if categoria not in ["Seleccione una opción", "Otros"]:
    subcategoria = st.selectbox(
        "Subcategoría",
        options=["Seleccione una opción"] + categorias[categoria],
        index=0,
        key=f"subcat_{categoria}_{fk}"
    )
elif categoria == "Otros":
    subcategoria = "Otros"
else:
    subcategoria = "Seleccione una opción"

# ---------------------------
# HORARIO — fuera del form para poder leerlo post-submit
# ---------------------------

horario = st.text_input(
    "Horario (HH:MM)",
    value="",
    placeholder="Ej: 08:30",
    key=f"horario_{fk}"
)

# ---------------------------
# FORMULARIO
# ---------------------------

with st.form(key=f"form_novedad_{fk}", clear_on_submit=True):

    col1, col2 = st.columns(2)

    with col1:
        fecha = st.date_input("Fecha del evento", datetime.today())

    with col2:
        comisaria = st.selectbox(
            "Comisaría",
            options=["Seleccione una opción"] + comisarias,
            index=0
        )
        camara_flag = st.selectbox(
            "¿Se ve por cámara?",
            options=["Seleccione una opción", "SI", "NO"],
            index=0
        )

    numero_camara = st.text_input("Número de cámara (si aplica)", value="")

    submitted = st.form_submit_button(
        "💾 Guardar Novedad", use_container_width=True)

# ---------------------------
# VALIDACIÓN + GUARDADO
# ---------------------------

if submitted:

    # ✅ Leer desde session_state lo que clear_on_submit limpió
    fk = st.session_state.form_key
    categoria_val = st.session_state.get(
        f"categoria_{fk}", "Seleccione una opción")
    subcat_key = f"subcat_{categoria_val}_{fk}"
    subcat_val = st.session_state.get(subcat_key, "Seleccione una opción")
    if categoria_val == "Otros":
        subcat_val = "Otros"

    horario_input = st.session_state.get(
        f"horario_{fk}", "").strip()  # ✅ FIX horario

    errores = []
    horario_valido = re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", horario_input)

    if not horario_valido:
        errores.append(
            "El horario debe tener formato HH:MM válido (ej: 08:30)")
    if comisaria == "Seleccione una opción":
        errores.append("Debe seleccionar una Comisaría")
    if categoria_val == "Seleccione una opción":
        errores.append("Debe seleccionar una Categoría")
    if categoria_val not in ["Seleccione una opción", "Otros"] and subcat_val == "Seleccione una opción":
        errores.append("Debe seleccionar una Subcategoría")
    if camara_flag == "Seleccione una opción":
        errores.append("Debe indicar si se ve por cámara")

    if errores:
        st.session_state.error_msg = "❌ " + " | ".join(errores)
        st.rerun()
    else:
        try:
            tz_argentina = pytz.timezone("America/Argentina/Buenos_Aires")

            # ✅ Marca temporal: string con fecha+hora (Google Sheets lo detecta como datetime)
            marca_temporal = datetime.now(
                tz_argentina).strftime("%d/%m/%Y %H:%M:%S")

            # ✅ Fecha evento: string formato DD/MM/YYYY → Sheets lo reconoce como fecha
            fecha_str = fecha.strftime("%d/%m/%Y")

            # ✅ Horario: string HH:MM:SS → Sheets lo reconoce como hora
            hora_obj = datetime.strptime(horario_input, "%H:%M")
            horario_str = hora_obj.strftime("%H:%M:%S")

            nueva_fila = {
                "Marca temporal":    marca_temporal,
                "Fecha evento":      fecha_str,
                "Horario":           horario_str,
                "¿Se ve por cámara?": camara_flag,
                "Camara del Evento": numero_camara,
                "Categoria":         categoria_val,
                "Comisaria":         comisaria,
                "Subcategoria":      subcat_val if subcat_val != "Seleccione una opción" else ""
            }

            sub_cols = {
                "Subcategoria Robo": "",
                "Subcategoria Hurto": "",
                "Subcategoria Accidente de tránsito": "",
                "Subcategoria Conflicto": "",
                "Subcategoria Violencia": "",
                "Subcategoria Heridos": "",
                "Subcategoria Persecución": "",
                "Subcategoria Obito": "",
                "Subcategoria Otros": "",
                "Subcategoria Incendios": ""
            }

            col_sub = f"Subcategoria {categoria_val}"
            if col_sub in sub_cols:
                sub_cols[col_sub] = nueva_fila["Subcategoria"]

            nueva_fila.update(sub_cols)

            columnas = sheet.row_values(1)
            fila_final = [nueva_fila.get(col, "") for col in columnas]

            sheet.append_row(fila_final)

            st.session_state.success_msg = "✅ Novedad cargada correctamente"
            st.session_state.form_key += 1
            st.rerun()

        except Exception as e:
            st.session_state.error_msg = f"❌ Error al guardar: {str(e)}"
            st.rerun()
