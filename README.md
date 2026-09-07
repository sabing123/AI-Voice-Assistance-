# AI Voice Assistant

A web-based AI Voice Assistant built with Python, Django, and Django REST Framework, featuring a Dark/Light Glassmorphic Spatial UI.

##envs
-create dir with local and inside in the dir use two dir .django and .postgres
- .django
   ```commandline
   AI_API_KEY=use-your-key
   STT_API_KEY=change-me
   TTS_API_KEY=change-me
   AI_MODEL=gemini-1.5-flash
   WHISPER_MODEL_SIZE=base
   TTS_LANG=en
   ```
  
- .postgres
   ```commandline
   POSTGRES_HOST=postgres
   POSTGRES_PORT=5432
   POSTGRES_DB=your-db
   POSTGRES_USER=your-username
   POSTGRES_PASSWORD=yoru-pass
   ```
## Requirements

- Python 3.11+
- Docker & Docker Compose

---

## Running with Docker Compose (Cookiecutter Style)

1. Build and start services using `local.yml`:
   ```bash
   docker-compose -f local.yml up --build
   ```

2. Open your browser at:
   `http://localhost:8000`

3. Stop containers:
   ```bash
   docker-compose -f local.yml down
   ```

---

## Local Development Installation

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables in `.env`.

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Run the development server:
   ```bash
   python manage.py runserver
   ```
