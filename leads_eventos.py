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
def _build_scraper_html(urls: list[str], source_labels: list[str]) -> str:
    urls_js    = json.dumps(urls)
    labels_js  = json.dumps(source_labels)

    return """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #07070F;
    font-family: 'DM Mono', 'Courier New', monospace;
    font-size: 12px;
    color: #E8E8F0;
    padding: 12px;
    min-height: 60px;
  }
  #status {
    color: #6B6B8A;
    font-size: 11px;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
    min-height: 16px;
  }
  .bar-wrap {
    background: #1C1C2E;
    border-radius: 3px;
    height: 4px;
    width: 100%;
    margin-bottom: 8px;
    overflow: hidden;
  }
  #bar {
    background: #D4FF00;
    height: 4px;
    width: 0%;
    transition: width 0.3s ease;
    border-radius: 3px;
  }
  #result-box {
    display: none;
    background: #0F0F1A;
    border: 1px solid #1C1C2E;
    border-radius: 6px;
    padding: 10px 14px;
    margin-top: 8px;
    font-size: 11px;
    color: #D4FF00;
    letter-spacing: 0.06em;
  }
  .err { color: #EF4444 !important; }
</style>
</head>
<body>
<div id="status">Iniciando scraping desde tu navegador...</div>
<div class="bar-wrap"><div id="bar"></div></div>
<div id="result-box"></div>

<script>
const URLS   = """ + urls_js + """;
const LABELS = """ + labels_js + """;
const PROXY  = 'https://api.allorigins.win/get?url=';

const CITIES = ['bogotá','bogota','medellín','medellin','cali','barranquilla',
  'cartagena','bucaramanga','pereira','manizales','armenia','santa marta',
  'ibagué','ibague','villavicencio','cúcuta','cucuta','pasto','montería',
  'monteria','sincelejo','valledupar','neiva','popayán','popayan','tunja',
  'rionegro','envigado','bello','itagüí','itagui','girardot','medellín'];

function guessCity(text) {
  const t = text.toLowerCase();
  for (const c of CITIES) { if (t.includes(c)) return c.charAt(0).toUpperCase() + c.slice(1); }
  return 'Colombia';
}
function guessTipo(text) {
  const t = text.toLowerCase();
  if (/cicl|bicicleta|bike|gran fondo/.test(t)) return 'Ciclismo';
  if (/\\bmtb\\b/.test(t)) return 'MTB';
  if (/trail/.test(t)) return 'Trail';
  if (/triat/.test(t)) return 'Triatlón';
  if (/duat/.test(t))  return 'Duatlón';
  return 'Running';
}
function extractEmail(text) {
  const m = text.match(/[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+/);
  if (!m) return '';
  const bad = ['example','wordpress','schema','google','w3','jquery','sentry','wix'];
  const domain = m[0].split('@')[1].split('.')[0].toLowerCase();
  return bad.includes(domain) ? '' : m[0];
}
function extractPhone(text) {
  const m = text.match(/(?:\\+?57[\\s-]?)?3\\d{2}[\\s-]?\\d{3}[\\s-]?\\d{4}/);
  return m ? m[0] : '';
}
function extractInsta(text) {
  const m = text.match(/instagram\\.com\\/([A-Za-z0-9_.]+)/);
  return m ? '@' + m[1] : '';
}
function extractDate(text) {
  const m = text.match(/\\d{1,2}[\\s\\/\\-\\.]\\w+[\\s\\/\\-\\.]\\d{2,4}|\\d{1,2}[\\/\\-]\\d{1,2}[\\/\\-]\\d{2,4}/);
  return m ? m[0] : '';
}

function parseHTML(html, baseUrl, fuente) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');
  const events = [];
  const seen = new Set();

  function addEvent(name, href, textContent, fecha) {
    name = (name || '').trim().replace(/\\s+/g,' ').substring(0,180);
    if (!name || name.length < 5 || seen.has(name.toLowerCase())) return;
    seen.add(name.toLowerCase());
    const fullUrl = href
      ? (href.startsWith('http') ? href : new URL(href, baseUrl).href)
      : baseUrl;
    const fecha2 = fecha || extractDate(textContent);
    events.push({
      nombre:     name,
      tipo:       guessTipo(name + ' ' + textContent),
      fecha:      fecha2,
      ciudad:     guessCity(name + ' ' + textContent),
      email:      extractEmail(textContent),
      telefono:   extractPhone(textContent),
      instagram:  extractInsta(textContent),
      web:        fullUrl,
      fuente:     fuente,
    });
  }

  // Strategy 1: Tribe Events Calendar
  const tribe = doc.querySelectorAll('article[class*="tribe_event"], article[class*="type-tribe"]');
  if (tribe.length > 0) {
    tribe.forEach(art => {
      const a = art.querySelector('a[class*="tribe-event-url"]') || art.querySelector('h2 a') || art.querySelector('h3 a');
      const name = a ? a.textContent.trim() : '';
      const href = a ? a.getAttribute('href') : '';
      const abbr = art.querySelector('abbr[title]');
      const timeEl = art.querySelector('time');
      const fecha  = abbr ? abbr.getAttribute('title') : (timeEl ? (timeEl.getAttribute('datetime') || timeEl.textContent.trim()) : '');
      addEvent(name, href, art.textContent, fecha);
    });
    if (events.length > 0) return events;
  }

  // Strategy 2: WordPress articles
  const arts = doc.querySelectorAll('article');
  if (arts.length > 0) {
    arts.forEach(art => {
      const h = art.querySelector('h1,h2,h3,h4');
      const a = h ? (h.querySelector('a') || art.querySelector('a[href]')) : art.querySelector('a[href]');
      const name = h ? h.textContent.trim() : '';
      const href = a ? a.getAttribute('href') : '';
      const t = art.querySelector('time');
      const fecha = t ? (t.getAttribute('datetime') || t.textContent.trim()) : '';
      addEvent(name, href, art.textContent, fecha);
    });
    if (events.length > 0) return events;
  }

  // Strategy 3: cards/items
  const cards = doc.querySelectorAll('[class*="event"],[class*="card"],[class*="item"],[class*="race"],[class*="carrera"]');
  cards.forEach(c => {
    const links = c.querySelectorAll('a[href]');
    const name  = links.length ? links[0].textContent.trim() : c.textContent.trim().substring(0,80);
    const href  = links.length ? links[0].getAttribute('href') : '';
    addEvent(name, href, c.textContent, '');
  });
  if (events.length > 0) return events;

  // Strategy 4: keyword links
  doc.querySelectorAll('a[href]').forEach(a => {
    const name = a.textContent.trim();
    if (name.split(' ').length >= 3 && name.length < 120 &&
        /run|trail|cicl|triat|carrera|maratón|maratón|ciclismo|duatl|mtb|travesía|fondo/i.test(name)) {
      addEvent(name, a.getAttribute('href'), name, '');
    }
  });

  return events;
}

async function fetchViaProxy(url) {
  const proxyUrl = PROXY + encodeURIComponent(url);
  const resp = await fetch(proxyUrl, { signal: AbortSignal.timeout(20000) });
  if (!resp.ok) throw new Error('proxy ' + resp.status);
  const data = await resp.json();
  if (!data.contents || data.contents.length < 500) throw new Error('empty response');
  return data.contents;
}

async function scrapeOne(url, label, index, total) {
  setStatus('Scrapeando ' + label + ' (' + (index+1) + '/' + total + ')...');
  setBar(Math.round((index / total) * 90));

  let html = null;

  // Try 1: direct fetch
  try {
    const resp = await fetch(url, {
      signal: AbortSignal.timeout(12000),
      headers: { 'Accept': 'text/html,*/*' }
    });
    if (resp.ok) { html = await resp.text(); }
  } catch(e) {}

  // Try 2: via allorigins proxy (works from real browser IPs)
  if (!html || html.length < 500) {
    try { html = await fetchViaProxy(url); } catch(e) {}
  }

  // Try 3: RSS feed variant
  if (!html || html.length < 500) {
    const rssUrl = url.replace(/\\/?$/, '') + '/feed/';
    try { html = await fetchViaProxy(rssUrl); } catch(e) {}
  }

  if (!html || html.length < 300) {
    return { source: label, events: [], error: 'No se pudo acceder al sitio' };
  }

  const events = parseHTML(html, url, label);
  return { source: label, events, error: null };
}

async function runAll() {
  const allEvents = [];
  const errors = [];

  for (let i = 0; i < URLS.length; i++) {
    try {
      const result = await scrapeOne(URLS[i], LABELS[i], i, URLS.length);
      if (result.events.length > 0) {
        allEvents.push(...result.events);
      } else if (result.error) {
        errors.push(LABELS[i] + ': ' + result.error);
      }
    } catch(e) {
      errors.push(LABELS[i] + ': ' + e.message);
    }
    // Small delay to avoid rate limiting
    await new Promise(r => setTimeout(r, 300));
  }

  // Deduplicate by name
  const seen = new Set();
  const unique = allEvents.filter(e => {
    const k = e.nombre.toLowerCase().trim();
    if (!k || seen.has(k)) return false;
    seen.add(k); return true;
  });

  setBar(100);
  setStatus('Listo — ' + unique.length + ' eventos encontrados');
  showResult(unique.length + ' eventos de ' + URLS.length + ' fuentes');

  // Send to Streamlit
  window.parent.postMessage({
    type: 'streamlit:setComponentValue',
    value: { events: unique, errors: errors, done: true }
  }, '*');
}

function setStatus(msg) {
  document.getElementById('status').textContent = msg;
}
function setBar(pct) {
  document.getElementById('bar').style.width = pct + '%';
}
function showResult(msg) {
  const box = document.getElementById('result-box');
  box.style.display = 'block';
  box.textContent = '✓ ' + msg;
}

runAll();
</script>
</body>
</html>"""


# ─────────────────────────────────────────────
# TAB 1 — DESCUBRIR
# ─────────────────────────────────────────────
def tab_descubrir():
    st.markdown(
        '<p class="terret-sub" style="font-size:0.8rem;letter-spacing:0.14em">MODO DE BÚSQUEDA</p>',
        unsafe_allow_html=True,
    )

    modo = st.radio(
        "Modo",
        ["🤖 Automático", "🔗 URL personalizada"],
        key="modo_busqueda",
        label_visibility="collapsed",
        horizontal=True,
    )

    # ── Source selector ──
    if modo == "🤖 Automático":
        st.markdown('<p class="mono-sm" style="margin-bottom:6px">Fuentes a scrapear:</p>', unsafe_allow_html=True)
        selected_sources = []
        cols = st.columns(3)
        for i, src in enumerate(DEFAULT_SOURCES):
            with cols[i % 3]:
                uid = uuid.uuid4().hex[:4]
                if st.checkbox(src["label"], value=True, key="src_" + str(i) + "_" + uid):
                    selected_sources.append(src)
        urls_to_scrape  = [s["url"]   for s in selected_sources]
        labels_to_scrape = [s["label"] for s in selected_sources]
    else:
        custom = st.text_input(
            "URL del directorio",
            placeholder="https://www.atletrack.com/eventos",
            key="custom_url_input",
        )
        urls_to_scrape   = [custom.strip()] if custom.strip() else []
        labels_to_scrape = [custom.strip()] if custom.strip() else []

    st.markdown(
        '<p class="mono-sm" style="color:#6B6B8A;margin-top:4px">'
        '⚡ El scraping corre en <strong style="color:#D4FF00">tu navegador</strong> '
        '(no en el servidor) — evita bloqueos de IP.</p>',
        unsafe_allow_html=True,
    )

    if st.button("Buscar eventos", key="btn_buscar"):
        if not urls_to_scrape:
            st.warning("Selecciona al menos una fuente o ingresa una URL")
            return
        st.session_state["scraping_active"] = True
        st.session_state["scraping_urls"]   = urls_to_scrape
        st.session_state["scraping_labels"] = labels_to_scrape
        st.session_state.pop("discovered", None)
        st.session_state.pop("js_result", None)
        st.rerun()

    # ── JS Component ──
    if st.session_state.get("scraping_active"):
        urls   = st.session_state.get("scraping_urls", [])
        labels = st.session_state.get("scraping_labels", [])

        html_code = _build_scraper_html(urls, labels)
        result = st.components.v1.html(html_code, height=90, scrolling=False)

        # Streamlit components return value via session state trick:
        # We show a "paste results" JSON area as reliable fallback
        st.markdown(
            '<p class="mono-sm" style="margin-top:12px;color:#6B6B8A">'
            'Cuando el scraping termine, los resultados aparecerán automáticamente abajo. '
            'Si no aparecen en 30 segundos, usa el botón de abajo.</p>',
            unsafe_allow_html=True,
        )

        # Polling mechanism: embed a hidden iframe that posts back
        # Use query_params to receive data back
        if "js_result" in st.session_state and st.session_state["js_result"]:
            raw = st.session_state["js_result"]
            try:
                data = json.loads(raw) if isinstance(raw, str) else raw
                events = data.get("events", [])
                if events:
                    rows = _rows_from_js(events)
                    st.session_state["discovered"] = rows
                    st.session_state["scraping_active"] = False
                    st.session_state.pop("js_result", None)
                    st.rerun()
            except Exception:
                pass

        # Manual paste fallback
        with st.expander("¿No aparecen resultados? Pega el JSON aquí", expanded=False):
            st.markdown(
                '<p class="mono-sm">Abre la consola del navegador (F12 → Console), '
                'copia el JSON que muestra y pégalo aquí.</p>',
                unsafe_allow_html=True,
            )
            json_paste = st.text_area("JSON de resultados", height=120, key="json_paste_area",
                                       placeholder='{"events": [...], "errors": []}')
            if st.button("Procesar JSON", key="btn_process_json"):
                try:
                    data   = json.loads(json_paste)
                    events = data.get("events", [])
                    if events:
                        rows = _rows_from_js(events)
                        st.session_state["discovered"] = rows
                        st.session_state["scraping_active"] = False
                        st.success(f"✅ {len(rows)} eventos cargados")
                        st.rerun()
                    else:
                        st.error("No se encontraron eventos en el JSON")
                except json.JSONDecodeError as e:
                    st.error("JSON inválido: " + str(e))

        if st.button("Cancelar búsqueda", key="btn_cancel"):
            st.session_state["scraping_active"] = False
            st.rerun()

    # ── Results table ──
    if "discovered" in st.session_state and st.session_state["discovered"]:
        discovered = st.session_state["discovered"]
        st.markdown("<br>", unsafe_allow_html=True)
        badge_text = str(len(discovered)) + " EVENTOS — EDITA Y SELECCIONA PARA GUARDAR"
        st.markdown(
            '<p class="terret-sub" style="font-size:0.8rem;letter-spacing:0.14em">' + badge_text + '</p>',
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
            label = str(row["Evento"])[:60] if row["Evento"] else "Fila " + str(i+1)
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
                    st.success("✅ " + str(added) + " leads guardados (duplicados omitidos)")
                    del st.session_state["discovered"]
                    st.rerun()
        with col_s2:
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
