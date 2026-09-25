import os
import random
import tempfile
import yt_dlp
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

import patterns
import scanner

app = FastAPI(
    title="yttrashbin",
    description="explore some forgotten videos or wtvr",
    version="1.0.0"
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "api is running but index file not found"}

@app.get("/api/stats")
async def get_stats():
    return patterns.get_stats()

@app.get("/api/categories")
async def get_categories():
    return {
        "tags": patterns.TAG_LABELS,
        "maps": patterns.MAP_LABELS
    }

@app.get("/api/generate")
async def generate(
    era: int = Query(0, description="(0=all, 1=new, 2=graveyard, 3=retro)"),
    tag: str = Query("all", description="category tag"),
    count: int = Query(1, le=10, description="how many queries to generate")
):
    results = [patterns.generate_query(era=era, tag=tag) for _ in range(count)]
    return {"queries": results}

@app.get("/api/search")
async def search(
    query: str = Query(None, description="custom query to search"),
    era: int = Query(0, description="(0=all, 1=new, 2=graveyard, 3=retro)"),
    tag: str = Query("all", description="category tag"),
    max_views: int = Query(50, description="max views (-1 for no limit)"),
    limit: int = Query(15, ge=1, le=30, description="max results from YouTube")
):
    active_query_meta = None
    if not query:
        active_query_meta = patterns.generate_query(era=era, tag=tag)
        search_query = active_query_meta["query"]
    else:
        search_query = query.strip()

    videos = await scanner.search_async(
        query=search_query,
        max_views=max_views,
        fetch_limit=limit
    )

    return {
        "query": search_query,
        "meta": active_query_meta,
        "count": len(videos),
        "videos": videos
    }

@app.get("/api/roulette")
async def roulette(
    era: int = Query(0),
    tag: str = Query("all"),
    max_views: int = Query(30)
):
    for _ in range(4):
        gen = patterns.generate_query(era=era, tag=tag)
        videos = await scanner.search_async(query=gen["query"], max_views=max_views, fetch_limit=8)
        if videos:
            chosen = random.choice(videos)
            return {
                "success": True,
                "video": chosen,
                "meta": gen
            }
            
    return {
        "success": False,
        "message": "try again"
    }

@app.get("/api/download/{video_id}")
def download_video(
    video_id: str,
    title: str = Query("video")
):
    url = f"https://www.youtube.com/watch?v={video_id}"
    safe_title = ''.join(c for c in title if c.isalnum() or c in ' -_.')[:100] or video_id

    tmp_dir = tempfile.mkdtemp()
    output_path = os.path.join(tmp_dir, f"{safe_title}.%(ext)s")

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            ext = info.get('ext', 'mp4')
            final_path = os.path.join(tmp_dir, f"{safe_title}.{ext}")
    except Exception:
        try:
            os.rmdir(tmp_dir)
        except Exception:
            pass
        return {"error": "download failed"}

    if not os.path.exists(final_path):
        files = os.listdir(tmp_dir)
        if files:
            final_path = os.path.join(tmp_dir, files[0])
        else:
            return {"error": "file not found"}

    def cleanup():
        try:
            for f in os.listdir(tmp_dir):
                os.remove(os.path.join(tmp_dir, f))
            os.rmdir(tmp_dir)
        except Exception:
            pass

    return FileResponse(
        final_path,
        filename=f"{safe_title}.mp4",
        media_type='video/mp4',
        background=BackgroundTask(cleanup)
    )

if __name__ == "__main__":
    import uvicorn
    print("run")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
