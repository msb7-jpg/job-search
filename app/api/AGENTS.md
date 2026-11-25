# Backend API Rules (`app/api/`)

- **Thin Routers Only:** Never write raw SQLAlchemy `select(...)` or `session.commit()` inside `app/api/routers/*.py`. Put all queries and mutations in `app/db.py` repository functions.
- **Dependency Injection:** Always use `Annotated[Session, Depends(get_db_session)]` (required by Ruff `B008`).
- **Strict Contracts:** Every endpoint must declare explicit Pydantic v2 `response_model` schemas (from `app/api/schemas.py` or module-local `BaseModel`s). Never return raw ORM rows.
- **OpenAPI Sync:** Whenever you add or change an API route or schema, run `make gen-api-types` so `web/src/api/openapi.d.ts` stays in sync.
