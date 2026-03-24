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

if 'sel' not in st.session_state:
    st.session_state.sel = None
if 'entered' not in st.session_state:
    st.session_state.entered = False


# ============================================================
# LOGO HELPER
# ============================================================
def get_logo_base64():
    import glob
    candidates = ['./logo.png', './Logo.png', './LOGO.png',
                  './shipadvisor_results/logo.png', './assets/logo.png',
                  './images/logo.png']
    candidates += glob.glob('./*logo*.*') + glob.glob('./*Logo*.*') + glob.glob('./*LOGO*.*')
    for p in candidates:
        if os.path.exists(p) and p.lower().endswith(('.png', '.jpg', '.jpeg')):
            with open(p, 'rb') as f:
                return base64.b64encode(f.read()).decode()
    return None


# ============================================================
# LANDING PAGE (pure Streamlit, no iframe)
# ============================================================
def show_landing():
    logo_b64 = get_logo_base64()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:170px;height:auto;border-radius:12px;filter:drop-shadow(0 4px 24px rgba(0,0,0,0.5));animation:fU 1s 0.3s ease forwards;opacity:0;margin-bottom:1rem">' if logo_b64 else ''

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500&display=swap');
    header[data-testid="stHeader"]{display:none!important}
    div[data-testid="stToolbar"]{display:none!important}
    div[data-testid="stDecoration"]{display:none!important}
    #MainMenu{display:none!important}
    footer{display:none!important}
    section[data-testid="stSidebar"]{display:none!important}
    .stApp{
        background:linear-gradient(180deg, #0d1117 0%, #1a2332 35%, #1b3a4b 65%, #2d6a7a 100%)!important;
        overflow:hidden;
    }
    div.block-container{
        display:flex!important; flex-direction:column!important;
        align-items:center!important; justify-content:center!important;
        min-height:100vh; padding:2rem!important; max-width:100%!important;
    }
    @keyframes fU{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}
    @keyframes twinkle{0%{opacity:0.5}100%{opacity:1}}

    /* Stars overlay */
    .stApp::before{
        content:''; position:fixed; top:0; left:0; right:0; height:45%; z-index:0; pointer-events:none;
        background:
            radial-gradient(1px 1px at 8% 12%, rgba(255,255,255,0.7) 50%, transparent 100%),
            radial-gradient(1.5px 1.5px at 22% 25%, rgba(255,255,255,0.5) 50%, transparent 100%),
            radial-gradient(1px 1px at 35% 8%, rgba(255,255,255,0.6) 50%, transparent 100%),
            radial-gradient(1px 1px at 52% 18%, rgba(255,255,255,0.4) 50%, transparent 100%),
            radial-gradient(1.5px 1.5px at 67% 22%, rgba(255,255,255,0.7) 50%, transparent 100%),
            radial-gradient(1px 1px at 78% 10%, rgba(255,255,255,0.5) 50%, transparent 100%);
        animation:twinkle 4s ease-in-out infinite alternate;
    }

    /* Embark button styling */
    div.stButton > button {
        background: transparent !important;
        border: 1px solid #c5993e !important;
        color: #c5993e !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.85rem !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
        padding: 14px 40px !important;
        border-radius: 0 !important;
        transition: all 0.4s ease !important;
        animation: fU 1s 1.2s ease forwards;
        opacity: 0;
    }
    div.stButton > button:hover {
        background: #c5993e !important;
        color: #1a1410 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f'''
    <div style="text-align:center;position:relative;z-index:1">
        {logo_html}
        <h1 style="font-family:Playfair Display,serif;font-size:clamp(2.5rem,6vw,4.2rem);font-weight:700;color:#faf6ee;line-height:1.1;opacity:0;animation:fU 1s 0.6s ease forwards">
            Voyage across the<br><em style="font-style:italic;color:#d4b06a;font-weight:400">Mediterranean</em>
        </h1>
        <p style="font-family:Playfair Display,serif;font-size:clamp(1.1rem,2.5vw,1.6rem);font-weight:400;font-style:italic;color:rgba(212,176,106,0.7);opacity:0;animation:fU 1s 0.85s ease forwards;margin-top:0.6rem">
            Are you ready to set sail?
        </p>
        <p style="font-family:Cormorant Garamond,serif;font-size:clamp(0.9rem,1.8vw,1.15rem);font-weight:300;font-style:italic;color:rgba(244,239,230,0.45);max-width:540px;line-height:1.6;opacity:0;animation:fU 1s 1s ease forwards;margin:0.8rem auto 0">
            Discover 18th &amp; 19th century travelogues through sentiment analysis
            and CLIP-powered illustration classification.
        </p>
        <div style="display:flex;gap:2.5rem;justify-content:center;margin-top:1.8rem;opacity:0;animation:fU 1s 1s ease forwards">
            <div style="text-align:center"><div style="font-family:Playfair Display,serif;font-size:1.5rem;font-weight:700;color:#c5993e">140+</div><div style="font-family:DM Sans,sans-serif;font-size:0.65rem;letter-spacing:1.5px;text-transform:uppercase;color:rgba(244,239,230,0.4);margin-top:2px">Travelogues</div></div>
            <div style="text-align:center"><div style="font-family:Playfair Display,serif;font-size:1.5rem;font-weight:700;color:#c5993e">200+</div><div style="font-family:DM Sans,sans-serif;font-size:0.65rem;letter-spacing:1.5px;text-transform:uppercase;color:rgba(244,239,230,0.4);margin-top:2px">Routes</div></div>
            <div style="text-align:center"><div style="font-family:Playfair Display,serif;font-size:1.5rem;font-weight:700;color:#c5993e">700+</div><div style="font-family:DM Sans,sans-serif;font-size:0.65rem;letter-spacing:1.5px;text-transform:uppercase;color:rgba(244,239,230,0.4);margin-top:2px">Illustrations</div></div>
        </div>
        <div style="display:flex;align-items:center;gap:12px;justify-content:center;margin:1.5rem auto 0;opacity:0;animation:fU 1s 1.1s ease forwards">
            <span style="width:50px;height:1px;background:#c5993e;opacity:0.3;display:inline-block"></span>
            <span style="width:5px;height:5px;background:#c5993e;transform:rotate(45deg);opacity:0.5;display:inline-block"></span>
            <span style="width:50px;height:1px;background:#c5993e;opacity:0.3;display:inline-block"></span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("EMBARK ON THE VOYAGE  →", use_container_width=True):
            st.session_state.entered = True
            st.rerun()


# ============================================================
# APP STYLES
# ============================================================
def inject_app_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Crimson+Text:wght@400;600;700&family=EB+Garamond:wght@400;500;600&display=swap');
    /* Fade in the whole page */
    .stApp {
        font-family:'Crimson Text','Georgia',serif;
        background: linear-gradient(180deg, #0f1a24 0%, #152736 100%);
        animation: pageIn 0.6s ease forwards;
    }
    @keyframes pageIn { from { opacity: 0; } to { opacity: 1; } }
    h1,h2,h3 { font-family:'Playfair Display',serif!important; color:#f0ebe3!important; }
    p, span, label, .stMarkdown { color: #c8c0b4; }
    .med-badge { display:inline-block; padding:2px 8px; border-radius:3px; font-size:0.7rem; background:rgba(42,111,151,0.2); color:#5ba8c8; border:1px solid rgba(42,111,151,0.3); }
    .tag { display:inline-block; padding:3px 10px; border-radius:3px; font-size:0.75rem; margin:2px; font-family:'EB Garamond',serif; }
    /* Tab styling */
    div[data-testid="stTabs"] button { color: rgba(200,192,180,0.5) !important; }
    div[data-testid="stTabs"] button[aria-selected="true"] { color: #c5993e !important; border-bottom-color: #c5993e !important; }
    div[data-testid="stTabs"] button:hover { color: rgba(200,192,180,0.8) !important; }
    /* Inputs */
    div[data-testid="stSelectbox"] label, div[data-testid="stSlider"] label,
    div[data-testid="stCheckbox"] label, div[data-testid="stNumberInput"] label { color: #c8c0b4 !important; }
    .stSelectbox > div > div { background: rgba(255,255,255,0.05) !important; border-color: rgba(197,153,62,0.2) !important; color: #f0ebe3 !important; }
    .stCaption, small { color: rgba(200,192,180,0.5) !important; }
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
    d = dict(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
             font=dict(family='Crimson Text,Georgia,serif', color='#c8c0b4'),
             title_font=dict(family='Playfair Display,serif', size=16, color='#f0ebe3'))
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
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:55px;border-radius:8px;margin-right:16px">' if logo_b64 else '<span style="font-size:2rem;margin-right:12px">⚓</span>'

    st.markdown(f'''
    <div style="display:flex;align-items:center;padding:0.8rem 0 1rem 0;border-bottom:1px solid rgba(197,153,62,0.15);margin-bottom:1rem">
        {logo_html}
        <div>
            <div style="font-family:Playfair Display,serif;font-size:1.8rem;font-weight:700;color:#f0ebe3;line-height:1.2">ShipAdvisor</div>
            <div style="font-family:EB Garamond,serif;font-size:0.95rem;color:rgba(197,153,62,0.6);font-style:italic;margin-top:2px">Know Before You Row &mdash; Navigating Mediterranean travel routes in early modern travelogues</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Sentiment Map", "Browse Illustrations"])

    # TAB 1: SENTIMENT MAP
    with tab1:
        st.markdown("### Mediterranean Sentiment Map")
        st.markdown('<p style="font-family:EB Garamond,serif;color:rgba(200,192,180,0.5);font-style:italic">Sentiment analysis of Mediterranean locations based on travelogue texts</p>', unsafe_allow_html=True)
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
                    st.markdown(f'<div style="font-size:11px;text-align:center;margin-top:-8px"><span style="color:{tcl};font-weight:600">{ill["illustration_type"]}</span><br><span style="color:rgba(200,192,180,0.6)">{ill["nearest_place"]} p.{int(ill["page"])}</span><br><span style="color:rgba(200,192,180,0.4);font-size:10px">{str(ill["book_title"])[:35]}</span></div>', unsafe_allow_html=True)
                    st.markdown("")
                shown += 1
            if shown == 0: st.info("No images found for current filter.")
        else:
            st.warning("No illustration data.")


# ============================================================
# ROUTING
# ============================================================
def main():
    if not st.session_state.entered:
        show_landing()
    else:
        show_app()

if __name__ == "__main__":
    main()
