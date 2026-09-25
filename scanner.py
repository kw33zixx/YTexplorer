import asyncio
import yt_dlp
from datetime import datetime

def format_duration(seconds):
    if not seconds:
        return "0:00"
    seconds = int(seconds)
    mins = seconds // 60
    secs = seconds % 60
    hours = mins // 60
    mins = mins % 60
    if hours > 0:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"

def format_date(date_str):
    if not date_str or len(str(date_str)) != 8:
        return ""
    try:
        d = datetime.strptime(str(date_str), "%Y%m%d")
        return d.strftime("%d.%m.%Y")
    except Exception:
        return str(date_str)

def run_search(query: str, max_views: int = 50, fetch_limit: int = 15) -> list:
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'socket_timeout': 10,
    }

    results = []
    search_target = f"ytsearch{fetch_limit}:{query}"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(search_target, download=False)
        except Exception as e:
            print(f"yt-dlp search error: {e}")
            return []

    if not info or 'entries' not in info:
        return []

    for entry in info['entries']:
        if not entry:
            continue

        video_id = entry.get('id')
        if not video_id:
            continue

        raw_views = entry.get('view_count')
        views = raw_views if raw_views is not None else 0

        if max_views != -1 and views > max_views:
            continue

        duration_sec = entry.get('duration')
        upload_date = format_date(entry.get('upload_date'))
        
        thumbnails = entry.get('thumbnails') or []
        thumbnail_url = thumbnails[-1].get('url') if thumbnails else f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

        results.append({
            "id": video_id,
            "title": entry.get('title') or "Без названия",
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "embed_url": f"https://www.youtube-nocookie.com/embed/{video_id}?autoplay=1",
            "uploader": entry.get('uploader') or entry.get('channel') or "unknown",
            "channel_url": entry.get('uploader_url') or entry.get('channel_url') or "",
            "views": views,
            "duration": format_duration(duration_sec),
            "duration_sec": duration_sec or 0,
            "upload_date": upload_date,
            "thumbnail": thumbnail_url,
            "matched_query": query
        })

    return results

async def search_async(query: str, max_views: int = 50, fetch_limit: int = 15) -> list:
    return await asyncio.to_thread(run_search, query, max_views, fetch_limit)

if __name__ == "__main__":
    test_q = '"IMG 3912"'
    print(f"{test_q}")
    res = run_search(test_q, max_views=100, fetch_limit=5)
    print(f"results {len(res)}")
    for r in res:
        print(f"{r['title']} {r['views']} https://youtu.be/{r['id']}")
