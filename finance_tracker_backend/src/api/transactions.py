"""
Transaction and analytics endpoints for the Finance Tracker backend.
Implements all REST endpoints for transactions, dashboard, categories, and analytics,
per the OpenAPI spec and Markdown API documentation.

In-memory database is used for demonstration purposes.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

from .auth import get_current_user, User

router = APIRouter(tags=["Transactions", "Dashboard", "Categories", "Analytics"])

# === Transaction Models ===

class TransactionBase(BaseModel):
    amount: float = Field(..., description="Amount of the transaction")
    currency: str = Field(..., description="Currency code, e.g. 'USD'", example="USD")
    category: str = Field(..., description="Category name, e.g. 'Food'", example="Food")
    type: str = Field(..., description="Transaction type ('income' or 'expense')", example="expense")
    date: datetime = Field(..., description="Datetime of the transaction")
    description: Optional[str] = Field(None, description="Transaction description")

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(TransactionBase):
    pass

class TransactionPartialUpdate(BaseModel):
    """Partial update (PATCH) fields for transaction."""
    amount: Optional[float]
    currency: Optional[str]
    category: Optional[str]
    type: Optional[str]
    date: Optional[datetime]
    description: Optional[str]

class Transaction(TransactionBase):
    id: str = Field(..., description="Transaction ID")
    user_id: str = Field(..., description="User ID transaction belongs to")

class TransactionListResponse(BaseModel):
    transactions: List[Transaction]
    total: int

class CategorySummaryItem(BaseModel):
    category: str
    total_spent: float

class CategorySummaryResponse(BaseModel):
    categories: List[CategorySummaryItem]

class CategoryBreakdownItem(BaseModel):
    category: str
    spent: float
    budgeted: float

class BudgetAnalyticsResponse(BaseModel):
    budgeted: float
    spent: float
    remaining: float
    category_breakdown: List[CategoryBreakdownItem]

class DashboardRecentResponse(BaseModel):
    recent: List[Transaction]


# === In-memory "database" ===

fake_transactions_db: Dict[str, List[Transaction]] = {}  # user_id: [Transaction]
category_budgets = {
    # Example per-category budget
    "Food": 200,
    "Transport": 100,
    "Entertainment": 120,
    "Utilities": 150,
    "Misc": 50,
}
DEFAULT_TOTAL_BUDGET = 500

def get_transactions_for_user(user_id: str) -> List[Transaction]:
    return fake_transactions_db.get(user_id, [])

def save_transaction_for_user(user_id: str, transaction: Transaction):
    fake_transactions_db.setdefault(user_id, []).append(transaction)

def remove_transaction_for_user(user_id: str, transaction_id: str) -> bool:
    txs = fake_transactions_db.get(user_id, [])
    before = len(txs)
    fake_transactions_db[user_id] = [t for t in txs if t.id != transaction_id]
    return len(fake_transactions_db[user_id]) < before

def get_transaction_by_id(user_id: str, tx_id: str) -> Optional[Transaction]:
    return next((t for t in fake_transactions_db.get(user_id, []) if t.id == tx_id), None)

def update_transaction(user_id: str, tx_id: str, tx_data: Dict[str, Any], patch: bool = False) -> Optional[Transaction]:
    tx = get_transaction_by_id(user_id, tx_id)
    if not tx:
        return None
    update_fields = tx_data if patch else {**tx_data}
    for field, value in update_fields.items():
        if value is not None:
            setattr(tx, field, value)
    return tx

# === Transaction Endpoints ===

# PUBLIC_INTERFACE
@router.get(
    "/transactions",
    response_model=TransactionListResponse,
    summary="List all user transactions (optionally paginated)",
    description="Returns a paginated list of all transactions for the current user.",
)
async def list_transactions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.user_id
    txs = get_transactions_for_user(user_id)
    paged = txs[offset:offset+limit]
    return TransactionListResponse(transactions=paged, total=len(txs))


# PUBLIC_INTERFACE
@router.post(
    "/transactions",
    response_model=Transaction,
    status_code=201,
    summary="Create new user transaction",
    description="Creates a new transaction for the current user."
)
async def create_transaction(
    tx_create: TransactionCreate,
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.user_id
    tx_id = str(uuid.uuid4())
    tx = Transaction(id=tx_id, user_id=user_id, **tx_create.dict())
    save_transaction_for_user(user_id, tx)
    return tx

# PUBLIC_INTERFACE
@router.get(
    "/transactions/{transaction_id}",
    response_model=Transaction,
    summary="Retrieve a single transaction by ID",
    description="Get details of a transaction by ID for the current user."
)
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user)
):
    tx = get_transaction_by_id(current_user.user_id, transaction_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx

# PUBLIC_INTERFACE
@router.put(
    "/transactions/{transaction_id}",
    response_model=Transaction,
    summary="Update a transaction (full update)",
    description="Fully update a transaction's fields (PUT)."
)
async def update_transaction_put(
    transaction_id: str,
    tx_update: TransactionUpdate,
    current_user: User = Depends(get_current_user)
):
    tx = get_transaction_by_id(current_user.user_id, transaction_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    newdata = tx_update.dict()
    for field, val in newdata.items():
        setattr(tx, field, val)
    return tx

# PUBLIC_INTERFACE
@router.patch(
    "/transactions/{transaction_id}",
    response_model=Transaction,
    summary="Update a transaction (partial update)",
    description="Partially update a transaction's fields (PATCH)."
)
async def update_transaction_patch(
    transaction_id: str,
    tx_pupdate: TransactionPartialUpdate,
    current_user: User = Depends(get_current_user)
):
    tx = get_transaction_by_id(current_user.user_id, transaction_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    update_data = tx_pupdate.dict(exclude_unset=True)
    for field, val in update_data.items():
        setattr(tx, field, val)
    return tx

# PUBLIC_INTERFACE
@router.delete(
    "/transactions/{transaction_id}",
    status_code=204,
    summary="Delete a transaction by ID",
    description="Delete a transaction by ID for the current user."
)
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user)
):
    success = remove_transaction_for_user(current_user.user_id, transaction_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    # 204 No Content
    return

# === Dashboard Endpoint ===

# PUBLIC_INTERFACE
@router.get(
    "/dashboard/recent",
    response_model=DashboardRecentResponse,
    summary="Retrieve list of the most recent transactions for display on the dashboard",
    description="Returns up to 'count' of the latest transactions for the current user."
)
async def dashboard_recent(
    count: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user)
):
    txs = sorted(get_transactions_for_user(current_user.user_id), key=lambda t: t.date, reverse=True)
    return DashboardRecentResponse(recent=txs[:count])

# === Categories Summary Endpoint ===

# PUBLIC_INTERFACE
@router.get(
    "/categories/summary",
    response_model=CategorySummaryResponse,
    summary="Retrieve spending amounts per category",
    description="Returns total spent grouped by category for the current user."
)
async def categories_summary(
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.user_id
    txs = get_transactions_for_user(user_id)
    category_map: Dict[str, float] = {}
    for tx in txs:
        if tx.type != "expense":
            continue
        category_map[tx.category] = category_map.get(tx.category, 0) + tx.amount
    result = [
        CategorySummaryItem(category=cat, total_spent=amount)
        for cat, amount in category_map.items()
    ]
    return CategorySummaryResponse(categories=result)

# === Budget Analytics Endpoint ===

# PUBLIC_INTERFACE
@router.get(
    "/analytics/budget",
    response_model=BudgetAnalyticsResponse,
    summary="Get analytics on budget vs. spending (current month)",
    description="Overall and per-category budget analytics for the current month."
)
async def analytics_budget(
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.user_id
    now = datetime.now(timezone.utc)
    txs = get_transactions_for_user(user_id)
    # Filter to current month:
    month_txs = [
        tx for tx in txs
        if tx.type == "expense"
        and tx.date.year == now.year
        and tx.date.month == now.month
    ]
    total_budgeted = float(sum(category_budgets.values())) if category_budgets else DEFAULT_TOTAL_BUDGET

    category_spent: Dict[str, float] = {}
    for tx in month_txs:
        category_spent[tx.category] = category_spent.get(tx.category, 0) + tx.amount

    spent = sum(category_spent.values())
    remaining = total_budgeted - spent
    breakdown = [
        CategoryBreakdownItem(
            category=cat,
            spent=category_spent.get(cat, 0.0),
            budgeted=category_budgets.get(cat, 0.0)
        )
        for cat in set(list(category_budgets.keys()) + list(category_spent.keys()))
    ]
    return BudgetAnalyticsResponse(
        budgeted=total_budgeted,
        spent=spent,
        remaining=remaining,
        category_breakdown=breakdown,
    )
