from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import re
import json
import os

app = FastAPI(title="Instagram Downloader API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Instagram Downloader API", "status": "active", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {"status": "running", "timestamp": "2024"}

def extract_video_url(html_content):
    """Extract video URL from Instagram HTML"""
    try:
        # Method 1: Find JSON data in script tags
        script_pattern = r'window\._sharedData\s*=\s*({.+?});'
        match = re.search(script_pattern, html_content)
        
        if match:
            json_data = json.loads(match.group(1))
            
            # Navigate to video URL
            try:
                post_data = json_data['entry_data']['PostPage'][0]['graphql']['shortcode_media']
                if post_data['is_video']:
                    return post_data['video_url']
            except:
                pass
        
        # Method 2: Find additional JSON data
        script_pattern_2 = r'{"config":{"viewer".*?}</script>'
        matches = re.findall(script_pattern_2, html_content)
        
        for match in matches:
            try:
                data = json.loads(match)
                # Try different JSON structures
                if 'entry_data' in data:
                    post_data = data['entry_data']['PostPage'][0]['graphql']['shortcode_media']
                    if post_data['is_video']:
                        return post_data['video_url']
            except:
                continue
        
        # Method 3: Direct video URL search
        video_pattern = r'"video_url":"([^"]+)"'
        video_matches = re.findall(video_pattern, html_content)
        if video_matches:
            return video_matches[0].replace('\\u0026', '&')
            
        return None
        
    except Exception as e:
        print(f"Extraction error: {e}")
        return None

@app.get("/api/download")
async def download_instagram(url: str):
    """
    Download Instagram Reel
    Example: /api/download?url=https://www.instagram.com/reel/ABC123/
    """
    try:
        if not url:
            raise HTTPException(status_code=400, detail="URL parameter is required")
        
        # Validate Instagram URL
        if "instagram.com/reel/" not in url and "instagram.com/p/" not in url:
            raise HTTPException(status_code=400, detail="Invalid Instagram URL. Only reels and posts supported.")
        
        print(f"Processing URL: {url}")
        
        # Headers to mimic browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Fetch Instagram page
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch Instagram page")
        
        # Extract video URL
        video_url = extract_video_url(response.text)
        
        if video_url:
            return {
                "success": True,
                "type": "reel",
                "video_url": video_url,
                "download_url": video_url,
                "message": "Right-click the video_url and select 'Save as' to download"
            }
        else:
            raise HTTPException(status_code=404, detail="Video not found. The post might be private or not a video.")
            
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="Request timeout")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Network error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/api/profile/{username}")
async def get_profile_pic(username: str):
    """Get Instagram profile picture"""
    try:
        profile_url = f"https://www.instagram.com/{username}/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(profile_url, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Extract profile picture URL
        html_content = response.text
        pic_pattern = r'"profile_pic_url_hd":"([^"]+)"'
        matches = re.findall(pic_pattern, html_content)
        
        if matches:
            profile_pic = matches[0].replace('\\u0026', '&')
            return {
                "success": True,
                "username": username,
                "profile_pic_url": profile_pic
            }
        else:
            raise HTTPException(status_code=404, detail="Profile picture not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Simple test endpoint
@app.get("/api/test")
async def test_endpoint():
    return {
        "message": "API is working!",
        "endpoints": {
            "reel_download": "/api/download?url=REEL_URL",
            "profile_pic": "/api/profile/USERNAME"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
