"""
ShipAdvisor — Complete Pipeline
================================
1. Filter Mediterranean books from metadata (Subject + Title)
2. CLIP zero-shot classification with UPDATED prompts (reduced noise, added maritime)
3. Extract travel routes from OCR text by page order
4. Match illustrations to route locations
5. Tag maritime pages with sea/voyage/med keywords

Usage (HPC):
    # Request a GPU node for CLIP (recommended)
    # Or run on CPU (slower but works)

    source ~/miniconda3/bin/activate
    pip install open_clip_torch pandas openpyxl tqdm pillow
    python shipadvisor_pipeline.py

Output:
    /scratch/leuven/387/vsc38785/shipadvisor_results/
        mediterranean_books.csv      — filtered book list
        classifications.csv          — CLIP classifications (updated prompts)
        routes.csv                   — per-book travel routes
        route_illustrations.csv      — illustrations matched to route locations
        summary.txt                  — pipeline summary
"""

import os, re, csv, json, glob, sys
from collections import OrderedDict
from pathlib import Path
from tqdm import tqdm
import numpy as np

# ============================================================
# CONFIGURATION
# ============================================================
METADATA_CSV = "/scratch/leuven/387/vsc38785/travelogues_raw/Travelogues_20260210_v2.csv"
DATASET9_XLSX = "/scratch/leuven/387/vsc38785/travelogues_raw/dataset_9.xlsx"
TRAVELOGUES_DIR = "/scratch/leuven/387/vsc38785/travelogues_raw"
OUTPUT_DIR = "/scratch/leuven/387/vsc38785/shipadvisor_results"
BATCH_SIZE = 64

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# UPDATED CLASSIFICATION PROMPTS
# - Optimized originals to reduce noise (e.g., map vs title_page)
# - Added maritime categories from team discussion
# ============================================================
CLASSIFICATION_PROMPTS = {
    # --- Maps & plans (optimized: more specific to avoid title_page confusion) ---
    "map":              "a hand-drawn geographical map showing countries, coastlines, borders and place names",
    "nautical_chart":   "a nautical chart or maritime navigation map showing sea routes and coastlines",
    "plan":             "an architectural floor plan or bird's-eye city plan drawing with streets",

    # --- Maritime (NEW: from team sea/voyage/med keywords) ---
    "harbour":          "an engraving of a harbour or port with sailing ships moored at docks",
    "seascape":         "an engraving of the open sea, ocean waves, or a coastal seashore",
    "ship":             "an illustration of a sailing ship or vessel on the sea",
    "coastal_city":     "a panoramic view of a coastal Mediterranean city seen from the sea",

    # --- Illustrations (optimized) ---
    "landscape":        "an engraving depicting mountains, rivers, valleys or natural countryside scenery",
    "architecture":     "an engraving of a building, church, mosque, castle, temple or ancient ruins",
    "portrait":         "an engraved portrait showing a person's face and upper body",
    "animal":           "an illustration of animals or exotic creatures",
    "engraving":        "a detailed steel or copper engraving illustration from an old book",
    "woodcut":          "a woodcut illustration with bold black lines from an early printed book",

    # --- Book structure (optimized: more specific to reduce misclassification) ---
    "title_page":       "an ornate book title page with large decorative text and the book's name",
    "frontispice":      "a full-page frontispiece illustration opposite the title page of a book",
    "decorative":       "a small decorative vignette, head piece, tail piece or ornamental initial letter",
    "folded_leaflet":   "a large folded panoramic plate or fold-out illustration bound into a book",

    # --- Text (the majority class) ---
    "text_page":        "a page of old printed text in columns with no illustrations or images",
}

# ============================================================
# MEDITERRANEAN DEFINITION (from team)
# ============================================================
include_terms = [
    'Palestina', 'Italië', 'Frankrijk', 'Afrika', 'Turkije',
    'Soedan', 'Ethiopië', 'Nabije-Oosten', 'Syrië', 'Egypte',
    'Spanje', 'Sovjetrepubliek Georgië', 'Algerije', 'Portugal',
    'Europa', 'Perzië', 'Azië', 'Rusland'
]
exclude_terms = ['Zuid-Afrika', 'Senegal']

# Place names for OCR route extraction (multi-language)
MEDITERRANEAN_PLACES = {
    # France
    'france': 'France', 'paris': 'France', 'marseille': 'France',
    'toulon': 'France', 'nice': 'France', 'lyon': 'France',
    'bordeaux': 'France', 'provence': 'France',
    # Italy
    'italie': 'Italy', 'italia': 'Italy', 'italy': 'Italy',
    'rome': 'Italy', 'roma': 'Italy', 'naples': 'Italy', 'napoli': 'Italy',
    'venise': 'Italy', 'venezia': 'Italy', 'venice': 'Italy',
    'florence': 'Italy', 'firenze': 'Italy', 'milan': 'Italy',
    'gênes': 'Italy', 'genova': 'Italy', 'genoa': 'Italy',
    'sicile': 'Italy', 'sicilia': 'Italy', 'sicily': 'Italy',
    'sardaigne': 'Italy', 'sardinia': 'Italy', 'livourne': 'Italy',
    'civitavecchia': 'Italy', 'messina': 'Italy', 'palerme': 'Italy',
    # Spain
    'espagne': 'Spain', 'españa': 'Spain', 'spain': 'Spain', 'spanje': 'Spain',
    'madrid': 'Spain', 'barcelona': 'Spain', 'séville': 'Spain',
    'valence': 'Spain', 'valencia': 'Spain', 'malaga': 'Spain',
    'cadix': 'Spain', 'gibraltar': 'Spain', 'alicante': 'Spain',
    # Portugal
    'portugal': 'Portugal', 'lisbonne': 'Portugal', 'lisboa': 'Portugal',
    # Greece
    'grèce': 'Greece', 'greece': 'Greece', 'griechenland': 'Greece',
    'athènes': 'Greece', 'athens': 'Greece',
    'corfou': 'Greece', 'corfu': 'Greece', 'crète': 'Greece', 'crete': 'Greece',
    'rhodes': 'Greece', 'patras': 'Greece', 'pirée': 'Greece',
    # Turkey
    'turquie': 'Turkey', 'turkey': 'Turkey', 'turkije': 'Turkey',
    'constantinople': 'Turkey', 'istanbul': 'Turkey',
    'smyrne': 'Turkey', 'izmir': 'Turkey',
    # Egypt
    'egypte': 'Egypt', 'egypt': 'Egypt', 'égypte': 'Egypt', 'ägypten': 'Egypt',
    'le caire': 'Egypt', 'cairo': 'Egypt',
    'alexandrie': 'Egypt', 'alexandria': 'Egypt', 'suez': 'Egypt',
    # Palestine / Holy Land
    'palestine': 'Palestine', 'palestina': 'Palestine',
    'jérusalem': 'Palestine', 'jerusalem': 'Palestine',
    'bethléem': 'Palestine', 'bethlehem': 'Palestine',
    'nazareth': 'Palestine', 'jaffa': 'Palestine', 'acre': 'Palestine',
    'terre sainte': 'Palestine', 'holy land': 'Palestine',
    # Syria / Lebanon
    'syrie': 'Syria', 'syria': 'Syria', 'syrië': 'Syria',
    'damas': 'Syria', 'damascus': 'Syria', 'alep': 'Syria', 'aleppo': 'Syria',
    'liban': 'Lebanon', 'lebanon': 'Lebanon',
    'beyrouth': 'Lebanon', 'beirut': 'Lebanon', 'sidon': 'Lebanon',
    # North Africa
    'algérie': 'Algeria', 'alger': 'Algeria', 'algeria': 'Algeria',
    'tunisie': 'Tunisia', 'tunis': 'Tunisia', 'tunisia': 'Tunisia',
    'maroc': 'Morocco', 'morocco': 'Morocco', 'tanger': 'Morocco',
    'libye': 'Libya', 'libya': 'Libya',
    # Islands
    'chypre': 'Cyprus', 'cyprus': 'Cyprus',
    'malte': 'Malta', 'malta': 'Malta',
    # Croatia
    'croatie': 'Croatia', 'dalmatie': 'Croatia', 'raguse': 'Croatia', 'dubrovnik': 'Croatia',
    # Non-Mediterranean (for full route context)
    'angleterre': 'England', 'england': 'England', 'londres': 'England', 'london': 'England',
    'belgique': 'Belgium', 'belgium': 'Belgium', 'bruxelles': 'Belgium', 'anvers': 'Belgium',
    'hollande': 'Netherlands', 'amsterdam': 'Netherlands', 'rotterdam': 'Netherlands',
    'allemagne': 'Germany', 'deutschland': 'Germany',
    'autriche': 'Austria', 'vienne': 'Austria', 'wien': 'Austria',
    'russie': 'Russia', 'russia': 'Russia', 'moscou': 'Russia',
    'perse': 'Persia', 'persia': 'Persia',
    'inde': 'India', 'india': 'India',
    'chine': 'China', 'china': 'China',
}

MEDITERRANEAN_COUNTRIES = {
    'France', 'Italy', 'Spain', 'Portugal', 'Greece', 'Turkey',
    'Egypt', 'Palestine', 'Syria', 'Lebanon', 'Algeria', 'Tunisia',
    'Morocco', 'Libya', 'Cyprus', 'Malta', 'Croatia'
}

SEA_KEYWORDS = [
    "sea", "seas", "ocean", "oceans",
    "mer", "mers", "océan", "océans",
    "zee", "zeeën", "oceaan", "oceanen",
    "meer", "meere", "see", "seen", "ozean", "ozeane",
    "mar", "mares", "oceano", "oceanos",
    "mare", "maria", "gurges", "oceanus"
]

VOYAGE_KEYWORDS = [
    "voyage", "voyages", "journey", "journeys",
    "trip", "trips", "travel", "travels", "sailing", "cruise",
    "traversée", "traversees", "navigation", "navigations",
    "reis", "reizen", "tocht", "tochten",
    "reise", "reisen", "fahrt", "fahrten", "seereise",
    "viaje", "viajes", "travesia",
    "viagem", "viagens",
    "navigatio", "iter", "itinera", "expeditio"
]

MED_KEYWORDS = [
    "mediterranean", "méditerranée", "mediterranee",
    "mediterráneo", "mediterrâneo", "mediterraneo",
    "mittelmeer", "middellandse zee", "middellandse",
    "mare nostrum", "mare internum", "mediterraneum"
]


# ============================================================
# STEP 1: Load metadata + filter Mediterranean books
# ============================================================
def step1_filter_books():
    print("=" * 60)
    print("STEP 1: Loading metadata and filtering Mediterranean books")
    print("=" * 60)

    import pandas as pd

    # Load metadata
    meta = pd.read_csv(METADATA_CSV, sep=';', encoding='latin-1')
    print(f"  Metadata loaded: {len(meta)} books, {meta.shape[1]} columns")

    # Load dataset_9 for IE folder mapping
    ie_mapping = {}
    if os.path.exists(DATASET9_XLSX):
        try:
            ds9 = pd.read_excel(DATASET9_XLSX)
            print(f"  dataset_9.xlsx loaded: {len(ds9)} rows")
            # Build IE → MMS mapping
            for _, row in ds9.iterrows():
                ie = str(row.get('IE PID', '')).strip()
                mms = str(row.get('MMS ID', '')).strip()
                if ie and mms and ie.startswith('IE'):
                    ie_mapping[mms] = ie_mapping.get(mms, [])
                    if ie not in ie_mapping[mms]:
                        ie_mapping[mms].append(ie)
        except Exception as e:
            print(f"  Warning: Could not load dataset_9.xlsx: {e}")

    # Filter Mediterranean books
    def is_mediterranean(row):
        subject = str(row.get('Subject', '')).lower()
        title = str(row.get('Main title', '')).lower()
        combined = subject + ' ' + title
        if any(t.lower() in combined for t in include_terms):
            if not any(t.lower() in combined for t in exclude_terms):
                return True
        return False

    med_mask = meta.apply(is_mediterranean, axis=1)
    med_books = meta[med_mask].copy()
    print(f"  Mediterranean books: {len(med_books)}")

    # Find IE folders for each book
    med_books['ie_folders'] = ''
    for idx, row in med_books.iterrows():
        mms = str(row.get('MMS ID', '')).strip()
        ies = ie_mapping.get(mms, [])
        if not ies:
            # Try to find from directory listing
            for entry in os.listdir(TRAVELOGUES_DIR):
                if entry.startswith('IE') and os.path.isdir(os.path.join(TRAVELOGUES_DIR, entry)):
                    manifest = os.path.join(TRAVELOGUES_DIR, entry, 'manifest.json')
                    if os.path.exists(manifest):
                        try:
                            with open(manifest, 'r') as f:
                                m = json.load(f)
                            if str(m.get('mms_id', '')) == mms:
                                ies.append(entry)
                        except:
                            pass
        med_books.at[idx, 'ie_folders'] = '|'.join(ies)

    matched = med_books[med_books['ie_folders'] != ''].shape[0]
    print(f"  Books with IE folders: {matched}")

    # Save filtered list
    out_file = os.path.join(OUTPUT_DIR, 'mediterranean_books.csv')
    cols = ['MMS ID', 'Main title', 'Subject', 'Place of publication',
            'Date 1', 'Language original', 'ie_folders']
    save_cols = [c for c in cols if c in med_books.columns]
    med_books[save_cols].to_csv(out_file, index=False, encoding='utf-8')
    print(f"  Saved: {out_file}")

    return med_books


# ============================================================
# STEP 2: CLIP classification with updated prompts
# ============================================================
def step2_clip_classification(med_books):
    print("\n" + "=" * 60)
    print("STEP 2: CLIP classification with updated prompts")
    print("=" * 60)

    import torch
    import open_clip
    from PIL import Image

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"  Device: {device}")

    # Load model
    model, _, preprocess = open_clip.create_model_and_transforms(
        'ViT-B-32', pretrained='laion2b_s34b_b79k'
    )
    tokenizer = open_clip.get_tokenizer('ViT-B-32')
    model = model.to(device).eval()
    print(f"  Model loaded: ViT-B-32 (laion2b)")

    # Encode prompts
    class_labels = list(CLASSIFICATION_PROMPTS.keys())
    class_prompts = list(CLASSIFICATION_PROMPTS.values())

    with torch.no_grad():
        text_tokens = tokenizer(class_prompts).to(device)
        class_text_emb = model.encode_text(text_tokens)
        class_text_emb = class_text_emb / class_text_emb.norm(dim=-1, keepdim=True)
        class_text_emb_np = class_text_emb.cpu().numpy()

    print(f"  Encoded {len(class_labels)} classification prompts")
    for label, prompt in CLASSIFICATION_PROMPTS.items():
        print(f"    {label:20s}: {prompt}")

    # Collect all image paths
    all_images = []
    for _, row in med_books.iterrows():
        ie_folders = str(row.get('ie_folders', '')).split('|')
        mms_id = str(row.get('MMS ID', '')).strip()
        title = str(row.get('Main title', '')).strip()[:80]
        dest = str(row.get('Subject', '')).strip()[:40]

        for ie in ie_folders:
            ie = ie.strip()
            if not ie:
                continue
            # Find image files (jpg in REP folders)
            rep_dirs = glob.glob(os.path.join(TRAVELOGUES_DIR, ie, 'REP*'))
            for rep_dir in rep_dirs:
                for img_file in sorted(glob.glob(os.path.join(rep_dir, '*.jpg'))):
                    # Extract page number
                    basename = os.path.basename(img_file)
                    page_match = re.search(r'_(\d{8})\.jpg$', basename)
                    page_num = int(page_match.group(1)) if page_match else 0
                    label = f"({page_num:04d})"

                    all_images.append({
                        'image_path': os.path.relpath(img_file, TRAVELOGUES_DIR),
                        'full_path': img_file,
                        'IE_PID': ie,
                        'MMS_ID': mms_id,
                        'LABEL': label,
                        'destination': dest,
                        'book_title': title,
                        'page': page_num,
                    })

    print(f"\n  Total images to process: {len(all_images)}")

    # --- CHECKPOINT SUPPORT ---
    # Load existing results if resuming from a previous run
    checkpoint_file = os.path.join(OUTPUT_DIR, 'classifications_checkpoint.csv')
    processed_paths = set()
    results = []
    embeddings = []

    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(row)
                results[-1]['confidence'] = float(row['confidence'])
                results[-1]['page'] = int(row['page'])
                processed_paths.add(row['image_path'])
        print(f"  Resuming from checkpoint: {len(results)} images already processed")

    # Filter out already-processed images
    remaining_images = [img for img in all_images if img['image_path'] not in processed_paths]
    print(f"  Remaining to process: {len(remaining_images)}")

    if len(remaining_images) == 0:
        print("  All images already processed!")
    else:
        # Process in batches
        processed = 0
        missing = 0
        SAVE_EVERY = 50  # save checkpoint every 50 batches

        for batch_idx, batch_start in enumerate(tqdm(range(0, len(remaining_images), BATCH_SIZE), desc="  Processing")):
            batch = remaining_images[batch_start:batch_start + BATCH_SIZE]
            batch_tensors = []
            batch_valid = []

            for item in batch:
                try:
                    img = Image.open(item['full_path']).convert('RGB')
                    img_tensor = preprocess(img).unsqueeze(0)
                    batch_tensors.append(img_tensor)
                    batch_valid.append(item)
                except Exception:
                    missing += 1
                    continue

            if not batch_tensors:
                continue

            batch_tensor = torch.cat(batch_tensors).to(device)

            with torch.no_grad():
                emb = model.encode_image(batch_tensor)
                emb = emb / emb.norm(dim=-1, keepdim=True)
                emb_np = emb.cpu().numpy()

            sims = emb_np @ class_text_emb_np.T

            for i, item in enumerate(batch_valid):
                top_idx = sims[i].argmax()
                top_label = class_labels[top_idx]
                top_conf = float(sims[i].max())
                top3_idx = sims[i].argsort()[-3:][::-1]
                top3 = ';'.join(class_labels[j] for j in top3_idx)

                results.append({
                    'image_path': item['image_path'],
                    'IE_PID': item['IE_PID'],
                    'MMS_ID': item['MMS_ID'],
                    'LABEL': item['LABEL'],
                    'destination': item['destination'],
                    'book_title': item['book_title'],
                    'predicted_type': top_label,
                    'confidence': top_conf,
                    'top3': top3,
                    'page': item['page'],
                })
                embeddings.append(emb_np[i])
                processed += 1

            # Save checkpoint every SAVE_EVERY batches
            if (batch_idx + 1) % SAVE_EVERY == 0:
                with open(checkpoint_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)
                print(f"\n  Checkpoint saved: {len(results)} results so far")

        print(f"\n  Processed: {processed} new images")
        print(f"  Missing/failed: {missing}")

    # Save final classifications
    cls_file = os.path.join(OUTPUT_DIR, 'classifications.csv')
    with open(cls_file, 'w', newline='', encoding='utf-8') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    print(f"  Saved: {cls_file} ({len(results)} rows)")

    # Clean up checkpoint file after successful completion
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)
        print(f"  Checkpoint file removed (completed successfully)")

    # Save embeddings
    if embeddings:
        emb_file = os.path.join(OUTPUT_DIR, 'embeddings.npz')
        np.savez_compressed(emb_file, embeddings=np.array(embeddings))
        print(f"  Saved: {emb_file} ({np.array(embeddings).shape})")

    # Print distribution
    print(f"\n  Classification distribution:")
    from collections import Counter
    dist = Counter(r['predicted_type'] for r in results)
    for label, count in dist.most_common():
        pct = 100 * count / len(results) if results else 0
        bar = '#' * int(pct / 2)
        print(f"    {label:20s}: {count:6d} ({pct:5.1f}%) {bar}")

    # Maritime stats
    maritime_types = {'harbour', 'seascape', 'ship', 'coastal_city', 'nautical_chart'}
    maritime = sum(1 for r in results if r['predicted_type'] in maritime_types)
    non_text = sum(1 for r in results if r['predicted_type'] != 'text_page')
    print(f"\n  Maritime illustrations: {maritime} ({100*maritime/len(results):.1f}%)" if results else "")
    print(f"  Total illustrations (non-text): {non_text} ({100*non_text/len(results):.1f}%)" if results else "")

    return results


# ============================================================
# STEP 3: Extract travel routes from OCR (IMPROVED)
#   - Frequency-based: place must appear on 3+ pages to count
#   - Cluster detection: finds densest mention range per place
#   - Arrival = start of densest cluster, not first mention
# ============================================================
def step3_extract_routes(med_books):
    print("\n" + "=" * 60)
    print("STEP 3: Extracting travel routes from OCR (frequency-based)")
    print("=" * 60)

    # Compile patterns
    place_patterns = {v: c for v, c in MEDITERRANEAN_PLACES.items() if len(v) >= 4}
    sea_re = re.compile(r'\b(' + '|'.join(re.escape(k) for k in SEA_KEYWORDS) + r')\b', re.IGNORECASE)
    voyage_re = re.compile(r'\b(' + '|'.join(re.escape(k) for k in VOYAGE_KEYWORDS) + r')\b', re.IGNORECASE)
    med_re = re.compile(r'\b(' + '|'.join(re.escape(k) for k in MED_KEYWORDS) + r')\b', re.IGNORECASE)

    MIN_MENTIONS = 3  # place must appear on 3+ pages to count as real visit

    all_routes = []
    books_processed = 0

    for _, row in tqdm(med_books.iterrows(), total=len(med_books), desc="  Extracting routes"):
        ie_folders = str(row.get('ie_folders', '')).split('|')
        mms_id = str(row.get('MMS ID', '')).strip()
        title = str(row.get('Main title', '')).strip()
        lang = str(row.get('Language original', '')).strip()
        date = str(row.get('Date 1', '')).strip()

        for ie in ie_folders:
            ie = ie.strip()
            if not ie:
                continue

            ocr_dir = os.path.join(TRAVELOGUES_DIR, ie, 'OCR')
            if not os.path.exists(ocr_dir):
                continue

            ocr_files = sorted(glob.glob(os.path.join(ocr_dir, '*.txt')))
            if not ocr_files:
                continue

            # Pass 1: collect ALL mentions of each place across all pages
            place_pages = {}  # canonical → [page_nums]
            sea_pages = 0
            voyage_pages = 0
            med_pages = 0

            for ocr_file in ocr_files:
                basename = os.path.basename(ocr_file).replace('.txt', '')
                try:
                    page_num = int(basename)
                except ValueError:
                    continue
                try:
                    with open(ocr_file, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                except:
                    continue
                if not text.strip():
                    continue
                text_lower = text.lower()

                for variant, canonical in place_patterns.items():
                    if variant in text_lower:
                        if canonical not in place_pages:
                            place_pages[canonical] = []
                        if page_num not in place_pages[canonical]:
                            place_pages[canonical].append(page_num)

                if sea_re.search(text_lower):
                    sea_pages += 1
                if voyage_re.search(text_lower):
                    voyage_pages += 1
                if med_re.search(text_lower):
                    med_pages += 1

            # Pass 2: find arrival page via densest cluster
            route = []
            for canonical, pages in place_pages.items():
                pages.sort()
                if len(pages) < MIN_MENTIONS:
                    if len(pages) < 2:
                        continue  # skip single mentions (passing reference)

                # Sliding window: find 20-page window with most mentions
                best_start = pages[0]
                best_count = 0
                for p in pages:
                    count = sum(1 for pp in pages if p <= pp <= p + 20)
                    if count > best_count:
                        best_count = count
                        best_start = p

                # Arrival = first page in densest cluster
                cluster = [p for p in pages if best_start <= p <= best_start + 20]
                arrival = min(cluster) if cluster else pages[0]

                route.append({
                    'page': arrival,
                    'place': canonical,
                    'is_mediterranean': canonical in MEDITERRANEAN_COUNTRIES,
                    'total_mentions': len(pages),
                    'page_range': f"{min(pages)}-{max(pages)}",
                    'matched_term': next((v for v, c in place_patterns.items() if c == canonical), ''),
                })

            route.sort(key=lambda x: x['page'])

            if route:
                books_processed += 1
                med_places = [r for r in route if r['is_mediterranean']]
                full_route_str = ' → '.join(r['place'] for r in route)
                med_segment_str = ' → '.join(r['place'] for r in med_places)

                all_routes.append({
                    'ie_folder': ie,
                    'mms_id': mms_id,
                    'title': title,
                    'language': lang,
                    'date': date,
                    'total_ocr_pages': len(ocr_files),
                    'origin': route[0]['place'],
                    'destination': route[-1]['place'],
                    'full_route': full_route_str,
                    'med_segment': med_segment_str,
                    'num_stops': len(route),
                    'num_med_stops': len(med_places),
                    'sea_pages': sea_pages,
                    'voyage_pages': voyage_pages,
                    'med_keyword_pages': med_pages,
                    'route_detail': json.dumps(route),
                })

    print(f"  Books with routes: {books_processed}")
    print(f"  Total routes: {len(all_routes)}")

    # Save routes
    routes_file = os.path.join(OUTPUT_DIR, 'routes.csv')
    with open(routes_file, 'w', newline='', encoding='utf-8') as f:
        if all_routes:
            writer = csv.DictWriter(f, fieldnames=all_routes[0].keys())
            writer.writeheader()
            writer.writerows(all_routes)
    print(f"  Saved: {routes_file}")

    # Print top routes
    if all_routes:
        print(f"\n  Top routes by Mediterranean stops:")
        sorted_routes = sorted(all_routes, key=lambda x: x['num_med_stops'], reverse=True)
        for r in sorted_routes[:10]:
            print(f"    {r['title'][:55]:55s} | {r['origin']} → ... → {r['destination']}")
            print(f"      Med: [{r['med_segment'][:70]}]")
            print(f"      {r['num_stops']} stops, {r['num_med_stops']} Med, {r['sea_pages']} sea pages, {r['med_keyword_pages']} med pages")

    return all_routes


# ============================================================
# STEP 4: Match illustrations to route locations (IMPROVED)
#   - Only match if illustration is within ±PAGE_WINDOW pages
#     of a route stop's arrival page
#   - Unmatched illustrations are discarded (not forced to
#     the nearest stop 50 pages away)
# ============================================================
PAGE_WINDOW = 3  # illustration must be within ±3 pages of a stop

def step4_match_illustrations(all_routes, clip_results):
    print("\n" + "=" * 60)
    print(f"STEP 4: Matching illustrations to route (±{PAGE_WINDOW} page window)")
    print("=" * 60)

    illustrations_by_ie = {}
    for r in clip_results:
        if r['predicted_type'] != 'text_page':
            ie = r['IE_PID']
            if ie not in illustrations_by_ie:
                illustrations_by_ie[ie] = []
            illustrations_by_ie[ie].append(r)

    all_matched = []
    unmatched = 0

    for route_info in all_routes:
        ie = route_info['ie_folder']
        route = json.loads(route_info['route_detail'])
        book_illusts = illustrations_by_ie.get(ie, [])

        for illust in book_illusts:
            illust_page = illust['page']

            # Find the closest stop WITHIN the page window
            best_stop = None
            best_dist = float('inf')

            for stop in route:
                dist = abs(stop['page'] - illust_page)
                if dist <= PAGE_WINDOW and dist < best_dist:
                    best_dist = dist
                    best_stop = stop

            if best_stop is None:
                unmatched += 1
                continue  # skip — no stop close enough

            all_matched.append({
                'ie_folder': ie,
                'mms_id': route_info['mms_id'],
                'book_title': route_info['title'],
                'image_path': illust['image_path'],
                'page': illust_page,
                'illustration_type': illust['predicted_type'],
                'confidence': illust['confidence'],
                'nearest_place': best_stop['place'],
                'nearest_place_page': best_stop['page'],
                'page_distance': best_dist,
                'is_med_location': best_stop['is_mediterranean'],
                'full_route': route_info['full_route'],
                'med_segment': route_info['med_segment'],
            })

    # Save
    out_file = os.path.join(OUTPUT_DIR, 'route_illustrations.csv')
    with open(out_file, 'w', newline='', encoding='utf-8') as f:
        if all_matched:
            writer = csv.DictWriter(f, fieldnames=all_matched[0].keys())
            writer.writeheader()
            writer.writerows(all_matched)

    med_matched = [m for m in all_matched if m['is_med_location']]
    print(f"  Matched illustrations: {len(all_matched)} (within ±{PAGE_WINDOW} pages)")
    print(f"  Unmatched (too far from any stop): {unmatched}")
    print(f"  Mediterranean illustrations: {len(med_matched)}")
    print(f"  Total matched illustrations: {len(all_matched)}")
    print(f"  Mediterranean illustrations: {len(med_matched)}")
    print(f"  Saved: {out_file}")

    # Stats by type
    from collections import Counter
    type_dist = Counter(m['illustration_type'] for m in med_matched)
    if type_dist:
        print(f"\n  Mediterranean illustration types:")
        for t, c in type_dist.most_common():
            print(f"    {t:20s}: {c}")

    return all_matched


# ============================================================
# MAIN
# ============================================================
def main():
    import sys
    skip_clip = '--skip-clip' in sys.argv

    # Step 1
    med_books = step1_filter_books()

    # Step 2: CLIP
    if skip_clip:
        print("\n" + "=" * 60)
        print("STEP 2: SKIPPED (--skip-clip) — loading existing classifications")
        print("=" * 60)
        cls_file = os.path.join(OUTPUT_DIR, 'classifications.csv')
        if not os.path.exists(cls_file):
            print(f"  ERROR: {cls_file} not found! Run without --skip-clip first.")
            return
        clip_results = []
        with open(cls_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['confidence'] = float(row['confidence'])
                row['page'] = int(row['page'])
                clip_results.append(row)
        print(f"  Loaded {len(clip_results)} existing classifications")
    else:
        clip_results = step2_clip_classification(med_books)

    # Step 3: Route extraction from OCR
    all_routes = step3_extract_routes(med_books)

    # Step 4: Match illustrations to routes
    all_matched = step4_match_illustrations(all_routes, clip_results)

    # Summary
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"  Mediterranean books: {len(med_books)}")
    print(f"  CLIP classifications: {len(clip_results)}")
    print(f"  Travel routes: {len(all_routes)}")
    print(f"  Matched illustrations: {len(all_matched)}")
    print(f"\n  Results in: {OUTPUT_DIR}/")
    print(f"    mediterranean_books.csv")
    print(f"    classifications.csv")
    print(f"    routes.csv")
    print(f"    route_illustrations.csv")


if __name__ == '__main__':
    main()
