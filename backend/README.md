# SwipeHire — Backend Setup & Developer Guide

## Overview
This package is the backend foundation for SwipeHire, owned by **Person 1**. It handles:
- Crustdata company and person resolution/enrichment
- Data persistence with SQLAlchemy and SQLite
- Canonical Pydantic schemas shared across all workstreams
- REST API endpoints for candidate discovery, deck management, and recruiter actions
- Integration orchestrator calling Person 2's AI and matching modules

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
Copy `.env.example` in the repository root to `.env` and set your Crustdata API key:
```env
crust_api_key="your_crustdata_api_key"
```

### 3. Run Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 4. Run Test Suite
```bash
python -m pytest tests
```
