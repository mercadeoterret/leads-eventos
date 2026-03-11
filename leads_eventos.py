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
EMAIL_RE    = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE    = re.compile(r"(?:\+?57[\s-]?)?(?:3\d{2}[\s-]?\d{3}[\s-]?\d{4}|(?:\(?\d{1,3}\)?[\s-]?)?\d{6,8})")
INSTA_RE    = re.compile(r"instagram\.com/([A-Za-z0-9_.]+)")
DATE_RE     = re.compile(
    r"(\d{1,2}[\s/\-\.]\w+[\s/\-\.]\d{2,4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\w+ \d{1,2},? \d{4})"
)


CITIES_CO = [
    "bogotá","bogota","medellín","medellin","cali","barranquilla","cartagena",
    "bucaramanga","pereira","manizales","armenia","santa marta","ibagué","ibague",
    "villavicencio","cúcuta","cucuta","pasto","montería","monteria","sincelejo",
    "valledupar","neiva","popayán","popayan","tunja","rionegro","envigado",
    "bello","itagüí","itagui","girardot","fusagasugá","fusagasuga","zipaquirá","zipaquira",
]


def _safe_get(url: str, timeout: int = 14) -> BeautifulSoup | None:
    """GET with retries and multiple User-Agent fallbacks."""
    uas = [
        HEADERS["User-Agent"],
        "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    ]
    for ua in uas:
        h = {**HEADERS, "User-Agent": ua}
        try:
            r = requests.get(url, headers=h, timeout=timeout,
                             allow_redirects=True)
            if r.status_code == 200 and len(r.text) > 500:
                return BeautifulSoup(r.text, "html.parser")
        except Exception:
            continue
    return None


def _extract_contact_info(text: str) -> dict:
    emails = EMAIL_RE.findall(text)
    phones = PHONE_RE.findall(text)
    instas = INSTA_RE.findall(text)
    # filter out common false-positive domains
    bad = {"example","sentry","wix","wordpress","schema","google","w3","jquery"}
    emails = [e for e in emails if e.split("@")[-1].split(".")[0].lower() not in bad]
    return {
        "Email":     emails[0] if emails else "",
        "Telefono":  phones[0] if phones else "",
        "Instagram": "@" + instas[0] if instas else "",
    }


def _guess_tipo(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["cicl","bicicleta","bike","mtb","gran fondo"]): return "Ciclismo"
    if "mtb" in t: return "MTB"
    if "trail" in t: return "Trail"
    if "triat" in t: return "Triatlón"
    if "duat"  in t: return "Duatlón"
    return "Running"


def _extract_city(text: str) -> str:
    tl = text.lower()
    return next((c.title() for c in CITIES_CO if c in tl), "Colombia")


def _abs_url(href: str, base: str) -> str:
    if not href:
        return ""
    if href.startswith("http"):
        return href
    from urllib.parse import urljoin
    return urljoin(base, href)


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


def _parse_events_generic(soup: BeautifulSoup, base_url: str, fuente: str) -> list[dict]:
    """
    Universal event extractor — tries multiple selector strategies in order.
    Returns list of row dicts.
    """
    results = []
    seen    = set()

    # Strategy 1: The Events Calendar (tribe) — used by Atletrack, many WP sites
    tribe_events = soup.find_all("article", class_=re.compile(r"tribe_event|type-tribe", re.I))
    if tribe_events:
        for art in tribe_events[:50]:
            title_a = art.find("a", class_=re.compile(r"tribe-event-url|url", re.I)) or art.find("h2 a") or art.find("h3 a")
            name    = title_a.get_text(strip=True) if title_a else ""
            href    = title_a.get("href","") if title_a else ""
            # date
            date_tag = art.find("abbr", class_=re.compile(r"tribe|date", re.I))
            fecha    = date_tag.get("title","") or date_tag.get_text(strip=True) if date_tag else ""
            if not fecha:
                time_tag = art.find("time")
                fecha = time_tag.get("datetime","") or time_tag.get_text(strip=True) if time_tag else ""
            # venue / city
            venue    = art.find(class_=re.compile(r"tribe-venue|location|venue", re.I))
            ciudad   = _extract_city(venue.get_text() if venue else art.get_text())
            text     = art.get_text(" ", strip=True)
            contact  = _extract_contact_info(text)
            if name and name not in seen:
                seen.add(name)
                results.append(_new_row(
                    evento=name, tipo=_guess_tipo(name+" "+text),
                    fecha=fecha, ciudad=ciudad,
                    web=_abs_url(href, base_url), fuente=fuente,
                    **contact,
                ))
        if results:
            return results

    # Strategy 2: Standard WordPress posts / articles
    articles = soup.find_all("article")
    if articles:
        for art in articles[:50]:
            title_tag = art.find(["h1","h2","h3","h4"])
            name      = title_tag.get_text(strip=True) if title_tag else ""
            link_tag  = (title_tag.find("a") if title_tag else None) or art.find("a", href=True)
            href      = link_tag.get("href","") if link_tag else ""
            time_tag  = art.find("time")
            fecha     = (time_tag.get("datetime","") or time_tag.get_text(strip=True)) if time_tag else ""
            if not fecha:
                m = DATE_RE.search(art.get_text())
                fecha = m.group(0) if m else ""
            text    = art.get_text(" ", strip=True)
            contact = _extract_contact_info(text)
            ciudad  = _extract_city(text)
            if name and name not in seen and len(name) > 4:
                seen.add(name)
                results.append(_new_row(
                    evento=name, tipo=_guess_tipo(name+" "+text),
                    fecha=fecha, ciudad=ciudad,
                    web=_abs_url(href, base_url), fuente=fuente,
                    **contact,
                ))
        if results:
            return results

    # Strategy 3: divs/li with event/card/item class
    for tag in ["div", "li", "section"]:
        cards = soup.find_all(
            tag,
            class_=re.compile(r"event|card|item|race|carrera|resultado|run", re.I),
        )
        for c in cards[:50]:
            links = c.find_all("a", href=True)
            name  = links[0].get_text(strip=True) if links else c.get_text(strip=True)[:80]
            href  = links[0]["href"] if links else ""
            text  = c.get_text(" ", strip=True)
            m     = DATE_RE.search(text)
            fecha = m.group(0) if m else ""
            contact = _extract_contact_info(text)
            ciudad  = _extract_city(text)
            if name and name not in seen and len(name) > 4:
                seen.add(name)
                results.append(_new_row(
                    evento=name, tipo=_guess_tipo(name+" "+text),
                    fecha=fecha, ciudad=ciudad,
                    web=_abs_url(href, base_url), fuente=fuente,
                    **contact,
                ))
        if results:
            return results

    # Strategy 4: All <a> links that look like event names (≥3 words, title-case)
    all_links = soup.find_all("a", href=True)
    for a in all_links:
        name = a.get_text(strip=True)
        href = a["href"]
        if (len(name.split()) >= 3
                and len(name) < 120
                and any(k in name.lower() for k in
                        ["run","trail","cicl","triat","carrera","maraton","maratón",
                         "km","ciclismo","duatl","mtb","cross","fondo","media"])):
            text    = name
            contact = _extract_contact_info(text)
            ciudad  = _extract_city(text)
            m       = DATE_RE.search(text)
            if name not in seen:
                seen.add(name)
                results.append(_new_row(
                    evento=name, tipo=_guess_tipo(name),
                    fecha=m.group(0) if m else "", ciudad=ciudad,
                    web=_abs_url(href, base_url), fuente=fuente,
                    **contact,
                ))
    return results


# ── Atletrack ──
def scrape_atletrack() -> list[dict]:
    for url in ATLETRACK_URLS:
        soup = _safe_get(url)
        if not soup:
            continue
        results = _parse_events_generic(soup, url, "Atletrack")
        if results:
            return results
    return []


# ── Sportadictos ──
def scrape_sportadictos() -> list[dict]:
    for url in SPORTADICTOS_URLS:
        soup = _safe_get(url)
        if not soup:
            continue
        results = _parse_events_generic(soup, url, "Sportadictos")
        if results:
            return results
    return []


# ── Custom URL ──
def scrape_custom_url(url: str) -> list[dict]:
    soup = _safe_get(url)
    if not soup:
        return []
    return _parse_events_generic(soup, url, url)


# ── Extra fallback sources ──
def scrape_extra_sources() -> list[dict]:
    """Try additional Colombian running/cycling directories."""
    all_results = []
    for url, name in EXTRA_SOURCES:
        soup = _safe_get(url)
        if not soup:
            continue
        r = _parse_events_generic(soup, url, name)
        all_results.extend(r)
    return all_results


# ── Google search enrichment (googlesearch-python) ──
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
        for url in urls[:2]:
            soup = _safe_get(url, timeout=6)
            if not soup:
                continue
            txt = soup.get_text(" ", strip=True)[:3000]
            c   = _extract_contact_info(txt)
            if c["Email"] and not ev["Email"]:
                ev["Email"] = c["Email"]
            if c["Telefono"] and not ev["Telefono"]:
                ev["Telefono"] = c["Telefono"]
            if c["Instagram"] and not ev["Instagram"]:
                ev["Instagram"] = c["Instagram"]
            if ev["Email"] and ev["Telefono"]:
                break
        enriched.append(ev)
    return enriched

# ─────────────────────────────────────────────
# EMAIL TEMPLATE
# ─────────────────────────────────────────────
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
def tab_descubrir():
    st.markdown('<p class="terret-sub" style="font-size:0.8rem;letter-spacing:0.14em">MODO DE BÚSQUEDA</p>', unsafe_allow_html=True)
    modo = st.radio(
        "Modo",
        ["🤖 Automático (Atletrack + Sportadictos)", "🔗 URL personalizada"],
        key="modo_busqueda",
        label_visibility="collapsed",
        horizontal=True,
    )

    events_raw: list[dict] = []

    if modo.startswith("🤖"):
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            do_atletrack    = st.checkbox("Atletrack.com",      value=True,  key="chk_atletrack")
        with col2:
            do_sportadictos = st.checkbox("Sportadictos.com",   value=True,  key="chk_sportadictos")
        with col3:
            do_extra        = st.checkbox("+ Otras fuentes CO", value=True,  key="chk_extra")
        with col4:
            do_enrich       = st.checkbox("Enriquecer con Google Search (lento)", value=False, key="chk_enrich")

        if st.button("Buscar eventos", key="btn_buscar_auto"):
            progress = st.progress(0, text="Iniciando búsqueda...")
            all_events: list[dict] = []
            step = 0
            total_steps = sum([do_atletrack, do_sportadictos, do_extra]) or 1

            if do_atletrack:
                progress.progress(int(step/total_steps*80)+5, text="Scrapeando Atletrack.com...")
                at = scrape_atletrack()
                if at:
                    st.success(f"✅ Atletrack: {len(at)} eventos encontrados")
                else:
                    st.warning("⚠️ Atletrack: 0 eventos — el sitio puede estar bloqueando temporalmente. Prueba con URL personalizada.")
                all_events.extend(at)
                step += 1

            if do_sportadictos:
                progress.progress(int(step/total_steps*80)+5, text="Scrapeando Sportadictos.com...")
                sp = scrape_sportadictos()
                if sp:
                    st.success(f"✅ Sportadictos: {len(sp)} eventos encontrados")
                else:
                    st.warning("⚠️ Sportadictos: 0 eventos — el sitio puede estar bloqueando temporalmente.")
                all_events.extend(sp)
                step += 1

            if do_extra:
                progress.progress(int(step/total_steps*80)+5, text="Buscando en fuentes adicionales...")
                ex = scrape_extra_sources()
                if ex:
                    st.success(f"✅ Fuentes adicionales: {len(ex)} eventos encontrados")
                all_events.extend(ex)
                step += 1

            if do_enrich and all_events:
                progress.progress(90, text="Enriqueciendo con Google Search...")
                all_events = enrich_with_google(all_events)

            progress.progress(100, text="Listo")
            time.sleep(0.4)
            progress.empty()

            if not all_events:
                st.error(
                    "**0 eventos en total.** Posibles causas:\n\n"
                    "• Los sitios bloquean IPs de Streamlit Cloud (muy común)\n"
                    "• Cambiaron su estructura HTML\n\n"
                    "**Solución rápida:** usa el modo **URL personalizada** y pega directamente "
                    "la URL de cualquier directorio de eventos que puedas abrir en tu navegador."
                )
            else:
                st.session_state["discovered"] = all_events

    else:
        url_input = st.text_input(
            "URL del directorio de eventos",
            placeholder="https://ejemplo.com/eventos",
            key="custom_url_input",
        )
        st.markdown(
            '<p class="mono-sm">Pega la URL de cualquier página con listado de eventos: '
            'Atletrack, Sportadictos, RunColombia, Facebook Events, etc.</p>',
            unsafe_allow_html=True,
        )
        do_enrich2 = st.checkbox("Enriquecer con Google Search", value=False, key="chk_enrich2")
        if st.button("Scrapear URL", key="btn_scrape_url"):
            if url_input:
                with st.spinner(f"Scrapeando {url_input}..."):
                    events_raw = scrape_custom_url(url_input)
                    if do_enrich2 and events_raw:
                        events_raw = enrich_with_google(events_raw)
                if events_raw:
                    st.success(f"✅ {len(events_raw)} eventos encontrados")
                    st.session_state["discovered"] = events_raw
                else:
                    st.error(
                        "No se pudieron extraer eventos de esa URL.\n\n"
                        "Puede que el sitio bloquee scraping o use JavaScript dinámico. "
                        "Intenta con otra URL del mismo sitio (ej: página 2, versión móvil)."
                    )
            else:
                st.warning("Ingresa una URL primero")

    # ── Results table ──
    if "discovered" in st.session_state and st.session_state["discovered"]:
        discovered = st.session_state["discovered"]
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<p class="terret-sub" style="font-size:0.8rem;letter-spacing:0.14em">'
            + str(len(discovered)) + " EVENTOS ENCONTRADOS — EDITA Y SELECCIONA</p>",
            unsafe_allow_html=True,
        )

        df_preview = pd.DataFrame(discovered)
        display_cols = ["Evento","Tipo","Fecha","Ciudad","Email","Telefono","Instagram","Web","Fuente"]
        df_show = df_preview[display_cols].copy()

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

        st.markdown('<p class="terret-sub" style="font-size:0.75rem;margin-top:8px">Selecciona filas a guardar</p>', unsafe_allow_html=True)
        seleccionados = []
        for i, row in edited.iterrows():
            uid = uuid.uuid4().hex[:6]
            if st.checkbox(
                row["Evento"][:60] if row["Evento"] else f"Fila {i+1}",
                value=True,
                key=f"sel_{i}_{uid}",
            ):
                seleccionados.append(i)

        col_save1, col_save2 = st.columns([1, 4])
        with col_save1:
            if st.button("💾 Guardar seleccionados", key="btn_guardar"):
                if not seleccionados:
                    st.warning("No hay filas seleccionadas")
                else:
                    rows_to_save = []
                    for i in seleccionados:
                        base = discovered[i].copy()
                        base.update({
                            col: edited.iloc[i][col]
                            for col in display_cols if col in edited.columns
                        })
                        rows_to_save.append(base)
                    with st.spinner("Guardando en Google Sheets..."):
                        added = save_leads(rows_to_save)
                    st.success(f"✅ {added} leads guardados (duplicados omitidos)")
                    if "discovered" in st.session_state:
                        del st.session_state["discovered"]
                    st.rerun()
        with col_save2:
            if st.button("Limpiar resultados", key="btn_limpiar"):
                del st.session_state["discovered"]
                st.rerun()

# ─────────────────────────────────────────────
# TAB 2 — LEADS / CRM
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
