# AI Voice Assistant

A web-based AI Voice Assistant built with Python, Django, and Django REST Framework, featuring a Dark/Light Glassmorphic Spatial UI.

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
