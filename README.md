# Hotel Demand Forecasting Platform

A microservice-based platform for importing hotel booking histories, running demand forecasts, and exposing the
results through a unified API gateway and lightweight front-end. The system is designed for production-grade
observability, consistent error handling, and extensible model management for multiple hotels.

## Table of contents
- [Architecture overview](#architecture-overview)
- [Repository layout](#repository-layout)
- [Key features](#key-features)
- [Getting started](#getting-started)
  - [Clone and configure](#clone-and-configure)
  - [Run with Docker Compose](#run-with-docker-compose)
  - [Run services locally](#run-services-locally)
- [Configuration reference](#configuration-reference)
- [Database and data tooling](#database-and-data-tooling)
- [Data workflow](#data-workflow)
  - [Auth service](#auth-service)
  - [Router service](#router-service)
  - [Data Interface service](#data-interface-service)
  - [Prediction service](#prediction-service)
  - [Scheduler service](#scheduler-service)
  - [Frontend UI](#frontend-ui)
- [Development notes](#development-notes)
- [Troubleshooting](#troubleshooting)

## Architecture overview
The platform is composed of independent FastAPI services communicating over HTTP and sharing a PostgreSQL
warehouse. Each service is packaged with its own Docker image and can be scaled independently.

```
+-------------+        +-------------------+        +--------------------+
|  Frontend   | <----> |      Router       | <----> |  Auth / Prediction |
|    (SPA)    |        |  (API Gateway)    |        |  / Data Interface  |
+-------------+        +-------------------+        +--------------------+
                             ^         |                     ^
                             |         |                     |
                             |         v                     |
                          +---------------+           +--------------+
                          |  Scheduler    | --------> |  PostgreSQL  |
                          |  (jobs)       |           |   database   |
                          +---------------+           +--------------+
```

* **Shared library** — common SQLAlchemy models, database session factories, reusable error hierarchy, and
  helper utilities imported by every microservice.
* **Router service** — central gateway responsible for JWT validation, proxying traffic to the downstream
  services using a pooled `httpx.AsyncClient`, and returning standardized error responses.
* **Auth service** — issues short-lived JWT tokens for hotels and internal schedulers by validating API keys
  stored in the shared database.
* **Data Interface service** — ingests CSV booking histories, stores them in PostgreSQL, and exposes forecast
  retrieval endpoints backed by the shared ORM models.
* **Prediction service** — orchestrates model loading, training, and inference while persisting generated
  forecasts back to PostgreSQL.
* **Scheduler service** — triggers batch forecasts on a schedule by calling the router with predefined hotel
  identifiers and target dates.
* **Frontend UI** — static dashboard (served by Nginx) that communicates with the router to visualize
  forecasts.

## Repository layout

| Path                      | Description                                                                                                                                                          |
|---------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `auth_service/`           | FastAPI microservice that authenticates clients and issues JWT tokens for hotels and the scheduler.                                                                  |
| `router/`                 | API gateway that proxies requests to downstream services, performs unified error formatting, enforces auth, and exposes a consolidated REST API                      |
| `data_interface_service/` | Service responsible for uploading booking CSVs and retrieving stored history/forecast data from PostgreSQL.                                                          |
| `prediction_service/`     | Model inference service handling model loading, forecast generation, and ML configuration validation.                                                                |
| `scheduler_service/`      | Lightweight periodic scheduler that triggers forecast updates via the router.                                                                                        |
| `shared/`                 | Common SQLAlchemy ORM models, database connection/session management, base configuration, and the centralized error framework.                                       |
| `data_import/`            | Seed datasets (bookings, weather, holidays, historical predictions) and helper loading utilities used by offline scripts.                                            |
| `scripts/`                | Utility scripts for schema initialization, seeding, migrations, maintenance tasks, and model evaluation; also includes a standalone Dockerfile for script execution. |
| `frontend_ui/`            | Static frontend (HTML/CSS/JS) served by Nginx; interacts exclusively with the router API.                                                                            |
| `docker-compose.yml`      | Multi-service orchestration including PostgreSQL, all APIs, and the frontend.                                                                                        |

## Key features
* Unified FastAPI gateway with central JWT authentication and centralized error formatting for consistent API
  responses across services.
* Booking ingestion pipeline that validates CSV uploads, deduplicates rows, and writes them to PostgreSQL via
  asynchronous SQLAlchemy sessions.
* Forecast retrieval endpoints combining historical booking aggregates with stored predictions for rich
  analytics dashboards.
* Prediction microservice capable of initializing model directories, training/fine-tuning models, and
  persisting forecast results atomically with rollback on failure.
* Batch scheduler that triggers forecast generation for configured hotels and manages horizon boundaries using
  shared settings.
* Docker Compose setup for spinning up the entire stack (database, APIs, frontend) with a single command and a
  shared `.env` file.

## Getting started

### Clone and configure
```bash
git clone https://github.com/<your-org>/hotel-demand-forecasting.git
cd hotel-demand-forecasting
cp .env.example .env
# Fill in database credentials, JWT secrets, and service URLs inside .env
```
The environment file is consumed by every service (including Docker Compose) to wire Postgres credentials,
JWT secrets, and downstream URLs.

### Run with Docker Compose
Ensure Docker Engine and Docker Compose v2+ are installed, then launch the stack:
```bash
docker compose up --build
```
This starts PostgreSQL, all FastAPI microservices, and the static frontend. Default exposed ports:

| Service                | Port   |
|------------------------|--------|
| Router API             | `8001` |
| Prediction service     | `8002` |
| Auth service           | `8003` |
| Data Interface service | `8004` |
| Scheduler service      | `8005` |
| Frontend UI            | `8080` |
| PostgreSQL             | `5432` |

### Run services locally
For iterative development you can run services directly with `uvicorn`.

1. **Start PostgreSQL** – either via Docker (`docker compose up db`) or a local instance with matching
   credentials from `.env`.
2. **Initialize the schema** – run `python scripts/db_init.py` to create tables, or use the seeding scripts
   described below.
3. **Install dependencies** per service and launch:
   ```bash
   python -m venv .venv
   source .venv/bin/activate

   pip install -r shared/requirements.txt  # if you maintain a common requirements file
   pip install -r auth_service/requirements.txt
   uvicorn auth_service.main:app --reload --port 8002

   # Repeat for router, data interface, prediction, and scheduler services
   ```
4. **Frontend** – serve `frontend_ui/index.html` with any static server (e.g., `npm install -g serve` and run
   `serve frontend_ui`), or rely on Docker for the Nginx image.

## Configuration reference
All services rely on the variables defined in `.env`:

| Variable                                                                                                                                  | Description                                                                                                                            |
|-------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`                                                                                 | PostgreSQL credentials for both sync and async SQLAlchemy engines.                                                                     |
| `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`                                                                                  | JWT signing parameters shared by auth and router services.                                                                             |
| `SCHEDULER_KEY`                                                                                                                           | API key required by the scheduler to fetch a system token.                                                                             |
| `ROUTER_SERVICE_URL`, `PREDICTION_SERVICE_URL`, `AUTH_SERVICE_URL`, `DATA_INTERFACE_SERVICE_URL`, `SCHEDULER_SERVICE_URL`, `FRONTEND_URL` | Inter-service URLs used by the services for composing internal HTTP requests, as well as the frontend URL used for CORS configuration. |
| `MODEL_DIR`                                                                                                                               | Filesystem path where prediction models and configs are stored.                                                                        |
| `MAX_DATA_DATE`                                                                                                                           | Upper bound for scheduler target dates to avoid requesting forecasts past loaded data.                                                 |

## Database and data tooling
All database tables — cities, hotels, bookings, weather, holidays, and stored predictions — are defined in 
`shared/db_models` and backed by the shared SQLAlchemy metadata. Use the utilities in `scripts/` and 
`data_import/` to initialize and populate the database:

* `scripts/db_seed.py` — end-to-end example that seeds cities, hotels, weather, bookings, and predictions
  (intended as a reference workflow; adjust before using in production).
* `data_import/import_*.py` — utilities for loading historical CSVs for bookings, weather, holidays, and legacy
  predictions into PostgreSQL.

During local development or when running under Docker Compose, the `./data_import` directory is mounted into the
`scripts/` container, making all CSV resources directly accessible to seed and import scripts executed there.

## Data workflow
The typical flow for a hotel operator is illustrated below.

### Auth service
1. The scheduler obtains a system token via `POST /token/system` with the shared `X-System-Key` header.
2. Hotels exchange their API key for a JWT through `POST /token/user`, validated against the `hotel` table in
   PostgreSQL.

Both endpoints return a Bearer token encapsulated by the `TokenResponse` schema and leverage centralized error
handlers for consistent responses.

### Router service
The router exposes a hotel-friendly API and forwards calls downstream while enforcing JWT verification with the
shared authorization errors. Key endpoints:

| Endpoint | Method | Description |
| -------- | ------ | ----------- |
| `/auth/login` | `POST` | Proxies hotel login requests to the auth service and returns a JWT token. |
| `/data/import-bookings` | `POST` | Uploads CSV booking data on behalf of the hotel after validating the JWT payload. |
| `/data/fetch-forecast` | `POST` | Retrieves historical bookings and stored forecasts for the requested horizon. |
| `/prediction/run-prediction` | `POST` | Triggers prediction runs via the prediction service using a shared async HTTP client. |

### Data Interface service
* Validates `X-Hotel-Id` headers, parses uploaded CSV data in a worker thread, and persists bookings while
  reporting duplicates and per-hotel audit logs.
* Aggregates booking history and joins stored forecasts from the `predictions` table, raising domain-specific
  errors when history is insufficient.

### Prediction service
* Loads persisted model artifacts from `MODEL_DIR`, falling back to base models when initializing a new hotel.
* Provides `/run-predict`, `/train`, `/init_hotel/{hotel_id}`, `/status/{hotel_id}`, and `/config/{hotel_id}`
  endpoints for inference and lifecycle management.
* Commits predictions to PostgreSQL with rollback on failure to ensure atomic writes.

### Scheduler service
A lightweight FastAPI app whose lifespan hook triggers the `trigger_forecast` job. The job enumerates hotels
(currently hardcoded) and calls the router’s prediction endpoint with safe target dates capped by
`MAX_DATA_DATE`. Replace the placeholder logic with database queries to support dynamic hotel lists.

### Frontend UI
The `frontend_ui` folder contains an Nginx-backed static site that communicates with the router API, enabling
operations teams to upload bookings and inspect forecasts from a browser.

## Development notes
* Error handling — prefer raising subclasses of `ServiceError` and decorate FastAPI routes with
  `@register_errors` so that responses stay consistent and automatically documented in OpenAPI.
* Database access — use the generator dependencies `get_sync_session`/`get_async_session` from `shared.db`
  inside FastAPI routes to guarantee proper session lifecycle management.
* HTTP clients — downstream calls should reuse the router’s app-scoped `httpx.AsyncClient` provided by the
  `get_http_client` dependency to avoid connection churn and to respect shared timeouts.
* Background work — CPU-bound tasks like CSV parsing are offloaded with `asyncio.to_thread` within the data
  interface service; follow the same pattern for additional heavy workloads.

## Troubleshooting
* **Auth failures** — ensure `SECRET_KEY`, `ALGORITHM`, and API keys seeded in the `hotel` table match what the
  auth service expects.
* **Scheduler requests fail** — verify the scheduler is using a valid system token obtained from the auth
  service and that `ROUTER_SERVICE_URL` points to the running router instance.
* **Missing forecasts** — load historical bookings via `/data/import-bookings` and confirm the prediction
  service successfully persisted results to the `predictions` table; the data interface service will raise
  `NoForecastError` until matching records exist.
