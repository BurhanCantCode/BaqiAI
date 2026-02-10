"""Generate realistic Pakistani banking transaction data for demo purposes."""

import random
from datetime import date, timedelta

from app.utils.constants import MERCHANTS, AMOUNT_RANGES


def generate_synthetic_transactions(
    user_id: int, months: int = 6, income: int = 150000
) -> list[dict]:
    """
    Generate realistic Pakistani banking transactions for a user.

    Returns a list of transaction dicts ready for Supabase insert.
    """
    transactions = []
    today = date.today()
    start_date = today - timedelta(days=months * 30)

    for month_offset in range(months):
        month_start = start_date + timedelta(days=month_offset * 30)

        # --- Salary on 1st ---
        salary_amount = income + random.randint(-5000, 5000)
        transactions.append(
            _make_txn(
                user_id=user_id,
                txn_date=month_start.replace(day=1),
                amount=salary_amount,
                merchant=random.choice(MERCHANTS["salary"]),
                category="salary",
                is_recurring=True,
                spending_type="income",
            )
        )

        # --- Rent on 5th (fixed, ~30-38% of income) ---
        rent = round(income * random.uniform(0.30, 0.38) / 1000) * 1000
        transactions.append(
            _make_txn(
                user_id=user_id,
                txn_date=month_start.replace(day=5),
                amount=rent,
                merchant=random.choice(MERCHANTS["rent"]),
                category="rent",
                is_recurring=True,
                spending_type="fixed",
            )
        )

        # --- Utilities mid-month (3-4 bills) ---
        for merchant in random.sample(
            MERCHANTS["utilities"], k=random.randint(3, 4)
        ):
            min_amt, max_amt = AMOUNT_RANGES["utilities"]
            transactions.append(
                _make_txn(
                    user_id=user_id,
                    txn_date=_random_date_in_range(
                        month_start.replace(day=10), month_start.replace(day=20)
                    ),
                    amount=random.randint(min_amt, max_amt),
                    merchant=merchant,
                    category="utilities",
                    is_recurring=True,
                    spending_type="fixed",
                )
            )

        # --- Groceries weekly (4 trips) ---
        for week in range(4):
            min_amt, max_amt = AMOUNT_RANGES["groceries"]
            transactions.append(
                _make_txn(
                    user_id=user_id,
                    txn_date=month_start + timedelta(days=7 * week + random.randint(0, 2)),
                    amount=random.randint(min_amt, max_amt),
                    merchant=random.choice(MERCHANTS["groceries"]),
                    category="groceries",
                    is_recurring=False,
                    spending_type="discretionary",
                )
            )

        # --- Transport (8-12 rides per month) ---
        for _ in range(random.randint(8, 12)):
            min_amt, max_amt = AMOUNT_RANGES["transport"]
            transactions.append(
                _make_txn(
                    user_id=user_id,
                    txn_date=_random_date_in_month(month_start),
                    amount=random.randint(min_amt, max_amt),
                    merchant=random.choice(MERCHANTS["transport"]),
                    category="transport",
                    is_recurring=False,
                    spending_type="discretionary",
                )
            )

        # --- Food / dining (6-10 orders per month) --- WATERY ---
        for _ in range(random.randint(6, 10)):
            min_amt, max_amt = AMOUNT_RANGES["food"]
            transactions.append(
                _make_txn(
                    user_id=user_id,
                    txn_date=_random_date_in_month(month_start),
                    amount=random.randint(min_amt, max_amt),
                    merchant=random.choice(MERCHANTS["food"]),
                    category="food",
                    is_recurring=False,
                    spending_type="watery",
                )
            )

        # --- Shopping (2-4 purchases per month) --- WATERY ---
        for _ in range(random.randint(2, 4)):
            min_amt, max_amt = AMOUNT_RANGES["shopping"]
            transactions.append(
                _make_txn(
                    user_id=user_id,
                    txn_date=_random_date_in_month(month_start),
                    amount=random.randint(min_amt, max_amt),
                    merchant=random.choice(MERCHANTS["shopping"]),
                    category="shopping",
                    is_recurring=False,
                    spending_type="watery",
                )
            )

        # --- Entertainment (2-4 per month) --- WATERY ---
        for _ in range(random.randint(2, 4)):
            min_amt, max_amt = AMOUNT_RANGES["entertainment"]
            transactions.append(
                _make_txn(
                    user_id=user_id,
                    txn_date=_random_date_in_month(month_start),
                    amount=random.randint(min_amt, max_amt),
                    merchant=random.choice(MERCHANTS["entertainment"]),
                    category="entertainment",
                    is_recurring=False,
                    spending_type="watery",
                )
            )

        # --- Healthcare (0-1 per month) ---
        if random.random() < 0.4:
            min_amt, max_amt = AMOUNT_RANGES["healthcare"]
            transactions.append(
                _make_txn(
                    user_id=user_id,
                    txn_date=_random_date_in_month(month_start),
                    amount=random.randint(min_amt, max_amt),
                    merchant=random.choice(MERCHANTS["healthcare"]),
                    category="healthcare",
                    is_recurring=False,
                    spending_type="discretionary",
                )
            )

    return transactions


def _make_txn(
    user_id: int,
    txn_date: date,
    amount: int,
    merchant: str,
    category: str,
    is_recurring: bool,
    spending_type: str,
) -> dict:
    return {
        "user_id": user_id,
        "date": txn_date.isoformat(),
        "amount": float(amount),
        "merchant": merchant,
        "category": category,
        "is_recurring": is_recurring,
        "spending_type": spending_type,
    }


def _random_date_in_month(month_start: date) -> date:
    return month_start + timedelta(days=random.randint(0, 29))


def _random_date_in_range(start: date, end: date) -> date:
    delta = (end - start).days
    if delta <= 0:
        return start
    return start + timedelta(days=random.randint(0, delta))
