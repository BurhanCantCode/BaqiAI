"""CSV file upload endpoint for user bank statements."""

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.services.csv_parser import CSVParser, CSVParseError

router = APIRouter(prefix="/upload", tags=["Upload"])

# Upload directory configuration
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# File constraints
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".csv"}


@router.post("/csv")
async def upload_csv(
    file: UploadFile = File(...),
    user_id: Optional[int] = Form(None),
    date_col: Optional[str] = Form(None),
    amount_col: Optional[str] = Form(None),
    description_col: Optional[str] = Form(None),
):
    """
    Upload a CSV file containing bank statement transactions.
    
    Args:
        file: CSV file upload
        user_id: Optional user ID for session tracking
        date_col: Optional specific column name for date
        amount_col: Optional specific column name for amount
        description_col: Optional specific column name for description
        
    Returns:
        Upload confirmation with file metadata and transaction count
    """
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only CSV files are allowed. Got: {file_ext}"
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Decode content
    try:
        csv_text = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            csv_text = content.decode('latin-1')
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Unable to decode file. Please ensure it's a valid CSV file with UTF-8 or Latin-1 encoding."
            )
    
    # Parse and validate CSV
    try:
        parser = CSVParser(csv_content=csv_text)
        
        # If column names not specified, try auto-detection
        if not all([date_col, amount_col, description_col]):
            detected = parser.detect_columns()
            
            # Use detected columns if user didn't specify
            date_col = date_col or detected.get("date")
            amount_col = amount_col or detected.get("amount")
            description_col = description_col or detected.get("description")
        
        # Parse transactions
        transactions = parser.parse(date_col, amount_col, description_col)
        
        if len(transactions) < 5:
            raise HTTPException(
                status_code=400,
                detail=f"CSV must contain at least 5 transactions. Found: {len(transactions)}"
            )
        
    except CSVParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing CSV: {str(e)}"
        )
    
    # Generate unique filename
    unique_id = str(uuid.uuid4())
    if user_id:
        filename = f"user_{user_id}_{unique_id}.csv"
    else:
        filename = f"upload_{unique_id}.csv"
    
    file_path = UPLOAD_DIR / filename
    
    # Save file
    try:
        file_path.write_text(csv_text, encoding='utf-8')
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Get date range for summary
    dates = sorted([t["date"] for t in transactions])
    date_range = f"{dates[0]} to {dates[-1]}" if dates else "Unknown"
    
    return JSONResponse({
        "message": "CSV uploaded successfully",
        "filename": filename,
        "file_path": str(file_path),
        "transaction_count": len(transactions),
        "date_range": date_range,
        "detected_columns": {
            "date": date_col,
            "amount": amount_col,
            "description": description_col,
        },
        "upload_id": unique_id,
    })


@router.post("/csv/preview")
async def preview_csv(file: UploadFile = File(...)):
    """
    Preview CSV structure without saving.
    
    Useful for showing users what columns are detected before final upload.
    """
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only CSV files are allowed. Got: {file_ext}"
        )
    
    # Read and decode content
    content = await file.read()
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    try:
        csv_text = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            csv_text = content.decode('latin-1')
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Unable to decode file. Please ensure it's a valid CSV file."
            )
    
    # Get preview
    try:
        parser = CSVParser(csv_content=csv_text)
        preview = parser.get_preview(num_rows=10)
        
        return JSONResponse({
            "headers": preview["headers"],
            "preview_rows": preview["preview_rows"],
            "total_rows": preview["total_rows"],
            "detected_columns": preview["detected_columns"],
            "filename": file.filename,
        })
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error reading CSV: {str(e)}"
        )


@router.get("/csv/{user_id}/info")
async def get_uploaded_csv_info(user_id: int):
    """Get information about user's uploaded CSV file."""
    # Find most recent upload for this user
    user_files = sorted(
        [f for f in UPLOAD_DIR.glob(f"user_{user_id}_*.csv")],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    if not user_files:
        raise HTTPException(
            status_code=404,
            detail="No uploaded CSV found for this user"
        )
    
    file_path = user_files[0]
    
    try:
        parser = CSVParser(csv_path=str(file_path))
        preview = parser.get_preview(num_rows=5)
        transactions = parser.parse()
        
        dates = sorted([t["date"] for t in transactions])
        
        return JSONResponse({
            "filename": file_path.name,
            "transaction_count": len(transactions),
            "date_range": f"{dates[0]} to {dates[-1]}" if dates else "Unknown",
            "detected_columns": preview["detected_columns"],
            "upload_date": file_path.stat().st_mtime,
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading uploaded file: {str(e)}"
        )
