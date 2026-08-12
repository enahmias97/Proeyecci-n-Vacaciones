# -*- coding: utf-8 -*-
"""
Control de Vacaciones del Equipo
Streamlit app - México / Colombia
"""

import calendar
import io
import os
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Control de Vacaciones",
    page_icon="🏖️",
    layout="wide",
)

DATA_DIR = "data"
F_EMPLEADOS = os.path.join(DATA_DIR, "empleados.csv")
F_VACACIONES = os.path.join(DATA_DIR, "vacaciones.csv")
F_FERIADOS = os.path.join(DATA_DIR, "feriados.csv")

PAISES = ["México", "Colombia"]
ESTADOS = ["Solicitada", "Aprobada", "Tomada", "Rechazada"]
TIPOS = ["Vacaciones", "Permiso", "Incapacidad", "Home office", "Otro"]

COLOR_ESTADO = {
    "Solicitada": "#F1C40F",
    "Aprobada": "#2ECC71",
    "Tomada": "#3498DB",
    "Rechazada": "#E74C3C",
}

PALETA = [
    "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
    "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC",
    "#86BCB6", "#D37295", "#8CD17D", "#B6992D", "#499894",
]

MESES_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
DIAS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

# ----------------------------------------------------------------------------
# PERSISTENCIA
# ----------------------------------------------------------------------------
COLS_EMPLEADOS = ["id", "nombre", "pais", "puesto", "email",
                  "fecha_ingreso", "dias_asignados", "activo"]
COLS_VACACIONES = ["id", "empleado_id", "fecha_inicio", "fecha_fin",
                   "tipo", "estado", "comentario"]
COLS_FERIADOS = ["id", "pais", "fecha", "descripcion"]

def _ensure_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    for path, cols in [
        (F_EMPLEADOS, COLS_EMPLEADOS),
        (F_VACACIONES, COLS_VACACIONES),
        (F_FERIADOS, COLS_FERIADOS),
    ]:
        if not os.path.exists(path):
            pd.DataFrame(columns=cols).to_csv(path, index=False)

def load_csv(path, cols):
    _ensure_files()
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df[cols]

def save_csv(df, path):
    df.to_csv(path, index=False)

def get_empleados():
    df = load_csv(F_EMPLEADOS, COLS_EMPLEADOS)
    if not df.empty:
        df["dias_asignados"] = pd.to_numeric(df["dias_asignados"], errors="coerce").fillna(0).astype(int)
        df["activo"] = df["activo"].astype(str).str.lower().isin(["true", "1", "sí", "si", "yes"])
    return df

def get_vacaciones():
    df = load_csv(F_VACACIONES, COLS_VACACIONES)
    if not df.empty:
        df["fecha_inicio"] = pd.to_datetime(df["fecha_inicio"], errors="coerce").dt.date
        df["fecha_fin"] = pd.to_datetime(df["fecha_fin"], errors="coerce").dt.date
        df = df.dropna(subset=["fecha_inicio", "fecha_fin"])
    return df

def get_feriados():
    df = load_csv(F_FERIADOS, COLS_FERIADOS)
    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
        df = df.dropna(subset=["fecha"])
    return df

def next_id(df):
    if df.empty or df["id"].isna().all():
        return 1
    return int(pd.to_numeric(df["id"], errors="coerce").max()) + 1

# ----------------------------------------------------------------------------
# LÓGICA DE NEGOCIO
# ----------------------------------------------------------------------------
def dias_habiles(inicio: date, fin: date, feriados_pais: set) -> int:
    """Cuenta días hábiles (lun-vie) excluyendo feriados del país."""
    if inicio is None or fin is None or fin < inicio:
        return 0
    total, d = 0, inicio
    while d <= fin:
        if d.weekday() < 5 and d not in feriados_pais:
            total += 1
        d += timedelta(days=1)
    return total

def dias_naturales(inicio: date, fin: date) -> int:
    if fin < inicio:
        return 0
    return (fin - inicio).days + 1

def feriados_por_pais(df_feriados):
    out = {p: set() for p in PAISES}
    for _, r in df_feriados.iterrows():
        out.setdefault(r["pais"], set()).add(r["fecha"])
    return out

def resumen_empleados(emp, vac, fer, anio, estados_cuentan=("Aprobada", "Tomada")):
    """Tabla con días asignados, usados, proyectados y saldo por empleado."""
    fset = feriados_por_pais(fer)
    filas = []
    for _, e in emp.iterrows():
        v = vac[vac["empleado_id"] == e["id"]]
        v = v[v["tipo"] == "Vacaciones"]
        usados = proyectados = solicitados = 0
        for _, r in v.iterrows():
            if r["fecha_inicio"].year != anio and r["fecha_fin"].year != anio:
                continue
            d = dias_habiles(r["fecha_inicio"], r["fecha_fin"], fset.get(e["pais"], set()))
            if r["estado"] == "Tomada":
                usados += d
            elif r["estado"] == "Aprobada":
                proyectados += d
            elif r["estado"] == "Solicitada":
                solicitados += d
        consumidos = usados + proyectados
        filas.append({
            "ID": e["id"],
            "Colaborador": e["nombre"],
            "País": e["pais"],
            "Puesto": e["puesto"],
            "Días asignados": e["dias_asignados"],
            "Días tomados": usados,
            "Días proyectados (aprobados)": proyectados,
            "Días en solicitud": solicitados,
            "Total comprometido": consumidos,
            "Saldo disponible": int(e["dias_asignados"]) - consumidos,
            "% consumido": round(100 * consumidos / e["dias_asignados"], 1) if e["dias_asignados"] else 0.0,
            "Activo": e["activo"],
        })
    return pd.DataFrame(filas)

def expandir_dias(vac, emp):
    """Devuelve un dict {fecha: [(nombre, estado, tipo, pais)]}."""
    mapa = {}
    nombres = dict(zip(emp["id"], emp["nombre"]))
    paises = dict(zip(emp["id"], emp["pais"]))
    for _, r in vac.iterrows():
        nombre = nombres.get(r["empleado_id"], f"ID {r['empleado_id']}")
        pais = paises.get(r["empleado_id"], "")
        d = r["fecha_inicio"]
        while d <= r["fecha_fin"]:
            mapa.setdefault(d, []).append((nombre, r["estado"], r["tipo"], pais))
            d += timedelta(days=1)
    return mapa

def color_empleado(emp_id, ids):
    try:
        i = list(ids).index(emp_id)
    except ValueError:
        i = 0
    return PALETA[i % len(PALETA)]

# ----------------------------------------------------------------------------
# CALENDARIO HTML
# ----------------------------------------------------------------------------
def render_calendario_mes(anio, mes, mapa_dias, feriados_dict, filtro_pais=None):
    cal = calendar.Calendar(firstweekday=0)
    semanas = cal.monthdatescalendar(anio, mes)
    hoy = date.today()

    fer_all = {}
    for p, s in feriados_dict.items():
        for f in s:
            fer_all.setdefault(f, []).append(p)

    html = """
    <style>
      .cal {width:100%; border-collapse:collapse; font-family:system-ui,sans-serif;}
      .cal th {background:#262730; color:#fff; padding:6px; font-size:13px; border:1px solid #3a3a44;}
      .cal td {vertical-align:top; height:92px; width:14.28%; border:1px solid #3a3a44;
               padding:4px; font-size:11px;}
      .out {background:#1c1c22; color:#666;}
      .wknd {background:#20232b;}
      .hoy {outline:2px solid #FF4B4B; outline-offset:-2px;}
      .fer {background:#3d2222;}
      .num {font-weight:700; font-size:13px; margin-bottom:3px;}
      .chip {display:block; border-radius:4px; padding:1px 4px; margin:1px 0;
             color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
      .ferlbl {color:#ff9b9b; font-size:10px; font-style:italic;}
    </style>
    <table class="cal"><tr>
    """
    html += "".join(f"<th>{d}</th>" for d in DIAS_ES) + "</tr>"

    for semana in semanas:
        html += "<tr>"
        for d in semana:
            clases = []
            if d.month != mes:
                clases.append("out")
            elif d.weekday() >= 5:
                clases.append("wknd")
            if d in fer_all:
                clases.append("fer")
            if d == hoy:
                clases.append("hoy")
            html += f'<td class="{" ".join(clases)}"><div class="num">{d.day}</div>'

            if d.month == mes:
                if d in fer_all:
                    html += f'<div class="ferlbl">🎉 {"/".join(fer_all[d])}</div>'
                for nombre, estado, tipo, pais in mapa_dias.get(d, []):
                    if filtro_pais and pais not in filtro_pais:
                        continue
                    c = COLOR_ESTADO.get(estado, "#888")
                    ini = "🌴" if tipo == "Vacaciones" else "•"
                    html += (f'<span class="chip" style="background:{c}" '
                             f'title="{nombre} — {tipo} ({estado})">{ini} {nombre}</span>')
            html += "</td>"
        html += "</tr>"
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------------
_ensure_files()

st.sidebar.title("🏖️ Control de Vacaciones")
seccion = st.sidebar.radio(
    "Navegación",
    ["📊 Dashboard", "👥 Equipo", "🗓️ Vacaciones", "📅 Calendario",
     "🎉 Feriados México", "🎉 Feriados Colombia", "💾 Datos"],
)
anio_sel = st.sidebar.number_input("Año de trabajo", 2020, 2100, date.today().year, step=1)
st.sidebar.caption(f"Hoy: {date.today().strftime('%d/%m/%Y')}")

emp = get_empleados()
vac = get_vacaciones()
fer = get_feriados()
fer_dict = feriados_por_pais(fer)

# ----------------------------------------------------------------------------
# 1. DASHBOARD
# ----------------------------------------------------------------------------
if seccion == "📊 Dashboard":
    st.title("📊 Dashboard del equipo")

    if emp.empty:
        st.info("Aún no hay colaboradores. Ve a **👥 Equipo** para agregar el primero.")
        st.stop()

    res = resumen_empleados(emp, vac, fer, anio_sel)
    activos = res[res["Activo"]]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Colaboradores activos", len(activos))
    c2.metric("Días asignados", int(activos["Días asignados"].sum()))
    c3.metric("Días tomados", int(activos["Días tomados"].sum()))
    c4.metric("Días proyectados", int(activos["Días proyectados (aprobados)"].sum()))
    c5.metric("Saldo total", int(activos["Saldo disponible"].sum()))

    st.divider()

    # Quién está de vacaciones hoy
    hoy = date.today()
    hoy_df = vac[(vac["fecha_inicio"] <= hoy) & (vac["fecha_fin"] >= hoy) &
                 (vac["estado"].isin(["Aprobada", "Tomada"]))]
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🌴 Ausentes hoy")
        if hoy_df.empty:
            st.success("Todo el equipo está disponible hoy.")
        else:
            nombres = dict(zip(emp["id"], emp["nombre"]))
            for _, r in hoy_df.iterrows():
                st.warning(f"**{nombres.get(r['empleado_id'],'?')}** — {r['tipo']} "
                           f"(regresa el {(r['fecha_fin'] + timedelta(days=1)).strftime('%d/%m/%Y')})")
    with col_b:
        st.subheader("⏭️ Próximas ausencias (30 días)")
        prox = vac[(vac["fecha_inicio"] > hoy) & (vac["fecha_inicio"] <= hoy + timedelta(days=30)) &
                   (vac["estado"].isin(["Aprobada", "Solicitada"]))].sort_values("fecha_inicio")
        if prox.empty:
            st.info("Sin ausencias programadas en los próximos 30 días.")
        else:
            nombres = dict(zip(emp["id"], emp["nombre"]))
            for _, r in prox.iterrows():
                st.write(f"• **{nombres.get(r['empleado_id'],'?')}** — "
                         f"{r['fecha_inicio'].strftime('%d/%m')} al {r['fecha_fin'].strftime('%d/%m')} "
                         f"· _{r['estado']}_")

    st.divider()
    st.subheader("📈 Días proyectados vs. asignados")
    plot_df = activos.melt(
        id_vars="Colaborador",
        value_vars=["Días tomados", "Días proyectados (aprobados)", "Saldo disponible"],
        var_name="Concepto", value_name="Días",
    )
    fig = px.bar(plot_df, x="Colaborador", y="Días", color="Concepto",
                 barmode="stack", height=420,
                 color_discrete_map={
                     "Días tomados": "#3498DB",
                     "Días proyectados (aprobados)": "#2ECC71",
                     "Saldo disponible": "#7f8c8d",
                 })
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🧾 Detalle por colaborador")
    st.dataframe(
        res.drop(columns=["ID"]),
        use_container_width=True, hide_index=True,
        column_config={"% consumido": st.column_config.ProgressColumn(
            "% consumido", min_value=0, max_value=100, format="%.1f%%")},
    )

# ----------------------------------------------------------------------------
# 2. EQUIPO
# ----------------------------------------------------------------------------
elif seccion == "👥 Equipo":
    st.title("👥 Miembros del equipo")
    st.caption("Sin límite de integrantes: agrega tantos como necesites.")

    with st.expander("➕ Agregar colaborador", expanded=emp.empty):
        with st.form("form_emp", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            nombre = c1.text_input("Nombre completo *")
            pais = c2.selectbox("País *", PAISES)
            puesto = c3.text_input("Puesto")
            c4, c5, c6 = st.columns(3)
            email = c4.text_input("Email")
            ingreso = c5.date_input("Fecha de ingreso", value=date.today(),
                                    min_value=date(1990, 1, 1), max_value=date(2100, 12, 31))
            dias = c6.number_input("Días de vacaciones asignados/año", 0, 365,
                                   12 if pais == "México" else 15)
            if st.form_submit_button("Guardar colaborador", type="primary"):
                if not nombre.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    df = get_empleados()
                    nuevo = pd.DataFrame([{
                        "id": next_id(df), "nombre": nombre.strip(), "pais": pais,
                        "puesto": puesto.strip(), "email": email.strip(),
                        "fecha_ingreso": ingreso.isoformat(),
                        "dias_asignados": int(dias), "activo": True,
                    }])
                    save_csv(pd.concat([df, nuevo], ignore_index=True), F_EMPLEADOS)
                    st.success(f"✅ {nombre} agregado.")
                    st.rerun()

    if emp.empty:
        st.info("Todavía no hay colaboradores registrados.")
        st.stop()

    st.subheader("Editar equipo")
    st.caption("Modifica las celdas y presiona **Guardar cambios**. Marca 🗑️ para eliminar.")
    edit = emp.copy()
    edit["🗑️ Eliminar"] = False
    editado = st.data_editor(
        edit, use_container_width=True, hide_index=True, key="ed_emp",
        disabled=["id"],
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "nombre": st.column_config.TextColumn("Nombre", required=True),
            "pais": st.column_config.SelectboxColumn("País", options=PAISES, required=True),
            "puesto": st.column_config.TextColumn("Puesto"),
            "email": st.column_config.TextColumn("Email"),
            "fecha_ingreso": st.column_config.TextColumn("Ingreso (YYYY-MM-DD)"),
            "dias_asignados": st.column_config.NumberColumn("Días/año", min_value=0, max_value=365),
            "activo": st.column_config.CheckboxColumn("Activo"),
            "🗑️ Eliminar": st.column_config.CheckboxColumn("🗑️"),
        },
    )
    c1, c2 = st.columns([1, 4])
    if c1.button("💾 Guardar cambios", type="primary"):
        final = editado[~editado["🗑️ Eliminar"]].drop(columns=["🗑️ Eliminar"])
        borrados = editado[editado["🗑️ Eliminar"]]["id"].tolist()
        save_csv(final, F_EMPLEADOS)
        if borrados:  # limpiar sus vacaciones
            v = get_vacaciones()
            save_csv(v[~v["empleado_id"].isin(borrados)], F_VACACIONES)
        st.success("Cambios guardados.")
        st.rerun()

# ----------------------------------------------------------------------------
# 3. VACACIONES
# ----------------------------------------------------------------------------
elif seccion == "🗓️ Vacaciones":
    st.title("🗓️ Registro y proyección de vacaciones")

    if emp.empty:
        st.warning("Primero registra colaboradores en **👥 Equipo**.")
        st.stop()

    opciones = {f"{r['nombre']} ({r['pais']})": r["id"] for _, r in emp.iterrows()}

    with st.expander("➕ Registrar periodo de vacaciones / ausencia", expanded=True):
        with st.form("form_vac", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            quien = c1.selectbox("Colaborador *", list(opciones.keys()))
            tipo = c2.selectbox("Tipo", TIPOS)
            estado = c3.selectbox("Estado", ESTADOS, index=1)
            c4, c5 = st.columns(2)
            f_ini = c4.date_input("Fecha inicio *", value=date.today())
            f_fin = c5.date_input("Fecha fin *", value=date.today() + timedelta(days=4))
            coment = st.text_input("Comentario")

            emp_id = opciones[quien]
            pais_emp = emp.loc[emp["id"] == emp_id, "pais"].iloc[0]
            dh = dias_habiles(f_ini, f_fin, fer_dict.get(pais_emp, set()))
            st.info(f"📌 **{dh} días hábiles** ({dias_naturales(f_ini, f_fin)} naturales) "
                    f"descontando fines de semana y feriados de {pais_emp}.")

            if st.form_submit_button("Guardar periodo", type="primary"):
                if f_fin < f_ini:
                    st.error("La fecha fin no puede ser anterior a la fecha inicio.")
                else:
                    df = get_vacaciones()
                    # Validación de traslape para el mismo colaborador
                    tras = df[(df["empleado_id"] == emp_id) &
                              (df["fecha_inicio"] <= f_fin) & (df["fecha_fin"] >= f_ini)]
                    if not tras.empty:
                        st.error("⚠️ Este colaborador ya tiene un periodo que se traslapa con esas fechas.")
                    else:
                        nuevo = pd.DataFrame([{
                            "id": next_id(df), "empleado_id": emp_id,
                            "fecha_inicio": f_ini.isoformat(), "fecha_fin": f_fin.isoformat(),
                            "tipo": tipo, "estado": estado, "comentario": coment,
                        }])
                        save_csv(pd.concat([df, nuevo], ignore_index=True), F_VACACIONES)
                        st.success("✅ Periodo registrado.")
                        st.rerun()

    if vac.empty:
        st.info("Sin periodos registrados aún.")
        st.stop()

    st.subheader("Periodos registrados")
    nombres = dict(zip(emp["id"], emp["nombre"]))
    paises = dict(zip(emp["id"], emp["pais"]))

    c1, c2, c3 = st.columns(3)
    f_pers = c1.multiselect("Colaborador", sorted(nombres.values()))
    f_est = c2.multiselect("Estado", ESTADOS)
    f_pais = c3.multiselect("País", PAISES)

    tabla = vac.copy()
    tabla["Colaborador"] = tabla["empleado_id"].map(nombres)
    tabla["País"] = tabla["empleado_id"].map(paises)
    tabla["Días hábiles"] = tabla.apply(
        lambda r: dias_habiles(r["fecha_inicio"], r["fecha_fin"],
                               fer_dict.get(paises.get(r["empleado_id"], ""), set())), axis=1)
    tabla["Días naturales"] = tabla.apply(
        lambda r: dias_naturales(r["fecha_inicio"], r["fecha_fin"]), axis=1)

    if f_pers:
        tabla = tabla[tabla["Colaborador"].isin(f_pers)]
    if f_est:
        tabla = tabla[tabla["estado"].isin(f_est)]
    if f_pais:
        tabla = tabla[tabla["País"].isin(f_pais)]

    vista = tabla[["id", "Colaborador", "País", "fecha_inicio", "fecha_fin",
                   "Días hábiles", "Días naturales", "tipo", "estado", "comentario"]] \
        .sort_values("fecha_inicio", ascending=False)
    vista = vista.rename(columns={"id": "ID", "fecha_inicio": "Inicio", "fecha_fin": "Fin",
                                  "tipo": "Tipo", "estado": "Estado", "comentario": "Comentario"})
    vista["🗑️"] = False
    ed = st.data_editor(
        vista, use_container_width=True, hide_index=True, key="ed_vac",
        disabled=["ID", "Colaborador", "País", "Días hábiles", "Días naturales"],
        column_config={
            "Estado": st.column_config.SelectboxColumn(options=ESTADOS),
            "Tipo": st.column_config.SelectboxColumn(options=TIPOS),
            "Inicio": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Fin": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "🗑️": st.column_config.CheckboxColumn("Eliminar"),
        },
    )
    if st.button("💾 Guardar cambios en periodos", type="primary"):
        base = get_vacaciones()
        base["id"] = pd.to_numeric(base["id"])
        for _, r in ed.iterrows():
            i = base.index[base["id"] == r["ID"]]
            if len(i):
                base.loc[i, "fecha_inicio"] = pd.to_datetime(r["Inicio"]).date().isoformat()
                base.loc[i, "fecha_fin"] = pd.to_datetime(r["Fin"]).date().isoformat()
                base.loc[i, "tipo"] = r["Tipo"]
                base.loc[i, "estado"] = r["Estado"]
                base.loc[i, "comentario"] = r["Comentario"]
        borrar = ed[ed["🗑️"]]["ID"].tolist()
        base = base[~base["id"].isin(borrar)]
        save_csv(base, F_VACACIONES)
        st.success("Cambios guardados.")
        st.rerun()

    st.divider()
    st.subheader("📊 Días proyectados por colaborador")
    res = resumen_empleados(emp, vac, fer, anio_sel)
    st.dataframe(
        res[["Colaborador", "País", "Días asignados", "Días tomados",
             "Días proyectados (aprobados)", "Días en solicitud",
             "Total comprometido", "Saldo disponible", "% consumido"]],
        use_container_width=True, hide_index=True,
        column_config={"% consumido": st.column_config.ProgressColumn(
            "% consumido", min_value=0, max_value=100, format="%.1f%%")},
    )

# ----------------------------------------------------------------------------
# 4. CALENDARIO
# ----------------------------------------------------------------------------
elif seccion == "📅 Calendario":
    st.title("📅 Calendario de vacaciones")

    if emp.empty:
        st.warning("Registra colaboradores para ver el calendario.")
        st.stop()

    c1, c2, c3 = st.columns([1, 1, 2])
    mes = c1.selectbox("Mes", range(1, 13), index=date.today().month - 1,
                       format_func=lambda m: MESES_ES[m - 1])
    anio_cal = c2.number_input("Año", 2020, 2100, anio_sel, step=1, key="anio_cal")
    paises_f = c3.multiselect("Filtrar por país", PAISES, default=PAISES)

    est_f = st.multiselect("Estados a mostrar", ESTADOS, default=["Aprobada", "Tomada", "Solicitada"])
    vfilt = vac[vac["estado"].isin(est_f)] if not vac.empty else vac

    leyenda = " &nbsp;&nbsp; ".join(
        f'<span style="background:{c};color:#fff;padding:2px 8px;border-radius:4px">{e}</span>'
        for e, c in COLOR_ESTADO.items() if e in est_f
    )
    st.markdown(leyenda + ' &nbsp;&nbsp; <span style="background:#3d2222;color:#ff9b9b;'
                'padding:2px 8px;border-radius:4px">🎉 Feriado</span>', unsafe_allow_html=True)
    st.markdown(f"### {MESES_ES[mes-1]} {int(anio_cal)}")

    mapa = expandir_dias(vfilt, emp) if not vfilt.empty else {}
    render_calendario_mes(int(anio_cal), mes, mapa, fer_dict, filtro_pais=paises_f)

    st.divider()
    st.subheader("📈 Línea de tiempo anual (Gantt)")
    if vfilt.empty:
        st.info("Sin periodos para graficar.")
    else:
        nombres = dict(zip(emp["id"], emp["nombre"]))
        paises = dict(zip(emp["id"], emp["pais"]))
        g = vfilt.copy()
        g["Colaborador"] = g["empleado_id"].map(nombres)
        g["País"] = g["empleado_id"].map(paises)
        g = g[g["País"].isin(paises_f)]
        g = g[(pd.to_datetime(g["fecha_inicio"]).dt.year <= int(anio_cal)) &
              (pd.to_datetime(g["fecha_fin"]).dt.year >= int(anio_cal))]
        if g.empty:
            st.info("Sin periodos en el año seleccionado.")
        else:
            g["Inicio"] = pd.to_datetime(g["fecha_inicio"])
            g["Fin"] = pd.to_datetime(g["fecha_fin"]) + pd.Timedelta(days=1)
            fig = px.timeline(g, x_start="Inicio", x_end="Fin", y="Colaborador",
                              color="estado", hover_data=["tipo", "comentario", "País"],
                              color_discrete_map=COLOR_ESTADO, height=90 + 32 * g["Colaborador"].nunique())
            fig.update_yaxes(autorange="reversed")
            fig.add_vline(x=datetime.now(), line_dash="dash", line_color="#FF4B4B")
            fig.update_layout(xaxis_range=[f"{int(anio_cal)}-01-01", f"{int(anio_cal)}-12-31"])
            st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------------
# 5 y 6. FERIADOS
# ----------------------------------------------------------------------------
elif seccion in ("🎉 Feriados México", "🎉 Feriados Colombia"):
    pais = "México" if "México" in seccion else "Colombia"
    bandera = "🇲🇽" if pais == "México" else "🇨🇴"
    st.title(f"{bandera} Días feriados — {pais}")
    st.caption("Estos días no se descuentan del saldo de vacaciones de los colaboradores de este país.")

    with st.form(f"form_fer_{pais}", clear_on_submit=True):
        c1, c2, c3 = st.columns([1, 2, 1])
        f = c1.date_input("Fecha", value=date(int(anio_sel), 1, 1))
        desc = c2.text_input("Descripción", placeholder="Ej. Día de la Independencia")
        c3.markdown("<br>", unsafe_allow_html=True)
        if c3.form_submit_button("➕ Agregar", type="primary"):
            df = get_feriados()
            if not df.empty and ((df["pais"] == pais) & (df["fecha"] == f)).any():
                st.warning("Ese feriado ya existe.")
            else:
                nuevo = pd.DataFrame([{"id": next_id(df), "pais": pais,
                                       "fecha": f.isoformat(),
                                       "descripcion": desc.strip() or "Feriado"}])
                save_csv(pd.concat([df, nuevo], ignore_index=True), F_FERIADOS)
                st.success("Feriado agregado.")
                st.rerun()

    fp = fer[fer["pais"] == pais].copy()
    fp = fp[pd.to_datetime(fp["fecha"]).dt.year == int(anio_sel)] if not fp.empty else fp

    if fp.empty:
        st.info(f"No hay feriados registrados para {pais} en {int(anio_sel)}.")
    else:
        fp["Día"] = fp["fecha"].apply(lambda d: DIAS_ES[d.weekday()])
        fp["Mes"] = fp["fecha"].apply(lambda d: MESES_ES[d.month - 1])
        vista = fp[["id", "fecha", "Día", "Mes", "descripcion"]].sort_values("fecha")
        vista = vista.rename(columns={"id": "ID", "fecha": "Fecha", "descripcion": "Descripción"})
        vista["🗑️"] = False
        ed = st.data_editor(vista, use_container_width=True, hide_index=True,
                            key=f"ed_fer_{pais}", disabled=["ID", "Día", "Mes"],
                            column_config={
                                "Fecha": st.column_config.DateColumn(format="DD/MM/YYYY"),
                                "🗑️": st.column_config.CheckboxColumn("Eliminar")})
        if st.button("💾 Guardar feriados", type="primary"):
            base = get_feriados()
            base["id"] = pd.to_numeric(base["id"])
            for _, r in ed.iterrows():
                i = base.index[base["id"] == r["ID"]]
                if len(i):
                    base.loc[i, "fecha"] = pd.to_datetime(r["Fecha"]).date().isoformat()
                    base.loc[i, "descripcion"] = r["Descripción"]
            base = base[~base["id"].isin(ed[ed["🗑️"]]["ID"].tolist())]
            save_csv(base, F_FERIADOS)
            st.success("Feriados actualizados.")
            st.rerun()
        st.metric(f"Total feriados {int(anio_sel)}", len(fp))

# ----------------------------------------------------------------------------
# 7. DATOS (respaldo / importación)
# ----------------------------------------------------------------------------
else:
    st.title("💾 Respaldo e importación de datos")
    st.caption("Descarga tus CSV para respaldarlos o súbelos para restaurar/migrar información.")

    c1, c2, c3 = st.columns(3)
    for col, (nombre, df) in zip([c1, c2, c3],
                                 [("empleados", emp), ("vacaciones", vac), ("feriados", fer)]):
        col.download_button(f"⬇️ {nombre}.csv",
                            df.to_csv(index=False).encode("utf-8"),
                            f"{nombre}.csv", "text/csv", use_container_width=True)

    st.divider()
    st.subheader("⬆️ Importar")
    destino = st.selectbox("Archivo destino", ["empleados", "vacaciones", "feriados"])
    up = st.file_uploader("Sube un CSV con la misma estructura", type="csv")
    if up and st.button("Reemplazar datos", type="primary"):
        nuevo = pd.read_csv(up)
        ruta = {"empleados": F_EMPLEADOS, "vacaciones": F_VACACIONES, "feriados": F_FERIADOS}[destino]
        save_csv(nuevo, ruta)
        st.success(f"Datos de {destino} reemplazados.")
        st.rerun()

    st.divider()
    with st.expander("🗑️ Zona peligrosa"):
        if st.checkbox("Confirmo que quiero borrar TODOS los datos"):
            if st.button("Borrar todo", type="primary"):
                for p, c in [(F_EMPLEADOS, COLS_EMPLEADOS), (F_VACACIONES, COLS_VACACIONES),
                             (F_FERIADOS, COLS_FERIADOS)]:
                    pd.DataFrame(columns=c).to_csv(p, index=False)
                st.success("Datos eliminados.")
                st.rerun()