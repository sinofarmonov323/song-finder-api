# from fastapi import FastAPI, Request
# import requests
# from songfinder import YouTubeSearch, encryptor, decryptor, base64_encoder, base64_decoder, YouTubeSongDownloader, delete_m4a_files
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import FileResponse, JSONResponse, StreamingResponse


import glob
import io
import json
import os
import tempfile
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse, StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from songfinder import (
    YouTubeSearch, encryptor, decryptor, base64_encoder, base64_decoder,
    YouTubeSongDownloader, delete_m4a_files, GetSongSubtitles, GetSongClip, recognize_song
)
from fastapi.templating import Jinja2Templates

app = FastAPI(
    title="SongFinder",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

templates = Jinja2Templates(directory="templates")

users_ip = set()

# Middleware to log IPs
@app.middleware("http")
async def log_ip(request: Request, call_next):
    ip = f"{request.client.host}:{request.client.port}"
    users_ip.add(ip)
    response = await call_next(request)
    return response

# Token verification
def verify_token(token: str):
    return token == "TGnwkZgAfHdAe5oHOPXgF2JyRj4ZKblZBZrbOZVW2abgwrRPXK"

# Homepage
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Count users
@app.get("/users", include_in_schema=False)
async def send_users():
    return JSONResponse(len(users_ip))

# See all users IPs
@app.get("/512448256112", include_in_schema=False)
async def see_users():
    return JSONResponse({"users_ip": list(users_ip)})

# Search songs
@app.get("/search-songs", tags=['Song Finder'])
async def search_from_youtube(query: str = None, token: str = None, limit: int = None, request: Request = None):
    if not all([query, token, limit]):
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="token muddati tugadi")
    
    # Cleanup
    for pattern in ["*.mp4", "*.m4a"]:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
            except:
                pass
    
    datas = YouTubeSearch(query, limit)
    return JSONResponse([{
        "title": data['title'],
        "song_id": encryptor(data['video_id']),
        "images": [f"{request.url.scheme}://{request.url.hostname}/download-image/" +
                   base64_encoder(thumb['url'].removeprefix("https://i.ytimg.com/"))
                   for thumb in data['thumbnails']]
    } for data in datas])

# Download song by ID
@app.get("/download-song-by-id", tags=['Song Finder'])
async def download_songs_by_video_id(id: str = None):
    if not id:
        raise HTTPException(status_code=400, detail="Missing id parameter")
    
    try:
        delete_m4a_files()
    except:
        pass
    
    full_url = f"https://www.youtube.com/watch?v={decryptor(id)}"
    response = requests.get(full_url)
    
    if response.status_code == 200:
        audio = YouTubeSongDownloader(full_url)
        return FileResponse(
            audio['path'],
            media_type=audio['type'],
            filename=f"song.{audio['type'].split('/')[-1]}"
        )
    else:
        raise HTTPException(status_code=404, detail="invalid id")

# Get subtitles
@app.get("/get-subtitles/{id}", tags=['Song Finder'])
async def send_subtitles(id: str):
    url = f"https://www.youtube.com/watch?v={decryptor(id)}"
    response = requests.get(url)
    if response.ok:
        return JSONResponse(GetSongSubtitles(url))
    else:
        raise HTTPException(status_code=response.status_code, detail="Error fetching subtitles")

# Get clip
@app.get("/get-clip/{id}", tags=['Song Finder'])
async def send_clip(id: str):
    url = f"https://www.youtube.com/watch?v={decryptor(id)}"
    response = requests.get(url)
    if response.ok:
        data = GetSongClip(url)
        encoded_url = base64_encoder(base64_encoder(data['url'])[::-1])
        return {"url": f"https://songfinder.alwaysdata.net/download-clip/download/{encoded_url}", "mime_type": data['type']}
    else:
        raise HTTPException(status_code=response.status_code, detail="Error fetching clip")

# Download clip now
@app.post("/download-clip/download/{url}", include_in_schema=False)
async def send_clip_now(url: str):
    rr_url = base64_decoder(base64_decoder(url)[::-1])
    return RedirectResponse(rr_url)

# Download thumbnail
@app.get("/download-image/{thumb}", tags=['Song Finder'])
async def download_thumbnail(thumb: str):
    thumb_url = f"https://i.ytimg.com/{base64_decoder(thumb)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.youtube.com/",
        "Range": "bytes=0-"
    }
    response = requests.get(thumb_url, stream=True, headers=headers)
    if response.status_code == 200:
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        return StreamingResponse(response.iter_content(chunk_size=1024), media_type=content_type)
    else:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

# Recognize song
@app.post("/recognize", tags=['Song Finder'])
async def song_recognizer(audio: UploadFile = File(...)):
    if not audio:
        raise HTTPException(status_code=400, detail="No audio file provided")
    
    suffix = os.path.splitext(audio.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    result = recognize_song(tmp_path)
    os.remove(tmp_path)

    return JSONResponse({'result': json.loads(result)})

# Custom error handlers
@app.exception_handler(404)
async def not_found(request: Request, exc):
    return JSONResponse({"error": "Endpoint not found"}, status_code=404)

@app.exception_handler(500)
async def internal_error(request: Request, exc):
    return JSONResponse({"error": "Internal server error"}, status_code=500)


# app = FastAPI(
#     title="Song Finder API",
#     docs_url="/",
#     redoc_url="/docs",
#     description="admin is [here](https://t.me/jackson_rodger)",
#     summary="API for song finding",
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# users_ip = set()

# try:
#     delete_m4a_files()
# except:
#     pass

# @app.middleware("http")
# async def middleware(request: Request, call_next):
#     ip = request.client.host
#     users_ip.add(ip)
#     response = await call_next(request)
#     return response

# @app.get('/users', include_in_schema=False)
# async def send_users():
#     return len(users_ip)

# def verify_token(token: str):
#     if token == "PBFU1Br5ohd4Fg9CD2kumko6i3ZyzMa2MqEwwvCedQyMfqNUWG":
#         return True
#     return False

# @app.get("/search-songs", tags=['Song Finder API'], name="Song finder API", description="API for song finding", response_class=JSONResponse)
# async def search_from_youtube(query: str, token: str, limit: int):
#     if verify_token(token):
#         datas = YouTubeSearch(query, limit)
#         return [{
#             "title": data['title'],
#             "song_id": encryptor(data['video_id']),
#             "images": ["https://song-finder-api323.vercel.app/download-thumb/" + base64_encoder(thumb['url'].removeprefix("https://i.ytimg.com/")) for thumb in data['thumbnails']],
#             } for data in datas]
#     else:
#         return {"error": "token muddati tugadi"}

# @app.get("/download-songs-by-id", tags=['Song Finder API'], name="song downloader by song id", response_class=StreamingResponse)
# async def download_songs_by_video_id(id: str, request: Request):
#     full_url = f"https://www.youtube.com/watch?v={decryptor(id)}"
#     response = requests.get(full_url)
#     if response.status_code == 200:
#         audio = YouTubeSongDownloader(full_url)
#         return FileResponse(audio['path'], media_type=audio['type'])
#     else:
#         return {"message": "invalid id"}

# @app.get("/download-thumb/{thumb}", tags=['Song Finder API'], name="search songs", include_in_schema=False, response_class=StreamingResponse)
# async def download_thumbnail(thumb: str, request: Request):
#     thumb = f"https://i.ytimg.com/{base64_decoder(thumb)}"
#     print(thumb)
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
#         "Referer": "https://www.youtube.com/",
#         "Range": "bytes=0-"
#     }
#     response = requests.get(thumb, stream=True, headers=headers)
#     ext = request.headers.get("Content-Type", "audio/jpg")
#     return StreamingResponse(
#         response.iter_content(chunk_size=1024),
#         media_type=ext,
#         headers={"Content-Disposition": f'inline; filename="thumbnail.{ext.split("/")[1]}"'}
#     )
