# Schedule Project (Monorepo)

Unified repository for the Schedule application, including backend, frontend, and Telegram bot.

## Project Structure

- **/backend** - Django-based backend server.
- **/frontend** - Next.js frontend application.
- **/telegram** - Telegram bot implementation.
- **main.py** - Main entry point or orchestration script.

## Setup

1. **Backend & Bot:**
   - Create and activate a virtual environment: `python -m venv .venv`
   - Install requirements (if you have them): `pip install -r requirements.txt` (Note: Check the `telegram/requirements.txt`)
   - Configure `.env` files in appropriate directories.

2. **Frontend:**
   - Navigate to `frontend/`: `cd frontend`
   - Install dependencies: `npm install`
   - Run development server: `npm run dev`

## Development

This is a monorepo structure, allowing you to manage all parts of the project in one place while keeping histories intact.
