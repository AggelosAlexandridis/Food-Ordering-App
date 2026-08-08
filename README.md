# Setup project
- ### Install requiremets
    - uv sync
- ### Create DB
    - mariadb -u USER -p < main.sql
- ### Setup .env
    - cp .env-sample .env 

# How to run test
uv run python -m unittest discover -s tests

Tests never touch the real database. On first run they create an isolated
"ghost" database (`<DATABASE>_test`, e.g. `ofd_test`) from `main.sql` and
point `DBManager` at it for the whole test run. The app's DB user usually
only has privileges on its own database, so an admin needs to run this once:

```
mariadb -u root -p -e "CREATE DATABASE IF NOT EXISTS ofd_test; GRANT ALL PRIVILEGES ON ofd_test.* TO 'ofd'@'%'; FLUSH PRIVILEGES;"
```

(swap `ofd`/`ofd_test` for your actual `DATABASE` value from `.env` if different,
or set `TEST_DATABASE` in `.env` to override the name).

# Run Project
uv run main.py
