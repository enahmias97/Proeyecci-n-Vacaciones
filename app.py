# -*- coding: utf-8 -*-
"""
🏖️ Control de Vacaciones del Equipo — v2
México 🇲🇽 / Colombia 🇨🇴
Autor: Fernando Nahmias
"""

import calendar
import os
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Control de Vacaciones",
    page_icon="🏖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = "data"
F_EMPLEADOS = os.path.join(DATA_DIR, "empleados.csv")
F_VACACIONES = os.path.join(DATA_DIR, "vacaciones.csv")
F_FERIADOS = os.path.join(DATA_DIR, "feriados.csv")

PAISES = ["México", "Colombia"]
BANDERAS = {"México": "🇲🇽", "Colombia": "🇨🇴"}
ESTADOS = ["Solicitada", "Aprobada", "Tomada", "Rechazada"]
TIPOS = ["Vacaciones", "Permiso", "Incapacidad", "Home office", "Otro"]

# --- Paleta de estados: (fondo suave, texto, color fuerte) ---
ESTADO_STYLE = {
    "Solicitada": ("#FFF3D2", "#8A6300", "#F5A524"),
    "Aprobada":   ("#DCF5E7", "#0B6B45", "#17A673"),
    "Tomada":     ("#DEEAFF", "#1B4F9C", "#3B82F6"),
    "Rechazada":  ("#FFE3E3", "#9B1C1C", "#E5484D"),
}
COLOR_ESTADO = {k: v[2] for k, v in ESTADO_STYLE.items()}

# --- Feriados por país: (fondo, borde, texto) ---
FERIADO_STYLE = {
    "México":   ("#E4F7EC", "#17A673", "#0B6B45"),   # verde
    "Colombia": ("#FFF6C9", "#E8B400", "#8A6300"),   # amarillo
}

PALETA_PERSONAS = [
    "#C9633F", "#3D5A80", "#8B5E83", "#2A9D8F", "#E9A03B",
    "#6D6875", "#457B9D", "#B5651D", "#5F7161", "#9C4F63",
    "#7B6CA6", "#0F8B8D", "#D06C4E", "#4A6FA5", "#A26769",
]

MESES_ES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
DIAS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

# ═══════════════════════════════════════════════════════════════════════════
# ESTILOS GLOBALES
# ═══════════════════════════════════════════════════════════════════════════
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family:'Inter',system-ui,sans-serif; }

    .stApp {
        background:
          radial-gradient(1100px 500px at 8% -8%, #FFF1E6 0%, rgba(255,241,230,0) 60%),
          radial-gradient(900px 450px at 100% 0%, #EFF4FB 0%, rgba(239,244,251,0) 55%),
          #FFFDFA;
    }
    .block-container { padding-top:1.6rem; padding-bottom:3rem; max-width:1500px; }

    /* ---------- HERO ---------- */
    .hero {
        background:linear-gradient(120deg,#C9633F 0%,#E08A63 48%,#EFB48F 100%);
        border-radius:20px; padding:22px 28px; margin-bottom:22px; color:#fff;
        box-shadow:0 12px 30px rgba(201,99,63,.26);
        position:relative; overflow:hidden;
    }
    .hero:after{
        content:""; position:absolute; right:-40px; top:-60px;
        width:220px; height:220px; border-radius:50%;
        background:rgba(255,255,255,.13);
    }
    .hero h1{ margin:0; font-size:1.72rem; font-weight:800; letter-spacing:-.4px; }
    .hero p{ margin:.35rem 0 0; opacity:.94; font-size:.95rem; font-weight:400; }

    /* ---------- MÉTRICAS ---------- */
    div[data-testid="stMetric"]{
        background:linear-gradient(160deg,#FFFFFF 0%,#FFF8F2 100%);
        border:1px solid #F2E4D6; border-radius:16px; padding:16px 18px;
        box-shadow:0 4px 14px rgba(190,150,120,.10);
        transition:transform .18s ease, box-shadow .18s ease;
    }
    div[data-testid="stMetric"]:hover{
        transform:translateY(-3px); box-shadow:0 10px 24px rgba(190,150,120,.18);
    }
    div[data-testid="stMetricLabel"] p{
        font-size:.72rem !important; font-weight:700; color:#9B8574;
        text-transform:uppercase; letter-spacing:.6px;
    }
    div[data-testid="stMetricValue"]{ color:#2F2A26; font-weight:800; }

    /* ---------- SIDEBAR ---------- */
    section[data-testid="stSidebar"]{
        background:linear-gradient(185deg,#FFF6EE 0%,#FBF3EA 100%);
        border-right:1px solid #F0E2D4;
    }
    section[data-testid="stSidebar"] .stRadio label{
        padding:6px 10px; border-radius:10px; font-weight:500;
    }

    /* ---------- BOTONES ---------- */
    .stButton>button, .stDownloadButton>button, .stFormSubmitButton>button{
        border-radius:11px; font-weight:600; border:1px solid #EADCCD;
        transition:all .18s ease;
    }
    .stButton>button:hover, .stFormSubmitButton>button:hover{
        transform:translateY(-1px); box-shadow:0 6px 16px rgba(201,99,63,.20);
    }
    button[kind="primary"], button[kind="primaryFormSubmit"]{
        background:linear-gradient(135deg,#C9633F,#E08A63) !important;
        border:none !important; color:#fff !important;
    }

    /* ---------- EXPANDERS / TABS ---------- */
    div[data-testid="stExpander"]{
        border:1px solid #F1E4D6; border-radius:14px; background:#fff;
        box-shadow:0 2px 10px rgba(190,150,120,.07); overflow:hidden;
    }
    .stTabs [data-baseweb="tab-list"]{ gap:6px; border-bottom:1px solid #F1E4D6; }
    .stTabs [data-baseweb="tab"]{
        border-radius:10px 10px 0 0; padding:8px 16px; font-weight:600;
    }
    .stTabs [aria-selected="true"]{ background:#FFF3E9; color:#C9633F !important; }

    /* ---------- SECCIONES ---------- */
    .sect{
        display:flex; align-items:center; gap:10px; margin:26px 0 12px;
        font-size:1.06rem; font-weight:700; color:#3A3128;
    }
    .sect:before{
        content:""; width:5px; height:22px; border-radius:4px;
        background:linear-gradient(180deg,#C9633F,#E9A03B);
    }

    /* ---------- CARDS ---------- */
    .card{
        background:#fff; border:1px solid #F1E4D6; border-radius:14px;
        padding:14px 16px; margin-bottom:10px;
        box-shadow:0 2px 10px rgba(190,150,120,.07);
    }
    .row{
        display:flex; align-items:center; gap:12px; padding:10px 14px;
        background:#fff; border:1px solid #F1E4D6; border-left:4px solid #C9633F;
        border-radius:12px; margin-bottom:8px;
        box-shadow:0 2px 8px rgba(190,150,120,.06);
    }
    .row .nm{ font-weight:700; color:#2F2A26; }
    .row .dt{ color:#8A7566; font-size:.86rem; }
    .pill{
        display:inline-block; padding:2px 10px; border-radius:20px;
        font-size:.72rem; font-weight:700; letter-spacing:.2px;
    }

    /* ---------- TABLAS ---------- */
    div[data-testid="stDataFrame"], div[data-testid="stDataEditor"]{
        border:1px solid #F1E4D6; border-radius:14px; overflow:hidden;
        box-shadow:0 2px 10px rgba(190,150,120,.07);
    }
    hr{ border-color:#F2E6D9 !important; }
    #MainMenu, footer{ visibility:hidden; }
    </style>
    """, unsafe_allow_html=True)

def hero(titulo, sub):
    st.markdown(f'<div class="hero"><h1>{titulo}</h1><p>{sub}</p></div>',
                unsafe_allow_html=True)

def sect(txt):
    st.markdown(f'<div class="sect">{txt}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# PERSISTENCIA
# ═══════════════════════════════════════════════════════════════════════════
COLS_EMPLEADOS = ["id", "nombre", "pais", "puesto", "email",
                  "fecha_ingreso", "dias_asignados", "activo"]
COLS_VACACIONES = ["id", "empleado_id", "fecha_inicio", "fecha_fin",
                   "tipo", "estado", "comentario"]
COLS_FERIADOS = ["id", "pais", "fecha", "descripcion"]

def _ensure_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    for path, cols in [(F_EMPLEADOS, COLS_EMPLEADOS),
                       (F_VACACIONES, COLS_VACACIONES),
                       (F_FERIADOS, COLS_FERIADOS)]:
        if not os.path.exists(path):
            pd.DataFrame(columns=cols).to_csv(path, index=False)

def load_csv(path, cols):
    _ensure_files()
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    except (pd.errors.EmptyDataError, FileNotFoundError):
        df = pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df[cols].copy()

def save_csv(df, path):
    df.to_csv(path, index=False)

def _txt(serie):
    """Normaliza cualquier columna a texto limpio (mata los NaN/float)."""
    return (serie.astype("object").where(serie.notna(), "").astype(str)
            .replace({"nan": "", "None": "", "<NA>": "", "NaN": ""}).str.strip())

def get_empleados():
    df = load_csv(F_EMPLEADOS, COLS_EMPLEADOS)
    df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)
    df["dias_asignados"] = pd.to_numeric(df["dias_asignados"], errors="coerce").fillna(0).astype(int)
    df["activo"] = _txt(df["activo"]).str.lower().isin(
        ["true", "1", "si", "sí", "yes", "verdadero", "x"])
    for c in ["nombre", "pais", "puesto", "email", "fecha_ingreso"]:
        df[c] = _txt(df[c])
    df.loc[~df["pais"].isin(PAISES), "pais"] = PAISES[0]
    return df.reset_index(drop=True)

def get_vacaciones():
    df = load_csv(F_VACACIONES, COLS_VACACIONES)
    df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)
    df["empleado_id"] = pd.to_numeric(df["empleado_id"], errors="coerce").fillna(0).astype(int)
    for c in ["tipo", "estado", "comentario"]:
        df[c] = _txt(df[c])
    df.loc[~df["tipo"].isin(TIPOS), "tipo"] = TIPOS[0]
    df.loc[~df["estado"].isin(ESTADOS), "estado"] = ESTADOS[1]
    if not df.empty:
        df["fecha_inicio"] = pd.to_datetime(df["fecha_inicio"], errors="coerce").dt.date
        df["fecha_fin"] = pd.to_datetime(df["fecha_fin"], errors="coerce").dt.date
        df = df.dropna(subset=["fecha_inicio", "fecha_fin"])
    return df.reset_index(drop=True)

def get_feriados():
    df = load_csv(F_FERIADOS, COLS_FERIADOS)
    df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)
    for c in ["pais", "descripcion"]:
        df[c] = _txt(df[c])
    df.loc[~df["pais"].isin(PAISES), "pais"] = PAISES[0]
    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
        df = df.dropna(subset=["fecha"])
    return df.reset_index(drop=True)

def next_id(df):
    if df.empty:
        return 1
    return int(pd.to_numeric(df["id"], errors="coerce").fillna(0).max()) + 1

def bump(k):
    """Refresca la key del data_editor para que no queden ediciones fantasma."""
    st.session_state[k] = st.session_state.get(k, 0) + 1

def ver(k):
    return st.session_state.setdefault(k, 0)

# ═══════════════════════════════════════════════════════════════════════════
# LÓGICA DE NEGOCIO
# ═══════════════════════════════════════════════════════════════════════════
def feriados_por_pais(df):
    out = {p: set() for p in PAISES}
    for _, r in df.iterrows():
        out.setdefault(r["pais"], set()).add(r["fecha"])
    return out

def dias_habiles(ini, fin, fset):
    if ini is None or fin is None or fin < ini:
        return 0
    n, d = 0, ini
    while d <= fin:
        if d.weekday() < 5 and d not in fset:
            n += 1
        d += timedelta(days=1)
    return n

def dias_naturales(ini, fin):
    return 0 if fin < ini else (fin - ini).days + 1

def resumen_empleados(emp, vac, fer, anio):
    fset = feriados_por_pais(fer)
    filas = []
    for _, e in emp.iterrows():
        v = vac[(vac["empleado_id"] == e["id"]) & (vac["tipo"] == "Vacaciones")]
        tom = apr = sol = 0
        for _, r in v.iterrows():
            if r["fecha_inicio"].year != anio and r["fecha_fin"].year != anio:
                continue
            d = dias_habiles(r["fecha_inicio"], r["fecha_fin"], fset.get(e["pais"], set()))
            if r["estado"] == "Tomada":
                tom += d
            elif r["estado"] == "Aprobada":
                apr += d
            elif r["estado"] == "Solicitada":
                sol += d
        comp = tom + apr
        asg = int(e["dias_asignados"])
        filas.append({
            "ID": e["id"],
            "Colaborador": e["nombre"],
            "País": f'{BANDERAS.get(e["pais"],"")} {e["pais"]}',
            "Puesto": e["puesto"],
            "Días asignados": asg,
            "Tomados": tom,
            "Proyectados": apr,
            "En solicitud": sol,
            "Comprometidos": comp,
            "Saldo": asg - comp,
            "% consumido": round(100 * comp / asg, 1) if asg else 0.0,
            "Activo": bool(e["activo"]),
        })
    return pd.DataFrame(filas)

def expandir_dias(vac, emp, cmap):
    mapa = {}
    nom = dict(zip(emp["id"], emp["nombre"]))
    pai = dict(zip(emp["id"], emp["pais"]))
    for _, r in vac.iterrows():
        eid = r["empleado_id"]
        if eid not in nom:
            continue
        d = r["fecha_inicio"]
        while d <= r["fecha_fin"]:
            mapa.setdefault(d, []).append({
                "nombre": nom[eid], "pais": pai.get(eid, ""),
                "estado": r["estado"], "tipo": r["tipo"],
                "color": cmap.get(eid, "#C9633F"),
            })
            d += timedelta(days=1)
    return mapa

def color_map_personas(emp):
    return {eid: PALETA_PERSONAS[i % len(PALETA_PERSONAS)]
            for i, eid in enumerate(emp["id"].tolist())}

# --------- Generadores de feriados oficiales ---------
def _nth_weekday(anio, mes, weekday, n):
    d = date(anio, mes, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)

def _pascua(anio):
    a = anio % 19
    b, c = divmod(anio, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(anio, mes, dia)

def _lunes_siguiente(d):
    return d if d.weekday() == 0 else d + timedelta(days=(7 - d.weekday()))

def feriados_mexico(a):
    return [
        (date(a, 1, 1), "Año Nuevo"),
        (_nth_weekday(a, 2, 0, 1), "Día de la Constitución"),
        (_nth_weekday(a, 3, 0, 3), "Natalicio de Benito Juárez"),
        (date(a, 5, 1), "Día del Trabajo"),
        (date(a, 9, 16), "Independencia de México"),
        (_nth_weekday(a, 11, 0, 3), "Revolución Mexicana"),
        (date(a, 12, 25), "Navidad"),
    ]

def feriados_colombia(a):
    p = _pascua(a)
    fijos = [(date(a, 1, 1), "Año Nuevo"), (date(a, 5, 1), "Día del Trabajo"),
             (date(a, 7, 20), "Independencia"), (date(a, 8, 7), "Batalla de Boyacá"),
             (date(a, 12, 8), "Inmaculada Concepción"), (date(a, 12, 25), "Navidad")]
    moviles = [(date(a, 1, 6), "Reyes Magos"), (date(a, 3, 19), "San José"),
               (date(a, 6, 29), "San Pedro y San Pablo"), (date(a, 8, 15), "Asunción"),
               (date(a, 10, 12), "Día de la Raza"), (date(a, 11, 1), "Todos los Santos"),
               (date(a, 11, 11), "Independencia de Cartagena")]
    pascuales = [(p - timedelta(days=3), "Jueves Santo"),
                 (p - timedelta(days=2), "Viernes Santo"),
                 (p + timedelta(days=43), "Ascensión del Señor"),
                 (p + timedelta(days=64), "Corpus Christi"),
                 (p + timedelta(days=71), "Sagrado Corazón")]
    return fijos + [(_lunes_siguiente(d), n) for d, n in moviles] + pascuales

# ═══════════════════════════════════════════════════════════════════════════
# CALENDARIO
# ═══════════════════════════════════════════════════════════════════════════
CAL_CSS = """
<style>
.calwrap{border:1px solid #F0E2D4;border-radius:18px;overflow:hidden;
         box-shadow:0 8px 26px rgba(190,150,120,.13);background:#fff;margin-top:6px;}
table.cal{width:100%;border-collapse:collapse;font-family:'Inter',system-ui,sans-serif;}
table.cal th{background:linear-gradient(135deg,#C9633F 0%,#E08A63 100%);
             color:#fff;padding:10px 6px;font-size:.76rem;font-weight:700;
             letter-spacing:1.1px;text-transform:uppercase;border:none;}
table.cal td{vertical-align:top;height:104px;width:14.28%;
             border:1px solid #F5EBE0;padding:5px 6px;background:#fff;}
td.out{background:#FFFFFF;}
td.out .dn{color:#EDE4DA;}
td.wknd{background:#FFFBF6;}
td.past{background:#FFF6EC;}
td.past .dn{color:#C4B2A2;}
td.wknd.past{background:#FDF3E8;}
td.today{box-shadow:inset 0 0 0 2px #C9633F;background:#FFF2EA !important;}
.dn{font-weight:700;font-size:.86rem;color:#453A30;margin-bottom:4px;
    display:flex;align-items:center;gap:5px;}
.dn .bul{background:#C9633F;color:#fff;border-radius:50%;width:20px;height:20px;
         display:inline-flex;align-items:center;justify-content:center;font-size:.72rem;}
.fchip{display:block;font-size:.63rem;font-weight:700;border-radius:5px;
       padding:1px 5px;margin-bottom:3px;white-space:nowrap;overflow:hidden;
       text-overflow:ellipsis;}
.chip{display:block;font-size:.66rem;font-weight:600;border-radius:6px;
      padding:2px 6px;margin-bottom:3px;white-space:nowrap;overflow:hidden;
      text-overflow:ellipsis;border-left:3px solid #999;}
.leg{display:flex;flex-wrap:wrap;gap:8px;margin:4px 0 8px;}
.leg span{font-size:.72rem;font-weight:700;padding:4px 11px;border-radius:20px;
          border:1px solid rgba(0,0,0,.05);}
</style>
"""

def leyenda(estados_visibles):
    h = '<div class="leg">'
    for e in ESTADOS:
        if e in estados_visibles:
            bg, tx, _ = ESTADO_STYLE[e]
            h += f'<span style="background:{bg};color:{tx}">● {e}</span>'
    for p, (bg, bd, tx) in FERIADO_STYLE.items():
        h += (f'<span style="background:{bg};color:{tx};border:1px solid {bd}">'
              f'{BANDERAS[p]} Feriado {p}</span>')
    h += ('<span style="background:#FFF6EC;color:#A9917C">◷ Días pasados</span>'
          '<span style="background:#FFF2EA;color:#C9633F;border:1px solid #C9633F">Hoy</span></div>')
    return h

def render_calendario(anio, mes, mapa, fer_dict, filtro_pais):
    hoy = date.today()
    fer_all = {}
    for p, s in fer_dict.items():
        for f in s:
            fer_all.setdefault(f, []).append(p)

    html = CAL_CSS + '<div class="calwrap"><table class="cal"><tr>'
    html += "".join(f"<th>{d}</th>" for d in DIAS_ES) + "</tr>"

    for semana in calendar.Calendar(firstweekday=0).monthdatescalendar(anio, mes):
        html += "<tr>"
        for d in semana:
            cls, style = [], ""
            in_month = d.month == mes and d.year == anio
            if not in_month:
                cls.append("out")
            else:
                if d.weekday() >= 5:
                    cls.append("wknd")
                if d < hoy:
                    cls.append("past")
                if d == hoy:
                    cls.append("today")
                paises_f = fer_all.get(d, [])
                if len(paises_f) == 1:
                    bg, bd, _ = FERIADO_STYLE[paises_f[0]]
                    style = f"background:{bg} !important;border-left:4px solid {bd} !important;"
                elif len(paises_f) > 1:
                    style = ("background:linear-gradient(135deg,#E4F7EC 0%,#E4F7EC 48%,"
                             "#FFF6C9 52%,#FFF6C9 100%) !important;"
                             "border-left:4px solid #17A673 !important;")

            num = (f'<span class="bul">{d.day}</span>' if d == hoy and in_month
                   else str(d.day))
            html += f'<td class="{" ".join(cls)}" style="{style}"><div class="dn">{num}</div>'

            if in_month:
                for p in fer_all.get(d, []):
                    bg, bd, tx = FERIADO_STYLE[p]
                    html += (f'<span class="fchip" style="background:{bd}22;color:{tx};'
                             f'border:1px solid {bd}">{BANDERAS[p]} Feriado</span>')
                for it in mapa.get(d, []):
                    if filtro_pais and it["pais"] not in filtro_pais:
                        continue
                    bg, tx, _ = ESTADO_STYLE.get(it["estado"], ("#EEE", "#444", "#999"))
                    ic = "🌴" if it["tipo"] == "Vacaciones" else "•"
                    html += (f'<span class="chip" style="background:{bg};color:{tx};'
                             f'border-left-color:{it["color"]}" '
                             f'title="{it["nombre"]} — {it["tipo"]} ({it["estado"]})">'
                             f'{ic} {it["nombre"]}</span>')
            html += "</td>"
        html += "</tr>"
    html += "</table></div>"
    st.markdown(html, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# APP
# ═══════════════════════════════════════════════════════════════════════════
inject_css()
_ensure_files()

st.sidebar.markdown(
    '<div style="text-align:center;padding:6px 0 14px">'
    '<div style="font-size:2.4rem;line-height:1">🏖️</div>'
    '<div style="font-weight:800;font-size:1.05rem;color:#3A3128">Control de Vacaciones</div>'
    '<div style="font-size:.74rem;color:#9B8574;font-weight:600;letter-spacing:.6px">'
    'MÉXICO 🇲🇽 · COLOMBIA 🇨🇴</div></div>', unsafe_allow_html=True)

seccion = st.sidebar.radio("Navegación", [
    "📊 Dashboard", "👥 Equipo", "🗓️ Vacaciones", "📅 Calendario",
    "🇲🇽 Feriados México", "🇨🇴 Feriados Colombia", "💾 Datos"],
    label_visibility="collapsed")

st.sidebar.divider()
anio_sel = st.sidebar.number_input("Año de trabajo", 2020, 2100, date.today().year, step=1)
st.sidebar.caption(f"📆 Hoy: {date.today().strftime('%d/%m/%Y')}")

emp = get_empleados()
vac = get_vacaciones()
fer = get_feriados()
fer_dict = feriados_por_pais(fer)
cmap = color_map_personas(emp)
nombres = dict(zip(emp["id"], emp["nombre"]))
paises = dict(zip(emp["id"], emp["pais"]))

# ─────────────────────────────── DASHBOARD ───────────────────────────────
if seccion == "📊 Dashboard":
    hero("📊 Panel de control del equipo",
         f"Resumen consolidado de vacaciones · Ejercicio {int(anio_sel)}")

    if emp.empty:
        st.info("👋 Aún no hay colaboradores. Ve a **👥 Equipo** para agregar el primero.")
        st.stop()

    res = resumen_empleados(emp, vac, fer, int(anio_sel))
    act = res[res["Activo"]]

    c = st.columns(5)
    c[0].metric("👥 Colaboradores", len(act))
    c[1].metric("🎯 Días asignados", int(act["Días asignados"].sum()))
    c[2].metric("✅ Días tomados", int(act["Tomados"].sum()))
    c[3].metric("📌 Proyectados", int(act["Proyectados"].sum()))
    c[4].metric("💰 Saldo total", int(act["Saldo"].sum()))

    hoy = date.today()
    col1, col2 = st.columns(2)

    with col1:
        sect("🌴 Ausentes hoy")
        h = vac[(vac["fecha_inicio"] <= hoy) & (vac["fecha_fin"] >= hoy) &
                (vac["estado"].isin(["Aprobada", "Tomada"]))]
        if h.empty:
            st.success("Todo el equipo está disponible hoy 🎉")
        else:
            for _, r in h.iterrows():
                col = cmap.get(r["empleado_id"], "#C9633F")
                bg, tx, _ = ESTADO_STYLE[r["estado"]]
                st.markdown(
                    f'<div class="row" style="border-left-color:{col}">'
                    f'<div style="flex:1"><span class="nm">{nombres.get(r["empleado_id"],"?")}</span>'
                    f' <span class="pill" style="background:{bg};color:{tx}">{r["tipo"]}</span><br>'
                    f'<span class="dt">Regresa el '
                    f'{(r["fecha_fin"]+timedelta(days=1)).strftime("%d/%m/%Y")}</span></div>'
                    f'</div>', unsafe_allow_html=True)

    with col2:
        sect("⏭️ Próximas ausencias (30 días)")
        p = vac[(vac["fecha_inicio"] > hoy) & (vac["fecha_inicio"] <= hoy + timedelta(days=30)) &
                (vac["estado"].isin(["Aprobada", "Solicitada"]))].sort_values("fecha_inicio")
        if p.empty:
            st.info("Sin ausencias programadas en los próximos 30 días.")
        else:
            for _, r in p.iterrows():
                col = cmap.get(r["empleado_id"], "#C9633F")
                bg, tx, _ = ESTADO_STYLE[r["estado"]]
                dias_para = (r["fecha_inicio"] - hoy).days
                st.markdown(
                    f'<div class="row" style="border-left-color:{col}">'
                    f'<div style="flex:1"><span class="nm">{nombres.get(r["empleado_id"],"?")}</span>'
                    f' <span class="pill" style="background:{bg};color:{tx}">{r["estado"]}</span><br>'
                    f'<span class="dt">{r["fecha_inicio"].strftime("%d/%m")} — '
                    f'{r["fecha_fin"].strftime("%d/%m")} · en {dias_para} días</span></div>'
                    f'</div>', unsafe_allow_html=True)

    sect("📈 Distribución de días por colaborador")
    pl = act.melt(id_vars="Colaborador", value_vars=["Tomados", "Proyectados", "Saldo"],
                  var_name="Concepto", value_name="Días")
    fig = px.bar(pl, x="Colaborador", y="Días", color="Concepto", barmode="stack",
                 height=420, template="plotly_white",
                 color_discrete_map={"Tomados": "#3B82F6", "Proyectados": "#17A673",
                                     "Saldo": "#E9CBB5"})
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=1.12, x=0),
                      margin=dict(l=10, r=10, t=30, b=10),
                      font=dict(family="Inter", color="#3A3128"))
    fig.update_yaxes(gridcolor="#F2E6D9")
    st.plotly_chart(fig, use_container_width=True)

    sect("🧾 Detalle por colaborador")
    st.dataframe(res.drop(columns=["ID"]), use_container_width=True, hide_index=True,
                 column_config={"% consumido": st.column_config.ProgressColumn(
                     "% consumido", min_value=0, max_value=100, format="%.1f%%")})

# ─────────────────────────────── EQUIPO ───────────────────────────────
elif seccion == "👥 Equipo":
    hero("👥 Miembros del equipo", "Sin límite de integrantes · agrega, edita y elimina")

    with st.expander("➕ Agregar colaborador", expanded=emp.empty):
        with st.form("f_emp", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            nombre = c1.text_input("Nombre completo *")
            pais = c2.selectbox("País *", PAISES)
            puesto = c3.text_input("Puesto")
            c4, c5, c6 = st.columns(3)
            email = c4.text_input("Email")
            ingreso = c5.date_input("Fecha de ingreso", value=date.today(),
                                    min_value=date(1980, 1, 1), max_value=date(2100, 12, 31))
            dias = c6.number_input("Días de vacaciones / año", 0, 365, 12)
            if st.form_submit_button("💾 Guardar colaborador", type="primary"):
                if not nombre.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    df = get_empleados()
                    nuevo = pd.DataFrame([{
                        "id": next_id(df), "nombre": nombre.strip(), "pais": pais,
                        "puesto": puesto.strip(), "email": email.strip(),
                        "fecha_ingreso": ingreso.isoformat(),
                        "dias_asignados": int(dias), "activo": True}])
                    save_csv(pd.concat([df, nuevo], ignore_index=True), F_EMPLEADOS)
                    bump("v_emp")
                    st.success(f"✅ {nombre} agregado.")
                    st.rerun()

    if emp.empty:
        st.info("Todavía no hay colaboradores registrados.")
        st.stop()

    tab1, tab2 = st.tabs(["✏️ Editar equipo", "🗑️ Eliminar colaboradores"])

    with tab1:
        st.caption("Modifica las celdas y presiona **Guardar cambios**.")
        ed = st.data_editor(
            emp, use_container_width=True, hide_index=True, num_rows="fixed",
            key=f"ed_emp_{ver('v_emp')}", disabled=["id"],
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "nombre": st.column_config.TextColumn("Nombre", required=True),
                "pais": st.column_config.SelectboxColumn("País", options=PAISES, required=True),
                "puesto": st.column_config.TextColumn("Puesto"),
                "email": st.column_config.TextColumn("Email"),
                "fecha_ingreso": st.column_config.TextColumn("Ingreso (YYYY-MM-DD)"),
                "dias_asignados": st.column_config.NumberColumn("Días/año", min_value=0, max_value=365),
                "activo": st.column_config.CheckboxColumn("Activo"),
            })
        if st.button("💾 Guardar cambios", type="primary", key="sv_emp"):
            save_csv(ed, F_EMPLEADOS)
            bump("v_emp")
            st.success("Cambios guardados.")
            st.rerun()

    with tab2:
        st.warning("⚠️ Al eliminar un colaborador también se borran **todos sus periodos** de vacaciones.")
        etiquetas = {f'#{r["id"]} · {r["nombre"]} ({r["pais"]})': r["id"]
                     for _, r in emp.iterrows()}
        sel = st.multiselect("Selecciona a quién eliminar", list(etiquetas.keys()))
        conf = st.checkbox("Confirmo que deseo eliminarlos permanentemente")
        if st.button("🗑️ Eliminar seleccionados", type="primary", disabled=not (sel and conf)):
            ids = [etiquetas[s] for s in sel]
            base = get_empleados()
            save_csv(base[~base["id"].isin(ids)], F_EMPLEADOS)
            v = get_vacaciones()
            save_csv(v[~v["empleado_id"].isin(ids)], F_VACACIONES)
            bump("v_emp"); bump("v_vac")
            st.success(f"Eliminados: {len(ids)} colaborador(es).")
            st.rerun()

# ─────────────────────────────── VACACIONES ───────────────────────────────
elif seccion == "🗓️ Vacaciones":
    hero("🗓️ Registro y proyección de vacaciones",
         "Cálculo automático de días hábiles según los feriados de cada país")

    if emp.empty:
        st.warning("Primero registra colaboradores en **👥 Equipo**.")
        st.stop()

    ops = {f'{r["nombre"]} {BANDERAS.get(r["pais"],"")}': r["id"] for _, r in emp.iterrows()}

    with st.expander("➕ Registrar periodo de vacaciones / ausencia", expanded=True):
        with st.form("f_vac", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            quien = c1.selectbox("Colaborador *", list(ops.keys()))
            tipo = c2.selectbox("Tipo", TIPOS)
            estado = c3.selectbox("Estado", ESTADOS, index=1)
            c4, c5 = st.columns(2)
            f_ini = c4.date_input("Fecha inicio *", value=date.today())
            f_fin = c5.date_input("Fecha fin *", value=date.today() + timedelta(days=4))
            coment = st.text_input("Comentario")

            eid = ops[quien]
            pe = emp.loc[emp["id"] == eid, "pais"].iloc[0]
            dh = dias_habiles(f_ini, f_fin, fer_dict.get(pe, set()))
            st.info(f"📌 **{dh} días hábiles** · {dias_naturales(f_ini, f_fin)} naturales "
                    f"(descontando fines de semana y feriados de {pe} {BANDERAS.get(pe,'')})")

            if st.form_submit_button("💾 Guardar periodo", type="primary"):
                if f_fin < f_ini:
                    st.error("La fecha fin no puede ser anterior a la de inicio.")
                else:
                    df = get_vacaciones()
                    tras = df[(df["empleado_id"] == eid) &
                              (df["fecha_inicio"] <= f_fin) & (df["fecha_fin"] >= f_ini)]
                    if not tras.empty:
                        st.error("⚠️ Ya existe un periodo que se traslapa con esas fechas.")
                    else:
                        nuevo = pd.DataFrame([{
                            "id": next_id(df), "empleado_id": eid,
                            "fecha_inicio": f_ini.isoformat(), "fecha_fin": f_fin.isoformat(),
                            "tipo": tipo, "estado": estado, "comentario": coment}])
                        save_csv(pd.concat([df, nuevo], ignore_index=True), F_VACACIONES)
                        bump("v_vac")
                        st.success("✅ Periodo registrado.")
                        st.rerun()

    if vac.empty:
        st.info("Sin periodos registrados aún.")
        st.stop()

    tabla = vac.copy()
    tabla["Colaborador"] = tabla["empleado_id"].map(nombres).fillna("(eliminado)")
    tabla["País"] = tabla["empleado_id"].map(paises).fillna("")
    tabla["Días hábiles"] = tabla.apply(lambda r: dias_habiles(
        r["fecha_inicio"], r["fecha_fin"], fer_dict.get(paises.get(r["empleado_id"], ""), set())), axis=1)
    tabla["Días naturales"] = tabla.apply(
        lambda r: dias_naturales(r["fecha_inicio"], r["fecha_fin"]), axis=1)

    tab1, tab2, tab3 = st.tabs(["📋 Periodos", "🗑️ Eliminar periodos", "📊 Proyección"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        f1 = c1.multiselect("Colaborador", sorted(set(tabla["Colaborador"])))
        f2 = c2.multiselect("Estado", ESTADOS)
        f3 = c3.multiselect("País", PAISES)
        t = tabla.copy()
        if f1: t = t[t["Colaborador"].isin(f1)]
        if f2: t = t[t["estado"].isin(f2)]
        if f3: t = t[t["País"].isin(f3)]

        vista = (t[["id", "Colaborador", "País", "fecha_inicio", "fecha_fin",
                    "Días hábiles", "Días naturales", "tipo", "estado", "comentario"]]
                 .sort_values("fecha_inicio", ascending=False)
                 .rename(columns={"id": "ID", "fecha_inicio": "Inicio", "fecha_fin": "Fin",
                                  "tipo": "Tipo", "estado": "Estado", "comentario": "Comentario"}))
        ed = st.data_editor(
            vista, use_container_width=True, hide_index=True, num_rows="fixed",
            key=f"ed_vac_{ver('v_vac')}",
            disabled=["ID", "Colaborador", "País", "Días hábiles", "Días naturales"],
            column_config={
                "Inicio": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Fin": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Tipo": st.column_config.SelectboxColumn(options=TIPOS),
                "Estado": st.column_config.SelectboxColumn(options=ESTADOS),
                "Comentario": st.column_config.TextColumn(),
            })
        if st.button("💾 Guardar cambios en periodos", type="primary", key="sv_vac"):
            base = get_vacaciones()
            for _, r in ed.iterrows():
                i = base.index[base["id"] == r["ID"]]
                if len(i):
                    base.loc[i, "fecha_inicio"] = pd.to_datetime(r["Inicio"]).date().isoformat()
                    base.loc[i, "fecha_fin"] = pd.to_datetime(r["Fin"]).date().isoformat()
                    base.loc[i, "tipo"] = r["Tipo"]
                    base.loc[i, "estado"] = r["Estado"]
                    base.loc[i, "comentario"] = r["Comentario"]
            save_csv(base, F_VACACIONES)
            bump("v_vac")
            st.success("Cambios guardados.")
            st.rerun()

    with tab2:
        etq = {f'#{r["id"]} · {r["Colaborador"]} · '
               f'{r["fecha_inicio"].strftime("%d/%m/%Y")} → {r["fecha_fin"].strftime("%d/%m/%Y")} '
               f'({r["estado"]})': r["id"]
               for _, r in tabla.sort_values("fecha_inicio", ascending=False).iterrows()}
        sel = st.multiselect("Selecciona los periodos a eliminar", list(etq.keys()))
        conf = st.checkbox("Confirmo la eliminación", key="cf_vac")
        if st.button("🗑️ Eliminar periodos", type="primary", disabled=not (sel and conf)):
            ids = [etq[s] for s in sel]
            base = get_vacaciones()
            save_csv(base[~base["id"].isin(ids)], F_VACACIONES)
            bump("v_vac")
            st.success(f"Eliminados: {len(ids)} periodo(s).")
            st.rerun()

    with tab3:
        res = resumen_empleados(emp, vac, fer, int(anio_sel))
        st.dataframe(res[["Colaborador", "País", "Días asignados", "Tomados", "Proyectados",
                          "En solicitud", "Comprometidos", "Saldo", "% consumido"]],
                     use_container_width=True, hide_index=True,
                     column_config={"% consumido": st.column_config.ProgressColumn(
                         "% consumido", min_value=0, max_value=100, format="%.1f%%")})
        st.download_button("⬇️ Descargar proyección (CSV)",
                           res.to_csv(index=False).encode("utf-8-sig"),
                           f"proyeccion_vacaciones_{int(anio_sel)}.csv", "text/csv")

# ─────────────────────────────── CALENDARIO ───────────────────────────────
elif seccion == "📅 Calendario":
    hero("📅 Calendario del equipo",
         "Vista mensual y línea de tiempo anual de ausencias")

    if emp.empty:
        st.warning("Registra colaboradores para ver el calendario.")
        st.stop()

    c1, c2, c3, c4 = st.columns([1.1, 1, 1.4, 1.8])
    mes = c1.selectbox("Mes", range(1, 13), index=date.today().month - 1,
                       format_func=lambda m: MESES_ES[m - 1])
    anio_cal = c2.number_input("Año", 2020, 2100, int(anio_sel), step=1, key="a_cal")
    pf = c3.multiselect("País", PAISES, default=PAISES)
    ef = c4.multiselect("Estados", ESTADOS, default=["Solicitada", "Aprobada", "Tomada"])

    vf = vac[vac["estado"].isin(ef)] if not vac.empty else vac
    st.markdown(CAL_CSS + leyenda(ef), unsafe_allow_html=True)
    st.markdown(f'<div class="sect">{MESES_ES[mes-1]} {int(anio_cal)}</div>',
                unsafe_allow_html=True)

    mapa = expandir_dias(vf, emp, cmap) if not vf.empty else {}
    render_calendario(int(anio_cal), mes, mapa, fer_dict, pf)

    sect("📈 Línea de tiempo anual")
    if vf.empty:
        st.info("Sin periodos para graficar.")
    else:
        g = vf.copy()
        g["Colaborador"] = g["empleado_id"].map(nombres)
        g["País"] = g["empleado_id"].map(paises)
        g = g.dropna(subset=["Colaborador"])
        g = g[g["País"].isin(pf)]
        g = g[(pd.to_datetime(g["fecha_inicio"]).dt.year <= int(anio_cal)) &
              (pd.to_datetime(g["fecha_fin"]).dt.year >= int(anio_cal))]
        if g.empty:
            st.info("Sin periodos en el año seleccionado.")
        else:
            g["Inicio"] = pd.to_datetime(g["fecha_inicio"])
            g["Fin"] = pd.to_datetime(g["fecha_fin"]) + pd.Timedelta(days=1)
            fig = px.timeline(g, x_start="Inicio", x_end="Fin", y="Colaborador",
                              color="estado", hover_data=["tipo", "comentario", "País"],
                              color_discrete_map=COLOR_ESTADO, template="plotly_white",
                              height=120 + 34 * g["Colaborador"].nunique())
            fig.update_yaxes(autorange="reversed", gridcolor="#F2E6D9", title=None)
            fig.update_xaxes(gridcolor="#F2E6D9",
                             range=[f"{int(anio_cal)}-01-01", f"{int(anio_cal)}-12-31"])
            fig.add_vline(x=datetime.now(), line_dash="dash", line_color="#C9633F")
            fig.update_traces(marker_line_color="white", marker_line_width=1.2, opacity=.92)
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                              legend=dict(orientation="h", y=1.12, x=0, title=None),
                              margin=dict(l=10, r=10, t=30, b=10),
                              font=dict(family="Inter", color="#3A3128"))
            st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────── FERIADOS ───────────────────────────────
elif seccion in ("🇲🇽 Feriados México", "🇨🇴 Feriados Colombia"):
    pais = "México" if "México" in seccion else "Colombia"
    bg, bd, tx = FERIADO_STYLE[pais]
    hero(f"{BANDERAS[pais]} Días feriados — {pais}",
         "Estos días no se descuentan del saldo de vacaciones de los colaboradores de este país")

    st.markdown(f'<div class="card" style="border-left:5px solid {bd};background:{bg}">'
                f'<b style="color:{tx}">Color en el calendario:</b> '
                f'<span class="pill" style="background:{bd};color:#fff">'
                f'{"Verde" if pais=="México" else "Amarillo"}</span></div>',
                unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        with st.form(f"f_fer_{pais}", clear_on_submit=True):
            a, b = st.columns([1, 2])
            f = a.date_input("Fecha", value=date(int(anio_sel), 1, 1))
            desc = b.text_input("Descripción", placeholder="Ej. Día de la Independencia")
            if st.form_submit_button("➕ Agregar feriado", type="primary"):
                df = get_feriados()
                if not df.empty and ((df["pais"] == pais) & (df["fecha"] == f)).any():
                    st.warning("Ese feriado ya existe.")
                else:
                    nuevo = pd.DataFrame([{"id": next_id(df), "pais": pais,
                                           "fecha": f.isoformat(),
                                           "descripcion": desc.strip() or "Feriado"}])
                    save_csv(pd.concat([df, nuevo], ignore_index=True), F_FERIADOS)
                    bump("v_fer")
                    st.success("Feriado agregado.")
                    st.rerun()
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(f"⚡ Cargar oficiales {int(anio_sel)}", use_container_width=True):
            base = get_feriados()
            oficiales = (feriados_mexico(int(anio_sel)) if pais == "México"
                         else feriados_colombia(int(anio_sel)))
            existentes = set(base[base["pais"] == pais]["fecha"]) if not base.empty else set()
            nuevos = []
            nid = next_id(base)
            for d, n in sorted(oficiales):
                if d not in existentes:
                    nuevos.append({"id": nid, "pais": pais, "fecha": d.isoformat(),
                                   "descripcion": n})
                    nid += 1
            if nuevos:
                save_csv(pd.concat([base, pd.DataFrame(nuevos)], ignore_index=True), F_FERIADOS)
                bump("v_fer")
                st.success(f"Agregados {len(nuevos)} feriados de {pais} {int(anio_sel)}.")
                st.rerun()
            else:
                st.info("Ya están todos cargados.")

    fp = fer[fer["pais"] == pais].copy()
    if not fp.empty:
        fp = fp[pd.to_datetime(fp["fecha"]).dt.year == int(anio_sel)]

    if fp.empty:
        st.info(f"No hay feriados registrados para {pais} en {int(anio_sel)}. "
                "Usa **⚡ Cargar oficiales** para llenarlos de golpe.")
        st.stop()

    m1, m2 = st.columns(2)
    m1.metric(f"🎉 Total feriados {int(anio_sel)}", len(fp))
    m2.metric("📅 En día hábil (lun-vie)",
              int(sum(1 for d in fp["fecha"] if d.weekday() < 5)))

    tab1, tab2 = st.tabs(["✏️ Editar", "🗑️ Eliminar"])

    with tab1:
        fp["Día"] = fp["fecha"].apply(lambda d: DIAS_ES[d.weekday()])
        fp["Mes"] = fp["fecha"].apply(lambda d: MESES_ES[d.month - 1])
        vista = (fp[["id", "fecha", "Día", "Mes", "descripcion"]].sort_values("fecha")
                 .rename(columns={"id": "ID", "fecha": "Fecha", "descripcion": "Descripción"}))
        ed = st.data_editor(vista, use_container_width=True, hide_index=True, num_rows="fixed",
                            key=f"ed_fer_{pais}_{ver('v_fer')}", disabled=["ID", "Día", "Mes"],
                            column_config={
                                "Fecha": st.column_config.DateColumn(format="DD/MM/YYYY"),
                                "Descripción": st.column_config.TextColumn()})
        if st.button("💾 Guardar feriados", type="primary", key=f"sv_fer_{pais}"):
            base = get_feriados()
            for _, r in ed.iterrows():
                i = base.index[base["id"] == r["ID"]]
                if len(i):
                    base.loc[i, "fecha"] = pd.to_datetime(r["Fecha"]).date().isoformat()
                    base.loc[i, "descripcion"] = r["Descripción"]
            save_csv(base, F_FERIADOS)
            bump("v_fer")
            st.success("Feriados actualizados.")
            st.rerun()

    with tab2:
        etq = {f'{r["fecha"].strftime("%d/%m/%Y")} — {r["descripcion"]}': r["id"]
               for _, r in fp.sort_values("fecha").iterrows()}
        sel = st.multiselect("Selecciona los feriados a eliminar", list(etq.keys()))
        conf = st.checkbox("Confirmo la eliminación", key=f"cf_fer_{pais}")
        if st.button("🗑️ Eliminar feriados", type="primary", disabled=not (sel and conf)):
            ids = [etq[s] for s in sel]
            base = get_feriados()
            save_csv(base[~base["id"].isin(ids)], F_FERIADOS)
            bump("v_fer")
            st.success(f"Eliminados: {len(ids)} feriado(s).")
            st.rerun()

# ─────────────────────────────── DATOS ───────────────────────────────
else:
    hero("💾 Respaldo e importación", "Descarga tus CSV o restaura información")

    sect("⬇️ Descargar respaldos")
    c = st.columns(3)
    for col, (n, df) in zip(c, [("empleados", emp), ("vacaciones", vac), ("feriados", fer)]):
        col.download_button(f"⬇️ {n}.csv", df.to_csv(index=False).encode("utf-8-sig"),
                            f"{n}.csv", "text/csv", use_container_width=True)

    sect("⬆️ Importar")
    destino = st.selectbox("Archivo destino", ["empleados", "vacaciones", "feriados"])
    up = st.file_uploader("Sube un CSV con la misma estructura", type="csv")
    if up is not None:
        prev = pd.read_csv(up, dtype=str, keep_default_na=False)
        st.dataframe(prev.head(10), use_container_width=True)
        if st.button("Reemplazar datos", type="primary"):
            ruta = {"empleados": F_EMPLEADOS, "vacaciones": F_VACACIONES,
                    "feriados": F_FERIADOS}[destino]
            save_csv(prev, ruta)
            bump("v_emp"); bump("v_vac"); bump("v_fer")
            st.success(f"Datos de {destino} reemplazados.")
            st.rerun()

    sect("🗑️ Zona peligrosa")
    with st.expander("Borrar todos los datos"):
        if st.checkbox("Confirmo que quiero borrar TODO"):
            if st.button("Borrar todo", type="primary"):
                for p, cols in [(F_EMPLEADOS, COLS_EMPLEADOS), (F_VACACIONES, COLS_VACACIONES),
                                (F_FERIADOS, COLS_FERIADOS)]:
                    pd.DataFrame(columns=cols).to_csv(p, index=False)
                bump("v_emp"); bump("v_vac"); bump("v_fer")
                st.success("Datos eliminados.")
                st.rerun()