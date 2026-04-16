"""Expense API Routes"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import get_logger
from models.database import get_db
from models.schemas import ExpenseCreate
from services.expense_service import add_expense as add_expense_service
from services.expense_service import delete_expense as delete_expense_service
from services.expense_service import get_expenses as get_expenses_service
from services.expense_service import get_summary as get_summary_service
from utils.helpers import StorageError

logger = get_logger(__name__)
router = APIRouter()


@router.post("/expense/add", response_model=None)
def add_expense(expense: ExpenseCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Add a new expense or income record."""
    logger.info(f"Adding {expense.type}: {expense.title} - Rs.{expense.amount}")

    try:
        return add_expense_service(db, expense.title, expense.amount, expense.type, expense.date, expense.crop_id)
    except StorageError as e:
        logger.warning(f"Storage error: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add expense: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add expense")


@router.get("/expense/list", response_model=None)
def get_expenses(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """List all expenses."""
    logger.info("Expenses list endpoint called")
    return get_expenses_service(db)


@router.get("/expense/summary", response_model=None)
def get_summary(db: Session = Depends(get_db)) -> dict[str, float]:
    """Get financial summary (income, expense, profit)."""
    logger.info("Financial summary endpoint called")
    return get_summary_service(db)


@router.delete("/expense/{expense_id}", response_model=None)
def delete_expense(expense_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Delete an expense by ID."""
    logger.info(f"Delete expense endpoint called for ID: {expense_id}")
    result = delete_expense_service(db, expense_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result
