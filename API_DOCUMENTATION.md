# API Documentation

## Authentication

### Register User
```http
POST /api/auth/register/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
}
```

Response:
```json
{
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

Response:
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Financial Management

### Accounts

#### List Accounts
```http
GET /api/finances/accounts/
Authorization: Bearer <access_token>
```

Response:
```json
{
    "count": 2,
    "results": [
        {
            "id": 1,
            "name": "Main Checking",
            "type": "checking",
            "balance": 5000.00,
            "currency": "USD",
            "is_active": true,
            "created_at": "2024-03-15T10:00:00Z"
        },
        {
            "id": 2,
            "name": "Savings",
            "type": "savings",
            "balance": 10000.00,
            "currency": "USD",
            "is_active": true,
            "created_at": "2024-03-15T10:00:00Z"
        }
    ]
}
```

#### Create Account
```http
POST /api/finances/accounts/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "Investment Account",
    "type": "investment",
    "initial_balance": 5000.00,
    "currency": "USD"
}
```

Response:
```json
{
    "id": 3,
    "name": "Investment Account",
    "type": "investment",
    "balance": 5000.00,
    "currency": "USD",
    "is_active": true,
    "created_at": "2024-03-15T10:00:00Z"
}
```

#### Get Account Summary
```http
GET /api/finances/accounts/1/summary/
Authorization: Bearer <access_token>
```

Response:
```json
{
    "id": 1,
    "name": "Main Checking",
    "current_balance": 5000.00,
    "total_income": 3000.00,
    "total_expenses": 2000.00,
    "net_change": 1000.00,
    "transactions_count": 25,
    "last_transaction": "2024-03-15T09:00:00Z",
    "balance_history": [
        {
            "date": "2024-03-01",
            "balance": 4000.00
        },
        {
            "date": "2024-03-15",
            "balance": 5000.00
        }
    ]
}
```

### Transactions

#### List Transactions
```http
GET /api/finances/transactions/
Authorization: Bearer <access_token>
```

Query Parameters:
- `account_id`: Filter by account
- `category_id`: Filter by category
- `start_date`: Filter by start date
- `end_date`: Filter by end date
- `type`: Filter by type (income/expense)
- `search`: Search in description
- `ordering`: Order by field (-field for descending)

Response:
```json
{
    "count": 25,
    "results": [
        {
            "id": 1,
            "account": 1,
            "category": 5,
            "amount": 100.00,
            "type": "expense",
            "description": "Grocery shopping",
            "date": "2024-03-15",
            "created_at": "2024-03-15T10:00:00Z"
        }
    ]
}
```

#### Create Transaction
```http
POST /api/finances/transactions/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "account": 1,
    "category": 5,
    "amount": 100.00,
    "type": "expense",
    "description": "Grocery shopping",
    "date": "2024-03-15"
}
```

Response:
```json
{
    "id": 26,
    "account": 1,
    "category": 5,
    "amount": 100.00,
    "type": "expense",
    "description": "Grocery shopping",
    "date": "2024-03-15",
    "created_at": "2024-03-15T10:00:00Z"
}
```

#### Get Transaction Summary
```http
GET /api/finances/transactions/summary/
Authorization: Bearer <access_token>
```

Query Parameters:
- `start_date`: Start date for summary
- `end_date`: End date for summary
- `account_id`: Filter by account
- `category_id`: Filter by category

Response:
```json
{
    "total_income": 3000.00,
    "total_expenses": 2000.00,
    "net_change": 1000.00,
    "category_breakdown": [
        {
            "category": "Groceries",
            "amount": 500.00,
            "percentage": 25.0
        },
        {
            "category": "Utilities",
            "amount": 300.00,
            "percentage": 15.0
        }
    ],
    "daily_totals": [
        {
            "date": "2024-03-15",
            "income": 1000.00,
            "expenses": 500.00
        }
    ]
}
```

### Categories

#### List Categories
```http
GET /api/finances/categories/
Authorization: Bearer <access_token>
```

Response:
```json
{
    "count": 10,
    "results": [
        {
            "id": 1,
            "name": "Food & Dining",
            "type": "expense",
            "parent": null,
            "created_at": "2024-03-15T10:00:00Z"
        },
        {
            "id": 2,
            "name": "Groceries",
            "type": "expense",
            "parent": 1,
            "created_at": "2024-03-15T10:00:00Z"
        }
    ]
}
```

#### Get Category Tree
```http
GET /api/finances/categories/tree/
Authorization: Bearer <access_token>
```

Response:
```json
{
    "categories": [
        {
            "id": 1,
            "name": "Food & Dining",
            "type": "expense",
            "children": [
                {
                    "id": 2,
                    "name": "Groceries",
                    "type": "expense",
                    "children": []
                }
            ]
        }
    ]
}
```

## AI Features

### Get AI Recommendations
```http
GET /api/ai/recommendations/
Authorization: Bearer <access_token>
```

Response:
```json
{
    "recommendations": [
        {
            "id": 1,
            "type": "savings",
            "title": "Increase Emergency Fund",
            "description": "Based on your spending patterns, consider increasing your emergency fund to cover 6 months of expenses.",
            "confidence_score": 0.85,
            "context_data": {
                "current_emergency_fund": 5000.00,
                "recommended_amount": 15000.00,
                "monthly_expenses": 2500.00
            },
            "created_at": "2024-03-15T10:00:00Z"
        }
    ]
}
```

### Get Stock News
```http
GET /api/ai/stock-news/
Authorization: Bearer <access_token>
```

Query Parameters:
- `symbol`: Stock symbol
- `limit`: Number of news items
- `start_date`: Filter by start date
- `end_date`: Filter by end date

Response:
```json
{
    "news": [
        {
            "id": 1,
            "symbol": "AAPL",
            "title": "Apple Announces New Product Line",
            "content": "Apple Inc. announced a new product line...",
            "source": "Bloomberg",
            "published_at": "2024-03-15T09:00:00Z",
            "sentiment_score": 0.8,
            "impact_score": 0.9
        }
    ]
}
```

### Upload and Process Bill
```http
POST /api/ai/bill-upload/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <file>
```

Response:
```json
{
    "id": 1,
    "file": "bills/bill_20240315.pdf",
    "uploaded_at": "2024-03-15T10:00:00Z",
    "processed": true,
    "extracted_data": {
        "vendor": "Electric Company",
        "amount": 150.00,
        "date": "2024-03-15",
        "due_date": "2024-03-30",
        "account_number": "123456789"
    },
    "transaction": {
        "id": 27,
        "account": 1,
        "category": 3,
        "amount": 150.00,
        "type": "expense",
        "description": "Electric Bill",
        "date": "2024-03-15"
    }
}
```

## Data Management

### Exports

#### List Exports
```http
GET /api/data/exports/
Authorization: Bearer <access_token>
```

Response:
```json
{
    "count": 2,
    "results": [
        {
            "id": 1,
            "export_type": "transactions",
            "format": "csv",
            "file": "exports/transactions_20240315.csv",
            "created_at": "2024-03-15T10:00:00Z",
            "status": "completed",
            "filters": {
                "start_date": "2024-03-01",
                "end_date": "2024-03-15"
            }
        }
    ]
}
```

#### Create Export
```http
POST /api/data/exports/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "export_type": "transactions",
    "format": "csv",
    "filters": {
        "start_date": "2024-03-01",
        "end_date": "2024-03-15"
    }
}
```

Response:
```json
{
    "id": 2,
    "export_type": "transactions",
    "format": "csv",
    "file": null,
    "created_at": "2024-03-15T10:00:00Z",
    "status": "processing",
    "filters": {
        "start_date": "2024-03-01",
        "end_date": "2024-03-15"
    }
}
```

### Visualizations

#### List Visualizations
```http
GET /api/data/visualizations/
Authorization: Bearer <access_token>
```

Response:
```json
{
    "count": 2,
    "results": [
        {
            "id": 1,
            "name": "Monthly Expenses",
            "chart_type": "bar",
            "data_source": "transactions",
            "filters": {
                "start_date": "2024-03-01",
                "end_date": "2024-03-15"
            },
            "configuration": {
                "x_axis": "category",
                "y_axis": "amount",
                "group_by": "month"
            },
            "created_at": "2024-03-15T10:00:00Z",
            "is_public": false
        }
    ]
}
```

#### Create Visualization
```http
POST /api/data/visualizations/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "Income vs Expenses",
    "chart_type": "line",
    "data_source": "transactions",
    "filters": {
        "start_date": "2024-03-01",
        "end_date": "2024-03-15"
    },
    "configuration": {
        "x_axis": "date",
        "y_axis": "amount",
        "series": ["income", "expenses"]
    },
    "is_public": false
}
```

Response:
```json
{
    "id": 3,
    "name": "Income vs Expenses",
    "chart_type": "line",
    "data_source": "transactions",
    "filters": {
        "start_date": "2024-03-01",
        "end_date": "2024-03-15"
    },
    "configuration": {
        "x_axis": "date",
        "y_axis": "amount",
        "series": ["income", "expenses"]
    },
    "created_at": "2024-03-15T10:00:00Z",
    "is_public": false
}
```

#### Get Visualization Data
```http
GET /api/data/visualizations/1/data/
Authorization: Bearer <access_token>
```

Response:
```json
{
    "labels": ["Jan", "Feb", "Mar"],
    "datasets": [
        {
            "label": "Income",
            "data": [3000, 3500, 4000]
        },
        {
            "label": "Expenses",
            "data": [2500, 2800, 3000]
        }
    ]
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
    "error": "Invalid input data",
    "details": {
        "field_name": ["Error message"]
    }
}
```

### 401 Unauthorized
```json
{
    "error": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "error": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
    "error": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
    "error": "An unexpected error occurred"
}
```

## Rate Limiting

API requests are rate-limited to:
- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1615809600
```

## Pagination

List endpoints support pagination with the following query parameters:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10, max: 100)

Response includes pagination metadata:
```json
{
    "count": 100,
    "next": "http://api.example.com/endpoint/?page=2",
    "previous": null,
    "results": [...]
}
```
