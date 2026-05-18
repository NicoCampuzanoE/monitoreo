import streamlit as st
from datetime import datetime
import gspread
from google.oauth2 import service_account
import re

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
# WIDGETS FUERA DEL FORM (reactivos)
# ---------------------------

col1, col2 = st.columns(2)

with col1:
    fecha = st.date_input("Fecha del evento", datetime.today(),
                          key=f"fecha_{st.session_state.form_key}")
    horario = st.text_input(
        "Horario (HH:MM)",
        value="",
        placeholder="Ej: 08:30",
        key=f"horario_{st.session_state.form_key}"
    )

with col2:
    comisaria = st.selectbox(
        "Comisaría",
        options=["Seleccione una opción"] + comisarias,
        index=0,
        key=f"comisaria_{st.session_state.form_key}"
    )
    # Categoría fuera del form → al cambiar, recarga y actualiza subcategoría
    categoria = st.selectbox(
        "Categoría",
        options=["Seleccione una opción"] + list(categorias.keys()),
        index=0,
        key=f"categoria_{st.session_state.form_key}"
    )

# Subcategoría dinámica — reacciona al cambio de categoría
if categoria not in ["Seleccione una opción", "Otros"]:
    subcategoria = st.selectbox(
        "Subcategoría",
        options=["Seleccione una opción"] + categorias[categoria],
        index=0,
        # key cambia con la categoría → resetea la selección
        key=f"subcat_{categoria}_{st.session_state.form_key}"
    )
elif categoria == "Otros":
    subcategoria = "Otros"
    st.info("Categoría: Otros (sin subcategoría)")
else:
    subcategoria = "Seleccione una opción"

camara_flag = st.selectbox(
    "¿Se ve por cámara?",
    options=["Seleccione una opción", "SI", "NO"],
    index=0,
    key=f"camara_{st.session_state.form_key}"
)

numero_camara = ""
if camara_flag == "SI":
    numero_camara = st.text_input(
        "Número de cámara",
        key=f"num_camara_{st.session_state.form_key}"
    )

# ---------------------------
# FORM solo para el botón submit
# ---------------------------

with st.form(key=f"form_novedad_{st.session_state.form_key}"):
    submitted = st.form_submit_button(
        "💾 Guardar Novedad", use_container_width=True)

# ---------------------------
# VALIDACIÓN + GUARDADO
# ---------------------------

if submitted:

    errores = []

    horario_input = horario.strip()
    horario_valido = re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", horario_input)

    if not horario_valido:
        errores.append(
            "El horario debe tener formato HH:MM válido (ej: 08:30)")
    if comisaria == "Seleccione una opción":
        errores.append("Debe seleccionar una Comisaría")
    if categoria == "Seleccione una opción":
        errores.append("Debe seleccionar una Categoría")
    if categoria not in ["Seleccione una opción", "Otros"] and subcategoria == "Seleccione una opción":
        errores.append("Debe seleccionar una Subcategoría")
    if camara_flag == "Seleccione una opción":
        errores.append("Debe indicar si se ve por cámara")

    if errores:
        st.session_state.error_msg = "❌ " + " | ".join(errores)
        st.rerun()
    else:
        try:
            hora_obj = datetime.strptime(horario_input, "%H:%M")
            horario_ampm = hora_obj.strftime("%I:%M:%S %p")

            marca_temporal = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            nueva_fila = {
                "Marca temporal": marca_temporal,
                "Fecha evento": fecha.strftime("%d/%m/%Y"),
                "Horario": horario_ampm,
                "¿Se ve por cámara?": camara_flag,
                "Camara del Evento": numero_camara,
                "Categoria": categoria,
                "Comisaria": comisaria,
                "Subcategoria": subcategoria if subcategoria != "Seleccione una opción" else ""
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
