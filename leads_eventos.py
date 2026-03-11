"""
leads_eventos.py — Terret Lead Mining App
Stack: Streamlit + Google Sheets (gspread) + BeautifulSoup scraping
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import uuid
from datetime import datetime, date
import io
import time
import json
from urllib.parse import quote_plus, urljoin

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

# ─────────────────────────────────────────────
# PAGE CONFIG & GLOBAL STYLES
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Terret · Leads Eventos",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ACCENT = "#D4FF00"
BG     = "#07070F"
SURF   = "#0F0F1A"
BORDER = "#1C1C2E"
TEXT   = "#E8E8F0"
MUTED  = "#6B6B8A"

STATE_COLORS = {
    "Nuevo":          "#3B82F6",
    "Contactado":     "#F59E0B",
    "En negociación": "#8B5CF6",
    "Cerrado":        "#10B981",
    "Descartado":     "#EF4444",
}

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        background-color: #07070F !important;
        color: #E8E8F0 !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stApp { background-color: #07070F !important; }

    /* Header */
    .terret-header {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.8rem;
        letter-spacing: 0.12em;
        color: #D4FF00;
        line-height: 1;
        margin-bottom: 0;
    }
    .terret-sub {
        font-family: 'DM Mono', monospace;
        font-size: 0.72rem;
        color: #6B6B8A;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        margin-top: 2px;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #0F0F1A !important;
        border-bottom: 1px solid #1C1C2E !important;
        gap: 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'DM Mono', monospace !important;
        font-size: 0.78rem !important;
        letter-spacing: 0.12em !important;
        text-transform: uppercase !important;
        color: #6B6B8A !important;
        padding: 12px 24px !important;
        border-bottom: 2px solid transparent !important;
    }
    .stTabs [aria-selected="true"] {
        color: #D4FF00 !important;
        border-bottom: 2px solid #D4FF00 !important;
        background: transparent !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 24px !important;
    }

    /* Buttons */
    .stButton > button {
        background: #D4FF00 !important;
        color: #07070F !important;
        font-family: 'DM Mono', monospace !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 8px 20px !important;
        transition: opacity 0.15s !important;
    }
    .stButton > button:hover { opacity: 0.85 !important; }
    .stButton > button[kind="secondary"] {
        background: #1C1C2E !important;
        color: #E8E8F0 !important;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea > div > div > textarea {
        background: #0F0F1A !important;
        border: 1px solid #1C1C2E !important;
        color: #E8E8F0 !important;
        border-radius: 4px !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #D4FF00 !important;
        box-shadow: 0 0 0 1px #D4FF00 !important;
    }

    /* DataFrames */
    .stDataFrame { border: 1px solid #1C1C2E !important; border-radius: 6px !important; }
    [data-testid="stDataFrameResizable"] { background: #0F0F1A !important; }

    /* Metrics */
    [data-testid="metric-container"] {
        background: #0F0F1A !important;
        border: 1px solid #1C1C2E !important;
        border-radius: 6px !important;
        padding: 16px !important;
    }
    [data-testid="metric-container"] label {
        font-family: 'DM Mono', monospace !important;
        font-size: 0.7rem !important;
        letter-spacing: 0.12em !important;
        color: #6B6B8A !important;
        text-transform: uppercase !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: 2.2rem !important;
        color: #D4FF00 !important;
    }

    /* Cards */
    .lead-card {
        background: #0F0F1A;
        border: 1px solid #1C1C2E;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    .lead-card-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.1rem;
        letter-spacing: 0.08em;
        color: #E8E8F0;
    }
    .mono-sm {
        font-family: 'DM Mono', monospace;
        font-size: 0.72rem;
        color: #6B6B8A;
    }
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-family: 'DM Mono', monospace;
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    /* Divider */
    hr { border-color: #1C1C2E !important; }

    /* Selectbox dropdown */
    [data-baseweb="popover"] { background: #0F0F1A !important; border: 1px solid #1C1C2E !important; }
    [data-baseweb="menu"] { background: #0F0F1A !important; }
    [data-baseweb="option"]:hover { background: #1C1C2E !important; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #07070F; }
    ::-webkit-scrollbar-thumb { background: #1C1C2E; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #2A2A42; }

    /* Checkbox */
    .stCheckbox > label { color: #E8E8F0 !important; font-family: 'DM Sans', sans-serif !important; }

    /* Info / warning boxes */
    .stInfo, .stWarning, .stSuccess, .stError {
        border-radius: 6px !important;
        font-family: 'DM Sans', sans-serif !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        font-family: 'DM Mono', monospace !important;
        font-size: 0.78rem !important;
        letter-spacing: 0.08em !important;
        background: #0F0F1A !important;
        border: 1px solid #1C1C2E !important;
        border-radius: 6px !important;
        color: #E8E8F0 !important;
    }
    .streamlit-expanderContent {
        background: #0F0F1A !important;
        border: 1px solid #1C1C2E !important;
        border-top: none !important;
        border-radius: 0 0 6px 6px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="terret-header" style="text-align:center">TERRET</div>', unsafe_allow_html=True)
        st.markdown('<div class="terret-sub" style="text-align:center;margin-bottom:2rem">Lead Mining · Eventos Deportivos</div>', unsafe_allow_html=True)
        pwd = st.text_input("Contraseña", type="password", key="login_pwd", placeholder="••••••••")
        if st.button("Entrar", key="login_btn"):
            if pwd == st.secrets.get("APP_PASSWORD", "terret2024"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    return False


# ─────────────────────────────────────────────
# GOOGLE SHEETS
# ─────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)


def get_or_create_sheet():
    gc = get_gspread_client()
    try:
        sh = gc.open(SHEET_NAME)
    except gspread.SpreadsheetNotFound:
        sh = gc.create(SHEET_NAME)
        sh.share(st.secrets["gcp_service_account"]["client_email"],
                 perm_type="user", role="writer")
    try:
        ws = sh.worksheet(WORKSHEET)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=WORKSHEET, rows=1000, cols=len(COLUMNS))
        ws.append_row(COLUMNS)
        try:
            ws.format("A1:N1", {
                "textFormat": {"bold": True, "fontSize": 10},
                "backgroundColor": {"red": 0.06, "green": 0.06, "blue": 0.12},
            })
        except Exception:
            pass
    return ws


def load_leads() -> pd.DataFrame:
    try:
        ws = get_or_create_sheet()
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame(columns=COLUMNS)
        df = pd.DataFrame(data)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[COLUMNS]
    except Exception as e:
        st.error("Error cargando Sheets: " + str(e))
        return pd.DataFrame(columns=COLUMNS)


def save_leads(rows: list[dict]) -> int:
    ws = get_or_create_sheet()
    existing = ws.get_all_records()
    existing_names = {r.get("Evento", "").lower().strip() for r in existing}
    added = 0
    for row in rows:
        key = row.get("Evento", "").lower().strip()
        if not key or key in existing_names:
            continue
        ws.append_row([row.get(c, "") for c in COLUMNS], value_input_option="USER_ENTERED")
        existing_names.add(key)
        added += 1
    return added


def update_lead_field(row_idx: int, field: str, value: str):
    ws = get_or_create_sheet()
    col_idx = COLUMNS.index(field) + 1
    ws.update_cell(row_idx + 2, col_idx, value)


# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
SHEET_NAME = "Terret — Leads Eventos"
WORKSHEET  = "Leads"
COLUMNS    = ["ID","Evento","Tipo","Fecha","Ciudad","Organizador",
              "Email","Telefono","Instagram","Web","Fuente","Estado",
              "Notas","Fecha_Agregado"]
ESTADOS    = ["Nuevo","Contactado","En negociación","Cerrado","Descartado"]
TIPOS      = ["Running","Ciclismo","Trail","Triatlón","Duatlón","MTB","Otro"]

DEFAULT_SOURCES = [
    {"label": "Atletrack — Eventos",       "url": "https://www.atletrack.com/eventos"},
    {"label": "Sportadictos — Carreras",   "url": "https://sportadictos.com/categoria/carreras-populares/"},
    {"label": "Correr.co — Carreras",      "url": "https://correr.co/carreras/"},
    {"label": "TravesiaDeportiva",         "url": "https://travesiadeportiva.com/"},
    {"label": "RunningColombia",           "url": "https://runningcolombia.co/eventos/"},
    {"label": "Triatlon.com.co",           "url": "https://triatlon.com.co/eventos/"},
]

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def _new_row(evento="", tipo="", fecha="", ciudad="", organizador="",
             email="", telefono="", instagram="", web="", fuente="",
             notas="") -> dict:
    return {
        "ID":             uuid.uuid4().hex[:8].upper(),
        "Evento":         evento,
        "Tipo":           tipo,
        "Fecha":          fecha,
        "Ciudad":         ciudad,
        "Organizador":    organizador,
        "Email":          email,
        "Telefono":       telefono,
        "Instagram":      instagram,
        "Web":            web,
        "Fuente":         fuente,
        "Estado":         "Nuevo",
        "Notas":          notas,
        "Fecha_Agregado": datetime.now().strftime("%Y-%m-%d"),
    }


def _rows_from_js(js_events: list[dict]) -> list[dict]:
    """Convert raw JS-scraped dicts into full CRM rows."""
    rows = []
    for e in js_events:
        rows.append(_new_row(
            evento    = e.get("nombre","")[:200],
            tipo      = e.get("tipo","Running"),
            fecha     = e.get("fecha",""),
            ciudad    = e.get("ciudad","Colombia"),
            organizador=e.get("organizador",""),
            email     = e.get("email",""),
            telefono  = e.get("telefono",""),
            instagram = e.get("instagram",""),
            web       = e.get("web",""),
            fuente    = e.get("fuente",""),
            notas     = e.get("notas",""),
        ))
    return rows


# ─────────────────────────────────────────────
# BROWSER-SIDE JS SCRAPER COMPONENT
# This runs fetch() in the USER's browser (real IP),
# bypassing any server-side IP blocks on Streamlit Cloud.
# allorigins.win proxy works from real IPs, not from AWS.
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# SCRAPING ENGINE — via Google Apps Script proxy
# GAS runs on Google servers → never blocked by any site
# ─────────────────────────────────────────────
import re as _re

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(?:\+?57[\s-]?)?3\d{2}[\s-]?\d{3}[\s-]?\d{4}")
INSTA_RE = re.compile(r"instagram\.com/([A-Za-z0-9_.]+)")
DATE_RE  = re.compile(r"\d{1,2}[\s/\-\.]\w+[\s/\-\.]\d{2,4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}")

CITIES_CO = [
    "bogotá","bogota","medellín","medellin","cali","barranquilla","cartagena",
    "bucaramanga","pereira","manizales","armenia","santa marta","ibagué","ibague",
    "villavicencio","cúcuta","cucuta","pasto","montería","monteria","sincelejo",
    "valledupar","neiva","popayán","popayan","tunja","rionegro","envigado",
    "bello","itagüí","itagui","girardot",
]

DEFAULT_SOURCES = [
    {"label": "Atletrack — Eventos",     "url": "https://www.atletrack.com/eventos"},
    {"label": "Sportadictos — Carreras", "url": "https://sportadictos.com/categoria/carreras-populares/"},
    {"label": "Correr.co",               "url": "https://correr.co/carreras/"},
    {"label": "TravesiaDeportiva",       "url": "https://travesiadeportiva.com/"},
    {"label": "Ciclismo a Fondo CO",     "url": "https://www.ciclismoafondo.es/colombia/"},
]

def _gas_url() -> str:
    return st.secrets.get("WEBAPP_URL", "")

def _extract_contact(text: str) -> dict:
    emails = EMAIL_RE.findall(text)
    phones = PHONE_RE.findall(text)
    instas = INSTA_RE.findall(text)
    bad = {"example","wordpress","schema","google","w3","jquery","sentry","wix","noreply"}
    emails = [e for e in emails if e.split("@")[-1].split(".")[0].lower() not in bad]
    return {
        "Email":     emails[0] if emails else "",
        "Telefono":  phones[0] if phones else "",
        "Instagram": "@" + instas[0] if instas else "",
    }

def _guess_tipo(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["cicl","bicicleta","bike","gran fondo"]): return "Ciclismo"
    if "mtb" in t:   return "MTB"
    if "trail" in t: return "Trail"
    if "triat" in t: return "Triatlón"
    if "duat"  in t: return "Duatlón"
    return "Running"

def _extract_city(text: str) -> str:
    tl = text.lower()
    return next((c.title() for c in CITIES_CO if c in tl), "Colombia")

def _fetch_via_gas(target_url: str) -> str | None:
    """Fetch a URL through the Google Apps Script proxy."""
    gas = _gas_url()
    if not gas:
        return None
    try:
        proxy_url = gas + "?action=scrape&url=" + requests.utils.quote(target_url, safe="")
        r = requests.get(proxy_url, timeout=30)
        if r.status_code != 200:
            return None
        data = r.json()
        if not data.get("ok"):
            return None
        return data.get("html", "")
    except Exception:
        return None

def _parse_html(html: str, base_url: str, fuente: str) -> list[dict]:
    """Extract events from raw HTML using multi-strategy parser."""
    from urllib.parse import urljoin
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen: set[str] = set()

    def _add(name, href, text, fecha=""):
        name = (name or "").strip()[:180]
        if not name or len(name) < 5 or name.lower() in seen:
            return
        seen.add(name.lower())
        if not fecha:
            m = DATE_RE.search(text)
            fecha = m.group(0) if m else ""
        contact = _extract_contact(text)
        ciudad  = _extract_city(name + " " + text)
        web = href if (href or "").startswith("http") else (urljoin(base_url, href) if href else base_url)
        results.append(_new_row(
            evento=name, tipo=_guess_tipo(name + " " + text),
            fecha=fecha, ciudad=ciudad, web=web, fuente=fuente, **contact,
        ))

    # Strategy 1: Tribe Events Calendar (Atletrack uses this)
    tribe = soup.find_all("article", class_=re.compile(r"tribe_event|type-tribe", re.I))
    if tribe:
        for art in tribe[:60]:
            a    = art.find("a", class_=re.compile(r"tribe-event-url", re.I)) or art.find("h2 a") or art.find("h3 a")
            name = a.get_text(strip=True) if a else ""
            href = a.get("href", "") if a else ""
            abbr = art.find("abbr")
            t    = art.find("time")
            fecha = (abbr.get("title","") or abbr.get_text(strip=True)) if abbr else \
                    ((t.get("datetime","") or t.get_text(strip=True)) if t else "")
            _add(name, href, art.get_text(" ", strip=True), fecha)
        if results: return results

    # Strategy 2: WordPress <article> posts
    articles = soup.find_all("article")
    if articles:
        for art in articles[:60]:
            h    = art.find(["h1","h2","h3","h4"])
            name = h.get_text(strip=True) if h else ""
            a    = (h.find("a") if h else None) or art.find("a", href=True)
            href = a.get("href","") if a else ""
            t    = art.find("time")
            fecha = (t.get("datetime","") or t.get_text(strip=True)) if t else ""
            _add(name, href, art.get_text(" ", strip=True), fecha)
        if results: return results

    # Strategy 3: Generic event cards
    for tag in ["div", "li", "section"]:
        cards = soup.find_all(tag, class_=re.compile(r"event|card|item|race|carrera|run", re.I))
        for c in cards[:60]:
            links = c.find_all("a", href=True)
            name  = links[0].get_text(strip=True) if links else c.get_text(strip=True)[:80]
            href  = links[0]["href"] if links else ""
            _add(name, href, c.get_text(" ", strip=True))
        if results: return results

    # Strategy 4: Keyword-matching links
    for a in soup.find_all("a", href=True):
        name = a.get_text(strip=True)
        if (3 <= len(name.split()) <= 12 and len(name) < 120 and
                re.search(r"run|trail|cicl|triat|carrera|maratón|maraton|ciclismo|duatl|mtb|travesía|travesia|fondo", name, re.I)):
            _add(name, a["href"], name)

    return results


def scrape_sources(sources: list[dict]) -> tuple[list[dict], list[str], list[str]]:
    """
    Scrape a list of {label, url} dicts through the GAS proxy.
    Returns (all_events, ok_labels, failed_labels).
    """
    gas = _gas_url()
    if not gas:
        return [], [], ["⚠️ WEBAPP_URL no configurado en secrets"]

    all_events: list[dict] = []
    ok: list[str] = []
    failed: list[str] = []
    seen_names: set[str] = set()

    for src in sources:
        label = src["label"]
        url   = src["url"]
        html  = _fetch_via_gas(url)
        if not html:
            failed.append(label)
            continue
        rows = _parse_html(html, url, label)
        # deduplicate
        new_rows = []
        for r in rows:
            k = r["Evento"].lower().strip()
            if k and k not in seen_names:
                seen_names.add(k)
                new_rows.append(r)
        if new_rows:
            all_events.extend(new_rows)
            ok.append(f"{label} ({len(new_rows)})")
        else:
            failed.append(label + " (sin eventos reconocibles)")

    return all_events, ok, failed


# ─────────────────────────────────────────────
# TAB 1 — DESCUBRIR
# ─────────────────────────────────────────────
def tab_descubrir():
    st.markdown(
        '<p class="terret-sub" style="font-size:0.8rem;letter-spacing:0.14em">MODO DE BÚSQUEDA</p>',
        unsafe_allow_html=True,
    )

    # Warn if GAS not configured
    if not _gas_url():
        st.error(
            "**WEBAPP_URL no está configurado en los secrets.**\n\n"
            "Agrega tu Google Apps Script URL en Streamlit Cloud → App settings → Secrets:\n"
            "`WEBAPP_URL = \"https://script.google.com/macros/s/.../exec\"`"
        )
        return

    modo = st.radio(
        "Modo", ["🤖 Automático", "🔗 URL personalizada"],
        key="modo_busqueda", label_visibility="collapsed", horizontal=True,
    )

    if modo == "🤖 Automático":
        st.markdown('<p class="mono-sm" style="margin-bottom:6px">Fuentes:</p>', unsafe_allow_html=True)
        selected = []
        cols = st.columns(3)
        for i, src in enumerate(DEFAULT_SOURCES):
            with cols[i % 3]:
                if st.checkbox(src["label"], value=True, key="src_" + str(i)):
                    selected.append(src)
        sources_to_scrape = selected

    else:
        custom = st.text_input(
            "URL del directorio", placeholder="https://www.atletrack.com/eventos",
            key="custom_url_input",
        )
        sources_to_scrape = [{"label": custom.strip(), "url": custom.strip()}] if custom.strip() else []

    st.markdown(
        '<p class="mono-sm" style="color:#6B6B8A;margin-top:4px">'
        '⚡ Scraping vía <strong style="color:#D4FF00">Google Apps Script</strong> '
        '— corre en servidores de Google, sin bloqueos de IP.</p>',
        unsafe_allow_html=True,
    )

    if st.button("Buscar eventos", key="btn_buscar"):
        if not sources_to_scrape:
            st.warning("Selecciona al menos una fuente o ingresa una URL")
            return

        all_events: list[dict] = []
        prog = st.progress(0, text="Iniciando...")
        n = len(sources_to_scrape)

        ok_labels: list[str] = []
        failed_labels: list[str] = []

        for i, src in enumerate(sources_to_scrape):
            prog.progress(int((i / n) * 90) + 5, text="Scrapeando " + src["label"] + "...")
            html = _fetch_via_gas(src["url"])
            if html:
                rows = _parse_html(html, src["url"], src["label"])
                seen = {e["Evento"].lower() for e in all_events}
                new  = [r for r in rows if r["Evento"].lower() not in seen]
                all_events.extend(new)
                if new:
                    ok_labels.append(src["label"] + " (" + str(len(new)) + ")")
                else:
                    failed_labels.append(src["label"] + " (sin eventos reconocibles)")
            else:
                failed_labels.append(src["label"] + " (no accesible)")

        prog.progress(100, text="Listo")
        time.sleep(0.3)
        prog.empty()

        for msg in ok_labels:
            st.success("✅ " + msg)
        for msg in failed_labels:
            st.warning("⚠️ " + msg)

        if all_events:
            st.session_state["discovered"] = all_events
        else:
            st.error(
                "**0 eventos encontrados.**\n\n"
                "Posibles causas:\n"
                "- El GAS script necesita ser actualizado (ver instrucciones abajo)\n"
                "- Los sitios cambiaron su estructura HTML\n\n"
                "Verifica que el GAS script esté desplegado con acceso: **Cualquier persona**."
            )

    # ── Results table ─────────────────────────────────────────
    if "discovered" in st.session_state and st.session_state["discovered"]:
        discovered = st.session_state["discovered"]
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<p class="terret-sub" style="font-size:0.8rem;letter-spacing:0.14em">'
            + str(len(discovered)) + " EVENTOS — EDITA Y SELECCIONA PARA GUARDAR</p>",
            unsafe_allow_html=True,
        )
        display_cols = ["Evento","Tipo","Fecha","Ciudad","Email","Telefono","Instagram","Web","Fuente"]
        df_show = pd.DataFrame(discovered)[display_cols].copy()

        edited = st.data_editor(
            df_show, use_container_width=True, num_rows="dynamic",
            key="editor_discovered",
            column_config={
                "Tipo": st.column_config.SelectboxColumn("Tipo", options=TIPOS),
                "Web":  st.column_config.LinkColumn("Web"),
            },
        )

        st.markdown(
            '<p class="terret-sub" style="font-size:0.75rem;margin-top:8px;letter-spacing:0.1em">'
            'SELECCIONA FILAS A GUARDAR</p>', unsafe_allow_html=True,
        )
        seleccionados = []
        for i, row in edited.iterrows():
            uid = uuid.uuid4().hex[:6]
            label = str(row["Evento"])[:60] if row["Evento"] else "Fila " + str(i+1)
            if st.checkbox(label, value=True, key="sel_" + str(i) + "_" + uid):
                seleccionados.append(i)

        c1, c2 = st.columns([1, 4])
        with c1:
            if st.button("💾 Guardar seleccionados", key="btn_guardar"):
                if not seleccionados:
                    st.warning("No hay filas seleccionadas")
                else:
                    rows_to_save = []
                    for i in seleccionados:
                        base = discovered[i].copy()
                        base.update({c: edited.iloc[i][c] for c in display_cols if c in edited.columns})
                        rows_to_save.append(base)
                    with st.spinner("Guardando en Google Sheets..."):
                        added = save_leads(rows_to_save)
                    st.success("✅ " + str(added) + " leads guardados")
                    del st.session_state["discovered"]
                    st.rerun()
        with c2:
            if st.button("Limpiar lista", key="btn_limpiar"):
                del st.session_state["discovered"]
                st.rerun()

def generate_email_template(lead: dict) -> str:
    nombre  = lead.get("Evento", "tu evento")
    ciudad  = lead.get("Ciudad", "Colombia")
    org     = lead.get("Organizador", "equipo organizador")
    tipo    = lead.get("Tipo", "evento deportivo")
    return (
        f"Asunto: Alianza Terret × {nombre} — Equipamiento Oficial\n\n"
        f"Hola {org},\n\n"
        f"Mi nombre es [TU NOMBRE] y soy parte del equipo comercial de Terret, "
        f"marca colombiana de running y ciclismo.\n\n"
        f"Estamos muy emocionados con {nombre} en {ciudad} y nos encantaría "
        f"explorar una alianza para ser el proveedor oficial de equipamiento para "
        f"este {tipo.lower()}.\n\n"
        f"Terret ofrece:\n"
        f"• Kits personalizados para participantes y staff\n"
        f"• Medias y accesorios técnicos de alto rendimiento\n"
        f"• Visibilidad de marca en toda la comunicación del evento\n"
        f"• Condiciones especiales para organizadores\n\n"
        f"¿Podríamos agendar una llamada de 20 minutos esta semana?\n\n"
        f"Quedo pendiente,\n[TU NOMBRE]\n"
        f"Terret | www.terret.co\n"
    )

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
def render_header():
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown('<div class="terret-header">TERRET · LEADS EVENTOS</div>', unsafe_allow_html=True)
        st.markdown('<div class="terret-sub">Lead Mining · Eventos Deportivos Colombia</div>', unsafe_allow_html=True)
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Cerrar sesión", key="logout_btn"):
            st.session_state.authenticated = False
            st.rerun()
    st.markdown('<hr style="margin:12px 0 4px 0">', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TAB 1 — DESCUBRIR
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# TAB 1 — DESCUBRIR
# ─────────────────────────────────────────────
def tab_crm():
    if st.button("🔄 Actualizar datos", key="btn_refresh_crm"):
        st.cache_resource.clear()
        st.rerun()

    df = load_leads()

    if df.empty:
        st.info("No hay leads aún. Ve a **Descubrir** para agregar eventos.")
        return

    # Metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.metric("Total",        len(df))
    with m2: st.metric("Nuevos",       len(df[df["Estado"]=="Nuevo"]))
    with m3: st.metric("Contactados",  len(df[df["Estado"]=="Contactado"]))
    with m4: st.metric("Negociando",   len(df[df["Estado"]=="En negociación"]))
    with m5: st.metric("Cerrados",     len(df[df["Estado"]=="Cerrado"]))

    st.markdown("<br>", unsafe_allow_html=True)

    # Filters
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        f_estado = st.multiselect("Estado", ESTADOS, key="f_estado")
    with fc2:
        ciudades = sorted(df["Ciudad"].dropna().unique().tolist())
        f_ciudad = st.multiselect("Ciudad", ciudades, key="f_ciudad")
    with fc3:
        tipos_available = sorted(df["Tipo"].dropna().unique().tolist())
        f_tipo = st.multiselect("Tipo de evento", tipos_available, key="f_tipo")

    mask = pd.Series([True] * len(df))
    if f_estado: mask &= df["Estado"].isin(f_estado)
    if f_ciudad: mask &= df["Ciudad"].isin(f_ciudad)
    if f_tipo:   mask &= df["Tipo"].isin(f_tipo)
    df_filt = df[mask].reset_index(drop=True)

    st.markdown(
        '<p class="terret-sub" style="font-size:0.78rem;margin:4px 0 12px">'
        + f"{len(df_filt)} leads mostrados</p>",
        unsafe_allow_html=True,
    )

    # Coloured state badges using HTML table
    badge_rows = []
    for _, row in df_filt.iterrows():
        color = STATE_COLORS.get(row["Estado"], "#6B6B8A")
        badge = (
            '<span class="badge" style="background:'
            + color
            + '22;color:'
            + color
            + ';border:1px solid '
            + color
            + '40">'
            + str(row["Estado"])
            + "</span>"
        )
        badge_rows.append(badge)
    df_display = df_filt[["Evento","Tipo","Fecha","Ciudad","Email","Telefono","Estado","Notas"]].copy()
    df_display["Estado_badge"] = badge_rows

    # Show HTML table
    html_rows = ""
    for i, row in df_filt.iterrows():
        color = STATE_COLORS.get(row["Estado"], "#6B6B8A")
        badge_html = (
            '<span class="badge" style="background:'
            + color + "22;color:" + color
            + ";border:1px solid " + color + '40">'
            + str(row["Estado"]) + "</span>"
        )
        html_rows += (
            "<tr style='border-bottom:1px solid #1C1C2E'>"
            + "<td style='padding:8px 12px;font-family:DM Mono,monospace;font-size:0.72rem;color:#6B6B8A'>" + str(row.get("ID","")) + "</td>"
            + "<td style='padding:8px 12px;font-weight:500'>" + str(row.get("Evento","")) + "</td>"
            + "<td style='padding:8px 12px;font-family:DM Mono,monospace;font-size:0.75rem;color:#D4FF00'>" + str(row.get("Tipo","")) + "</td>"
            + "<td style='padding:8px 12px;font-family:DM Mono,monospace;font-size:0.72rem'>" + str(row.get("Fecha","")) + "</td>"
            + "<td style='padding:8px 12px'>" + str(row.get("Ciudad","")) + "</td>"
            + "<td style='padding:8px 12px;font-family:DM Mono,monospace;font-size:0.72rem;color:#6B6B8A'>" + str(row.get("Email","")) + "</td>"
            + "<td style='padding:8px 12px'>" + badge_html + "</td>"
            + "</tr>"
        )

    table_html = (
        "<div style='overflow-x:auto;border:1px solid #1C1C2E;border-radius:8px'>"
        + "<table style='width:100%;border-collapse:collapse;background:#0F0F1A'>"
        + "<thead><tr style='background:#07070F'>"
        + "<th style='padding:10px 12px;text-align:left;font-family:DM Mono,monospace;font-size:0.7rem;letter-spacing:0.1em;color:#6B6B8A;text-transform:uppercase'>ID</th>"
        + "<th style='padding:10px 12px;text-align:left;font-family:DM Mono,monospace;font-size:0.7rem;letter-spacing:0.1em;color:#6B6B8A;text-transform:uppercase'>Evento</th>"
        + "<th style='padding:10px 12px;text-align:left;font-family:DM Mono,monospace;font-size:0.7rem;letter-spacing:0.1em;color:#6B6B8A;text-transform:uppercase'>Tipo</th>"
        + "<th style='padding:10px 12px;text-align:left;font-family:DM Mono,monospace;font-size:0.7rem;letter-spacing:0.1em;color:#6B6B8A;text-transform:uppercase'>Fecha</th>"
        + "<th style='padding:10px 12px;text-align:left;font-family:DM Mono,monospace;font-size:0.7rem;letter-spacing:0.1em;color:#6B6B8A;text-transform:uppercase'>Ciudad</th>"
        + "<th style='padding:10px 12px;text-align:left;font-family:DM Mono,monospace;font-size:0.7rem;letter-spacing:0.1em;color:#6B6B8A;text-transform:uppercase'>Email</th>"
        + "<th style='padding:10px 12px;text-align:left;font-family:DM Mono,monospace;font-size:0.7rem;letter-spacing:0.1em;color:#6B6B8A;text-transform:uppercase'>Estado</th>"
        + "</tr></thead><tbody>"
        + html_rows
        + "</tbody></table></div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)

    # Inline edit
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="terret-sub" style="font-size:0.8rem;letter-spacing:0.14em">EDITAR LEAD</p>', unsafe_allow_html=True)

    lead_names = df_filt["Evento"].tolist()
    if lead_names:
        sel_name = st.selectbox("Selecciona un lead para editar", lead_names, key="edit_lead_sel")
        sel_row  = df_filt[df_filt["Evento"] == sel_name].iloc[0]
        # real index in full df
        real_idx = df[df["ID"] == sel_row["ID"]].index[0]

        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            nuevo_estado = st.selectbox(
                "Estado",
                ESTADOS,
                index=ESTADOS.index(sel_row["Estado"]) if sel_row["Estado"] in ESTADOS else 0,
                key="edit_estado",
            )
        with ec2:
            notas_edit = st.text_input("Notas", value=str(sel_row.get("Notas","")), key="edit_notas")
        with ec3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Guardar cambios", key="btn_save_edit"):
                update_lead_field(real_idx, "Estado", nuevo_estado)
                update_lead_field(real_idx, "Notas",  notas_edit)
                st.success("Lead actualizado ✅")
                st.rerun()

        if st.button("Marcar como Contactado ahora", key="btn_contactado"):
            update_lead_field(real_idx, "Estado", "Contactado")
            update_lead_field(real_idx, "Notas",
                              f"Contactado el {datetime.now().strftime('%Y-%m-%d %H:%M')}. " + str(sel_row.get("Notas","")))
            st.success("Marcado como Contactado ✅")
            st.rerun()

# ─────────────────────────────────────────────
# TAB 3 — EXPORTAR
# ─────────────────────────────────────────────
def tab_exportar():
    df = load_leads()

    if df.empty:
        st.info("No hay leads para exportar.")
        return

    st.markdown('<p class="terret-sub" style="font-size:0.8rem;letter-spacing:0.14em">FILTROS DE EXPORTACIÓN</p>', unsafe_allow_html=True)

    xc1, xc2, xc3 = st.columns(3)
    with xc1:
        xf_estado = st.multiselect("Estado", ESTADOS, key="xf_estado")
    with xc2:
        ciudades = sorted(df["Ciudad"].dropna().unique().tolist())
        xf_ciudad = st.multiselect("Ciudad", ciudades, key="xf_ciudad")
    with xc3:
        tipos_available = sorted(df["Tipo"].dropna().unique().tolist())
        xf_tipo = st.multiselect("Tipo", tipos_available, key="xf_tipo")

    mask = pd.Series([True] * len(df))
    if xf_estado: mask &= df["Estado"].isin(xf_estado)
    if xf_ciudad: mask &= df["Ciudad"].isin(xf_ciudad)
    if xf_tipo:   mask &= df["Tipo"].isin(xf_tipo)
    df_exp = df[mask].reset_index(drop=True)

    st.markdown(f'<p class="mono-sm">{len(df_exp)} leads en esta exportación</p>', unsafe_allow_html=True)
    st.dataframe(df_exp, use_container_width=True, height=280)

    # CSV download
    csv_buffer = io.StringIO()
    df_exp.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    uid_dl = uuid.uuid4().hex[:6]
    st.download_button(
        label="⬇️ Descargar CSV",
        data=csv_buffer.getvalue().encode("utf-8-sig"),
        file_name=f"terret_leads_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        key=f"dl_csv_{uid_dl}",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="terret-sub" style="font-size:0.8rem;letter-spacing:0.14em">TEMPLATE DE EMAIL</p>', unsafe_allow_html=True)

    if df_exp.empty:
        st.info("No hay leads con los filtros actuales.")
        return

    lead_names = df_exp["Evento"].tolist()
    sel_email  = st.selectbox("Selecciona lead para generar email", lead_names, key="email_sel")
    lead_data  = df_exp[df_exp["Evento"] == sel_email].iloc[0].to_dict()
    template   = generate_email_template(lead_data)

    st.text_area(
        "Template (copia y pega)",
        value=template,
        height=320,
        key="email_template_area",
    )

    uid_et = uuid.uuid4().hex[:6]
    st.download_button(
        label="⬇️ Descargar template .txt",
        data=template.encode("utf-8"),
        file_name=f"email_terret_{sel_email[:30].replace(' ','_')}.txt",
        mime="text/plain",
        key=f"dl_email_{uid_et}",
    )

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    if not check_password():
        return

    render_header()

    tab1, tab2, tab3 = st.tabs(["⚡ Descubrir", "📋 Leads / CRM", "📤 Exportar"])

    with tab1:
        tab_descubrir()
    with tab2:
        tab_crm()
    with tab3:
        tab_exportar()


if __name__ == "__main__":
    main()
