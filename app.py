"""
ShipAdvisor - Mediterranean Travel Route Explorer
Usage:  python -m streamlit run app.py

Landing page -> Sentiment Map / Browse Illustrations / Statistics / Route Explorer
All in one Streamlit app, no page jumps.
"""

import streamlit as st
import pandas as pd
import os, json, base64
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components

RESULTS_DIR = './shipadvisor_results'
ROUTES_FILE = os.path.join(RESULTS_DIR, 'routes.csv')
ILLUSTRATIONS_FILE = os.path.join(RESULTS_DIR, 'route_illustrations.csv')
CLASSIFICATIONS_FILE = os.path.join(RESULTS_DIR, 'classifications.csv')
BOOKS_FILE = os.path.join(RESULTS_DIR, 'mediterranean_books.csv')
IMAGE_DIRS = ['./shipadvisor_images', './travelogues_raw']

PLACE_SUBJECT_KEYWORDS = {
    'Italy': ['itali\xeb'], 'France': ['frankrijk'], 'Spain': ['spanje'],
    'Portugal': ['portugal'], 'Greece': [], 'Turkey': ['turkije'],
    'Egypt': ['egypte'], 'Palestine': ['palestina'], 'Syria': ['syri\xeb'],
    'Lebanon': [], 'Algeria': ['algerije', 'noord-afrikaanse staten', 'maghreb'],
    'Tunisia': ['tunesi', 'noord-afrikaanse staten', 'maghreb'],
    'Morocco': ['marokko', 'noord-afrikaanse staten', 'maghreb'],
    'Libya': ['libi\xeb', 'noord-afrikaanse staten', 'maghreb'],
    'Cyprus': [], 'Malta': [], 'Croatia': [], 'Russia': ['rusland'],
    'India': ['india', 'azi\xeb'], 'China': ['china', 'azi\xeb'], 'Persia': ['perzi\xeb'],
    'England': [], 'Belgium': [], 'Netherlands': [], 'Germany': [], 'Austria': [],
}

PLACE_COORDS = {
    'France': (46.6, 2.2), 'Italy': (42.5, 12.5), 'Spain': (40.4, -3.7),
    'Portugal': (39.4, -8.2), 'Greece': (39.1, 22.4), 'Turkey': (39.9, 32.9),
    'Egypt': (26.8, 30.8), 'Palestine': (31.8, 35.2), 'Syria': (34.8, 38.9),
    'Lebanon': (33.9, 35.5), 'Algeria': (36.7, 3.0), 'Tunisia': (36.8, 10.2),
    'Morocco': (31.8, -7.1), 'Libya': (32.9, 13.2), 'Cyprus': (35.1, 33.4),
    'Malta': (35.9, 14.5), 'Croatia': (43.5, 16.4),
    'England': (51.5, -0.1), 'Belgium': (50.8, 4.4), 'Netherlands': (52.4, 4.9),
    'Germany': (51.2, 10.4), 'Austria': (48.2, 16.4), 'Russia': (55.8, 37.6),
    'Persia': (32.4, 53.7), 'India': (20.6, 78.9), 'China': (35.9, 104.2),
}

VISUAL_TYPES = {
    'map', 'nautical_chart', 'plan', 'harbour', 'seascape', 'ship',
    'coastal_city', 'landscape', 'architecture', 'portrait', 'animal',
    'engraving', 'woodcut', 'botanical',
}
MARITIME_TYPES = {'harbour', 'seascape', 'ship', 'coastal_city', 'nautical_chart'}

C = {
    'bg': '#F3EDE2', 'bg_dark': '#E8DFD0', 'ink': '#2B2B2B', 'ink_light': '#5A5A5A',
    'gold': '#8B6F47', 'red': '#A23E48', 'indigo': '#3D5A80', 'sage': '#5E7E5F',
    'plum': '#6D4C6E', 'slate': '#6B7B8D', 'terra': '#B07245', 'olive': '#7A7A4E',
    'sea': '#2A6F97', 'sand': '#C9A96E',
}
TYPE_COLORS = {
    'map': C['sage'], 'nautical_chart': C['sea'], 'plan': C['slate'],
    'harbour': C['indigo'], 'seascape': C['sea'], 'ship': C['indigo'],
    'coastal_city': C['terra'], 'landscape': C['sage'],
    'architecture': C['plum'], 'portrait': C['red'],
    'engraving': C['gold'], 'woodcut': C['terra'], 'animal': C['olive'],
    'botanical': C['sage'],
}

st.set_page_config(page_title="ShipAdvisor", page_icon="\u2693", layout="wide", initial_sidebar_state="collapsed")

if 'entered' not in st.session_state:
    st.session_state.entered = False
if 'sel' not in st.session_state:
    st.session_state.sel = None


# ============================================================
# LOGO HELPER
# ============================================================
def get_logo_base64():
    for p in ['./logo.png', './shipadvisor_results/logo.png', './assets/logo.png']:
        if os.path.exists(p):
            with open(p, 'rb') as f:
                return base64.b64encode(f.read()).decode()
    return None


# ============================================================
# LANDING PAGE
# ============================================================
def show_landing():
    logo_b64 = get_logo_base64()
    logo_tag = f"<img src='data:image/png;base64,{logo_b64}' class='logo-img'>" if logo_b64 else ""

    landing_html = """
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--ink:#1a1410;--gold:#c5993e;--gold-light:#d4b06a;--cream:#faf6ee}
html,body{width:100%;height:100%;overflow:hidden;background:#0d1117}
.landing{
  position:absolute;inset:0;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  background:linear-gradient(180deg, #0d1117 0%, #1a2332 35%, #1b3a4b 65%, #2d6a7a 100%);
}
.stars{
  position:absolute;top:0;left:0;right:0;height:45%;
  background:
    radial-gradient(1px 1px at 8% 12%, rgba(255,255,255,0.7) 50%, transparent 100%),
    radial-gradient(1.5px 1.5px at 22% 25%, rgba(255,255,255,0.5) 50%, transparent 100%),
    radial-gradient(1px 1px at 35% 8%, rgba(255,255,255,0.6) 50%, transparent 100%),
    radial-gradient(1px 1px at 52% 18%, rgba(255,255,255,0.4) 50%, transparent 100%),
    radial-gradient(1.5px 1.5px at 67% 22%, rgba(255,255,255,0.7) 50%, transparent 100%),
    radial-gradient(1px 1px at 78% 10%, rgba(255,255,255,0.5) 50%, transparent 100%),
    radial-gradient(1px 1px at 90% 28%, rgba(255,255,255,0.3) 50%, transparent 100%),
    radial-gradient(1px 1px at 45% 32%, rgba(255,255,255,0.4) 50%, transparent 100%);
  animation:twinkle 4s ease-in-out infinite alternate;
}
@keyframes twinkle{0%{opacity:0.5}100%{opacity:1}}
.sea-floor{position:absolute;bottom:0;left:0;right:0;height:30%;overflow:hidden}
.sea-floor svg{position:absolute;bottom:0;width:100%;height:100%}
.big-ship{
  position:absolute;bottom:19%;z-index:6;opacity:0;
  animation:bsA 2s 1s ease forwards, bsS 28s 1s linear infinite;
}
@keyframes bsA{to{opacity:0.75}}
@keyframes bsS{
  0%{left:-12%;transform:translateY(0) rotate(0deg)}
  12%{transform:translateY(-5px) rotate(-1deg)}
  25%{transform:translateY(2px) rotate(0.5deg)}
  37%{transform:translateY(-7px) rotate(-1.5deg)}
  50%{left:45%;transform:translateY(0) rotate(0deg)}
  62%{transform:translateY(-4px) rotate(-0.8deg)}
  75%{transform:translateY(3px) rotate(0.6deg)}
  87%{transform:translateY(-6px) rotate(-1.2deg)}
  100%{left:105%;transform:translateY(0) rotate(0deg)}
}
.ds{position:absolute;z-index:3;opacity:0}
.ds1{bottom:27%;left:65%;animation:da1 2s 2.5s ease forwards,db1 6s 2.5s ease-in-out infinite}
.ds2{bottom:29%;left:30%;animation:da2 2s 3s ease forwards,db2 7s 3s ease-in-out infinite}
.ds3{bottom:26%;left:80%;animation:da3 2s 3.5s ease forwards,db3 8s 3.5s ease-in-out infinite}
@keyframes da1{to{opacity:0.2}} @keyframes da2{to{opacity:0.15}} @keyframes da3{to{opacity:0.12}}
@keyframes db1{0%,100%{transform:translateY(0)}50%{transform:translateY(-2px)}}
@keyframes db2{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}
@keyframes db3{0%,100%{transform:translateY(0)}50%{transform:translateY(-1.5px)}}
.compass{position:absolute;top:5%;right:5%;width:65px;height:65px;opacity:0;animation:cIn 1.5s 1.5s ease forwards}
@keyframes cIn{to{opacity:0.18}}
.lc{position:relative;z-index:10;text-align:center;padding:1.5rem;display:flex;flex-direction:column;align-items:center}
.logo-img{width:160px;height:auto;border-radius:12px;opacity:0;animation:fU 1s 0.3s ease forwards;margin-bottom:0.8rem;filter:drop-shadow(0 4px 24px rgba(0,0,0,0.5))}
.mt{font-family:'Playfair Display',serif;font-size:clamp(2rem,5vw,3.5rem);font-weight:700;color:var(--cream);line-height:1.15;opacity:0;animation:fU 1s 0.6s ease forwards}
.mt em{font-style:italic;color:var(--gold-light);font-weight:400}
.st{font-family:'Cormorant Garamond',serif;font-size:clamp(1rem,2vw,1.25rem);font-weight:300;font-style:italic;color:rgba(244,239,230,0.6);max-width:520px;line-height:1.6;opacity:0;animation:fU 1s 0.8s ease forwards;margin-top:0.8rem}
.sr{display:flex;gap:2.5rem;margin-top:1.6rem;opacity:0;animation:fU 1s 1s ease forwards}
.stt{text-align:center}
.sn{font-family:'Playfair Display',serif;font-size:1.5rem;font-weight:700;color:var(--gold)}
.sl{font-family:'DM Sans',sans-serif;font-size:0.65rem;letter-spacing:1.5px;text-transform:uppercase;color:rgba(244,239,230,0.4);margin-top:2px}
.orn{display:flex;align-items:center;gap:12px;justify-content:center;margin:1.5rem auto 0;opacity:0;animation:fU 1s 1.1s ease forwards}
.orn .ln{width:50px;height:1px;background:var(--gold);opacity:0.3}
.orn .dm{width:5px;height:5px;background:var(--gold);transform:rotate(45deg);opacity:0.5}
.eb{display:inline-flex;align-items:center;gap:10px;margin-top:1.5rem;padding:13px 36px;background:transparent;border:1px solid var(--gold);color:var(--gold);font-family:'DM Sans',sans-serif;font-size:0.82rem;letter-spacing:3px;text-transform:uppercase;cursor:pointer;transition:all 0.4s ease;opacity:0;animation:fU 1s 1.2s ease forwards;position:relative;overflow:hidden}
.eb::before{content:'';position:absolute;inset:0;background:var(--gold);transform:translateX(-101%);transition:transform 0.4s ease;z-index:0}
.eb:hover::before{transform:translateX(0)} .eb:hover{color:var(--ink)}
.eb span{position:relative;z-index:1}
.eb .ar{position:relative;z-index:1;transition:transform 0.3s ease}
.eb:hover .ar{transform:translateX(6px)}
@keyframes fU{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}
</style>

<div class="landing">
  <div class="stars"></div>
  <div class="sea-floor">
    <svg viewBox="0 0 1440 320" preserveAspectRatio="none">
      <path fill="rgba(27,58,75,0.35)"><animate attributeName="d" dur="8s" repeatCount="indefinite" values="M0,224L60,213C120,203,240,181,360,187C480,192,600,224,720,235C840,245,960,235,1080,213C1200,192,1320,160,1380,165L1440,171L1440,320L0,320Z;M0,192L60,208C120,224,240,256,360,251C480,245,600,203,720,187C840,171,960,181,1080,197C1200,213,1320,235,1380,229L1440,224L1440,320L0,320Z;M0,224L60,213C120,203,240,181,360,187C480,192,600,224,720,235C840,245,960,235,1080,213C1200,192,1320,160,1380,165L1440,171L1440,320L0,320Z"/></path>
      <path fill="rgba(45,106,122,0.25)"><animate attributeName="d" dur="6s" repeatCount="indefinite" values="M0,256L60,251C120,245,240,235,360,229C480,224,600,224,720,229C840,235,960,245,1080,240C1200,235,1320,213,1380,219L1440,224L1440,320L0,320Z;M0,240L60,245C120,251,240,261,360,256C480,251,600,229,720,219C840,208,960,208,1080,219C1200,229,1320,251,1380,256L1440,261L1440,320L0,320Z;M0,256L60,251C120,245,240,235,360,229C480,224,600,224,720,229C840,235,960,245,1080,240C1200,235,1320,213,1380,219L1440,224L1440,320L0,320Z"/></path>
      <path fill="rgba(27,58,75,0.55)" d="M0,288L60,283C120,277,240,267,360,267C480,267,600,277,720,277C840,277,960,267,1080,261C1200,256,1320,256,1380,261L1440,267L1440,320L0,320Z"/>
    </svg>
  </div>
  <div class="big-ship">
    <svg width="120" height="100" viewBox="0 0 120 100" fill="none">
      <path d="M15 72 L60 72 L105 72 L95 84 L25 84 Z" fill="rgba(100,70,35,0.9)"/>
      <path d="M20 72 L100 72 L95 78 L25 78 Z" fill="rgba(120,85,45,0.7)"/>
      <line x1="60" y1="72" x2="60" y2="14" stroke="rgba(100,70,35,0.9)" stroke-width="1.8"/>
      <rect x="55" y="16" width="10" height="4" rx="1" fill="rgba(100,70,35,0.7)"/>
      <path d="M62 18 Q85 35 88 55 L62 62 Z" fill="rgba(244,239,230,0.75)"/>
      <path d="M58 22 Q38 38 32 58 L58 62 Z" fill="rgba(244,239,230,0.55)"/>
      <path d="M62 14 Q78 25 80 38 L62 40 Z" fill="rgba(197,153,62,0.4)"/>
      <line x1="60" y1="14" x2="60" y2="8" stroke="rgba(197,153,62,0.7)" stroke-width="0.8"/>
      <polygon points="60,8 68,10.5 60,12" fill="rgba(197,153,62,0.5)"/>
      <line x1="105" y1="72" x2="118" y2="65" stroke="rgba(100,70,35,0.7)" stroke-width="1"/>
      <path d="M62 20 L115 67 L105 72 Z" fill="rgba(244,239,230,0.3)"/>
      <line x1="60" y1="16" x2="30" y2="72" stroke="rgba(139,108,66,0.2)" stroke-width="0.3"/>
      <line x1="60" y1="16" x2="90" y2="72" stroke="rgba(139,108,66,0.2)" stroke-width="0.3"/>
      <circle cx="40" cy="75" r="1.5" fill="rgba(197,153,62,0.35)"/>
      <circle cx="52" cy="75" r="1.5" fill="rgba(197,153,62,0.35)"/>
      <circle cx="64" cy="75" r="1.5" fill="rgba(197,153,62,0.35)"/>
      <circle cx="76" cy="75" r="1.5" fill="rgba(197,153,62,0.35)"/>
    </svg>
  </div>
  <div class="ds ds1"><svg width="24" height="18" viewBox="0 0 60 45" fill="none"><path d="M10 32 L30 32 L50 32 L44 37 L16 37 Z" fill="rgba(180,170,155,0.6)"/><line x1="30" y1="32" x2="30" y2="12" stroke="rgba(180,170,155,0.7)" stroke-width="1.2"/><path d="M31 14 L46 28 L31 31 Z" fill="rgba(220,215,205,0.4)"/></svg></div>
  <div class="ds ds2"><svg width="18" height="14" viewBox="0 0 60 45" fill="none"><path d="M10 32 L30 32 L50 32 L44 37 L16 37 Z" fill="rgba(180,170,155,0.5)"/><line x1="30" y1="32" x2="30" y2="15" stroke="rgba(180,170,155,0.6)" stroke-width="1.5"/><path d="M31 17 L44 29 L31 31 Z" fill="rgba(220,215,205,0.35)"/></svg></div>
  <div class="ds ds3"><svg width="14" height="10" viewBox="0 0 60 45" fill="none"><path d="M12 32 L30 32 L48 32 L42 36 L18 36 Z" fill="rgba(180,170,155,0.4)"/><line x1="30" y1="32" x2="30" y2="18" stroke="rgba(180,170,155,0.5)" stroke-width="1.8"/><path d="M31 20 L42 30 L31 31 Z" fill="rgba(220,215,205,0.3)"/></svg></div>
  <svg class="compass" viewBox="0 0 100 100" fill="none">
    <circle cx="50" cy="50" r="45" stroke="#c5993e" stroke-width="0.5" opacity="0.5"/>
    <circle cx="50" cy="50" r="38" stroke="#c5993e" stroke-width="0.3" opacity="0.3"/>
    <line x1="50" y1="8" x2="50" y2="92" stroke="#c5993e" stroke-width="0.5" opacity="0.4"/>
    <line x1="8" y1="50" x2="92" y2="50" stroke="#c5993e" stroke-width="0.5" opacity="0.4"/>
    <polygon points="50,12 46,50 54,50" fill="#c5993e" opacity="0.6"/>
    <polygon points="50,88 46,50 54,50" fill="#c5993e" opacity="0.25"/>
    <text x="50" y="7" text-anchor="middle" fill="#c5993e" font-family="DM Sans" font-size="7" opacity="0.7">N</text>
    <text x="50" y="99" text-anchor="middle" fill="#c5993e" font-family="DM Sans" font-size="7" opacity="0.5">S</text>
    <text x="96" y="52" text-anchor="middle" fill="#c5993e" font-family="DM Sans" font-size="7" opacity="0.5">E</text>
    <text x="4" y="52" text-anchor="middle" fill="#c5993e" font-family="DM Sans" font-size="7" opacity="0.5">W</text>
  </svg>
  <div class="lc">
    LOGO_PLACEHOLDER
    <h1 class="mt">Are You Ready to <em>Set Sail?</em></h1>
    <p class="st">Hop aboard and explore the Mediterranean through the eyes of 18th &amp; 19th century travellers &mdash; their sketches, sentiments, and sea routes, all in one place.</p>
    <div class="sr">
      <div class="stt"><div class="sn">140+</div><div class="sl">Travelogues</div></div>
      <div class="stt"><div class="sn">200+</div><div class="sl">Routes</div></div>
      <div class="stt"><div class="sn">700+</div><div class="sl">Illustrations</div></div>
    </div>
    <div class="orn"><span class="ln"></span><span class="dm"></span><span class="ln"></span></div>
    <button class="eb" onclick="enterApp()"><span>Embark on the Voyage</span><span class="ar">&rarr;</span></button>
  </div>
</div>
<script>
function enterApp(){
  var url=new URL(window.parent.location);
  url.searchParams.set('entered','true');
  window.parent.location.href=url.toString();
}
</script>
""".replace("LOGO_PLACEHOLDER", logo_tag)

    st.markdown("""
    <style>
    header[data-testid="stHeader"]{display:none!important}
    div[data-testid="stToolbar"]{display:none!important}
    div[data-testid="stDecoration"]{display:none!important}
    #MainMenu{display:none!important}
    footer{display:none!important}
    div.block-container{padding:0!important;max-width:100%!important}
    section[data-testid="stSidebar"]{display:none!important}
    </style>
    """, unsafe_allow_html=True)

    components.html(landing_html, height=800, scrolling=False)


# ============================================================
# APP STYLES
# ============================================================
def inject_app_styles():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Crimson+Text:wght@400;600;700&family=EB+Garamond:wght@400;500;600&display=swap');
    .stApp {{ font-family:'Crimson Text','Georgia',serif; background-color:{C['bg']}; }}
    h1,h2,h3 {{ font-family:'Playfair Display',serif!important; color:{C['ink']}!important; }}
    .main-title {{ font-family:'Playfair Display',serif; font-size:2.8rem; font-weight:700; color:{C['ink']}; margin-bottom:0; }}
    .subtitle {{ font-family:'EB Garamond',serif; font-size:1.15rem; color:{C['ink_light']}; font-style:italic; margin-bottom:1.5rem; }}
    .ornament {{ text-align:center; color:{C['gold']}; font-size:1.2rem; letter-spacing:0.5em; margin:0.5rem 0 1.5rem 0; }}
    .metric-card {{ background:{C['bg_dark']}; border-radius:4px; padding:1rem; text-align:center; border:1px solid rgba(139,111,71,0.2); }}
    .metric-number {{ font-family:'Playfair Display',serif; font-size:2rem; font-weight:700; color:{C['ink']}; }}
    .metric-label {{ font-family:'EB Garamond',serif; font-size:0.85rem; color:{C['gold']}; text-transform:uppercase; letter-spacing:2px; }}
    .med-badge {{ display:inline-block; padding:2px 8px; border-radius:3px; font-size:0.7rem; background:rgba(42,111,151,0.12); color:{C['sea']}; border:1px solid rgba(42,111,151,0.25); }}
    .tag {{ display:inline-block; padding:3px 10px; border-radius:3px; font-size:0.75rem; margin:2px; font-family:'EB Garamond',serif; }}
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# DATA & HELPERS
# ============================================================
@st.cache_data
def load_data():
    r = pd.read_csv(ROUTES_FILE) if os.path.exists(ROUTES_FILE) else None
    i = pd.read_csv(ILLUSTRATIONS_FILE) if os.path.exists(ILLUSTRATIONS_FILE) else None
    b = pd.read_csv(BOOKS_FILE) if os.path.exists(BOOKS_FILE) else None
    return r, i, b

def build_ie_subject_map(books_df):
    m = {}
    if books_df is None: return m
    for _, row in books_df.iterrows():
        subj = str(row.get('Subject', '')).lower()
        for ie in str(row.get('ie_folders', '')).replace(';', '|').split('|'):
            ie = ie.strip()
            if ie: m[ie] = subj
    return m

def ie_matches_place(ie_folder, place, ie_subject_map):
    keywords = PLACE_SUBJECT_KEYWORDS.get(place)
    if keywords is None or len(keywords) == 0: return True
    subj = ie_subject_map.get(ie_folder, '')
    if not subj: return True
    return any(kw in subj for kw in keywords)

def find_image(p):
    for b in IMAGE_DIRS:
        f = os.path.join(b, p)
        if os.path.exists(f) and os.path.getsize(f) > 0: return f
    return None

def get_stop_images(ills, ie, place):
    if ills is None: return []
    m = (ills['ie_folder'] == ie) & (ills['nearest_place'] == place) & (ills['illustration_type'].isin(VISUAL_TYPES))
    out = []
    for _, r in ills[m].sort_values('confidence', ascending=False).iterrows():
        p = find_image(r['image_path'])
        if p: out.append({'path': p, 'type': r['illustration_type'], 'page': int(r['page'])})
    return out

def base_layout(**kw):
    d = dict(plot_bgcolor=C['bg'], paper_bgcolor=C['bg'], font=dict(family='Crimson Text,Georgia,serif', color=C['ink']),
             title_font=dict(family='Playfair Display,serif', size=16, color=C['ink']))
    d.update(kw); return d

def draw_overview_map(routes):
    pd2 = {}
    for _, row in routes.iterrows():
        try:
            for s in json.loads(row['route_detail']):
                p = s['place']
                if p not in pd2: pd2[p] = {'n': 0, 'med': s['is_mediterranean']}
                pd2[p]['n'] += 1
        except: pass
    fig = go.Figure()
    for place, d in pd2.items():
        co = PLACE_COORDS.get(place)
        if not co: continue
        fig.add_trace(go.Scattergeo(
            lat=[co[0]], lon=[co[1]], mode='markers+text',
            marker=dict(size=max(8, min(30, d['n']*0.8)), color=C['sea'] if d['med'] else C['slate'], opacity=0.75, line=dict(width=1, color='white')),
            text=[place], textposition='top center', textfont=dict(size=10, family='Playfair Display,serif', color=C['ink']),
            hovertext=f"<b>{place}</b><br>{d['n']} routes", showlegend=False))
    fig.update_layout(paper_bgcolor=C['bg'], height=550, margin=dict(l=0, r=0, t=0, b=0),
        geo=dict(bgcolor=C['bg'], landcolor=C['bg_dark'], showland=True, showcountries=True,
                 countrycolor='rgba(139,111,71,0.3)', coastlinecolor='rgba(139,111,71,0.5)',
                 showocean=True, oceancolor='rgba(42,111,151,0.06)', showframe=False,
                 projection_type='natural earth', center=dict(lat=38, lon=18),
                 lataxis=dict(range=[15, 62]), lonaxis=dict(range=[-15, 55])))
    return fig

def draw_route_map(rd):
    la, lo, nm, md = [], [], [], []
    for s in rd:
        co = PLACE_COORDS.get(s['place'])
        if co: la.append(co[0]); lo.append(co[1]); nm.append(s['place']); md.append(s['is_mediterranean'])
    if not la: return None
    fig = go.Figure()
    for i in range(len(la)-1):
        cl = C['sea'] if (md[i] and md[i+1]) else C['gold']
        fig.add_trace(go.Scattergeo(lat=[la[i],la[i+1]], lon=[lo[i],lo[i+1]], mode='lines',
            line=dict(width=2.5, color=cl, dash='dot'), showlegend=False, hoverinfo='skip'))
    for i in range(len(la)):
        cl = C['sea'] if md[i] else C['slate']
        fig.add_trace(go.Scattergeo(lat=[la[i]], lon=[lo[i]], mode='markers+text',
            marker=dict(size=14 if md[i] else 10, color=cl, line=dict(width=1.5, color='white')),
            text=[str(i+1)], textposition='middle center', textfont=dict(size=8, color='white', family='Arial'),
            hovertext=f"<b>{i+1}. {nm[i]}</b>", showlegend=False))
        fig.add_trace(go.Scattergeo(lat=[la[i]+1.2], lon=[lo[i]], mode='text', text=[nm[i]],
            textfont=dict(size=10, family='Playfair Display,serif', color=C['ink']), showlegend=False, hoverinfo='skip'))
    fig.add_trace(go.Scattergeo(lat=[la[0]], lon=[lo[0]], mode='markers',
        marker=dict(size=20, color=C['sage'], symbol='star', line=dict(width=1, color='white')),
        name=f'Start: {nm[0]}', hovertext=f"START: {nm[0]}"))
    fig.add_trace(go.Scattergeo(lat=[la[-1]], lon=[lo[-1]], mode='markers',
        marker=dict(size=18, color=C['red'], symbol='square', line=dict(width=1, color='white')),
        name=f'End: {nm[-1]}', hovertext=f"END: {nm[-1]}"))
    pl = max(3.0, (max(la)-min(la))*0.3)
    pn = max(3.0, (max(lo)-min(lo))*0.3)
    fig.update_layout(paper_bgcolor=C['bg'], height=550, margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(x=0.01, y=0.99, font=dict(family='Crimson Text,serif', size=12)),
        geo=dict(bgcolor=C['bg'], landcolor=C['bg_dark'], showland=True, showcountries=True,
                 countrycolor='rgba(139,111,71,0.3)', coastlinecolor='rgba(139,111,71,0.5)',
                 showocean=True, oceancolor='rgba(42,111,151,0.06)', showframe=False,
                 lonaxis=dict(range=[min(lo)-pn, max(lo)+pn]), lataxis=dict(range=[min(la)-pl, max(la)+pl])))
    return fig


# ============================================================
# MAIN APP CONTENT
# ============================================================
def show_app():
    inject_app_styles()
    routes, illustrations, books = load_data()
    ie_subject_map = build_ie_subject_map(books)
    if routes is None:
        st.error("No data. Place shipadvisor_results/ next to app.py."); return

    logo_b64 = get_logo_base64()
    if logo_b64:
        hdr_l, hdr_m, hdr_r = st.columns([1, 6, 1])
        with hdr_l: st.image(f"data:image/png;base64,{logo_b64}", width=60)
        with hdr_m:
            st.markdown('<p class="main-title">ShipAdvisor</p>', unsafe_allow_html=True)
            st.markdown('<p class="subtitle">Navigating Mediterranean travel routes in early modern travelogues</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="main-title">ShipAdvisor</p>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Navigating Mediterranean travel routes in early modern travelogues</p>', unsafe_allow_html=True)

    st.markdown("")

    tab1, tab2 = st.tabs(["Sentiment Map", "Browse Illustrations"])

    # TAB 1: SENTIMENT MAP
    with tab1:
        st.markdown("### Mediterranean Sentiment Map")
        st.markdown(f'<p style="font-family:EB Garamond,serif;color:{C["ink_light"]};font-style:italic">Sentiment analysis of Mediterranean locations based on travelogue texts</p>', unsafe_allow_html=True)
        map_path = "mediterranean_sentiment_map_offline.html"
        if os.path.exists(map_path):
            with open(map_path, "r", encoding="utf-8") as f:
                map_html = f.read()
            components.html(map_html, height=700, scrolling=True)
        else:
            st.warning("Sentiment map file not found. Place mediterranean_sentiment_map_offline.html in the app root directory.")

    # TAB 2: BROWSE ILLUSTRATIONS
    with tab2:
        st.markdown("### Browse Illustrations by Type")
        if illustrations is not None:
            med_vis = illustrations[(illustrations['is_med_location'] == True) & (illustrations['illustration_type'].isin(VISUAL_TYPES))].copy()
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                all_types = sorted(med_vis['illustration_type'].unique())
                sel_type = st.selectbox("Illustration type", ['All types'] + all_types)
            with fc2:
                all_places = sorted(med_vis['nearest_place'].dropna().unique())
                sel_place = st.selectbox("Location", ['All locations'] + all_places)
            with fc3:
                strict_filter = st.checkbox("Strict: only books about this place", value=True,
                    help="Only shows illustrations from books whose catalogue Subject matches the selected location.")
            if sel_type != 'All types': med_vis = med_vis[med_vis['illustration_type'] == sel_type]
            if sel_place != 'All locations':
                med_vis = med_vis[med_vis['nearest_place'] == sel_place]
                if strict_filter and sel_place in PLACE_SUBJECT_KEYWORDS:
                    kws = PLACE_SUBJECT_KEYWORDS[sel_place]
                    if len(kws) == 0:
                        st.warning(f"No books catalogued specifically under **{sel_place}**.")
                    else:
                        mask = med_vis['ie_folder'].apply(lambda ie: ie_matches_place(ie, sel_place, ie_subject_map))
                        n_before = len(med_vis); med_vis = med_vis[mask]
                        n_filtered = n_before - len(med_vis)
                        if n_filtered > 0: st.info(f"Strict filter removed {n_filtered} illustrations.")
            st.caption(f"{len(med_vis)} illustrations")
            PER_PAGE = 30
            tp = max(1, len(med_vis) // PER_PAGE + 1)
            pg = st.number_input("Page", 1, tp, 1) - 1
            page_data = med_vis.iloc[pg*PER_PAGE:(pg+1)*PER_PAGE]
            cols = st.columns(6); shown = 0
            for _, ill in page_data.iterrows():
                ip = find_image(ill['image_path'])
                if not ip: continue
                with cols[shown % 6]:
                    st.image(ip, use_container_width=True)
                    tcl = TYPE_COLORS.get(ill['illustration_type'], C['slate'])
                    st.markdown(f'<div style="font-size:11px;text-align:center;margin-top:-8px"><span style="color:{tcl};font-weight:600">{ill["illustration_type"]}</span><br><span style="color:{C["ink_light"]}">{ill["nearest_place"]} p.{int(ill["page"])}</span><br><span style="color:{C["ink_light"]};font-size:10px">{str(ill["book_title"])[:35]}</span></div>', unsafe_allow_html=True)
                    st.markdown("")
                shown += 1
            if shown == 0: st.info("No images found for current filter.")
        else:
            st.warning("No illustration data.")


# ============================================================
# ROUTING
# ============================================================
def main():
    params = st.query_params
    if params.get('entered') == 'true':
        st.session_state.entered = True

    if not st.session_state.entered:
        show_landing()
    else:
        show_app()

if __name__ == "__main__":
    main()
