# Deploying for free

This project can run on Render's free web services. Free Render services sleep
after 15 minutes without traffic, and the first request after that can take
about a minute while the service starts. This is suitable for a demo or
portfolio project, not a latency-sensitive production booking system.

## 1. Publish the repository

Create a **public** GitHub repository named `hotel-guest-assistant`, then push
this project from its root directory. The root `.gitignore` excludes local
environment files, Python virtual environments, and generated frontend files.

## 2. Deploy the backend on Render

Create a Render **Web Service** connected to the GitHub repository, with:

- Root directory: `backend`
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/api/health`
- Instance type: Free

The deployed backend URL is:

`https://grand-horizon-hotel-api.onrender.com`

Set `CORS_ORIGINS` to the frontend's `onrender.com` URL after creating the
frontend service. `AI_PROVIDER=mock` is the default and needs no API key.

## 3. Deploy the frontend on Render

Create a second Render **Web Service** for the same repository, with:

- Name: `grand-horizon-hotel-web`
- Root directory: `frontend`
- Runtime: Node
- Build command: `npm install && npm run build`
- Start command: `npm run start`
- Instance type: Free
- Environment variable `NEXT_PUBLIC_API_URL`:
  `https://grand-horizon-hotel-api.onrender.com`

After creating the frontend, copy its public URL (for example,
`https://grand-horizon-hotel-web.onrender.com`). In the backend service's
Environment page, set `CORS_ORIGINS` to that URL and use **Manual Deploy →
Deploy latest commit**. Open the frontend URL and try both a hotel FAQ question
and an availability search.

## Local environment files

For local development, copy `backend/.env.example` to `backend/.env` and
`frontend/.env.local.example` to `frontend/.env.local`. Never commit those
local files or put an AI provider key in a `NEXT_PUBLIC_` variable.
