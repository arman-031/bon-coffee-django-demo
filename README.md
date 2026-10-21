# BON Coffee

BON Coffee is a Django REST Framework + PostgreSQL storefront demo built around the existing HTML, CSS, and vanilla JavaScript frontend. The original RTL design, product routes, responsive layout, images, and animations remain the frontend source of truth. Authenticated checkout creates a database order and records a clearly simulated payment; it does not process real transactions.

## Features

- Catalog API with category and product listing
- Search and filtering by category
- Product detail endpoints
- Django session authentication for registration, login, logout, and profile
- CSRF-protected authenticated mutations; cross-origin session cookies require HTTPS in production
- Persistent per-user favorites and cart API with quantity control
- Checkout and PostgreSQL order creation with server-side price, shipping, and coupon calculation
- Separate simulated-payment endpoint and payment record (no real payment gateway)
- Authenticated order history and order-reference tracking
- Django admin for catalog and shop management

## Tech stack

- Python 3.11+
- Django 5.2
- Django REST Framework
- PostgreSQL
- python-dotenv
- django-cors-headers
- drf-spectacular
- Vanilla JavaScript frontend

## Project structure

- `index.html`, `app.js`, and `integration.js` – existing frontend and API integration
- `products.js` – static fallback product catalog
- `backend/` – Django project and apps
- `backend/catalog/` – categories and products
- `backend/shop/` – authentication, favorites, cart, checkout, payment, orders

## Local development

1. Create and activate a Python 3.11 virtual environment.
2. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Copy `backend/.env.example` to `backend/.env` and set a private `DJANGO_SECRET_KEY`. Leave all `DB_*` values blank to use SQLite for local development, or configure PostgreSQL explicitly. `SQLITE_NAME` can point SQLite to a separate file when you want to keep the default local database untouched.
4. Run migrations:

```bash
cd backend
python manage.py migrate
```

5. Start the backend:

```bash
python manage.py runserver 127.0.0.1:8000
```

6. Serve the project root on `http://127.0.0.1:5500` (for example, `python -m http.server 5500`) and open that address. The frontend uses `http://127.0.0.1:8000` as its local API by default. The `seed_catalog` command is also available to load the current static catalog into the database.

For a separate frontend/backend deployment, set `window.BON_API_BASE_URL` before loading `app.js` to the backend origin. Configure that exact frontend origin in `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`; use HTTPS, `SESSION_COOKIE_SAMESITE=None`, and secure session/CSRF cookies for cross-site Netlify-to-backend requests.

Run `python manage.py test` for local tests. The command automatically selects `config.test_settings`, disables dotenv loading, and uses an in-memory SQLite database, regardless of database values in `backend/.env`. An explicit `--settings` option overrides this safeguard and should only be used with an intentionally isolated database, as in CI.

## Docker

Build and start the local development stack with:

```bash
docker compose up --build
```

This starts PostgreSQL and Django, waits for the database health check, applies migrations, and seeds an empty catalog without overwriting existing product data on restarts. PostgreSQL is reachable by the app over the Compose network and is not published on a host port, avoiding conflicts with a local PostgreSQL server. Data is stored in the named `bon-coffee_postgres_data` volume. To run a verification stack without sharing the default volume, use `docker compose -p bon-coffee-verify up --build`; it creates a separate `bon-coffee-verify_postgres_data` volume. The default Compose credentials and Django key are for local development only; supply private values and `DEBUG=False` for a deployment. The bundled Django development server is not a production server.

## API docs

- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`
- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- Auth: `/api/auth/csrf/`, `/api/auth/register/`, `/api/auth/login/`, `/api/auth/logout/`, `/api/auth/profile/`
- Catalog: `/api/categories/`, `/api/products/`
- User data and orders: `/api/favorites/`, `/api/cart/`, `/api/orders/`, `/api/orders/create/`, `/api/payments/simulated/`

## Environment variables

Use environment variables in `backend/.env` (not committed to Git):

```env
DJANGO_SECRET_KEY=your-secret
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,[::1]
DB_NAME=bon_coffee
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=127.0.0.1
DB_PORT=5432
CORS_ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000
CSRF_TRUSTED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000
SESSION_COOKIE_SAMESITE=Lax
SESSION_COOKIE_SECURE=False
```

## Tests

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test
cd ..
node --check app.js
node --check integration.js
docker compose config
```

GitHub Actions runs Django checks, migration checks, migrations, backend tests, and JavaScript syntax checks against a PostgreSQL service on Python 3.11. It receives CI environment variables directly and does not require a local `.env` file.

## Live frontend demo and deployment limits

The static frontend is deployed on Netlify: [bon-demo-showcase.netlify.app](https://bon-demo-showcase.netlify.app/). This demo serves the frontend only. The Django REST API and PostgreSQL database in this repository are local development components and have not been deployed or published as a live backend.

Because there is no deployed API configured for the Netlify site, API-backed features such as authentication, persistent favorites and cart, checkout, simulated payment, and order history are not available through the public demo. They can be tested by running the frontend and backend locally as described above. Do not enter real customer or payment information; simulated payment does not contact a payment provider.

This workspace does not contain production credentials or an automated backend deployment configuration. To connect a future backend, set `window.BON_API_BASE_URL` to its HTTPS origin and configure the exact frontend origin in `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`, with secure cross-site session and CSRF cookies. No live backend, real payment provider, or production deployment is claimed here. Keep secrets out of source control, use explicit `ALLOWED_HOSTS`, and set `DEBUG=False` in production.
