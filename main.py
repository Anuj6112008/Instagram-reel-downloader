from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import instaloader
import os

app = FastAPI(
    title="Instagram Downloader API",
    description="Download Instagram reels, stories, and profile pictures",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def home():
    return {"message": "Instagram Downloader API", "status": "active", "docs": "/docs"}

@app.get("/api/download")
async def download_instagram(url: str):
    try:
        if not url:
            raise HTTPException(status_code=400, detail="URL parameter is required")
        
        if "instagram.com/reel/" in url:
            return await download_reel(url)
        elif "instagram.com/p/" in url:
            return await download_post(url)
        else:
            raise HTTPException(status_code=400, detail="Supported: Instagram Reels and Posts")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def download_reel(url):
    try:
        if "/reel/" in url:
            shortcode = url.split("/reel/")[1].split("/")[0]
        elif "/p/" in url:
            shortcode = url.split("/p/")[1].split("/")[0]
        else:
            raise HTTPException(status_code=400, detail="Invalid Instagram URL")
        
        L = instaloader.Instaloader()
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        if not post.is_video:
            raise HTTPException(status_code=400, detail="This post doesn't contain a video")
        
        return {
            "success": True,
            "type": "reel",
            "video_url": post.video_url,
            "thumbnail": post.url,
            "caption": post.caption or "No caption",
            "duration": post.video_duration
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download: {str(e)}")

@app.get("/api/profile/{username}")
async def get_profile(username: str):
    try:
        L = instaloader.Instaloader()
        profile = instaloader.Profile.from_username(L.context, username)
        
        return {
            "success": True,
            "username": username,
            "profile_pic_url": profile.profile_pic_url,
            "followers": profile.followers,
            "following": profile.followees,
            "posts": profile.mediacount,
            "bio": profile.biography
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Profile not found: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
