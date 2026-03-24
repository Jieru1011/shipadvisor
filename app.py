"""
ShipAdvisor - Mediterranean Travel Route Explorer
Usage:  python -m streamlit run app.py
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
BOOKS_FILE = os.path.join(RESULTS_DIR, 'mediterranean_books.csv')
IMAGE_DIRS = ['./shipadvisor_images', './travelogues_raw']
PLACE_SUBJECT_KEYWORDS = {'Italy':['itali\xeb'],'France':['frankrijk'],'Spain':['spanje'],'Portugal':['portugal'],'Greece':[],'Turkey':['turkije'],'Egypt':['egypte'],'Palestine':['palestina'],'Syria':['syri\xeb'],'Lebanon':[],'Algeria':['algerije','noord-afrikaanse staten','maghreb'],'Tunisia':['tunesi','noord-afrikaanse staten','maghreb'],'Morocco':['marokko','noord-afrikaanse staten','maghreb'],'Libya':['libi\xeb','noord-afrikaanse staten','maghreb'],'Cyprus':[],'Malta':[],'Croatia':[],'Russia':['rusland'],'India':['india','azi\xeb'],'China':['china','azi\xeb'],'Persia':['perzi\xeb'],'England':[],'Belgium':[],'Netherlands':[],'Germany':[],'Austria':[]}
PLACE_COORDS = {'France':(46.6,2.2),'Italy':(42.5,12.5),'Spain':(40.4,-3.7),'Portugal':(39.4,-8.2),'Greece':(39.1,22.4),'Turkey':(39.9,32.9),'Egypt':(26.8,30.8),'Palestine':(31.8,35.2),'Syria':(34.8,38.9),'Lebanon':(33.9,35.5),'Algeria':(36.7,3.0),'Tunisia':(36.8,10.2),'Morocco':(31.8,-7.1),'Libya':(32.9,13.2),'Cyprus':(35.1,33.4),'Malta':(35.9,14.5),'Croatia':(43.5,16.4),'England':(51.5,-0.1),'Belgium':(50.8,4.4),'Netherlands':(52.4,4.9),'Germany':(51.2,10.4),'Austria':(48.2,16.4),'Russia':(55.8,37.6),'Persia':(32.4,53.7),'India':(20.6,78.9),'China':(35.9,104.2)}
VISUAL_TYPES = {'map','nautical_chart','plan','harbour','seascape','ship','coastal_city','landscape','architecture','portrait','animal','engraving','woodcut','botanical'}
MARITIME_TYPES = {'harbour','seascape','ship','coastal_city','nautical_chart'}
C = {'bg':'#F3EDE2','bg_dark':'#E8DFD0','ink':'#2B2B2B','ink_light':'#5A5A5A','gold':'#8B6F47','red':'#A23E48','indigo':'#3D5A80','sage':'#5E7E5F','plum':'#6D4C6E','slate':'#6B7B8D','terra':'#B07245','olive':'#7A7A4E','sea':'#2A6F97','sand':'#C9A96E'}
TYPE_COLORS = {'map':C['sage'],'nautical_chart':C['sea'],'plan':C['slate'],'harbour':C['indigo'],'seascape':C['sea'],'ship':C['indigo'],'coastal_city':C['terra'],'landscape':C['sage'],'architecture':C['plum'],'portrait':C['red'],'engraving':C['gold'],'woodcut':C['terra'],'animal':C['olive'],'botanical':C['sage']}
st.set_page_config(page_title="ShipAdvisor", page_icon="\u2693", layout="wide", initial_sidebar_state="collapsed")
if 'sel' not in st.session_state: st.session_state.sel = None
if 'entered' not in st.session_state: st.session_state.entered = False
def get_logo_base64():
    import glob
    for p in ['./logo.png','./Logo.png','./LOGO.png','./shipadvisor_results/logo.png'] + glob.glob('./*logo*.*'):
        if os.path.exists(p) and p.lower().endswith(('.png','.jpg','.jpeg')):
            with open(p,'rb') as f: return base64.b64encode(f.read()).decode()
    return None
def show_landing():
    logo_b64 = get_logo_base64()
    logo_tag = f"<img src='data:image/png;base64,{logo_b64}' style='width:160px;height:auto;border-radius:12px;filter:drop-shadow(0 4px 24px rgba(0,0,0,0.5));animation:fU 1s 0.3s ease forwards;opacity:0;margin-bottom:0.8rem'>" if logo_b64 else ""
    landing_html = """<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet"><style>*{margin:0;padding:0;box-sizing:border-box}:root{--gold:#c5993e;--gold-light:#d4b06a;--cream:#faf6ee}html,body{width:100%;height:100%;overflow:hidden;background:#0d1117}.scene{position:fixed;inset:0;background:linear-gradient(180deg,#0d1117 0%,#1a2332 35%,#1b3a4b 65%,#2d6a7a 100%)}.stars{position:absolute;top:0;left:0;right:0;height:45%;background:radial-gradient(1px 1px at 8% 12%,rgba(255,255,255,0.7) 50%,transparent 100%),radial-gradient(1.5px 1.5px at 22% 25%,rgba(255,255,255,0.5) 50%,transparent 100%),radial-gradient(1px 1px at 35% 8%,rgba(255,255,255,0.6) 50%,transparent 100%),radial-gradient(1px 1px at 52% 18%,rgba(255,255,255,0.4) 50%,transparent 100%),radial-gradient(1.5px 1.5px at 67% 22%,rgba(255,255,255,0.7) 50%,transparent 100%),radial-gradient(1px 1px at 78% 10%,rgba(255,255,255,0.5) 50%,transparent 100%);animation:twinkle 4s ease-in-out infinite alternate}@keyframes twinkle{0%{opacity:0.5}100%{opacity:1}}.sea{position:absolute;bottom:0;left:0;right:0;height:45%;overflow:hidden}.sea svg{position:absolute;bottom:0;width:100%;height:100%}.big-ship{position:absolute;bottom:15%;z-index:6;opacity:0;animation:bsA 2s 1s ease forwards,bsS 28s 1s linear infinite}@keyframes bsA{to{opacity:0.75}}@keyframes bsS{0%{left:-12%;transform:translateY(0) rotate(0deg)}12%{transform:translateY(-5px) rotate(-1deg)}25%{transform:translateY(2px) rotate(0.5deg)}37%{transform:translateY(-7px) rotate(-1.5deg)}50%{left:45%;transform:translateY(0) rotate(0deg)}62%{transform:translateY(-4px) rotate(-0.8deg)}75%{transform:translateY(3px) rotate(0.6deg)}87%{transform:translateY(-6px) rotate(-1.2deg)}100%{left:105%;transform:translateY(0) rotate(0deg)}}.ds{position:absolute;z-index:3;opacity:0}.ds1{bottom:24%;left:65%;animation:da1 2s 2.5s ease forwards,db1 6s 2.5s ease-in-out infinite}.ds2{bottom:26%;left:30%;animation:da2 2s 3s ease forwards,db2 7s 3s ease-in-out infinite}.ds3{bottom:23%;left:80%;animation:da3 2s 3.5s ease forwards,db3 8s 3.5s ease-in-out infinite}@keyframes da1{to{opacity:0.2}}@keyframes da2{to{opacity:0.15}}@keyframes da3{to{opacity:0.12}}@keyframes db1{0%,100%{transform:translateY(0)}50%{transform:translateY(-2px)}}@keyframes db2{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}@keyframes db3{0%,100%{transform:translateY(0)}50%{transform:translateY(-1.5px)}}.compass{position:absolute;top:5%;right:5%;width:65px;height:65px;opacity:0;animation:cIn 1.5s 1.5s ease forwards}@keyframes cIn{to{opacity:0.18}}.content{position:relative;z-index:10;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;text-align:center;padding:1.5rem}.eb{display:inline-flex;align-items:center;gap:10px;margin-top:1.2rem;padding:14px 40px;background:transparent;border:1px solid var(--gold);color:var(--gold);font-family:'DM Sans',sans-serif;font-size:0.85rem;letter-spacing:3px;text-transform:uppercase;cursor:pointer;transition:all 0.4s ease;opacity:0;animation:fU 1s 1.3s ease forwards;position:relative;overflow:hidden}.eb::before{content:'';position:absolute;inset:0;background:var(--gold);transform:translateX(-101%);transition:transform 0.4s ease;z-index:0}.eb:hover::before{transform:translateX(0)}.eb:hover{color:#0d1117}.eb span{position:relative;z-index:1}.eb .ar{position:relative;z-index:1;transition:transform 0.3s ease}.eb:hover .ar{transform:translateX(6px)}@keyframes fU{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}</style><div class="scene"><div class="stars"></div><div class="sea"><svg viewBox="0 0 1440 320" preserveAspectRatio="none"><path fill="rgba(27,58,75,0.35)"><animate attributeName="d" dur="8s" repeatCount="indefinite" values="M0,224L60,213C120,203,240,181,360,187C480,192,600,224,720,235C840,245,960,235,1080,213C1200,192,1320,160,1380,165L1440,171L1440,320L0,320Z;M0,192L60,208C120,224,240,256,360,251C480,245,600,203,720,187C840,171,960,181,1080,197C1200,213,1320,235,1380,229L1440,224L1440,320L0,320Z;M0,224L60,213C120,203,240,181,360,187C480,192,600,224,720,235C840,245,960,235,1080,213C1200,192,1320,160,1380,165L1440,171L1440,320L0,320Z"/></path><path fill="rgba(45,106,122,0.25)"><animate attributeName="d" dur="6s" repeatCount="indefinite" values="M0,256L60,251C120,245,240,235,360,229C480,224,600,224,720,229C840,235,960,245,1080,240C1200,235,1320,213,1380,219L1440,224L1440,320L0,320Z;M0,240L60,245C120,251,240,261,360,256C480,251,600,229,720,219C840,208,960,208,1080,219C1200,229,1320,251,1380,256L1440,261L1440,320L0,320Z;M0,256L60,251C120,245,240,235,360,229C480,224,600,224,720,229C840,235,960,245,1080,240C1200,235,1320,213,1380,219L1440,224L1440,320L0,320Z"/></path><path fill="rgba(27,58,75,0.55)" d="M0,288L60,283C120,277,240,267,360,267C480,267,600,277,720,277C840,277,960,267,1080,261C1200,256,1320,256,1380,261L1440,267L1440,320L0,320Z"/></svg></div><div class="big-ship"><svg width="120" height="100" viewBox="0 0 120 100" fill="none"><path d="M15 72 L60 72 L105 72 L95 84 L25 84 Z" fill="rgba(100,70,35,0.9)"/><path d="M20 72 L100 72 L95 78 L25 78 Z" fill="rgba(120,85,45,0.7)"/><line x1="60" y1="72" x2="60" y2="14" stroke="rgba(100,70,35,0.9)" stroke-width="1.8"/><rect x="55" y="16" width="10" height="4" rx="1" fill="rgba(100,70,35,0.7)"/><path d="M62 18 Q85 35 88 55 L62 62 Z" fill="rgba(244,239,230,0.75)"/><path d="M58 22 Q38 38 32 58 L58 62 Z" fill="rgba(244,239,230,0.55)"/><path d="M62 14 Q78 25 80 38 L62 40 Z" fill="rgba(197,153,62,0.4)"/><line x1="60" y1="14" x2="60" y2="8" stroke="rgba(197,153,62,0.7)" stroke-width="0.8"/><polygon points="60,8 68,10.5 60,12" fill="rgba(197,153,62,0.5)"/><line x1="105" y1="72" x2="118" y2="65" stroke="rgba(100,70,35,0.7)" stroke-width="1"/><path d="M62 20 L115 67 L105 72 Z" fill="rgba(244,239,230,0.3)"/><circle cx="40" cy="75" r="1.5" fill="rgba(197,153,62,0.35)"/><circle cx="52" cy="75" r="1.5" fill="rgba(197,153,62,0.35)"/><circle cx="64" cy="75" r="1.5" fill="rgba(197,153,62,0.35)"/><circle cx="76" cy="75" r="1.5" fill="rgba(197,153,62,0.35)"/></svg></div><div class="ds ds1"><svg width="24" height="18" viewBox="0 0 60 45" fill="none"><path d="M10 32 L30 32 L50 32 L44 37 L16 37 Z" fill="rgba(180,170,155,0.6)"/><line x1="30" y1="32" x2="30" y2="12" stroke="rgba(180,170,155,0.7)" stroke-width="1.2"/><path d="M31 14 L46 28 L31 31 Z" fill="rgba(220,215,205,0.4)"/></svg></div><div class="ds ds2"><svg width="18" height="14" viewBox="0 0 60 45" fill="none"><path d="M10 32 L30 32 L50 32 L44 37 L16 37 Z" fill="rgba(180,170,155,0.5)"/><line x1="30" y1="32" x2="30" y2="15" stroke="rgba(180,170,155,0.6)" stroke-width="1.5"/><path d="M31 17 L44 29 L31 31 Z" fill="rgba(220,215,205,0.35)"/></svg></div><div class="ds ds3"><svg width="14" height="10" viewBox="0 0 60 45" fill="none"><path d="M12 32 L30 32 L48 32 L42 36 L18 36 Z" fill="rgba(180,170,155,0.4)"/><line x1="30" y1="32" x2="30" y2="18" stroke="rgba(180,170,155,0.5)" stroke-width="1.8"/><path d="M31 20 L42 30 L31 31 Z" fill="rgba(220,215,205,0.3)"/></svg></div><svg class="compass" viewBox="0 0 100 100" fill="none"><circle cx="50" cy="50" r="45" stroke="#c5993e" stroke-width="0.5" opacity="0.5"/><circle cx="50" cy="50" r="38" stroke="#c5993e" stroke-width="0.3" opacity="0.3"/><line x1="50" y1="8" x2="50" y2="92" stroke="#c5993e" stroke-width="0.5" opacity="0.4"/><line x1="8" y1="50" x2="92" y2="50" stroke="#c5993e" stroke-width="0.5" opacity="0.4"/><polygon points="50,12 46,50 54,50" fill="#c5993e" opacity="0.6"/><polygon points="50,88 46,50 54,50" fill="#c5993e" opacity="0.25"/></svg><div class="content">LOGO_PLACEHOLDER<h1 style="font-family:Playfair Display,serif;font-size:clamp(2.5rem,6vw,4.2rem);font-weight:700;color:var(--cream);line-height:1.1;opacity:0;animation:fU 1s 0.6s ease forwards">Voyage across the<br><em style="font-style:italic;color:var(--gold-light);font-weight:400">Mediterranean</em></h1><p style="font-family:Playfair Display,serif;font-size:clamp(1.1rem,2.5vw,1.6rem);font-weight:400;font-style:italic;color:rgba(212,176,106,0.7);opacity:0;animation:fU 1s 0.85s ease forwards;margin-top:0.6rem">Are you ready to set sail?</p><p style="font-family:Cormorant Garamond,serif;font-size:clamp(0.9rem,1.8vw,1.15rem);font-weight:300;font-style:italic;color:rgba(244,239,230,0.45);max-width:540px;line-height:1.6;opacity:0;animation:fU 1s 1s ease forwards;margin:0.6rem auto 0">Discover 18th &amp; 19th century travelogues through sentiment analysis and CLIP-powered illustration classification.</p><div style="display:flex;gap:2.5rem;justify-content:center;margin-top:1.4rem;opacity:0;animation:fU 1s 1.1s ease forwards"><div style="text-align:center"><div style="font-family:Playfair Display,serif;font-size:1.5rem;font-weight:700;color:var(--gold)">140+</div><div style="font-family:DM Sans,sans-serif;font-size:0.65rem;letter-spacing:1.5px;text-transform:uppercase;color:rgba(244,239,230,0.4);margin-top:2px">Travelogues</div></div><div style="text-align:center"><div style="font-family:Playfair Display,serif;font-size:1.5rem;font-weight:700;color:var(--gold)">200+</div><div style="font-family:DM Sans,sans-serif;font-size:0.65rem;letter-spacing:1.5px;text-transform:uppercase;color:rgba(244,239,230,0.4);margin-top:2px">Routes</div></div><div style="text-align:center"><div style="font-family:Playfair Display,serif;font-size:1.5rem;font-weight:700;color:var(--gold)">700+</div><div style="font-family:DM Sans,sans-serif;font-size:0.65rem;letter-spacing:1.5px;text-transform:uppercase;color:rgba(244,239,230,0.4);margin-top:2px">Illustrations</div></div></div><div style="display:flex;align-items:center;gap:12px;justify-content:center;margin:1rem auto 0;opacity:0;animation:fU 1s 1.2s ease forwards"><span style="width:50px;height:1px;background:var(--gold);opacity:0.3;display:inline-block"></span><span style="width:5px;height:5px;background:var(--gold);transform:rotate(45deg);opacity:0.5;display:inline-block"></span><span style="width:50px;height:1px;background:var(--gold);opacity:0.3;display:inline-block"></span></div><button class="eb" onclick="embark()"><span>Embark on the Voyage</span><span class="ar">&rarr;</span></button></div></div><script>function embark(){try{var b=window.parent.document.querySelectorAll('button');for(var i=0;i<b.length;i++){if(b[i].innerText.indexOf('__ENTER__')!==-1){b[i].click();return;}}}catch(e){}try{window.parent.location.search='?entered=true';}catch(e){}}</script>""".replace("LOGO_PLACEHOLDER", logo_tag)
    st.markdown("""<style>header[data-testid="stHeader"]{display:none!important}div[data-testid="stToolbar"]{display:none!important}div[data-testid="stDecoration"]{display:none!important}#MainMenu{display:none!important}footer{display:none!important}section[data-testid="stSidebar"]{display:none!important}div.block-container{padding:0!important;max-width:100%!important}.stApp{background:#0d1117!important}iframe{border:none!important}.hidden-btn{position:fixed;top:-9999px;left:-9999px;height:0;overflow:hidden}</style>""", unsafe_allow_html=True)
    components.html(landing_html, height=1000, scrolling=False)
    st.markdown('<div class="hidden-btn">', unsafe_allow_html=True)
    if st.button("__ENTER__"):
        st.session_state.entered = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
def inject_app_styles():
    st.markdown("""<style>@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Crimson+Text:wght@400;600;700&family=EB+Garamond:wght@400;500;600&display=swap');.stApp{font-family:'Crimson Text','Georgia',serif;background:linear-gradient(180deg,#0f1a24 0%,#152736 100%);animation:pageIn 0.6s ease forwards}@keyframes pageIn{from{opacity:0}to{opacity:1}}h1,h2,h3{font-family:'Playfair Display',serif!important;color:#f0ebe3!important}p,span,label,.stMarkdown{color:#c8c0b4}.med-badge{display:inline-block;padding:2px 8px;border-radius:3px;font-size:0.7rem;background:rgba(42,111,151,0.2);color:#5ba8c8;border:1px solid rgba(42,111,151,0.3)}.tag{display:inline-block;padding:3px 10px;border-radius:3px;font-size:0.75rem;margin:2px;font-family:'EB Garamond',serif}div[data-testid="stTabs"] button{color:rgba(200,192,180,0.5)!important}div[data-testid="stTabs"] button[aria-selected="true"]{color:#c5993e!important;border-bottom-color:#c5993e!important}div[data-testid="stTabs"] button:hover{color:rgba(200,192,180,0.8)!important}div[data-testid="stSelectbox"] label,div[data-testid="stSlider"] label,div[data-testid="stCheckbox"] label,div[data-testid="stNumberInput"] label{color:#c8c0b4!important}.stSelectbox>div>div{background:rgba(255,255,255,0.05)!important;border-color:rgba(197,153,62,0.2)!important;color:#f0ebe3!important}.stCaption,small{color:rgba(200,192,180,0.5)!important}</style>""", unsafe_allow_html=True)
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
        subj = str(row.get('Subject','')).lower()
        for ie in str(row.get('ie_folders','')).replace(';','|').split('|'):
            ie = ie.strip()
            if ie: m[ie] = subj
    return m
def ie_matches_place(ie_folder, place, ie_subject_map):
    keywords = PLACE_SUBJECT_KEYWORDS.get(place)
    if keywords is None or len(keywords)==0: return True
    subj = ie_subject_map.get(ie_folder,'')
    if not subj: return True
    return any(kw in subj for kw in keywords)
def find_image(p):
    for b in IMAGE_DIRS:
        f = os.path.join(b, p)
        if os.path.exists(f) and os.path.getsize(f)>0: return f
    return None
def get_stop_images(ills, ie, place):
    if ills is None: return []
    m = (ills['ie_folder']==ie)&(ills['nearest_place']==place)&(ills['illustration_type'].isin(VISUAL_TYPES))
    out = []
    for _, r in ills[m].sort_values('confidence',ascending=False).iterrows():
        p = find_image(r['image_path'])
        if p: out.append({'path':p,'type':r['illustration_type'],'page':int(r['page'])})
    return out
def base_layout(**kw):
    d = dict(plot_bgcolor='rgba(0,0,0,0)',paper_bgcolor='rgba(0,0,0,0)',font=dict(family='Crimson Text,Georgia,serif',color='#c8c0b4'),title_font=dict(family='Playfair Display,serif',size=16,color='#f0ebe3'))
    d.update(kw); return d
def show_app():
    inject_app_styles()
    routes, illustrations, books = load_data()
    ie_subject_map = build_ie_subject_map(books)
    if routes is None: st.error("No data. Place shipadvisor_results/ next to app.py."); return
    logo_b64 = get_logo_base64()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:55px;border-radius:8px;margin-right:16px">' if logo_b64 else '<span style="font-size:2rem;margin-right:12px">&#9875;</span>'
    st.markdown(f'<div style="display:flex;align-items:center;padding:0.8rem 0 1rem 0;border-bottom:1px solid rgba(197,153,62,0.15);margin-bottom:1rem">{logo_html}<div><div style="font-family:Playfair Display,serif;font-size:1.8rem;font-weight:700;color:#f0ebe3;line-height:1.2">ShipAdvisor</div><div style="font-family:EB Garamond,serif;font-size:0.95rem;color:rgba(197,153,62,0.6);font-style:italic;margin-top:2px">Know Before You Row</div></div></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Sentiment Map", "Browse Illustrations"])
    with tab1:
        st.markdown("### Mediterranean Sentiment Map")
        st.markdown('<p style="font-family:EB Garamond,serif;color:rgba(200,192,180,0.5);font-style:italic">Sentiment analysis of Mediterranean locations based on travelogue texts</p>', unsafe_allow_html=True)
        map_path = "mediterranean_sentiment_map_offline.html"
        if os.path.exists(map_path):
            with open(map_path,"r",encoding="utf-8") as f: map_html = f.read()
            components.html(map_html, height=700, scrolling=True)
        else: st.warning("Sentiment map file not found.")
    with tab2:
        st.markdown("### Browse Illustrations by Type")
        if illustrations is not None:
            med_vis = illustrations[(illustrations['is_med_location']==True)&(illustrations['illustration_type'].isin(VISUAL_TYPES))].copy()
            fc1,fc2,fc3 = st.columns(3)
            with fc1: sel_type = st.selectbox("Illustration type",['All types']+sorted(med_vis['illustration_type'].unique()))
            with fc2: sel_place = st.selectbox("Location",['All locations']+sorted(med_vis['nearest_place'].dropna().unique()))
            with fc3: strict_filter = st.checkbox("Strict: only books about this place",value=True)
            if sel_type!='All types': med_vis = med_vis[med_vis['illustration_type']==sel_type]
            if sel_place!='All locations':
                med_vis = med_vis[med_vis['nearest_place']==sel_place]
                if strict_filter and sel_place in PLACE_SUBJECT_KEYWORDS:
                    kws = PLACE_SUBJECT_KEYWORDS[sel_place]
                    if len(kws)==0: st.warning(f"No books catalogued under **{sel_place}**.")
                    else:
                        mask = med_vis['ie_folder'].apply(lambda ie: ie_matches_place(ie,sel_place,ie_subject_map))
                        n_before=len(med_vis); med_vis=med_vis[mask]
                        if n_before-len(med_vis)>0: st.info(f"Strict filter removed {n_before-len(med_vis)} illustrations.")
            st.caption(f"{len(med_vis)} illustrations")
            PER_PAGE=30; tp=max(1,len(med_vis)//PER_PAGE+1); pg=st.number_input("Page",1,tp,1)-1
            page_data=med_vis.iloc[pg*PER_PAGE:(pg+1)*PER_PAGE]; cols=st.columns(6); shown=0
            for _,ill in page_data.iterrows():
                ip=find_image(ill['image_path'])
                if not ip: continue
                with cols[shown%6]:
                    st.image(ip,use_container_width=True)
                    tcl=TYPE_COLORS.get(ill['illustration_type'],C['slate'])
                    st.markdown(f'<div style="font-size:11px;text-align:center;margin-top:-8px"><span style="color:{tcl};font-weight:600">{ill["illustration_type"]}</span><br><span style="color:rgba(200,192,180,0.6)">{ill["nearest_place"]} p.{int(ill["page"])}</span><br><span style="color:rgba(200,192,180,0.4);font-size:10px">{str(ill["book_title"])[:35]}</span></div>',unsafe_allow_html=True)
                    st.markdown("")
                shown+=1
            if shown==0: st.info("No images found.")
        else: st.warning("No illustration data.")
def main():
    params = st.query_params
    if params.get('entered')=='true': st.session_state.entered = True
    if not st.session_state.entered: show_landing()
    else: show_app()
if __name__ == "__main__": main()
