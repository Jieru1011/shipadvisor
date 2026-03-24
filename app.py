"""
ShipAdvisor — Mediterranean Travel Route Explorer
Usage:  python -m streamlit run app.py
"""

import streamlit as st
import pandas as pd
import os, json
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components

RESULTS_DIR = './shipadvisor_results'
ROUTES_FILE = os.path.join(RESULTS_DIR, 'routes.csv')
ILLUSTRATIONS_FILE = os.path.join(RESULTS_DIR, 'route_illustrations.csv')
CLASSIFICATIONS_FILE = os.path.join(RESULTS_DIR, 'classifications.csv')
BOOKS_FILE = os.path.join(RESULTS_DIR, 'mediterranean_books.csv')
IMAGE_DIRS = ['./shipadvisor_images', './travelogues_raw']

# ============================================================
# SUBJECT → DESTINATION MAPPING
# Maps nearest_place values to keywords found in the Subject field.
# Used to filter out illustrations from books whose Subject does
# not match the selected location (e.g. an Africa book that
# mentions Italy in passing should not show up under "Italy").
# ============================================================
PLACE_SUBJECT_KEYWORDS = {
    'Italy':     ['italië'],
    'France':    ['frankrijk'],
    'Spain':     ['spanje'],
    'Portugal':  ['portugal'],
    'Greece':    [],
    'Turkey':    ['turkije'],
    'Egypt':     ['egypte'],
    'Palestine': ['palestina'],
    'Syria':     ['syrië'],
    'Lebanon':   [],
    'Algeria':   ['algerije', 'noord-afrikaanse staten', 'maghreb'],
    'Tunisia':   ['tunesi', 'noord-afrikaanse staten', 'maghreb'],
    'Morocco':   ['marokko', 'noord-afrikaanse staten', 'maghreb'],
    'Libya':     ['libië', 'noord-afrikaanse staten', 'maghreb'],
    'Cyprus':    [],
    'Malta':     [],
    'Croatia':   [],
    'Russia':    ['rusland'],
    'India':     ['india', 'azië'],
    'China':     ['china', 'azië'],
    'Persia':    ['perzië'],
    'England':   [],
    'Belgium':   [],
    'Netherlands': [],
    'Germany':   [],
    'Austria':   [],
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

st.set_page_config(page_title="ShipAdvisor", page_icon="⚓", layout="wide", initial_sidebar_state="collapsed")
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


# --- helpers ---
@st.cache_data
def load_data():
    r = pd.read_csv(ROUTES_FILE) if os.path.exists(ROUTES_FILE) else None
    i = pd.read_csv(ILLUSTRATIONS_FILE) if os.path.exists(ILLUSTRATIONS_FILE) else None
    c = None
    b = pd.read_csv(BOOKS_FILE) if os.path.exists(BOOKS_FILE) else None
    return r, i, c, b


def build_ie_subject_map(books_df):
    """Build a dict: ie_folder → Subject string (lowercased)."""
    m = {}
    if books_df is None:
        return m
    for _, row in books_df.iterrows():
        subj = str(row.get('Subject', '')).lower()
        for ie in str(row.get('ie_folders', '')).replace(';', '|').split('|'):
            ie = ie.strip()
            if ie:
                m[ie] = subj
    return m


def ie_matches_place(ie_folder, place, ie_subject_map):
    """Check if a book's Subject field mentions the given place."""
    keywords = PLACE_SUBJECT_KEYWORDS.get(place)
    if keywords is None:
        return True
    if len(keywords) == 0:
        return True
    subj = ie_subject_map.get(ie_folder, '')
    if not subj:
        return True
    return any(kw in subj for kw in keywords)

def find_image(p):
    for b in IMAGE_DIRS:
        f = os.path.join(b, p)
        if os.path.exists(f) and os.path.getsize(f) > 0:
            return f
    return None

def get_stop_images(ills, ie, place):
    if ills is None:
        return []
    m = (ills['ie_folder'] == ie) & (ills['nearest_place'] == place) & (ills['illustration_type'].isin(VISUAL_TYPES))
    out = []
    for _, r in ills[m].sort_values('confidence', ascending=False).iterrows():
        p = find_image(r['image_path'])
        if p:
            out.append({'path': p, 'type': r['illustration_type'], 'page': int(r['page'])})
    return out

def base_layout(**kw):
    d = dict(plot_bgcolor=C['bg'], paper_bgcolor=C['bg'], font=dict(family='Crimson Text,Georgia,serif', color=C['ink']),
             title_font=dict(family='Playfair Display,serif', size=16, color=C['ink']))
    d.update(kw)
    return d

def draw_overview_map(routes):
    pd2 = {}
    for _, row in routes.iterrows():
        try:
            for s in json.loads(row['route_detail']):
                p = s['place']
                if p not in pd2:
                    pd2[p] = {'n': 0, 'med': s['is_mediterranean']}
                pd2[p]['n'] += 1
        except:
            pass
    fig = go.Figure()
    for place, d in pd2.items():
        co = PLACE_COORDS.get(place)
        if not co:
            continue
        fig.add_trace(go.Scattergeo(
            lat=[co[0]], lon=[co[1]], mode='markers+text',
            marker=dict(size=max(8, min(30, d['n']*0.8)), color=C['sea'] if d['med'] else C['slate'],
                        opacity=0.75, line=dict(width=1, color='white')),
            text=[place], textposition='top center',
            textfont=dict(size=10, family='Playfair Display,serif', color=C['ink']),
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
        if co:
            la.append(co[0]); lo.append(co[1]); nm.append(s['place']); md.append(s['is_mediterranean'])
    if not la:
        return None
    fig = go.Figure()
    for i in range(len(la)-1):
        cl = C['sea'] if (md[i] and md[i+1]) else C['gold']
        fig.add_trace(go.Scattergeo(lat=[la[i],la[i+1]], lon=[lo[i],lo[i+1]], mode='lines',
            line=dict(width=2.5, color=cl, dash='dot'), showlegend=False, hoverinfo='skip'))
        fig.add_trace(go.Scattergeo(lat=[(la[i]+la[i+1])/2], lon=[(lo[i]+lo[i+1])/2], mode='markers',
            marker=dict(size=5, color=cl, symbol='triangle-right', opacity=0.6), showlegend=False, hoverinfo='skip'))
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
    pl, pn = max(3.0, (max(la)-min(la))*0.3), max(3.0, (max(lo)-min(lo))*0.3)
    fig.update_layout(paper_bgcolor=C['bg'], height=550, margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(x=0.01, y=0.99, font=dict(family='Crimson Text,serif', size=12)),
        geo=dict(bgcolor=C['bg'], landcolor=C['bg_dark'], showland=True, showcountries=True,
                 countrycolor='rgba(139,111,71,0.3)', coastlinecolor='rgba(139,111,71,0.5)',
                 showocean=True, oceancolor='rgba(42,111,151,0.06)', showframe=False,
                 lonaxis=dict(range=[min(lo)-pn, max(lo)+pn]), lataxis=dict(range=[min(la)-pl, max(la)+pl])))
    return fig


# ---------------------------------------------------------------------------
def main():
    routes, illustrations, classifications, books = load_data()
    ie_subject_map = build_ie_subject_map(books)
    if routes is None:
        st.error("No data. Place `shipadvisor_results/` next to `app.py`."); return

    st.markdown('<p class="main-title">ShipAdvisor</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Navigating Mediterranean travel routes in early modern travelogues · KU Leuven Libraries</p>', unsafe_allow_html=True)
    st.markdown('<div class="ornament">— ⚓ —</div>', unsafe_allow_html=True)

    nb = routes['ie_folder'].nunique()
    mi = int(illustrations['is_med_location'].sum()) if illustrations is not None else 0
    c1, c2, c3, c4 = st.columns(4)
    for col, num, lbl in [(c1, str(nb), "Books"), (c2, str(len(routes)), "Routes"),
        (c3, f"{len(illustrations):,}" if illustrations is not None else "0", "Illustrations"), (c4, f"{mi:,}", "Mediterranean")]:
        col.markdown(f'<div class="metric-card"><div class="metric-number">{num}</div><div class="metric-label">{lbl}</div></div>', unsafe_allow_html=True)
    st.markdown("")

    if 'sel' not in st.session_state:
        st.session_state.sel = None

    tab1, tab2, tab3, tab4 = st.tabs(["Statistics", "Browse Illustrations", "Route Explorer", "Sentiment Map"])

    # ================================================================
    # TAB 3: ROUTE EXPLORER
    # ================================================================
    with tab3:
        if st.session_state.sel is None:
            # --- OVERVIEW ---
            st.markdown("### All Mediterranean Routes")
            st.plotly_chart(draw_overview_map(routes), use_container_width=True)
            fc1, fc2 = st.columns(2)
            with fc1:
                min_med = st.slider("Min Mediterranean stops", 0, 20, 3)
            with fc2:
                sort_by = st.selectbox("Sort by", ['Most Mediterranean stops', 'Most sea pages', 'Title A-Z'])
            df_r = routes[routes['num_med_stops'] >= min_med].copy()
            if sort_by == 'Most Mediterranean stops':
                df_r = df_r.sort_values('num_med_stops', ascending=False)
            elif sort_by == 'Most sea pages':
                df_r = df_r.sort_values('sea_pages', ascending=False)
            else:
                df_r = df_r.sort_values('title')
            st.markdown(f"#### Select a route ({len(df_r)} routes)")
            for idx, (_, row) in enumerate(df_r.iterrows()):
                pct = int(100 * row['num_med_stops'] / max(1, row['num_stops']))
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(
                        f'<div style="background:{C["bg_dark"]};border-radius:6px;padding:14px 18px;'
                        f'margin-bottom:6px;border-left:4px solid {C["sea"]}">'
                        f'<div style="font-family:Playfair Display,serif;font-size:16px;color:{C["ink"]}">{row["title"][:75]}</div>'
                        f'<div style="font-size:12px;color:{C["ink_light"]};margin:3px 0">'
                        f'{row.get("language","")} · {row.get("date","")} · {row["origin"]} ➜ {row["destination"]}</div>'
                        f'<div style="margin-top:4px"><span class="med-badge">{row["num_med_stops"]} Med ({pct}%)</span> '
                        f'<span style="font-size:12px;color:{C["ink_light"]}">{row["num_stops"]} stops · {int(row["sea_pages"])} sea pages</span></div>'
                        f'<div style="font-size:12px;color:{C["ink_light"]};margin-top:3px">{str(row["med_segment"])[:90]}</div></div>',
                        unsafe_allow_html=True)
                with col2:
                    if st.button("Explore ➜", key=f"r_{idx}_{row['ie_folder']}", use_container_width=True):
                        st.session_state.sel = row.to_dict()
                        st.rerun()
        else:
            # --- ROUTE DETAIL ---
            row = st.session_state.sel
            if st.button("← Back to all routes"):
                st.session_state.sel = None
                st.rerun()

            st.markdown(
                f'<div style="background:{C["bg_dark"]};border-radius:8px;padding:18px 24px;margin:8px 0 20px 0;border:1px solid rgba(139,111,71,0.2)">'
                f'<div style="font-family:Playfair Display,serif;font-size:22px;color:{C["ink"]}">{row["title"]}</div>'
                f'<div style="font-size:13px;color:{C["ink_light"]};margin-top:4px">'
                f'{row.get("language","")} · {row.get("date","")} · {int(row["num_stops"])} stops · {int(row["num_med_stops"])} Mediterranean · {int(row["sea_pages"])} sea pages</div>'
                f'<div style="margin-top:8px;font-size:13px"><b>Route:</b> {row["full_route"]}</div>'
                f'<div style="margin-top:4px;font-size:13px"><span class="med-badge">Med segment</span> {row["med_segment"]}</div></div>',
                unsafe_allow_html=True)

            try:
                route_detail = json.loads(row['route_detail'])
            except:
                route_detail = []
            ie = row['ie_folder']

            # Preload images
            stop_images = {}
            for stop in route_detail:
                imgs = get_stop_images(illustrations, ie, stop['place'])
                if imgs:
                    stop_images[stop['place']] = imgs

            # Route map
            fig = draw_route_map(route_detail)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

            # Image timeline
            st.markdown("### Route illustration timeline")
            timeline = [{'place': s['place'], 'med': s['is_mediterranean'], 'img': stop_images[s['place']][0], 'total': len(stop_images[s['place']])}
                        for s in route_detail if s['place'] in stop_images]
            if timeline:
                nc = min(len(timeline), 6)
                cols = st.columns(nc)
                for i, ts in enumerate(timeline[:nc*2]):
                    with cols[i % nc]:
                        st.image(ts['img']['path'], use_container_width=True)
                        cl = C['sea'] if ts['med'] else C['slate']
                        st.markdown(f'<div style="text-align:center;font-size:13px;margin-top:-8px">'
                            f'<b style="color:{cl}">{"🌊 " if ts["med"] else ""}{ts["place"]}</b><br>'
                            f'<span style="font-size:11px;color:{C["ink_light"]}">{ts["img"]["type"]} · p.{ts["img"]["page"]} · {ts["total"]} imgs</span></div>',
                            unsafe_allow_html=True)
            else:
                st.info("No illustrations found for this route.")

            # Journey stops
            st.markdown("### Journey stops")
            for i, stop in enumerate(route_detail):
                is_med = stop['is_mediterranean']
                color = C['sea'] if is_med else C['slate']
                badge = '<span class="med-badge">Mediterranean</span> ' if is_med else ''
                place = stop['place']
                imgs = stop_images.get(place, [])

                tags_html = ''
                if imgs:
                    tc2 = {}
                    for im in imgs:
                        tc2[im['type']] = tc2.get(im['type'], 0) + 1
                    for t, cnt in sorted(tc2.items(), key=lambda x: -x[1]):
                        tcl = TYPE_COLORS.get(t, C['slate'])
                        tags_html += f'<span class="tag" style="background:rgba(139,111,71,0.08);color:{tcl};border:1px solid rgba(139,111,71,0.2)">{t} ({cnt})</span>'

                st.markdown(
                    f'<div style="background:{C["bg_dark"]};border-radius:6px;padding:14px 18px;margin-bottom:4px;border-left:4px solid {color}">'
                    f'<div style="display:flex;gap:12px;align-items:flex-start">'
                    f'<div style="min-width:32px;height:32px;border-radius:50%;background:{color};color:white;display:flex;align-items:center;justify-content:center;font-weight:600;font-family:Playfair Display,serif;font-size:14px">{i+1}</div>'
                    f'<div style="flex:1"><div style="font-family:Playfair Display,serif;font-size:17px;color:{C["ink"]}">{badge}{place}</div>'
                    f'<div style="font-size:12px;color:{C["ink_light"]};margin:2px 0">First mentioned p.{stop["page"]}{f" · {len(imgs)} illustrations" if imgs else ""}</div>'
                    f'{f"<div style=margin-top:6px>{tags_html}</div>" if tags_html else ""}</div></div></div>',
                    unsafe_allow_html=True)

                if imgs:
                    nc = min(6, len(imgs))
                    cols = st.columns(nc)
                    for j, im in enumerate(imgs[:12]):
                        with cols[j % nc]:
                            st.image(im['path'], use_container_width=True)
                            st.caption(f"{im['type']} · p.{im['page']}")
                st.markdown("")

            st.caption("Route: OCR text · Illustrations: CLIP zero-shot (18 prompts) · Mediterranean in blue")

    # ================================================================
    # TAB 2: BROWSE ILLUSTRATIONS
    # ================================================================
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
                strict_filter = st.checkbox(
                    "Strict: only books about this place",
                    value=True,
                    help="When enabled, only shows illustrations from books whose catalogue Subject matches the selected location. "
                         "This filters out images from books that merely mention the place in passing (e.g. an Africa book mentioning Italy as a transit point)."
                )

            if sel_type != 'All types':
                med_vis = med_vis[med_vis['illustration_type'] == sel_type]
            if sel_place != 'All locations':
                med_vis = med_vis[med_vis['nearest_place'] == sel_place]
                if strict_filter and sel_place in PLACE_SUBJECT_KEYWORDS:
                    kws = PLACE_SUBJECT_KEYWORDS[sel_place]
                    if len(kws) == 0:
                        st.warning(f"No books in the corpus are catalogued specifically under **{sel_place}** — strict filter has no effect. "
                                   f"These illustrations come from books that mention {sel_place} in passing.")
                    else:
                        mask = med_vis['ie_folder'].apply(
                            lambda ie: ie_matches_place(ie, sel_place, ie_subject_map)
                        )
                        n_before = len(med_vis)
                        med_vis = med_vis[mask]
                        n_filtered = n_before - len(med_vis)
                        if n_filtered > 0:
                            st.info(f"Strict filter removed {n_filtered} illustrations from books not catalogued under {sel_place}.")

            st.caption(f"{len(med_vis)} illustrations")

            PER_PAGE = 30
            tp = max(1, len(med_vis) // PER_PAGE + 1)
            pg = st.number_input("Page", 1, tp, 1) - 1
            page_data = med_vis.iloc[pg*PER_PAGE:(pg+1)*PER_PAGE]

            cols = st.columns(6)
            shown = 0
            for _, ill in page_data.iterrows():
                ip = find_image(ill['image_path'])
                if not ip:
                    continue
                with cols[shown % 6]:
                    st.image(ip, use_container_width=True)
                    tcl = TYPE_COLORS.get(ill['illustration_type'], C['slate'])
                    st.markdown(
                        f'<div style="font-size:11px;text-align:center;margin-top:-8px">'
                        f'<span style="color:{tcl};font-weight:600">{ill["illustration_type"]}</span><br>'
                        f'<span style="color:{C["ink_light"]}">{ill["nearest_place"]} · p.{int(ill["page"])}</span><br>'
                        f'<span style="color:{C["ink_light"]};font-size:10px">{str(ill["book_title"])[:35]}</span></div>',
                        unsafe_allow_html=True)
                    st.markdown("")
                shown += 1
            if shown == 0:
                st.info("No images found for current filter.")
        else:
            st.warning("No illustration data.")

    # ================================================================
    # TAB 1: STATISTICS
    # ================================================================
    with tab1:
        st.markdown("### Dataset Statistics")

        if illustrations is not None:
            vis_only = illustrations[illustrations['illustration_type'].isin(VISUAL_TYPES)].copy()
        else:
            vis_only = None

        cl, cr = st.columns(2)
        with cl:
            if vis_only is not None:
                md = vis_only[vis_only['is_med_location'] == True]
                pc = md['nearest_place'].value_counts().head(15)
                fig = px.bar(x=pc.values, y=pc.index, orientation='h', title='Top Mediterranean locations',
                             color_discrete_sequence=[C['sea']],
                             labels={'x': 'Number of illustrations', 'y': 'Location'})
                fig.update_traces(texttemplate='%{x}', textposition='outside')
                fig.update_layout(**base_layout(height=450)); fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)
        with cr:
            if vis_only is not None:
                dist = vis_only['illustration_type'].value_counts()
                fig = px.bar(x=dist.values, y=dist.index, orientation='h', title='Illustration types',
                             color_discrete_sequence=[C['gold']],
                             labels={'x': 'Count', 'y': 'Type'})
                fig.update_traces(texttemplate='%{x}', textposition='outside')
                fig.update_layout(**base_layout(height=450)); fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)

        cl2, cr2 = st.columns(2)
        with cl2:
            if vis_only is not None:
                mc = vis_only[vis_only['illustration_type'].isin(MARITIME_TYPES)].shape[0]
                nt = len(vis_only)
                fig = px.pie(values=[mc, nt-mc], names=['Maritime', 'Other'], title='Maritime vs other',
                             color_discrete_sequence=[C['sea'], C['terra']])
                fig.update_traces(textinfo='label+value+percent')
                fig.update_layout(paper_bgcolor=C['bg'], height=400,
                    font=dict(family='Crimson Text,serif', color=C['ink']),
                    title_font=dict(family='Playfair Display,serif', size=16, color=C['ink']))
                st.plotly_chart(fig, use_container_width=True)
        with cr2:
            fig = px.histogram(routes, x='sea_pages', nbins=30, title='Sea pages per book',
                               color_discrete_sequence=[C['indigo']],
                               labels={'sea_pages': 'Sea pages', 'count': 'Books'})
            fig.update_layout(**base_layout(height=400, showlegend=False))
            st.plotly_chart(fig, use_container_width=True)

        cl3, cr3 = st.columns(2)
        with cl3:
            oc = routes['origin'].value_counts().head(10)
            fig = px.bar(x=oc.values, y=oc.index, orientation='h', title='Departure points',
                         color_discrete_sequence=[C['sage']],
                         labels={'x': 'Count', 'y': 'Origin'})
            fig.update_traces(texttemplate='%{x}', textposition='outside')
            fig.update_layout(**base_layout(height=400)); fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        with cr3:
            dc = routes['destination'].value_counts().head(10)
            fig = px.bar(x=dc.values, y=dc.index, orientation='h', title='Final destinations',
                         color_discrete_sequence=[C['red']],
                         labels={'x': 'Count', 'y': 'Destination'})
            fig.update_traces(texttemplate='%{x}', textposition='outside')
            fig.update_layout(**base_layout(height=400)); fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)

        fig = px.histogram(routes, x='num_med_stops', nbins=20, title='Mediterranean stops per route',
                           color_discrete_sequence=[C['sea']],
                           labels={'num_med_stops': 'Mediterranean stops', 'count': 'Routes'})
        fig.update_layout(**base_layout(height=350, showlegend=False))
        st.plotly_chart(fig, use_container_width=True)

    # ================================================================
    # TAB 4: SENTIMENT MAP
    # ================================================================
    with tab4:
        st.markdown("### Mediterranean Sentiment Map")
        st.markdown(
            f'<p style="font-family:EB Garamond,serif;color:{C["ink_light"]};font-style:italic">'
            f'Sentiment analysis of Mediterranean locations based on travelogue texts</p>',
            unsafe_allow_html=True
        )
        map_path = "mediterranean_sentiment_map_offline.html"
        if os.path.exists(map_path):
            with open(map_path, "r", encoding="utf-8") as f:
                map_html = f.read()
            components.html(map_html, height=700, scrolling=True)
        else:
            st.warning("Sentiment map file not found. Please place `mediterranean_sentiment_map_offline.html` in the app root directory.")


if __name__ == "__main__":
    main()
