# Finance Tracker & Budgeting App: REST API Documentation

**CORS & Connectivity Note:** If your client receives "connection refused" or CORS error, ensure:
- Backend FastAPI service is running and reachable at the configured base URL.
- The frontend uses the correct base URL (including port—default is 8000 if running locally, or as deployed).
- CORS middleware is enabled to allow your frontend's origin. For debugging, all origins are accepted.
- Backend `/` endpoint (health check) responds with 200 OK if the service is up.

This document provides a human-readable summary of all REST API endpoints offered by the backend. For full technical details, see `openapi.yaml`.

---

## Authentication

### Register
- **POST** `/auth/register`
- **Request**: `{ "username": "alice", "email": "alice@example.com", "password": "secret" }`
- **Response**: `201 Created`
  ```json
  { "access_token": "jwt...", "token_type": "bearer", "user_id": "..." }
  ```
- **Description**: Registers a new user.

### Login
- **POST** `/auth/login`
- **Request**: `{ "username": "alice", "password": "secret" }`
- **Response**: `200 OK` (see above)
- **Description**: Authenticates and returns JWT on success.

### Logout
- **POST** `/auth/logout`
- **Headers**: Requires valid JWT in header.
- **Response**: `204 No Content`
- **Description**: Logout (mainly for frontend).

---

## Transactions

### List Transactions
- **GET** `/transactions?limit=20&offset=0`
- **Headers**: `Authorization: Bearer <token>`
- **Response**: `{ "transactions": [ ... ], "total": 123 }`
- **Description**: Returns all transactions for user (paginated).

### Create Transaction
- **POST** `/transactions`
- **Headers**: JWT
- **Body**:
  ```json
  {
    "amount": 25.50,
    "currency": "USD",
    "category": "Food",
    "type": "expense",
    "date": "2024-06-02T12:23:00Z",
    "description": "Lunch"
  }
  ```
- **Response**: `201 Created`, returns created transaction.

### Retrieve Transaction
- **GET** `/transactions/{transaction_id}`

### Update Transaction (full)
- **PUT** `/transactions/{transaction_id}`

### Update Transaction (partial)
- **PATCH** `/transactions/{transaction_id}`

### Delete Transaction
- **DELETE** `/transactions/{transaction_id}`

---

## Dashboard

### Recent Transactions List
- **GET** `/dashboard/recent?count=5`
- **Headers**: JWT
- **Response**: `{ "recent": [ ... ] }`
- **Description**: Returns up to {count} latest transactions.

---

## Categories & Analytics

### Category Spending Summary
- **GET** `/categories/summary`
- **Headers**: JWT
- **Response**:
  ```json
  { "categories": [ { "category": "Food", "total_spent": 123.25 } ] }
  ```
- **Description**: Total spent grouped by category.

### Budget Analytics
- **GET** `/analytics/budget`
- **Headers**: JWT
- **Response**:
  ```json
  {
    "budgeted": 500,
    "spent": 322,
    "remaining": 178,
    "category_breakdown": [
      { "category": "Food", "spent": 123, "budgeted": 200 }
    ]
  }
  ```
- **Description**: Overall and per-category budget analytics for current month.

---

# Authentication

All endpoints except `/auth/*` require Bearer JWT in `Authorization` header.

# See Also

- Full OpenAPI spec: [`openapi.yaml`](./openapi.yaml)

---

_Maintained automatically. For implementation, see backend source code._
