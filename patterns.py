import os
import re
import json
import random
import urllib.parse
from datetime import datetime, timedelta

DATASET_PATH = os.path.join(os.path.dirname(__file__), "keywords.json")

try:
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        RAW_PATTERNS = json.load(f)
except Exception:
    RAW_PATTERNS = []

TAG_LABELS = {
    'all': 'any categories',
    'phone': '📱 mobile devices',
    'camera': '📷 cameras',
    'action_drone': '🛹 drones, action cameras',
    'editor': '✂️ video editors',
    'webcam_screen': '🎙️ web cameras, screen recordings',
    'games': '🎮 game recordings',
    'russian': '🇷🇺 russian videos',
    'general': '📦 something'
}

MAP_LABELS = {
    0: 'any period',
    1: 'fresh (~0 views)',
    2: 'pretty old videos (2008–2020)',
    3: 'retro (2006–2009)'
}

def get_stats():
    stats = {
        'total': len(RAW_PATTERNS),
        'by_map': {1: 0, 2: 0, 3: 0},
        'by_tag': {}
    }
    for item in RAW_PATTERNS:
        m = item.get('map', 2)
        stats['by_map'][m] = stats['by_map'].get(m, 0) + 1
        for t in item.get('tags', []):
            stats['by_tag'][t] = stats['by_tag'].get(t, 0) + 1
    return stats

def generate_query(era: int = 0, tag: str = None) -> dict:
    candidates = RAW_PATTERNS
    if era in (1, 2, 3):
        candidates = [p for p in candidates if p.get('map') == era]
        
    if tag and tag != 'all':
        candidates = [p for p in candidates if tag in p.get('tags', [])]
        
    if not candidates:
        candidates = RAW_PATTERNS

    item = random.choice(candidates)
    pattern = item['pattern']
    in_quotes = item.get('in_quotes', False)
    map_num = item.get('map', 2)
    tags = item.get('tags', [])
    raw_str = item.get('raw', '')

    now = datetime.now()
    if map_num == 1:
        rand_date = now - timedelta(days=random.randint(0, 45))
    elif map_num == 2:
        rand_date = datetime(random.randint(2008, 2019), random.randint(1, 12), random.randint(1, 28))
    else:
        rand_date = datetime(random.randint(2005, 2008), random.randint(1, 12), random.randint(1, 28))

    q = pattern
    
    q = q.replace('YYYYMMDD', rand_date.strftime('%Y%m%d'))
    q = q.replace('YYYY MM DD', rand_date.strftime('%Y %m %d'))
    q = q.replace('YYYY', str(rand_date.year))
    q = q.replace('YYMMDD', rand_date.strftime('%y%m%d'))
    q = q.replace('DDMMYYYY', rand_date.strftime('%d%m%Y'))
    q = q.replace('Month DD, YYYY', rand_date.strftime('%B %d, %Y'))
    q = q.replace('Month D, YYYY', rand_date.strftime('%B %d, %Y'))
    q = q.replace('Month YYYY', rand_date.strftime('%B %Y'))

    if 'AAA-FFF' in raw_str:
        hex_val = f"{random.randint(0x1000, 0xFFFF):04X}"
        q = q.replace('4XXX', hex_val)
    if 'MOL0XX' in q:
        hex_val = f"{random.randint(0x00, 0xFF):02X}"
        q = f"MOL0{hex_val}"

    def repl_x(m):
        length = len(m.group(0))
        return f"{random.randint(1, 10**length - 1):0{length}d}"

    q = re.sub(r'X{2,}', repl_x, q)
    q = re.sub(r'\bX\b', str(random.randint(1, 9)), q)
    q = re.sub(r'(?<=[a-zA-Z_])X\b', str(random.randint(1, 9)), q)

    if in_quotes or ' ' in q:
        final_query = f'"{q}"'
    else:
        final_query = q

    sp_param = ""
    if map_num == 1:
        sp_param = "&sp=CAISAhAB"
    elif map_num == 3:
        if 'before:' not in final_query:
            final_query += " before:2008"

    encoded = urllib.parse.quote_plus(final_query)
    yt_url = f"https://www.youtube.com/results?search_query={encoded}{sp_param}"

    return {
        "query": final_query,
        "clean_query": q,
        "youtube_url": yt_url,
        "map": map_num,
        "map_label": MAP_LABELS.get(map_num, 'Map'),
        "tags": tags,
        "tag_labels": [TAG_LABELS.get(t, t) for t in tags],
        "raw_description": raw_str
    }
