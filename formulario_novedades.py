import streamlit as st
from datetime import datetime
import gspread
from google.oauth2 import service_account
import re

# ---------------------------
# CONFIG GOOGLE SHEETS (SECRETS)
# ---------------------------

google_secrets = dict(st.secrets["google"])

# Fix private key
google_secrets["private_key"] = (
    google_secrets["private_key"]
    .replace("\\n", "\n")
    .replace("\r\n", "\n")
)

# ✅ Credenciales con scopes explícitos
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = service_account.Credentials.from_service_account_info(
    google_secrets,
    scopes=SCOPES
)
client = gspread.authorize(creds)

# ✅ ID del Sheet
SHEET_ID = "1RFsEMgRx-nfnVxKLTGt_hzB_BmLspqJb9GIRusd8dKM"
sheet = client.open_by_key(SHEET_ID).get_worksheet(0)

# ---------------------------
# CONFIG UI
# ---------------------------

st.set_page_config(page_title="Carga de Novedades", layout="centered")

# Ocultar elementos de Streamlit
st.markdown("""
    <style>
        header[data-testid="stHeader"] { display: none; }
        footer { display: none; }
        #MainMenu { display: none; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
        header[data-testid="stHeader"] { display: none; }
        footer { display: none; }
        #MainMenu { display: none; }
        /* Oculta el banner inferior "Created by / Hosted with Streamlit" */
        [data-testid="stBottomBlockContainer"] { display: none; }
    </style>
""", unsafe_allow_html=True)

# HEADER PROLIJO
col1, col2, col3 = st.columns([2, 5, 2])

with col1:
    st.image("logo_izquierda.png", width=70)

with col2:
    st.markdown(
        """
        <div style="text-align:center;">
            <h1 style="color:#0d9488; margin-bottom:5px;">
                Carga de Novedades
            </h1>
            <p style="color:gray; margin-top:0;">
                Sistema de monitoreo
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.image("logo_derecha.png", width=70)

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
# FORMULARIO
# ---------------------------

with st.form("form_novedad", clear_on_submit=True):

    col1, col2 = st.columns(2)

    with col1:
        fecha = st.date_input("Fecha del evento", datetime.today())

        horario = st.text_input(
            "Horario (HH:MM)",
            datetime.now().strftime("%H:%M"),
            placeholder="Ej: 08:30"
        )

    with col2:
        comisaria = st.selectbox("Comisaría", comisarias)
        categoria = st.selectbox("Categoría", list(categorias.keys()))

    # Subcategoría dinámica
    if categoria != "Otros":
        subcategoria = st.selectbox("Subcategoría", categorias[categoria])
    else:
        subcategoria = ""

    camara_flag = st.selectbox("¿Se ve por cámara?", ["SI", "NO"])

    numero_camara = ""
    if camara_flag == "SI":
        numero_camara = st.text_input("Número de cámara")

    submitted = st.form_submit_button("Guardar Novedad")

# ---------------------------
# VALIDACIÓN + GUARDADO
# ---------------------------

if submitted:

    horario = horario.strip()
    horario_valido = re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", horario)

    if not horario_valido:
        st.error("❌ El horario debe tener formato HH:MM válido (ej: 08:30)")
    else:

        marca_temporal = datetime.now()

        nueva_fila = {
            "Marca temporal": marca_temporal.strftime("%d/%m/%Y %H:%M:%S"),
            "Fecha evento": fecha.strftime("%d/%m/%Y"),
            "Horario": horario,
            "¿Se ve por cámara?": camara_flag,
            "Camara del Evento": numero_camara,
            "Categoria": categoria,
            "Comisaria": comisaria,
            "Subcategoria": subcategoria
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

        col_sub = f"Subcategoria {categoria}"
        if col_sub in sub_cols:
            sub_cols[col_sub] = subcategoria

        nueva_fila.update(sub_cols)

        columnas = sheet.row_values(1)
        fila_final = [nueva_fila.get(col, "") for col in columnas]

        sheet.append_row(fila_final)

        st.success("✅ Novedad cargada correctamente")

        st.rerun()