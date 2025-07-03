from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from urllib.parse import urlencode
import secrets
from dotenv import load_dotenv
import base64

load_dotenv()

# GitHub OAuth settings
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/auth/github/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "https://yourdomain.com"],  # Add your production frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# In-memory storage for demo (use proper database in production)
user_tokens = {}
auth_states = {}


@app.get("/auth/github")
async def github_auth():
    """Initiate GitHub OAuth flow"""
    state = secrets.token_urlsafe(32)
    auth_states[state] = True

    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": "repo user",  # repo scope for private repos
        "state": state,
        "allow_signup": "true"
    }

    auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    return {"auth_url": auth_url, "state": state}


@app.get("/auth/github/callback")
async def github_callback(code: str, state: str):
    """Handle GitHub OAuth callback"""
    if state not in auth_states:
        raise HTTPException(status_code=400, detail="Invalid state")

    # Exchange code for access token
    token_data = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": GITHUB_REDIRECT_URI,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            data=token_data,
            headers={"Accept": "application/json"}
        )

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token")

        token_info = response.json()
        access_token = token_info.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received")

        # Get user info
        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {access_token}"}
        )

        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")

        user_info = user_response.json()
        user_id = user_info["id"]

        # Store token
        user_tokens[user_id] = {
            "access_token": access_token,
            "user_info": user_info
        }

        # Clean up state
        del auth_states[state]

        # Redirect to frontend with user_id
        return RedirectResponse(f"{FRONTEND_URL}/?user_id={user_id}")


@app.get("/user/{user_id}/repos")
async def get_user_repos(user_id: int):
    """Get user's repositories (including private ones)"""
    if user_id not in user_tokens:
        raise HTTPException(status_code=401, detail="User not authenticated")

    access_token = user_tokens[user_id]["access_token"]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user/repos",
            headers={"Authorization": f"token {access_token}"},
            params={"visibility": "all", "sort": "updated"}
        )

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch repositories")

        return response.json()


@app.get("/user/{user_id}/repo/{owner}/{repo}/contents")
async def get_repo_contents(user_id: int, owner: str, repo: str, path: str = ""):
    """Get contents of a repository"""
    if user_id not in user_tokens:
        raise HTTPException(status_code=401, detail="User not authenticated")

    access_token = user_tokens[user_id]["access_token"]

    async with httpx.AsyncClient() as client:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        response = await client.get(
            url,
            headers={"Authorization": f"token {access_token}"}
        )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch contents")

        return response.json()


@app.get("/user/{user_id}/repo/{owner}/{repo}/file")
async def get_file_content(user_id: int, owner: str, repo: str, path: str):
    """Get decoded content of a specific file"""
    if user_id not in user_tokens:
        raise HTTPException(status_code=401, detail="User not authenticated")

    access_token = user_tokens[user_id]["access_token"]

    async with httpx.AsyncClient() as client:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        response = await client.get(
            url,
            headers={"Authorization": f"token {access_token}"}
        )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch file")

        file_data = response.json()

        # Decode base64 content
        if file_data.get("encoding") == "base64":
            content = base64.b64decode(file_data["content"]).decode("utf-8")
            return {
                "name": file_data["name"],
                "path": file_data["path"],
                "content": content,
                "size": file_data["size"]
            }

        return file_data


@app.get("/user/{user_id}/info")
async def get_user_info(user_id: int):
    """Get authenticated user info"""
    if user_id not in user_tokens:
        raise HTTPException(status_code=401, detail="User not authenticated")

    return user_tokens[user_id]["user_info"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)