# PlatformTech SD1 MS2 - React Dashboard Final Fetch Fix

This version fixes the login `Failed to fetch` issue by using a Vite proxy. The frontend no longer directly calls `http://127.0.0.1:8000`; it calls `/api/v1`, and Vite forwards API requests to FastAPI.

## Fastest Windows run

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start-dev.ps1
```

Then open:

```text
http://127.0.0.1:5173
```

Confirm backend:

```text
http://127.0.0.1:8000/api/v1/health
```

---

# FinMark Prototype

FinMark is a FastAPI + React prototype for authenticated commerce workflows. The latest version includes a protected **React add-to-cart dashboard** with product listing, cart quantity controls, checkout form, coupon calculation, tax/shipping estimate, and FastAPI checkout confirmation.

## Latest Upgrade


### White Professional Dashboard UI

The active React dashboard was refreshed into a clean white professional admin-dashboard interface. The new UI includes:

- White, slate, and blue enterprise dashboard theme
- Fixed rounded sidebar
- Professional blue primary action buttons
- Search bar, low-stock pill, notification button, and profile chip
- KPI cards with mini bar charts
- Neutral white countdown card with subtle blue accents
- Clean product cards with better spacing, borders, and stock indicators
- Stock status pills and segmented stock progress bars
- Right-side activity feed
- Cart and checkout panel integrated into the right rail

Additional design analysis is documented in:

```text
DEEP_ANALYSIS_WHITE_UI_UPGRADE.md
```

### React Add-to-Cart Dashboard

The old static frontend was moved into:

```text
frontend/legacy-static/
```

The active frontend is now a Vite React app:

```text
frontend/
├── package.json
├── index.html
└── src/
    ├── App.jsx
    ├── main.jsx
    ├── styles.css
    ├── api/
    │   └── client.js
    ├── components/
    │   ├── CartPanel.jsx
    │   ├── ProductCard.jsx
    │   └── StatCard.jsx
    └── pages/
        ├── CartDashboard.jsx
        └── LoginPage.jsx
```

### New Protected Shop API

The backend now includes:

```text
GET  /api/v1/shop/products
POST /api/v1/shop/checkout
```

Both endpoints require a valid bearer token. The React app logs in through the existing auth endpoint, stores the token, loads products from FastAPI, and submits checkout orders to FastAPI.

The checkout endpoint validates:

- Product existence
- Product stock
- Cart quantity
- Customer name
- Delivery address
- Coupon code `SAVE10`
- Shipping rule: free shipping when subtotal is at least ₱3,000
- Demo VAT/tax calculation: 12%

## Implemented Features

- User login endpoint: `POST /api/v1/auth/token`
- User registration endpoint: `POST /api/v1/auth/register`
- Confirm-password validation during registration
- Frontend and backend password strength validation
- Email verification before login
- Forgot-password and reset-password flow
- Password hashing with `passlib[bcrypt]`
- Signed JWT access and refresh tokens using `python-jose`
- Refresh token endpoint: `POST /api/v1/auth/refresh`
- Protected data route with bearer-token validation
- Protected product catalog route
- Protected checkout route
- React login page
- React add-to-cart dashboard
- Product search and category filtering
- Cart quantity increment/decrement
- Cart clearing
- Checkout form
- Coupon code support
- Order confirmation UI
- Backend tests for auth and shop flow

## Project Structure

```text
.
├── .env.example
├── requirements.txt
├── README.md
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   └── config.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── data.py
│   │   └── shop.py
│   ├── controllers/
│   │   └── auth_controller.py
│   ├── services/
│   │   └── auth_service.py
│   └── tests/
│       ├── conftest.py
│       ├── test_auth_flow.py
│       └── test_shop_flow.py
└── frontend/
    ├── package.json
    ├── index.html
    ├── legacy-static/
    └── src/
```

## How to Run

Run the backend and frontend in two separate terminals.

### 1. Start the Backend

From the project root:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install backend dependencies:

```bash
python -m pip install -r requirements.txt
```

Run FastAPI from the project root:

```bash
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Backend URL:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

### 2. Start the React Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

Demo login:

```text
Email: user@example.com
Password: Password123!
```

## How to Test the Backend

From the project root with the virtual environment activated:

```bash
pytest
```

## Notes for Production Improvement

This is still a prototype. For a production-grade system, the next best upgrades are:

1. Replace the in-memory user store with a real database.
2. Store products and orders in database tables instead of static lists.
3. Add order history per user.
4. Add role-based access control for admin, seller, finance, and customer views.
5. Store refresh tokens in the database so logout and token revocation are secure.
6. Move token storage from `localStorage` to secure HttpOnly cookies.
7. Add payment provider integration.
8. Add Redis caching for product catalog and dashboard metrics.

## MySQL 1045 Access Denied Fix

If backend startup shows:

```text
Access denied for user 'root'@'localhost'
```

run this in MySQL Workbench:

```text
backend/scripts/fix_mysql_access_denied.sql
```

Then set your project-level `.env` to:

```env
DATABASE_URL=mysql+pymysql://finmark_app:FinmarkApp123@127.0.0.1:3306/finmark_db
```

Test it with:

```powershell
python -m backend.scripts.check_database_connection
```


## Full Refactor Notes

This version includes a backend architecture refactor with separated schemas, services, dependencies, security utilities, and database configuration.

For database configuration, you may now use separated `.env` values:

```env
DB_DRIVER=mysql+pymysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=finmark_db
DB_USER=root
DB_PASSWORD=your_mysql_password
```

`DATABASE_URL` is still supported as an override, but it is no longer required for local MySQL Workbench setup.

See `FULL_REFACTOR_GUIDE.md` for the complete explanation.
