dev:
    uv run fastapi dev main.py

lint:
    uv run ty check .

format:
    uv run ruff check .
