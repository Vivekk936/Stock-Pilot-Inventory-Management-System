# Enterprise Inventory Management System (Backend API)

A robust, enterprise-grade RESTful API built with **Django** and **Django REST Framework (DRF)** for scalable inventory control, warehouse stock tracking, procurement, supplier relations, and compliance audit logging.

---

## Table of Contents

- [Overview & Architecture](#overview--architecture)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Environment Configuration](#environment-configuration)
- [Database Migrations & Seeding](#database-migrations--seeding)
- [Running the Server](#running-the-server)
- [Running the Test Suite](#running-the-test-suite)
- [API Reference](#api-reference)
  - [Authentication](#authentication)
  - [Inventory & Catalogue](#inventory--catalogue)
  - [Stock Movement Operations](#stock-movement-operations)
  - [Reports & Analytics](#reports--analytics)
  - [Suppliers](#suppliers)
  - [Purchasing & PO Receiving](#purchasing--po-receiving)
  - [Audit Logging](#audit-logging)
- [Security & Permissions](#security--permissions)

---

## Overview & Architecture

The backend is engineered following service-layer patterns where core business logic (stock allocation, validation, ledger balancing, and audit generation) resides in dedicated service modules rather than views or serializers.

- **Transactional Consistency**: All multi-step inventory adjustments run within atomic database transactions (`@transaction.atomic`).
- **Atomic Balance Updates**: Inventory balances are calculated and updated with database-level row locking (`select_for_update()`) to prevent race conditions during concurrent stock issues.
- **Audit Immutability**: All critical operations automatically record immutable audit events (`auditlog.AuditEvent`).

---

## Key Features

- **Product & Catalogue Management**: SKU tracking, multi-category organization, cost pricing, selling pricing, and reorder levels.
- **Multi-Warehouse Support**: Distinct storage facilities and inventory segregation.
- **Dual Stock Movement Engine**:
  - Direct ledger issues and count adjustments (`ISSUE`, `ADJUSTMENT_IN`, `ADJUSTMENT_OUT`).
  - Purchase-order item receiving (`RECEIPT`) with automated PO status updates (`ORDERED` -> `PARTIAL` -> `RECEIVED`).
- **Real-Time Reporting**:
  - Automated low-stock alerts based on configurable per-product reorder levels.
  - Live inventory valuation calculated by quantity on hand multiplied by unit cost.
- **Security & RBAC**: Token-based (`TokenAuthentication`) and session-based authentication with granular model permissions and staff authorization guards.
- **Immutable Audit Trail**: Append-only log recording actor, IP address, timestamp, affected entity, and JSON state diffs.

---

## Technology Stack

- **Framework**: Django 5.2 / Django 6.1
- **API Engine**: Django REST Framework (DRF) 3.16+
- **Database**: PostgreSQL (via `psycopg` 3.x)
- **Authentication**: DRF Token Authentication & Session Authentication
- **CORS Support**: `django-cors-headers`
- **Filtering & Search**: `django-filter`, DRF `SearchFilter`, `OrderingFilter`
- **Testing**: `pytest`, `pytest-django`

---

## Project Structure

```text
d:\django\
├── config/                  # Django project root configuration
│   ├── auth_views.py        # Token & session auth endpoints (login, logout, me)
│   ├── settings.py          # DRF, CORS, database, and installed apps config
│   ├── urls.py              # Central URL routing
│   └── wsgi.py              # WSGI application entrypoint
├── inventory/               # Core inventory app
│   ├── models.py            # Category, Product, Warehouse, InventoryBalance, StockMovement
│   ├── permissions.py       # InventoryAccessPermission RBAC class
│   ├── reports.py           # LowStockReportView & InventoryValuationView
│   ├── serializers.py       # DRF serializers for inventory entities
│   ├── services.py          # Atomic change_stock() business logic
│   ├── urls.py              # Inventory router endpoints
│   ├── views.py             # ViewSets for products, categories, balances, movements
│   └── tests.py             # App test cases
├── purchasing/              # Procurement & purchase order app
│   ├── models.py            # PurchaseOrder, PurchaseOrderItem
│   ├── serializers.py       # PO & receiving serializers
│   ├── services.py          # Atomic receive_purchase_order_item() logic
│   ├── urls.py              # Purchase order router endpoints
│   └── views.py             # PurchaseOrderViewSet with item-receiving action
├── suppliers/               # Vendor management app
│   ├── models.py            # Supplier model
│   ├── serializers.py       # Supplier serializer
│   ├── urls.py              # Supplier router endpoints
│   └── views.py             # SupplierViewSet with DjangoModelPermissions
├── auditlog/                # Immutable compliance logging app
│   ├── models.py            # AuditEvent model (immutable save/delete guards)
│   ├── serializers.py       # AuditEvent serializer
│   ├── urls.py              # Audit log router endpoints
│   ├── views.py             # Read-only audit log viewset
│   └── test_api.py          # Auth & audit endpoint unit tests
├── requirements.txt         # Python package dependencies
├── manage.py                # Django CLI utility
└── .env                     # Environment variables (secret keys, DB config)
```

---

## Installation & Setup

### Prerequisites

- **Python**: 3.11+ (Python 3.14 supported)
- **PostgreSQL**: 14+ running locally or remotely

### 1. Clone & Navigate

```bash
cd d:\django
```

### 2. Activate Virtual Environment

```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows Command Prompt
.\venv\Scripts\activate.bat

# Linux/macOS
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Configuration

Create a `.env` file in the project root (see `.env.example`):

```ini
SECRET_KEY=your-secure-django-secret-key
DEBUG=True

DB_NAME=enterprise_inventory
DB_USER=inventory_user
DB_PASSWORD=your_db_password
DB_HOST=127.0.0.1
DB_PORT=5432

ALLOWED_HOSTS=127.0.0.1,localhost
```

---

## Database Migrations & Seeding

### 1. Apply Migrations

```bash
python manage.py migrate
```

### 2. Create an Admin / Superuser

```bash
python manage.py createsuperuser
```

*(You will be prompted for username, email, and password.)*

---

## Running the Server

Start the Django development server:

```bash
python manage.py runserver 127.0.0.1:8000
```

- API Base: `http://127.0.0.1:8000/api/`
- Django Admin: `http://127.0.0.1:8000/admin/`
- Browsable API Auth: `http://127.0.0.1:8000/api-auth/login/`

---

## Running the Test Suite

Run the full pytest suite with Django settings:

```bash
pytest --ds=config.settings
```

To run tests with verbose output:

```bash
pytest --ds=config.settings -v
```

---

## API Reference

All protected endpoints require an `Authorization` header containing a valid DRF Token:

```http
Authorization: Token <your_token_key>
```

*(Session authentication with CSRF tokens is also supported).*

---

### Authentication

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login/` | Authenticate user; returns API token and profile | No |
| `POST` | `/api/auth/logout/` | Invalidate current user token and session | Yes |
| `GET` | `/api/auth/me/` | Get current authenticated user profile | Yes |

#### Login Request Payload
```json
{
  "username": "admin",
  "password": "yourpassword"
}
```

#### Login Success Response (`200 OK`)
```json
{
  "token": "40e7dcab98462c8d140236e3a3d13505381d322c",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_staff": true,
    "is_superuser": true
  }
}
```

---

### Inventory & Catalogue

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` / `POST` | `/api/categories/` | List categories or create a new category |
| `GET` / `PUT` / `PATCH` / `DELETE` | `/api/categories/{id}/` | Retrieve, update, or remove a category |
| `GET` / `POST` | `/api/products/` | List products (supports `?search=`, `?category=`, `?is_active=`) or create product |
| `GET` / `PUT` / `PATCH` / `DELETE` | `/api/products/{id}/` | Retrieve, update, or delete a product |
| `GET` / `POST` | `/api/warehouses/` | List warehouses or register a new warehouse |
| `GET` / `PUT` / `PATCH` / `DELETE` | `/api/warehouses/{id}/` | Retrieve, update, or modify warehouse |
| `GET` | `/api/balances/` | Read-only current stock on hand per product and warehouse |

#### Product Creation Payload (`POST /api/products/`)
```json
{
  "sku": "ELEC-MOUSE-001",
  "name": "Optical Wireless Mouse",
  "category": 1,
  "cost_price": "450.00",
  "selling_price": "799.00",
  "reorder_level": 15,
  "description": "2.4GHz ergonomical mouse",
  "is_active": true
}
```

---

### Stock Movement Operations

All stock movements update warehouse inventory balances atomically and record an immutable audit event.

| Method | Endpoint | Description | Permissions |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/movements/` | View transaction history | `IsAuthenticated` |
| `POST` | `/api/movements/issue/` | Deduct stock (Stock Out) | Staff with `add_stockmovement` |
| `POST` | `/api/movements/adjust_in/` | Count adjustment (Increase stock) | Staff with `add_stockmovement` |
| `POST` | `/api/movements/adjust_out/` | Count adjustment (Decrease stock) | Staff with `add_stockmovement` |

#### Stock Issue / Adjustment Payload
```json
{
  "product_id": 1,
  "warehouse_id": 1,
  "quantity": 5,
  "reason": "Sales dispatch to customer #1042"
}
```

---

### Reports & Analytics

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/reports/low-stock/` | Returns items where quantity on hand ≤ configured reorder level |
| `GET` | `/api/reports/valuation/` | Returns total inventory units and overall valuation based on unit cost |

#### Valuation Response Example
```json
{
  "total_units": 140,
  "inventory_value": "185000.00",
  "valuation_basis": "product cost price"
}
```

---

### Suppliers

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` / `POST` | `/api/suppliers/` | List active suppliers or register a new vendor |
| `GET` / `PUT` / `PATCH` / `DELETE` | `/api/suppliers/{id}/` | Retrieve or modify supplier information |

---

### Purchasing & PO Receiving

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/purchase-orders/` | List purchase orders with nested items |
| `GET` | `/api/purchase-orders/{id}/` | Get details for an individual purchase order |
| `POST` | `/api/purchase-orders/{id}/receive/{item_id}/` | Receive partial or complete quantity for a PO item |

#### Receive PO Item Payload
```json
{
  "quantity": 10
}
```
*Receiving updates warehouse balances, sets PO status to `PARTIAL` or `RECEIVED`, and logs the corresponding audit event.*

---

### Audit Logging

The audit log is an immutable trail capturing user events, entity types, changed details, and IP addresses.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/audit-logs/` | Query audit trail (ordered chronologically descending) |
| `GET` | `/api/audit-logs/{id}/` | Inspect single audit record |

---

## Security & Permissions

1. **Authentication Hierarchy**:
   - `TokenAuthentication`: Primary mechanism for REST consumers (`Authorization: Token <token>`).
   - `SessionAuthentication`: Used for Django admin and browser sessions.
2. **Access Control**:
   - View/Read permissions: Any authenticated user (`IsAuthenticated`).
   - Catalog management (add/change/delete product, category, warehouse): Staff user with corresponding Django model permissions (`InventoryAccessPermission`).
   - Stock movement operations (`issue`, `adjust`, `receive`): Staff users with `inventory.add_stockmovement`.
3. **CORS / CSRF**:
   - Explicitly configured in `config/settings.py` to permit secure cross-origin communication from trusted local and production origins.

