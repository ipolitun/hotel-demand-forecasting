# Hotel Demand Forecasting Platform

A microservice-based platform for importing hotel booking histories, running demand forecasts, and exposing the
results through a unified API gateway and lightweight front-end. The system consists of several backend services 
that handle data ingestion, forecasting, and API access for multiple hotels.

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
- [Services overview](#services-overview)
  - [Auth service](#auth-service)
  - [Router service](#router-service)
  - [Data Interface service](#data-interface-service)
  - [Prediction service](#prediction-service)
  - [Scheduler service](#scheduler-service)
  - [Frontend UI](#frontend-ui)
- [Development notes](#development-notes)
- [Troubleshooting](#troubleshooting)

## Architecture overview
The Router service acts as a central API Gateway and is used as the single entry point for external clients, 
the frontend, and internal service-to-service interactions, exposing a structured API grouped by service prefixes.

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
  helper utilities imported by every microservice to reduce duplication at early stages. 
* **Router service** — centralized API Gateway responsible for authentication, JWT validation, 
  request routing, and acting as a security boundary between external clients and internal services.
* **Auth service** — handles user registration and authentication, issues and rotates JWT tokens, and uses Redis 
  for refresh token storage.
* **Data Interface service** — handles uploading hotel booking histories and provides access to previously generated 
  demand forecasts.
* **Prediction service** — orchestrates model loading, training, and inference while persisting generated
  forecasts back to PostgreSQL.
* **Scheduler service** — triggers batch forecasts on a schedule by calling the router with predefined hotel
  identifiers and target dates as a temporary simplification.
* **Frontend UI** — static dashboard (served by Nginx) that communicates with the router to visualize
  forecasts.

## Repository layout

| Path                      | Description                                                                                                                                                                              |
|---------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `auth_service/`           | FastAPI service responsible for user registration and authentication, JWT issuance and rotation, and refresh token management.                                                           |
| `router/`                 | API Gateway that serves as the single external interface to the platform, enforces authentication, extracts user context, and proxies authorized requests to internal backend services.  |
| `data_interface_service/` | Service responsible for uploading booking CSVs and providing access to previously generated forecasts.                                                                                   |
| `prediction_service/`     | Model inference service handling model loading, forecast generation, and inference.                                                                                                      |
| `scheduler_service/`      | Lightweight periodic scheduler that triggers forecast updates via the router.                                                                                                            |
| `shared/`                 | Common SQLAlchemy ORM models, database connection/session management, base configuration, and the centralized error framework.                                                           |
| `migrations/`             | Alembic migration environment and revision scripts for managing database schema changes.                                                                                                 |
| `data_import/`            | Seed datasets (bookings, weather, holidays, historical predictions) and helper loading utilities used by offline scripts.                                                                |
| `scripts/`                | Utility scripts for schema initialization, seeding, maintenance tasks, and model evaluation; also includes a standalone Dockerfile for script execution.                                 |
| `tests/`                  | Unit and integration tests for the Auth service.                                                                                                                                         |
| `frontend_ui/`            | Static frontend (HTML/CSS/JS) served by Nginx; interacts exclusively with the router API.                                                                                                |
| `docker-compose.yml`      | Multi-service orchestration including PostgreSQL, all APIs, and the frontend.                                                                                                            |

## Key features
* Unified FastAPI gateway with centralized JWT validation and consistent error formatting across services.
* Booking ingestion pipeline that validates CSV uploads, deduplicates rows, and writes them to PostgreSQL via
  asynchronous SQLAlchemy sessions.
* Forecast retrieval endpoints providing access to historical booking data and previously generated predictions.
* Prediction microservice responsible for model loading, training, inference, and persisting forecast results.
* Batch scheduler that triggers forecast generation for configured hotels using shared scheduling settings.
* Docker Compose setup for spinning up the entire stack (database, APIs, frontend) with a single command and a
  shared `.env` file.

## Getting started

### Clone and configure
```bash
git clone https://github.com/ipolitun/hotel-demand-forecasting.git
cd hotel-demand-forecasting
cp .env.example .env
# Fill in database credentials, JWT secrets, and service URLs inside .env
```
The `.env` file is used by all services and Docker Compose for database credentials, JWT secrets, and service URLs.

### Run with Docker Compose
Ensure Docker Engine and Docker Compose v2+ are installed, then launch the stack:
```bash
docker compose up --build
```
This starts PostgreSQL, all FastAPI microservices, and the static frontend. Default service ports (host ports exposed 
by Docker Compose for local development):

| Service                | Port   |
|------------------------|--------|
| Router API             | `8001` |
| Prediction service     | `8002` |
| Auth service           | `8003` |
| Data Interface service | `8004` |
| Scheduler service      | `8005` |
| Frontend UI            | `8080` |
| PostgreSQL             | `5432` |

External clients should interact exclusively with the Router API; direct access to other services is intended
for local development and debugging purposes only.

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

   pip install -r shared/requirements.txt 
   pip install -r auth_service/requirements.txt
   uvicorn auth_service.main:app --reload --port 8002

   # Repeat the process for other services as needed.
   ```
4. **Frontend** – serve `frontend_ui/index.html` with any static server (e.g., `npm install -g serve` and run
   `serve frontend_ui`), or rely on Docker for the Nginx image.

## Configuration reference
All services rely on the variables defined in `.env`:

| Variable                                                                                                                                  | Description                                                                                                                            |
|-------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`                                                                                 | PostgreSQL credentials for both sync and async SQLAlchemy engines.                                                                     |
| `JWT_SECRET_KEY`, `JWT_PUBLIC_KEY`, `JWT_HASH_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_MINUTES`                   | JWT signing parameters shared by auth and router services.                                                                             |
| `PASSWORD_HASH_ALGORITHM`                                                                                                                 | Password hashing algorithm used by the Auth service.                                                                                   |
| `ROUTER_SERVICE_URL`, `PREDICTION_SERVICE_URL`, `AUTH_SERVICE_URL`, `DATA_INTERFACE_SERVICE_URL`, `SCHEDULER_SERVICE_URL`, `FRONTEND_URL` | Inter-service URLs used by the services for composing internal HTTP requests, as well as the frontend URL used for CORS configuration. |
| `REDIS_HOST`, `REDIS_PORT`                                                                                                                | Redis connection settings used by the Auth service for refresh token storage.                                                          |


## Database and data tooling
All database tables — cities, users, users_hotels, hotels, bookings, weather, holidays, and stored predictions — are 
defined as SQLAlchemy models in `shared/db_models` and managed via Alembic migrations.
 Use the utilities in `scripts/` and `data_import/` to initialize and populate the database:

* `scripts/db_seed.py` — end-to-end example that seeds cities, hotels, weather, bookings, and predictions
  (intended as a reference workflow).
* `data_import/import_*.py` — utilities for loading historical CSVs for bookings, weather, holidays, and legacy
  predictions into PostgreSQL.

When running under Docker Compose, the `data_import/` directory is mounted into the `scripts` container, making CSV resources available to seed and import utilities.

## Services overview
The typical interaction flow for a user working with the system is illustrated below.

### Auth service
The Auth service is responsible for user registration, authentication, and session management.
Its API is intended for internal use and is accessed via the Router service.

1. A user registers via `POST /users/register`.
2. Authentication is performed via `POST /auth/login`, submitting user login data (e.g., email and password).
   On success, the service issues access and refresh JWT tokens and sets them as HTTP-only cookies.
3. Token rotation is handled via `POST /auth/refresh`, with refresh tokens stored and validated using Redis.
4. Sessions can be terminated via `POST /auth/logout` or fully revoked via `POST /auth/logout/all`.
5. Password updates are handled via `POST /auth/change-password`, which revokes all existing tokens.

The service provides centralized error handling and consistent response schemas across all authentication endpoints.

### Router service
The Router service acts as a central API Gateway and defines the external contract of the platform.
It enforces authentication, validates access JWTs, extracts authenticated user context, 
and routes authorized requests to internal services.

Internal services are not exposed directly and rely on the Router as a trusted entry point.

| Endpoint                     | Method | Description                                                                              |
|------------------------------|--------|------------------------------------------------------------------------------------------|
| `/auth/login`                | `POST` | Proxies authentication requests to the Auth service and forwards authentication cookies. |
| `/auth/refresh`              | `POST` | Proxies access/refresh token rotation requests.                                          |
| `/auth/logout`               | `POST` | Terminates the current user session.                                                     |
| `/auth/logout/all`           | `POST` | Invalidates all active user sessions.                                                    |
| `/auth/register`             | `POST` | Proxies user registration requests to the Auth service.                                  |
| `/auth/change-password`      | `POST` | Updates the user password and revokes existing tokens.                                   |
| `/auth/me`                   | `GET`  | Returns the authenticated user payload extracted from the access JWT.                    |
| `/data/import-bookings`      | `POST` | Uploads CSV booking data on behalf of the hotel after validating the JWT payload.        |
| `/data/fetch-forecast`       | `POST` | Retrieves historical bookings and stored forecasts for the requested horizon.            |
| `/prediction/run-prediction` | `POST` | Triggers prediction runs via the prediction service using a shared async HTTP client.    |

### Data Interface service
* Validates `X-Hotel-Id` headers, parses uploaded CSV data in a worker thread, and persists bookings while
  reporting duplicates and per-hotel audit logs.
* Aggregates booking history and joins stored forecasts from the `predictions` table, raising domain-specific
  errors when history is insufficient.

### Prediction service
* Loads persisted model artifacts and performs demand forecasting for configured hotels.
* Provides `/run-predict`, `/train`, `/init-hotel/{hotel_id}`, `/status/{hotel_id}`, and `/config/{hotel_id}`
  endpoints for inference and lifecycle management.
* Commits predictions to PostgreSQL.

### Scheduler service
A lightweight FastAPI app whose lifespan hook triggers the `trigger_forecast` job. The scheduler currently
uses a predefined list of hotels and calls the router’s prediction endpoint with target dates. The 
implementation can be extended to support dynamic hotel discovery via database queries.

### Frontend UI
The `frontend_ui` folder contains an Nginx-backed static site that communicates with the router API, allowing
users to upload booking data and view forecast results through a browser interface.

## Development notes
* Error handling — prefer raising subclasses of `ServiceError` and decorate FastAPI routes with
  `@register_errors` so that responses stay consistent and automatically documented in OpenAPI.
* Database access — use the generator dependencies `get_sync_session`/`get_async_session` from `shared.db`
  inside FastAPI routes to guarantee proper session lifecycle management.
* HTTP clients — downstream calls should reuse the router’s app-scoped `httpx.AsyncClient` provided by the
  `get_http_client` dependency to avoid connection churn and to respect shared timeouts.
* Router responsibilities — the Router is intentionally designed as a thin orchestration layer and does not 
  contain business logic beyond authentication, authorization, and request routing.
* Background work — CPU-bound tasks such as CSV parsing are offloaded using `asyncio.to_thread`
  within the data interface service. Similar patterns can be applied to other isolated CPU-heavy tasks.

## Troubleshooting
* **Auth failures** — ensure JWT configuration (`JWT_SECRET_KEY`, `JWT_HASH_ALGORITHM`) is consistent
  between the router and auth services, and that Redis is available for refresh token validation.
* **Missing forecasts** — ensure historical bookings have been uploaded via `/data/import-bookings`
  and that the prediction service has successfully persisted forecast results to the `predictions`
  table. Until matching records exist, forecast retrieval endpoints may return a `NoForecastError`.

