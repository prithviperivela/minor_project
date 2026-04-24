# SyteScan Prototype

SyteScan is a working academic prototype for multimodal interior site analysis and contractor discovery.

It implements the main ideas from `main.pdf`:

- web-based site data collection
- room measurement and budget structuring
- image analysis for lighting, color, quality, layout complexity, and material hints
- NLP-style extraction of interior requirements from free text
- generated Interior Site Report
- conceptual marketplace listing with contractor match scores and quote estimates

## Stack

- Frontend: Next.js
- Backend: FastAPI
- Image processing: Pillow-based computer vision heuristics
- Storage: local JSON file plus uploaded images

The synopsis mentions OpenCV, spaCy/transformers, PostgreSQL, and object storage. This prototype keeps the same system behavior but uses lightweight local implementations so it is easy to run and demonstrate.

## Run

Start the backend:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Start the frontend:

```powershell
cd frontend
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

The API health check is available at:

```text
http://127.0.0.1:8000/api/health
```

  ## How to Run This Project

  ### 1. Clone the repository

  Steps to run this project:
  
  git clone <YOUR_GITHUB_REPO_LINK>
  cd <REPOSITORY_FOLDER_NAME>

  ### 2. Install backend dependencies

  From the project root folder, run:

  python -m pip install -r backend/requirements.txt

  ### 3. Start the backend server

  python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

  Keep this terminal open.

  ### 4. Open a new terminal and start the frontend

  cd frontend
  npm install
  npm run dev

  ### 5. Open the app in browser

  http://localhost:3000

  ### Notes

  - Backend runs on: http://127.0.0.1:8000
  - Frontend runs on: http://localhost:3000
  - If port 3000 or 8000 is already busy, stop the old process and run again.


  If you want, I can also give you an even cleaner **5-line version** for GitHub.

## Demo Flow

1. Enter room, measurement, budget, and requirement details.
2. Upload one or more site photos.
3. Click `Generate Interior Site Report`.
4. Review extracted requirements, image analysis, budget feasibility, recommendations, discovery confidence, and contractor quote comparison.
