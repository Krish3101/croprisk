"""Expense Service
Handles financial tracking and expense management using SQLite database
"""

from typing import Any

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from config import get_logger
from models.database import Expense
from utils.helpers import StorageError, format_date_display, format_date_iso

logger = get_logger(__name__)


def add_expense(db: Session, title: str, amount: float, transaction_type: str, date: str, crop_id: int = None) -> dict[str, Any]:
    """Add a new expense or income transaction

    Args:
        db: Database session
        title: Transaction title/description
        amount: Transaction amount
        transaction_type: Transaction type ("income" or "expense")
        date: Transaction date (YYYY-MM-DD format)
        crop_id: Optional crop ID to link the expense to

    Returns:
        Dictionary with status and new transaction data

    """
    from models.database import Crop

    logger.info(f"Adding {transaction_type}: {title} - ₹{amount}" + (f" (linked to crop {crop_id})" if crop_id else ""))

    try:
        # Validate crop_id exists if provided
        if crop_id is not None:
            crop = db.query(Crop).filter(Crop.id == crop_id).first()
            if not crop:
                logger.warning(f"Crop with ID {crop_id} not found")
                raise StorageError(f"Crop with ID {crop_id} does not exist")

        # Convert and format date
        ts = format_date_iso(date)
        formatted_date = format_date_display(date) if ts else date

        new_expense = Expense(
            title=title,
            amount=float(amount),
            type=transaction_type,
            date=formatted_date,
            description="",  # Optional description
            crop_id=crop_id if crop_id else None,
        )

        db.add(new_expense)
        db.commit()
        db.refresh(new_expense)

        logger.info(f"Successfully added {transaction_type}: {title}")

        return {
            "status": "success",
            "message": "Expense added",
            "data": {
                "id": new_expense.id,
                "title": new_expense.title,
                "amount": new_expense.amount,
                "type": new_expense.type,
                "date": new_expense.date,
                "crop_id": new_expense.crop_id,
                "ts": ts,
            },
        }
    except Exception as e:
        logger.error(f"Error adding expense: {e}")
        db.rollback()
        raise StorageError(f"Failed to add expense: {e}") from e


def get_expenses(db: Session) -> list[dict[str, Any]]:
    """Get all expenses sorted by date (latest first)

    Args:
        db: Database session

    Returns:
        List of expense dictionaries with crop information

    """
    from sqlalchemy.orm import joinedload

    logger.info("Fetching all expenses")

    try:
        # Use joinedload to avoid N+1 query problem
        expenses = db.query(Expense).options(joinedload(Expense.crop)).order_by(desc(Expense.created_at)).all()

        return [
            {
                "id": e.id,
                "title": e.title,
                "amount": e.amount,
                "type": e.type,
                "date": e.date,
                "category": e.category,
                "crop_id": e.crop_id,
                "crop_name": e.crop.crop if e.crop else None,
            }
            for e in expenses
        ]
    except Exception as e:
        logger.error(f"Error fetching expenses: {e}")
        return []


def delete_expense(db: Session, expense_id: int) -> dict[str, Any]:
    """Delete an expense by ID

    Args:
        db: Database session
        expense_id: ID of expense to delete

    Returns:
        Dictionary with status and deleted expense data

    """
    logger.info(f"Deleting expense with ID: {expense_id}")

    try:
        expense = db.query(Expense).filter(Expense.id == expense_id).first()

        if not expense:
            logger.warning(f"Expense not found with ID: {expense_id}")
            return {"error": "Expense not found"}

        # Store data for return
        expense_data = {"id": expense.id, "title": expense.title, "amount": expense.amount, "type": expense.type}

        db.delete(expense)
        db.commit()

        logger.info(f"Successfully deleted expense: {expense.title}")

        return {"status": "success", "message": "Expense deleted", "data": expense_data}
    except Exception as e:
        logger.error(f"Error deleting expense: {e}")
        db.rollback()
        raise StorageError(f"Failed to delete expense: {e}") from e


def get_summary(db: Session) -> dict[str, float]:
    """Get financial summary

    Args:
        db: Database session

    Returns:
        Dictionary with total_income, total_expense, and profit

    """
    logger.info("Calculating financial summary")

    try:
        # Calculate totals using SQL aggregation
        income = db.query(func.sum(Expense.amount)).filter(Expense.type == "income").scalar() or 0.0
        expense = db.query(func.sum(Expense.amount)).filter(Expense.type == "expense").scalar() or 0.0

        profit = income - expense

        logger.info(f"Summary - Income: Rs.{income}, Expense: Rs.{expense}, Profit: Rs.{profit}")

        return {"total_income": float(income), "total_expense": float(expense), "profit": float(profit)}
    except Exception as e:
        logger.error(f"Error calculating summary: {e}")
        return {"total_income": 0.0, "total_expense": 0.0, "profit": 0.0}
