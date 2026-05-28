# webEng Backend


FastAPI backend running on `http://localhost:5001`.

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate it

**macOS / Linux:**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
cd api
pip install .
```

## Run

Must be run from API folder, due to deployment paths

```bash
cd api
python main.py
```

The server starts at [http://localhost:5001](http://localhost:5001)

## API Endpoints

All available endpoints and their request/response schemas can be explored interactively at [http://localhost:5001/docs](http://localhost:5001/docs)
