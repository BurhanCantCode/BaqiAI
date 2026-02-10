from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.database import get_supabase
from app.services.synthetic_data import generate_synthetic_transactions

router = APIRouter(prefix="/demo", tags=["Demo"])


@router.post("/synthetic-data")
async def generate_demo_data(
    name: str = "Asad Khan",
    phone: str = "+923001234567",
    age: int = 28,
    income: int = 150000,
    months: int = 6,
    db: Client = Depends(get_supabase),
):
    """
    Generate a demo user with synthetic Pakistani banking transactions.

    This is the key endpoint for hackathon judges to see realistic data instantly.
    """
    # Create or fetch user
    existing = db.table("users").select("id").eq("phone", phone).execute()

    if existing.data:
        user_id = existing.data[0]["id"]
        # Clear old transactions for fresh demo
        db.table("transactions").delete().eq("user_id", user_id).execute()
        db.table("investments").delete().eq("user_id", user_id).execute()
        db.table("portfolio_snapshots").delete().eq("user_id", user_id).execute()
        # Update user info
        db.table("users").update({
            "name": name,
            "age": age,
            "monthly_income": income,
        }).eq("id", user_id).execute()
    else:
        user_result = (
            db.table("users")
            .insert({
                "name": name,
                "phone": phone,
                "age": age,
                "monthly_income": income,
                "halal_preference": True,
                "risk_profile": "moderate",
            })
            .execute()
        )
        if not user_result.data:
            raise HTTPException(status_code=500, detail="Failed to create demo user")
        user_id = user_result.data[0]["id"]

    # Generate transactions
    transactions = generate_synthetic_transactions(
        user_id=user_id, months=months, income=income
    )

    # Batch insert transactions (Supabase supports bulk insert)
    BATCH_SIZE = 50
    total_inserted = 0
    for i in range(0, len(transactions), BATCH_SIZE):
        batch = transactions[i : i + BATCH_SIZE]
        result = db.table("transactions").insert(batch).execute()
        total_inserted += len(result.data)

    return {
        "message": "Demo data generated successfully",
        "user_id": user_id,
        "user_name": name,
        "transactions_generated": total_inserted,
        "months": months,
        "monthly_income": income,
    }
