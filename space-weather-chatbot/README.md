# Space Weather Chatbot

A production-ready full-stack application that provides simple space weather insights powered by a live CatBoost Geomagnetic prediction model & a Large Language Model.

## Directory Structure
```
space-weather-chatbot/
├── backend/
│   ├── main.py
│   ├── llm_service.py
│   ├── prediction_loader.py
├── frontend/
│   ├── index.html
│   ├── script.js
├── data/
│   └── latest_prediction.json
├── requirements.txt
└── README.md
```

## Setup and Run Instructions

### Preferred Method: Docker (Recommended)
You can run the entire application (frontend + backend + dependencies) automatically using Docker from the **root directory of the project**:
```bash
docker-compose up --build
```
*Note: Make sure your `.env` file with `OPENAI_API_KEY` is present in the root folder, or export it in your shell.*

Then navigate to `http://localhost:8000/`.

---

### Alternative Method: Local Setup

#### 1. Install Dependencies
Open your terminal and make sure you have the required packages:
```bash
pip install -r requirements.txt
```

#### 2. Configure OpenAI 
Set your OpenAI API key so the assistant can parse logic with the specified Persona.
**Windows Command Prompt:**
```cmd
set OPENAI_API_KEY="sk-...."
```
**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY="sk-...."
```
**Mac/Linux:**
```bash
export OPENAI_API_KEY="sk-...."
```

### 3. Run the Backend API
Navigate into `backend/` and start the FastAPI service:
```bash
cd backend
uvicorn main:app --reload --port 8000
```
*The API will start at `http://127.0.0.1:8000`.*

### 4. Open the Interface
Because this is pure HTML/JS without need to compile a React bundle, you can simply **double-click the `frontend/index.html` file** to open it locally.

Or serve it explicitly via python if desired:
```bash
cd ../frontend
python -m http.server 8080
```
Then visit `http://localhost:8080`!
