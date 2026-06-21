# Setup project
- ### Install requiremets
    - uv sync
- ### Create DB
    - mariadb -u USER -p < main.sql
- ### Setup .env
    - cp .env-sample .env 

# How to run test
uv run python -m unittest discover -s tests

# Run Project
uv run main.py
