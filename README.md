[![CI](https://github.com/Bla-vk/simple-crud-api-flask/actions/workflows/ci.yml/badge.svg)](https://github.com/Bla-vk/simple-crud-api-flask/actions/workflows/ci.yml)

# Simple CRUD API (Flask)

A REST API for tracking **items** and the **locations** they are stored in.
Built with Flask and Flask-SQLAlchemy, packaged with Docker.

- Full Create / Read / Update / Delete for items and locations
- Versioned paths under `/api/v1/`
- Paginated lists (20 per page)
- Filter items by location: `/api/v1/items/?location=<id>`
- Location names are unique; deleting a location deletes its items
- A `/health/` endpoint for load balancer and container health checks
- 47 automated tests (pytest)

## Endpoints

| Method                  | Path                      | Purpose                                                  |
| ----------------------- | ------------------------- | -------------------------------------------------------- |
| GET, POST               | `/api/v1/locations/`      | List / create locations                                  |
| GET, PUT, PATCH, DELETE | `/api/v1/locations/<id>/` | Read / update / delete a location                        |
| GET, POST               | `/api/v1/items/`          | List (supports `?location=` and `?page=`) / create items |
| GET, PUT, PATCH, DELETE | `/api/v1/items/<id>/`     | Read / update / delete an item                           |
| GET                     | `/health/`                | Returns `{"status": "ok"}`                               |

List responses look like `{"count": 45, "pages": 3, "page": 1, "results": [...]}`.
Validation errors return 400 with the field names, for example `{"name": ["This field is required."]}`.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

flask --app wsgi run --debug --port 8000
```

The SQLite database is created automatically in `instance/app.db`.
Set `DATABASE_URL` to use a different database.

## Try it

```bash
curl -X POST localhost:8000/api/v1/locations/ \
  -H 'Content-Type: application/json' -d '{"name":"Shelf A"}'

curl -X POST localhost:8000/api/v1/items/ \
  -H 'Content-Type: application/json' \
  -d '{"name":"Laptop","description":"14 inch","location":1}'

curl "localhost:8000/api/v1/items/?location=1&page=1"
curl -X PATCH localhost:8000/api/v1/items/1/ \
  -H 'Content-Type: application/json' -d '{"description":"updated"}'
curl -X DELETE localhost:8000/api/v1/items/1/
```

## Run the tests

```bash
pytest
```

## Docker

```bash
docker build -t simple-crud-flask .
docker run -p 8000:8000 simple-crud-flask
```

The image runs as a non-root user and serves with gunicorn on port 8000.

If you push the image to ECR with `docker buildx`, add `--provenance=false` so ECR can scan it.

## Configuration

| Variable       | Default            | Purpose                 |
| -------------- | ------------------ | ----------------------- |
| `DATABASE_URL` | `sqlite:///app.db` | SQLAlchemy database URL |

## Known limits

- Uses SQLite, so data is lost when a container or ECS task is replaced. Set `DATABASE_URL` to an RDS PostgreSQL URL (and add `psycopg2-binary` to `requirements.txt`) for persistence.
- Tables are created on start with `create_all()`. Add Flask-Migrate if you start changing the schema.
- No authentication yet.

## Project layout

```
app/          create_app(), models, routes
tests/        pytest suite
wsgi.py       gunicorn entry point
Dockerfile
requirements.txt
```
