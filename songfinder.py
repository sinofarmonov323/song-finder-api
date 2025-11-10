import base64
import glob
import json
import os
import random
import subprocess
import  urllib.request
import string
import json
import re
from pytubefix import YouTube
import acoustid


def get_fingerprint(file_path):
    result = subprocess.run(
        ["fpcalc", "-json", file_path],
        capture_output=True,
        text=True
    )
    info = json.loads(result.stdout)
    return info["duration"], info["fingerprint"]

def recognize_song(file_path, api_key="UxTSsZdw0n"):
    duration, fingerprint = get_fingerprint(file_path)
    result = acoustid.lookup(api_key, fingerprint, duration)
    return json.dumps(result, indent=2)

def YouTubeSearch(query: str, limit: int = 10):
    query = query.replace(" ", "+")
    
    useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'
    
    request = urllib.request.Request(
        f"https://www.youtube.com/results?search_query={query}", 
        headers={"User-Agent": useragent}
    )
    response = urllib.request.urlopen(request).read().decode('utf-8')
    
    match = re.search(r'ytInitialData\s*=\s*(\{.*?\});', response, re.DOTALL)
    if not match:
        return "No data found"

    data = json.loads(match.group(1))

    results = []
    try:
        with open("data.json", "w") as file:
            file.write(json.dumps(data, indent=4))
        videos = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
        for item in videos:
            if "videoRenderer" in item:
                video = item["videoRenderer"]
                video_id = video["videoId"]
                title = video["title"]["runs"][0]["text"]
                thumbnails = video["thumbnail"]["thumbnails"]
                url = f"https://www.youtube.com/watch?v={video_id}"
                results.append({
                    "title": title,
                    "video_id": video_id,
                    "thumbnails": thumbnails,
                    "url": url
                })
                
                if len(results) >= limit:
                    break
    except KeyError:
        return "Failed to extract data"

    return results

def potoken_verifier():
    # return "MnhJnyVREeZ2h0mj6K04mggCubxK9Q9zz484x4eaFctWqjCRbJYWz6xCNoDdi4KpSRPte_NLsp8EEt-niT9oAz6gP_jQfataDuvOtzTn89sYf8H2AzRv2SxnDABa95ni5-VoGUBg2vkaE3VampurFPuDrXwN1dZDrSA=", "CgtSTXlNakx1d0lFdyi1tOHEBjIKCgJVWhIEGgAgMw"
    return ("MnhYSvTvSyeQuVh274Jt9825zFH3rvlIMIS5Bo2i7EjuMz-LEV88wZhj8ovxSMTOxF6Zl9uK4bIaMMjfJl73KJU8S1RbNms5NSGNDz7jVZHc7hlBxvIB3pcqVgBSSZ0Cv2mJsHO9LgjY60Nvo3L9COYnGPDHwwQsIKQ=", "Cgs0bUVxVmlqdGp5byjGvOHEBjIKCgJVWhIEGgAgOQ%3D%3D")

def GetSongSubtitles(url: str):
    yt = YouTube(url)
    return [{caption.code: caption.generate_txt_captions()} for caption in yt.captions]

def GetSongClip(url: str):
    data = YouTube(url).streams.get_highest_resolution()
    return {"url": data.url, "type": data.mime_type}

def generate_token(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def YouTubeSongDownloader(url: str):
    yt = YouTube(url)
    data = yt.streams.get_audio_only(subtype="mp3") or yt.streams.get_audio_only()
    return {'path': data.download(), "type": data.mime_type}

def encryptor(word: str):
    return "".join([str(ord(w)).zfill(3)[::-1] for w in word])

def decryptor(encrypted: str):
    return ''.join(
        chr(int(encrypted[i:i+3][::-1]))
        for i in range(0, len(encrypted), 3)
    )

def  base64_encoder(word: str):
    return base64.b64encode(base64.b64encode(word.encode())).decode()

def base64_decoder(encoded: str):
    return base64.b64decode(base64.b64decode(encoded)).decode()

def delete_m4a_files():
    files = glob.glob("*m4a")
    for file in files:
        os.remove(file)

# def YouTubeSearch(query: str, limit: int = 10):
#     query = query.replace(" ", "+")
    
#     useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'
    
#     request = urllib.request.Request(
#         f"https://www.youtube.com/results?search_query={query}", 
#         headers={"User-Agent": useragent}
#     )
#     response = urllib.request.urlopen(request).read().decode('utf-8')
#     match = re.search(r'ytInitialData\s*=\s*(\{.*?\});', response, re.DOTALL)
#     if not match:
#         return "No data found"

#     data = json.loads(match.group(1))

#     results = []
#     try:
#         videos = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
#         for item in videos:
#             if "videoRenderer" in item:
#                 video = item["videoRenderer"]
#                 video_id = video["videoId"]
#                 title = video["title"]["runs"][0]["text"]
#                 thumbnails = video["thumbnail"]["thumbnails"]
#                 url = f"https://www.youtube.com/watch?v={video_id}"
#                 results.append({
#                     "title": title,
#                     "video_id": video_id,
#                     "thumbnails": thumbnails,
#                     "url": url
#                 })
                
#                 if len(results) >= limit:
#                     break
#     except KeyError:
#         return "Failed to extract data"
#     return results

# def generate_token(length):
#     return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

# def YouTubeSongDownloader(url: str):
#     yt = YouTube(url)
#     data = yt.streams.get_audio_only(subtype="webm")
#     return {'path': data.download(), "type": data.mime_type}

# def encryptor(word: str):
#     return "".join([str(ord(w)).zfill(3)[::-1] for w in word])

# def decryptor(encrypted: str):
#     return ''.join(
#         chr(int(encrypted[i:i+3][::-1]))
#         for i in range(0, len(encrypted), 3)
#     )

# def  base64_encoder(word: str):
#     return base64.b64encode(base64.b64encode(word.encode())).decode()

# def base64_decoder(encoded: str):
#     return base64.b64decode(base64.b64decode(encoded)).decode()

# def delete_m4a_files():
#     files = glob.glob("*m4a")
#     for file in files:
#         os.remove(file)

# print(generate_token(50))

# print(YouTubeSearch("Egzod & Maestro Chives feat. Neoni - Royalty"))
print(YouTubeSongDownloader("https://youtu.be/s7-GTShjcqY?si=N2uPKEVcJFdesWbU"))
