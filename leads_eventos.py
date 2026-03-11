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
# CONSTANTS
# ─────────────────────────────────────────────
SHEET_NAME  = "Terret — Leads Eventos"
WORKSHEET   = "Leads"
COLUMNS     = ["ID","Evento","Tipo","Fecha","Ciudad","Organizador",
               "Email","Telefono","Instagram","Web","Fuente","Estado",
               "Notas","Fecha_Agregado"]
ESTADOS     = ["Nuevo","Contactado","En negociación","Cerrado","Descartado"]
TIPOS       = ["Running","Ciclismo","Trail","Triatlón","Duatlón","MTB","Otro"]

ATLETRACK_URLS = [
    "https://www.atletrack.com/eventos",
    "https://www.atletrack.com/eventos/list/",
    "https://www.atletrack.com/calendario",
]
SPORTADICTOS_URLS = [
    "https://sportadictos.com/categoria/carreras-populares/",
    "https://sportadictos.com/category/carreras/",
    "https://sportadictos.com/carreras/",
]
EXTRA_SOURCES = [
    ("https://correr.co/carreras/",            "Correr.co"),
    ("https://www.carrerasenruta.com/eventos/", "CarrerasEnRuta"),
    ("https://runningcolombia.co/eventos/",     "RunningColombia"),
    ("https://triatlon.com.co/eventos/",        "Triatlon.com.co"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-CO,es;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}

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

        pwd = st.text_input("Contraseña", type="password", key="login_pwd",
                            placeholder="••••••••")
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
        sh.share(
            st.secrets["gcp_service_account"]["client_email"],
            perm_type="user",
            role="writer",
        )
    try:
        ws = sh.worksheet(WORKSHEET)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=WORKSHEET, rows=1000, cols=len(COLUMNS))
        ws.append_row(COLUMNS)
        _fmt_header(ws)
    return ws


def _fmt_header(ws):
    """Bold header row."""
    try:
        ws.format("A1:N1", {
            "textFormat": {"bold": True, "fontSize": 10},
            "backgroundColor": {"red": 0.06, "green": 0.06, "blue": 0.12},
        })
    except Exception:
        pass


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


def save_leads(rows: list[dict]):
    """Append new rows to the sheet."""
    ws = get_or_create_sheet()
    existing = ws.get_all_records()
    existing_events = {r.get("Evento", "").lower().strip() for r in existing}
    added = 0
    for row in rows:
        if row.get("Evento", "").lower().strip() in existing_events:
            continue
        row_vals = [row.get(c, "") for c in COLUMNS]
        ws.append_row(row_vals, value_input_option="USER_ENTERED")
        existing_events.add(row.get("Evento", "").lower().strip())
        added += 1
    return added


def update_lead_field(row_idx: int, field: str, value: str):
    """Update a single cell. row_idx is 0-based DataFrame index."""
    ws = get_or_create_sheet()
    col_idx = COLUMNS.index(field) + 1
    ws_row   = row_idx + 2          # +1 header +1 1-based
    ws.update_cell(ws_row, col_idx, value)

# ─────────────────────────────────────────────
# SCRAPING UTILITIES
# ─────────────────────────────────────────────
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(?:\+?57[\s-]?)?(?:3\d{2}[\s-]?\d{3}[\s-]?\d{4}|(?:\(?\d{1,3}\)?[\s-]?)?\d{6,8})")
INSTA_RE = re.compile(r"instagram\.com/([A-Za-z0-9_.]+)")
DATE_RE  = re.compile(
    r"(\d{1,2}[\s/\-\.]\w+[\s/\-\.]\d{2,4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\w+ \d{1,2},? \d{4})"
)

CITIES_CO = [
    "bogotá","bogota","medellín","medellin","cali","barranquilla","cartagena",
    "bucaramanga","pereira","manizales","armenia","santa marta","ibagué","ibague",
    "villavicencio","cúcuta","cucuta","pasto","montería","monteria","sincelejo",
    "valledupar","neiva","popayán","popayan","tunja","rionegro","envigado",
    "bello","itagüí","itagui","girardot","fusagasugá","fusagasuga","zipaquirá","zipaquira",
    "eje cafetero","antioquia","cundinamarca","tolima","santander","boyacá","boyaca",
]

# Sources with RSS feeds (WordPress /feed/ always works, never blocked)
RSS_SOURCES = [
    ("https://sportadictos.com/feed/",                          "Sportadictos"),
    ("https://correr.co/feed/",                                 "Correr.co"),
    ("https://runningcolombia.co/feed/",                        "RunningColombia"),
    ("https://www.ciclismoafondo.es/feed/",                     "CiclismoAfondo"),
    ("https://triatlon.org/feed/",                              "Triatlon.org"),
    ("https://sportadictos.com/categoria/carreras-populares/feed/", "Sportadictos-Carreras"),
    ("https://correr.co/carreras/feed/",                        "Correr.co-Carreras"),
]

# AllOrigins proxy — bypasses IP blocks from Streamlit Cloud
ALLORIGINS = "https://api.allorigins.win/get?url={}"

DIRECT_URLS = [
    ("https://www.atletrack.com/eventos",                       "Atletrack"),
    ("https://www.atletrack.com/eventos/list/",                 "Atletrack"),
    ("https://sportadictos.com/categoria/carreras-populares/",  "Sportadictos"),
    ("https://correr.co/carreras/",                             "Correr.co"),
    ("https://travesiadeportiva.com/eventos/",                  "TravesiaDeportiva"),
    ("https://travesiadeportiva.com/",                          "TravesiaDeportiva"),
    ("https://www.carrerasenruta.com/eventos/",                 "CarrerasEnRuta"),
]

HEADERS_SCRAPE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


def _extract_contact_info(text: str) -> dict:
    emails = EMAIL_RE.findall(text)
    phones = PHONE_RE.findall(text)
    instas = INSTA_RE.findall(text)
    bad = {"example","sentry","wix","wordpress","schema","google","w3","jquery",
           "domain","email","support","info","noreply","test"}
    emails = [e for e in emails if e.split("@")[-1].split(".")[0].lower() not in bad]
    return {
        "Email":     emails[0] if emails else "",
        "Telefono":  phones[0] if phones else "",
        "Instagram": "@" + instas[0] if instas else "",
    }


def _guess_tipo(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["cicl","bicicleta","bike","gran fondo","ciclovía"]): return "Ciclismo"
    if "mtb" in t: return "MTB"
    if "trail" in t: return "Trail"
    if "triat" in t: return "Triatlón"
    if "duat"  in t: return "Duatlón"
    return "Running"


def _extract_city(text: str) -> str:
    tl = text.lower()
    return next((c.title() for c in CITIES_CO if c in tl), "Colombia")


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


# ── Method 1: RSS feed (most reliable — WordPress /feed/ is never blocked) ──
def _scrape_rss(feed_url: str, source_name: str) -> list[dict]:
    """Parse an RSS/Atom feed. Returns list of event rows."""
    if not HAS_FEEDPARSER:
        return []
    try:
        # feedparser handles redirects and encoding automatically
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            # Try via allorigins proxy
            proxied = ALLORIGINS.format(quote_plus(feed_url))
            r = requests.get(proxied, timeout=12)
            if r.status_code == 200:
                data = r.json()
                feed = feedparser.parse(data.get("contents",""))
        results = []
        seen = set()
        for entry in feed.entries[:40]:
            name = entry.get("title","").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            link    = entry.get("link","")
            summary = BeautifulSoup(
                entry.get("summary","") + entry.get("content",[{"value":""}])[0].get("value",""),
                "html.parser"
            ).get_text(" ", strip=True)
            pub     = entry.get("published","") or entry.get("updated","")
            # Try to extract date from published field
            fecha = pub[:10] if pub else ""
            if not fecha:
                m = DATE_RE.search(summary)
                fecha = m.group(0) if m else ""
            contact = _extract_contact_info(summary)
            ciudad  = _extract_city(name + " " + summary)
            results.append(_new_row(
                evento=name,
                tipo=_guess_tipo(name + " " + summary),
                fecha=fecha,
                ciudad=ciudad,
                web=link,
                fuente=source_name,
                **contact,
            ))
        return results
    except Exception:
        return []


# ── Method 2: Direct HTTP (works when site doesn't block cloud IPs) ──
def _scrape_direct(url: str, source_name: str) -> list[dict]:
    """Direct HTTP GET with multiple UA fallbacks."""
    uas = [
        HEADERS_SCRAPE["User-Agent"],
        "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "curl/8.4.0",
    ]
    soup = None
    for ua in uas:
        try:
            r = requests.get(url, headers={**HEADERS_SCRAPE, "User-Agent": ua},
                             timeout=14, allow_redirects=True)
            if r.status_code == 200 and len(r.text) > 800:
                soup = BeautifulSoup(r.text, "html.parser")
                break
        except Exception:
            continue
    if not soup:
        return []
    return _parse_html(soup, url, source_name)


# ── Method 3: AllOrigins proxy (bypasses IP blocks) ──
def _scrape_via_proxy(url: str, source_name: str) -> list[dict]:
    """Fetch through allorigins.win free proxy."""
    try:
        proxied = ALLORIGINS.format(quote_plus(url))
        r = requests.get(proxied, timeout=20)
        if r.status_code != 200:
            return []
        data = r.json()
        html = data.get("contents","")
        if len(html) < 500:
            return []
        soup = BeautifulSoup(html, "html.parser")
        return _parse_html(soup, url, source_name)
    except Exception:
        return []


# ── HTML parser (shared by direct + proxy) ──
def _parse_html(soup: BeautifulSoup, base_url: str, fuente: str) -> list[dict]:
    results = []
    seen    = set()

    def _add(name, href, text, fecha=""):
        nonlocal results
        if not name or name in seen or len(name) < 5:
            return
        seen.add(name)
        if not fecha:
            m = DATE_RE.search(text)
            fecha = m.group(0) if m else ""
        contact = _extract_contact_info(text)
        ciudad  = _extract_city(name + " " + text)
        web     = href if href.startswith("http") else urljoin(base_url, href)
        results.append(_new_row(
            evento=name, tipo=_guess_tipo(name+" "+text),
            fecha=fecha, ciudad=ciudad, web=web, fuente=fuente,
            **contact,
        ))

    # Tribe Events Calendar
    for art in soup.find_all("article", class_=re.compile(r"tribe_event|type-tribe", re.I))[:50]:
        a      = art.find("a", class_=re.compile(r"tribe-event-url", re.I)) or art.find("h2")
        name   = a.get_text(strip=True) if a else ""
        href   = a.get("href","") if hasattr(a,"get") else ""
        dt_tag = art.find("abbr") or art.find("time")
        fecha  = (dt_tag.get("title","") or dt_tag.get("datetime","") or dt_tag.get_text(strip=True)) if dt_tag else ""
        _add(name, href, art.get_text(" ", strip=True), fecha)
    if results: return results

    # WordPress articles
    for art in soup.find_all("article")[:50]:
        h     = art.find(["h2","h3","h4"])
        name  = h.get_text(strip=True) if h else ""
        a     = (h.find("a") if h else None) or art.find("a", href=True)
        href  = a.get("href","") if a else ""
        t_tag = art.find("time")
        fecha = (t_tag.get("datetime","") or t_tag.get_text(strip=True)) if t_tag else ""
        _add(name, href, art.get_text(" ", strip=True), fecha)
    if results: return results

    # Generic cards/items
    for tag in ["div","li","section"]:
        for c in soup.find_all(tag, class_=re.compile(r"event|card|item|race|carrera|run", re.I))[:50]:
            links = c.find_all("a", href=True)
            name  = links[0].get_text(strip=True) if links else c.get_text(strip=True)[:80]
            href  = links[0]["href"] if links else ""
            _add(name, href, c.get_text(" ", strip=True))
        if results: return results

    # Event-keyword links fallback
    for a in soup.find_all("a", href=True):
        name = a.get_text(strip=True)
        if (3 <= len(name.split()) <= 12
                and any(k in name.lower() for k in
                        ["run","trail","cicl","triat","carrera","maratón","maratón",
                         "km","ciclismo","duatl","mtb","cross","fondo","travesía"])):
            _add(name, a["href"], name)
    return results


# ── Orchestrators ──
def scrape_rss_all() -> tuple[list[dict], list[str]]:
    """Try all RSS feeds. Returns (events, working_sources)."""
    all_events  : list[dict] = []
    working     : list[str]  = []
    for feed_url, name in RSS_SOURCES:
        rows = _scrape_rss(feed_url, name)
        if rows:
            all_events.extend(rows)
            working.append(name)
    return all_events, working


def scrape_direct_all() -> tuple[list[dict], list[str], list[str]]:
    """Try all direct URLs. Returns (events, working_sources, failed_sources)."""
    all_events : list[dict] = []
    working    : list[str]  = []
    failed     : list[str]  = []
    for url, name in DIRECT_URLS:
        rows = _scrape_direct(url, name)
        if rows:
            all_events.extend(rows)
            if name not in working:
                working.append(name)
        else:
            # Try proxy fallback
            rows = _scrape_via_proxy(url, name)
            if rows:
                all_events.extend(rows)
                if name not in working:
                    working.append(name + " (proxy)")
            else:
                if name not in failed:
                    failed.append(name)
    return all_events, working, failed


def scrape_url(url: str) -> list[dict]:
    """Scrape a single URL: try direct first, then proxy."""
    rows = _scrape_direct(url, url)
    if rows:
        return rows
    return _scrape_via_proxy(url, url)


def enrich_with_google(events: list[dict]) -> list[dict]:
    try:
        from googlesearch import search as gsearch
    except ImportError:
        return events
    enriched = []
    for ev in events:
        if ev.get("Email") and ev.get("Telefono"):
            enriched.append(ev)
            continue
        query = '"' + ev["Evento"] + ' Colombia" contacto organizador email'
        try:
            urls = list(gsearch(query, num_results=3, lang="es", sleep_interval=1))
        except Exception:
            enriched.append(ev)
            continue
        for u in urls[:2]:
            rows = _scrape_direct(u, "")
            soup_txt = ""
            try:
                r = requests.get(u, headers=HEADERS_SCRAPE, timeout=8)
                soup_txt = BeautifulSoup(r.text,"html.parser").get_text(" ",strip=True)[:3000]
            except Exception:
                pass
            c = _extract_contact_info(soup_txt)
            if c["Email"]     and not ev["Email"]:     ev["Email"]     = c["Email"]
            if c["Telefono"]  and not ev["Telefono"]:  ev["Telefono"]  = c["Telefono"]
            if c["Instagram"] and not ev["Instagram"]: ev["Instagram"] = c["Instagram"]
            if ev["Email"] and ev["Telefono"]:
                break
        enriched.append(ev)
    return enriched

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
def tab_descubrir():
    st.markdown('<p class="terret-sub" style="font-size:0.8rem;letter-spacing:0.14em">MODO DE BÚSQUEDA</p>', unsafe_allow_html=True)

    modo = st.radio(
        "Modo",
        ["🤖 Automático", "🔗 URL personalizada", "✏️ Entrada manual"],
        key="modo_busqueda",
        label_visibility="collapsed",
        horizontal=True,
    )

    # ──────────────────────────────────
    # MODO AUTOMÁTICO
    # ──────────────────────────────────
    if modo == "🤖 Automático":
        st.markdown(
            '<p class="mono-sm">Intenta RSS feeds primero (más confiable), luego HTTP directo '
            'y proxy como fallback.</p>',
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns([1, 3])
        with col1:
            do_enrich = st.checkbox("Enriquecer con Google Search (lento)", value=False, key="chk_enrich")

        if st.button("Buscar eventos", key="btn_buscar_auto"):
            all_events: list[dict] = []
            log_msgs: list[tuple[str,str]] = []  # (level, msg)

            prog = st.progress(0, text="Buscando vía RSS feeds...")

            # Step 1 — RSS (most reliable)
            rss_events, rss_ok = scrape_rss_all()
            if rss_events:
                all_events.extend(rss_events)
                log_msgs.append(("ok", f"RSS feeds: {len(rss_events)} eventos de {', '.join(rss_ok)}"))
            else:
                log_msgs.append(("warn", "RSS feeds: sin resultados"))

            prog.progress(40, text="Intentando scraping directo...")

            # Step 2 — Direct + proxy
            direct_events, direct_ok, direct_fail = scrape_direct_all()
            if direct_events:
                all_events.extend(direct_events)
                log_msgs.append(("ok", f"Scraping: {len(direct_events)} eventos de {', '.join(direct_ok)}"))
            if direct_fail:
                log_msgs.append(("warn", f"Bloqueados (normal en cloud): {', '.join(direct_fail)}"))

            prog.progress(80, text="Deduplicando...")

            # Deduplicate by name
            seen_names: set[str] = set()
            unique: list[dict] = []
            for ev in all_events:
                k = ev["Evento"].lower().strip()
                if k and k not in seen_names:
                    seen_names.add(k)
                    unique.append(ev)
            all_events = unique

            if do_enrich and all_events:
                prog.progress(85, text="Enriqueciendo con Google Search...")
                all_events = enrich_with_google(all_events)

            prog.progress(100, text="Listo")
            time.sleep(0.3)
            prog.empty()

            # Show log
            for level, msg in log_msgs:
                if level == "ok":
                    st.success("✅ " + msg)
                else:
                    st.warning("⚠️ " + msg)

            if all_events:
                st.session_state["discovered"] = all_events
            else:
                st.error(
                    "**0 eventos encontrados.** Los sitios están bloqueando las IPs de Streamlit Cloud. "
                    "Soluciones:\n\n"
                    "**1.** Cambia a **🔗 URL personalizada** — abre el sitio en tu navegador, "
                    "copia la URL y pégala aquí.\n\n"
                    "**2.** Usa **✏️ Entrada manual** para agregar eventos directamente."
                )

    # ──────────────────────────────────
    # MODO URL PERSONALIZADA
    # ──────────────────────────────────
    elif modo == "🔗 URL personalizada":
        st.markdown(
            '<p class="mono-sm">Abre el sitio de eventos en tu navegador, copia la URL y pégala aquí. '
            'La app intenta scraping directo y luego proxy automáticamente.</p>',
            unsafe_allow_html=True,
        )
        url_input = st.text_input(
            "URL del directorio",
            placeholder="https://www.atletrack.com/eventos",
            key="custom_url_input",
        )
        do_enrich2 = st.checkbox("Enriquecer con Google Search", value=False, key="chk_enrich2")

        if st.button("Scrapear URL", key="btn_scrape_url"):
            if not url_input.strip():
                st.warning("Ingresa una URL primero")
            else:
                with st.spinner("Intentando scraping directo..."):
                    rows = _scrape_direct(url_input.strip(), url_input.strip())
                if not rows:
                    with st.spinner("Directo bloqueado — intentando vía proxy..."):
                        rows = _scrape_via_proxy(url_input.strip(), url_input.strip())
                if not rows:
                    # Try as RSS
                    with st.spinner("Intentando como RSS feed..."):
                        rows = _scrape_rss(url_input.strip(), url_input.strip())

                if rows:
                    if do_enrich2:
                        with st.spinner("Enriqueciendo con Google..."):
                            rows = enrich_with_google(rows)
                    st.success(f"✅ {len(rows)} eventos encontrados")
                    st.session_state["discovered"] = rows
                else:
                    st.error(
                        "No se pudieron extraer eventos. El sitio posiblemente usa **JavaScript dinámico** "
                        "(React/Angular/Vue) que no es scrapeable sin un navegador real.\n\n"
                        "**Alternativas:**\n"
                        "- Prueba con la URL del feed RSS: agrega `/feed/` al final de la URL\n"
                        "- Usa **✏️ Entrada manual** para agregar el evento directamente"
                    )

    # ──────────────────────────────────
    # MODO ENTRADA MANUAL
    # ──────────────────────────────────
    else:
        st.markdown(
            '<p class="mono-sm">Agrega eventos manualmente — útil cuando el scraping '
            'no funciona o para eventos que encuentras navegando.</p>',
            unsafe_allow_html=True,
        )
        with st.form("form_manual", clear_on_submit=True):
            mc1, mc2 = st.columns(2)
            with mc1:
                m_evento  = st.text_input("Nombre del evento *", placeholder="Maratón de Bogotá 2025")
                m_ciudad  = st.text_input("Ciudad", placeholder="Bogotá")
                m_fecha   = st.text_input("Fecha", placeholder="2025-08-10")
                m_tipo    = st.selectbox("Tipo", TIPOS, key="manual_tipo")
            with mc2:
                m_org     = st.text_input("Organizador", placeholder="Club Atlético XYZ")
                m_email   = st.text_input("Email", placeholder="contacto@evento.com")
                m_telefono= st.text_input("Teléfono", placeholder="310 123 4567")
                m_insta   = st.text_input("Instagram", placeholder="@maratondebogota")
            m_web     = st.text_input("Sitio web", placeholder="https://maratondebogota.com")
            m_notas   = st.text_area("Notas", placeholder="Info adicional sobre el evento...", height=80)
            submitted = st.form_submit_button("Agregar a la lista")

        if submitted:
            if not m_evento.strip():
                st.warning("El nombre del evento es obligatorio")
            else:
                row = _new_row(
                    evento=m_evento.strip(), tipo=m_tipo, fecha=m_fecha.strip(),
                    ciudad=m_ciudad.strip(), organizador=m_org.strip(),
                    email=m_email.strip(), telefono=m_telefono.strip(),
                    instagram=m_insta.strip(), web=m_web.strip(),
                    fuente="Manual", notas=m_notas.strip(),
                )
                prev = st.session_state.get("discovered", [])
                prev.append(row)
                st.session_state["discovered"] = prev
                st.success(f"✅ Evento '{m_evento}' agregado a la lista")

    # ── Results table ──────────────────
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
            df_show,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_discovered",
            column_config={
                "Tipo": st.column_config.SelectboxColumn("Tipo", options=TIPOS),
                "Web":  st.column_config.LinkColumn("Web"),
            },
        )

        st.markdown(
            '<p class="terret-sub" style="font-size:0.75rem;margin-top:8px;letter-spacing:0.1em">'
            'SELECCIONA FILAS A GUARDAR</p>',
            unsafe_allow_html=True,
        )
        seleccionados = []
        for i, row in edited.iterrows():
            uid = uuid.uuid4().hex[:6]
            label = row["Evento"][:60] if row["Evento"] else f"Fila {i+1}"
            if st.checkbox(label, value=True, key="sel_" + str(i) + "_" + uid):
                seleccionados.append(i)

        col_s1, col_s2 = st.columns([1, 4])
        with col_s1:
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
                    st.success(f"✅ {added} leads guardados (duplicados omitidos)")
                    del st.session_state["discovered"]
                    st.rerun()
        with col_s2:
            if st.button("Limpiar lista", key="btn_limpiar"):
                del st.session_state["discovered"]
                st.rerun()

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
