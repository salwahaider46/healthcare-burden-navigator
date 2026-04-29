# Healthcare Burden Navigator

Group 089 – CS-6440 Introduction to Health Informatics

## Project Structure

```
backend/          # FastAPI backend
  app/            # Application package (routers, services, models, schemas)
  fhir_docker_setup/  # Docker Compose for Postgres + FHIR data loader
  seed_providers.py   # Script to create tables and seed sample provider data
  main.py         # FastAPI entry point
frontend/         # React (Vite) frontend
  src/
    pages/        # ChatPage and SearchPage
    components/   # ProviderCard
```

## Prerequisites

- **Docker** (for PostgreSQL)
- **Python 3.10+** (tested with 3.12)
- **Node.js 18+**
- A **Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey) (needed for the chat feature)

## Quick Start

### 1. Start PostgreSQL

```bash
cd backend/fhir_docker_setup
cp .env.example .env
docker compose up -d
```

This starts:
- **Postgres** on `localhost:5432` (user: `fhir_user`, password: `fhir_password`)
- **pgAdmin** on `http://localhost:5050` (optional, for browsing data)

### 2. Create the application database

The Docker Compose creates the `fhir_demo` database for FHIR data. The backend app uses a separate database called `healthcare_nav`:

```bash
docker exec -it fhir_postgres psql -U fhir_user -d fhir_demo -c "CREATE DATABASE healthcare_nav;"
```

### 3. Configure environment variables

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` with these values:

```
DATABASE_URL=postgresql://fhir_user:fhir_password@localhost:5432/healthcare_nav
FHIR_BASE_URL=http://localhost:8081/fhir
GEMINI_API_KEY=your_actual_gemini_api_key
```

### 4. Set up the Python environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5. Seed the database

This creates the `providers` table and inserts 20 sample providers:

```bash
cd backend
.venv/bin/python seed_providers.py
```

Expected output:
```
Connecting to: postgresql://fhir_user:fhir_password@localhost:5432/healthcare_nav
Tables created (or already exist).
Seeded 20 providers successfully.
```

### 6. Start the backend

```bash
cd backend
.venv/bin/uvicorn main:app --reload --port 8000
```

Verify it works:
```bash
curl -s http://localhost:8000/
# → {"status":"ok","message":"Healthcare Burden Navigator API"}

curl -s "http://localhost:8000/api/v1/providers/recommendations?limit=3"
# → JSON array of providers
```

API docs available at: http://localhost:8000/docs

### 7. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

- **Chat** tab (`/`) — natural language provider search powered by Gemini
- **Search** tab (`/search`) — filter-based search with controls for specialty, insurance, telehealth, distance, and language

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/providers/recommendations` | Ranked provider results filtered by specialty, insurance, telehealth, distance, and optional FHIR patient context |
| GET | `/api/v1/providers/search` | Search providers by name, specialty, city, state, zip, insurance |
| GET | `/api/v1/providers/{id}` | Get a single provider by ID |
| GET | `/api/v1/providers/{id}/details` | Get provider merged with FHIR Practitioner data |
| POST | `/api/v1/chat` | Chat-based provider search via Gemini |
| GET | `/api/v1/fhir/practitioners` | Search FHIR Practitioner resources |
| GET | `/api/v1/fhir/practitioners/{fhir_id}` | Get a single FHIR Practitioner |
| GET | `/api/v1/fhir/conditions` | Search FHIR Condition resources by patient |
| GET | `/api/v1/fhir/encounters` | Search FHIR Encounter resources by patient |
| GET | `/api/v1/fhir/coverage` | Search FHIR Coverage resources by patient |

## Loading FHIR Patient Data (Optional)

To load FHIR patient bundles (for patient-context-aware ranking):

```bash
cd backend/fhir_docker_setup
docker compose --profile loader run --rm fhir_loader
```

See `backend/fhir_docker_setup/README.md` for more details.

## EC2 Deployment

### Prerequisites (on the EC2 instance)

```bash
# Update system (Ubuntu)
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable docker --now
sudo usermod -aG docker $USER
# Log out and back in for the group change to take effect

# Install Python
sudo apt install -y python3 python3-venv python3-pip

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### Clone and set up

```bash
git clone https://github.com/salwahaider46/healthcare-burden-navigator.git
cd healthcare-burden-navigator
```

Then follow Quick Start steps 1–5 above (start Postgres, create DB, configure `.env`, install Python deps, seed).

### Run the backend (production)

Use `--host 0.0.0.0` so the API is accessible externally:

```bash
cd backend
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

For **persistent background running**, create a systemd service:

```bash
sudo nano /etc/systemd/system/healthcare-backend.service
```

```ini
[Unit]
Description=Healthcare Burden Navigator Backend
After=network.target docker.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/healthcare-burden-navigator/backend
ExecStart=/home/ubuntu/healthcare-burden-navigator/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=5
EnvironmentFile=/home/ubuntu/healthcare-burden-navigator/backend/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable healthcare-backend --now
sudo systemctl status healthcare-backend   # check it's running
journalctl -u healthcare-backend -f        # view logs
```

### Serve the frontend with nginx

Build the frontend as static files:

```bash
cd frontend
npm install
npm run build   # outputs to dist/
```

Install and configure nginx:

```bash
sudo apt install -y nginx
sudo nano /etc/nginx/sites-available/healthcare
```

```nginx
server {
    listen 80;
    server_name _;

    root /home/ubuntu/healthcare-burden-navigator/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/healthcare /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
```

**Important:** When using nginx to proxy `/api/`, update `API_BASE` in both `frontend/src/pages/ChatPage.jsx` and `frontend/src/pages/SearchPage.jsx` from:

```js
const API_BASE = "http://localhost:8000/api/v1";
```

to:

```js
const API_BASE = "/api/v1";
```

Then rebuild: `npm run build`.

### EC2 Security Group

In the AWS Console under **EC2 → Security Groups**, add these inbound rules:

| Type | Port | Source | Purpose |
|------|------|--------|---------|
| Custom TCP | 8000 | Your IP | Backend API (direct access) |
| HTTP | 80 | 0.0.0.0/0 | Frontend + API via nginx |

**Do NOT** expose port 5432 (Postgres) publicly.

### Verify

```bash
curl http://<EC2_PUBLIC_IP>/api/v1/providers/recommendations?limit=3
```

Open `http://<EC2_PUBLIC_IP>` in your browser.

## Reset Everything

```bash
# Stop and remove Docker volumes
cd backend/fhir_docker_setup
docker compose down -v

# Then start fresh from Step 1
```
