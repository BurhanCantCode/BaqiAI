"""Advanced CSV parser with flexible column detection for bank statements.

Handles various CSV formats from different banks with intelligent column mapping.
"""

import csv
import io
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class CSVParseError(Exception):
    """Raised when CSV parsing fails."""
    pass


class CSVParser:
    """Intelligent CSV parser for bank statement files."""
    
    # Common column name patterns
    DATE_PATTERNS = ['date', 'transaction date', 'posted date', 'trans date', 'datetime']
    AMOUNT_PATTERNS = ['amount', 'debit', 'credit', 'transaction amount', 'value', 'sum']
    DESCRIPTION_PATTERNS = ['description', 'merchant', 'name', 'details', 'memo', 'payee', 'transaction']
    
    # Date format patterns to try
    DATE_FORMATS = [
        '%Y-%m-%d',  # 2024-01-15
        '%m/%d/%Y',  # 01/15/2024
        '%d/%m/%Y',  # 15/01/2024
        '%Y/%m/%d',  # 2024/01/15
        '%d-%m-%Y',  # 15-01-2024
        '%m-%d-%Y',  # 01-15-2024
        '%B %d, %Y', # January 15, 2024
        '%b %d, %Y', # Jan 15, 2024
        '%d %b %Y',  # 15 Jan 2024
    ]
    
    def __init__(self, csv_content: str = None, csv_path: str = None):
        """Initialize parser with either content string or file path."""
        if csv_content:
            self.content = csv_content
        elif csv_path:
            path = Path(csv_path)
            self.content = path.read_text(encoding='utf-8', errors='replace')
        else:
            raise ValueError("Either csv_content or csv_path must be provided")
    
    def parse(self, date_col: Optional[str] = None, 
              amount_col: Optional[str] = None,
              description_col: Optional[str] = None) -> List[Dict]:
        """
        Parse CSV and return normalized transaction list.
        
        Args:
            date_col: Specific column name for date (auto-detected if None)
            amount_col: Specific column name for amount (auto-detected if None)
            description_col: Specific column name for description (auto-detected if None)
            
        Returns:
            List of transaction dicts with keys: date, name, amount
        """
        reader = csv.reader(io.StringIO(self.content))
        
        # Read all rows
        rows = [row for row in reader if row and any(cell.strip() for cell in row)]
        
        if len(rows) < 2:
            raise CSVParseError("CSV file must have at least a header row and one data row")
        
        # Detect header row
        header_idx, header = self._detect_header(rows)
        data_rows = rows[header_idx + 1:]
        
        if not data_rows:
            raise CSVParseError("No data rows found in CSV")
        
        # Detect or validate column indices
        date_idx = self._find_column_index(header, self.DATE_PATTERNS, date_col, "date")
        amount_idx = self._find_column_index(header, self.AMOUNT_PATTERNS, amount_col, "amount")
        desc_idx = self._find_column_index(header, self.DESCRIPTION_PATTERNS, description_col, "description")
        
        # Parse transactions
        transactions = []
        errors = []
        
        for i, row in enumerate(data_rows, start=header_idx + 2):
            try:
                txn = self._parse_row(row, date_idx, amount_idx, desc_idx)
                if txn:
                    transactions.append(txn)
            except Exception as e:
                errors.append(f"Row {i}: {str(e)}")
                # Continue parsing other rows
        
        if not transactions:
            error_msg = "No valid transactions found. "
            if errors:
                error_msg += f"Errors: {'; '.join(errors[:3])}"
            raise CSVParseError(error_msg)
        
        return transactions
    
    def detect_columns(self) -> Dict[str, Optional[str]]:
        """Detect column mappings without parsing the full file."""
        reader = csv.reader(io.StringIO(self.content))
        rows = [row for row in reader if row and any(cell.strip() for cell in row)]
        
        if not rows:
            return {"date": None, "amount": None, "description": None}
        
        header_idx, header = self._detect_header(rows)
        
        return {
            "date": self._find_best_match(header, self.DATE_PATTERNS),
            "amount": self._find_best_match(header, self.AMOUNT_PATTERNS),
            "description": self._find_best_match(header, self.DESCRIPTION_PATTERNS),
        }
    
    def get_preview(self, num_rows: int = 10) -> Dict:
        """Get preview of CSV structure for UI display."""
        reader = csv.reader(io.StringIO(self.content))
        rows = [row for row in reader if row and any(cell.strip() for cell in row)]
        
        if not rows:
            return {"headers": [], "preview_rows": [], "total_rows": 0}
        
        header_idx, header = self._detect_header(rows)
        data_rows = rows[header_idx + 1:header_idx + 1 + num_rows]
        total_data_rows = len(rows) - header_idx - 1
        
        return {
            "headers": header,
            "preview_rows": data_rows,
            "total_rows": total_data_rows,
            "detected_columns": self.detect_columns(),
        }
    
    def _detect_header(self, rows: List[List[str]]) -> Tuple[int, List[str]]:
        """Find the header row index and return it."""
        for i, row in enumerate(rows[:5]):  # Check first 5 rows
            # Header likely has text-heavy columns and matches our patterns
            lower_row = [cell.strip().lower() for cell in row]
            
            # Check if this row contains known header patterns
            has_date = any(any(pattern in cell for pattern in self.DATE_PATTERNS) for cell in lower_row)
            has_amount = any(any(pattern in cell for pattern in self.AMOUNT_PATTERNS) for cell in lower_row)
            has_desc = any(any(pattern in cell for pattern in self.DESCRIPTION_PATTERNS) for cell in lower_row)
            
            if (has_date or has_amount) and len(row) >= 2:
                return i, [cell.strip() for cell in row]
        
        # Fallback: assume first row is header
        return 0, [cell.strip() for cell in rows[0]]
    
    def _find_column_index(self, header: List[str], patterns: List[str], 
                          specified_col: Optional[str], col_type: str) -> int:
        """Find column index by pattern matching or specified name."""
        if specified_col:
            # User specified exact column name
            try:
                return header.index(specified_col)
            except ValueError:
                raise CSVParseError(f"Specified {col_type} column '{specified_col}' not found in header")
        
        # Auto-detect
        best_match = self._find_best_match(header, patterns)
        if best_match is None:
            raise CSVParseError(f"Could not detect {col_type} column. Please specify manually.")
        
        return header.index(best_match)
    
    def _find_best_match(self, header: List[str], patterns: List[str]) -> Optional[str]:
        """Find best matching column name for given patterns."""
        lower_header = [col.strip().lower() for col in header]
        
        for pattern in patterns:
            for i, col in enumerate(lower_header):
                if pattern in col:
                    return header[i]
        
        return None
    
    def _parse_row(self, row: List[str], date_idx: int, amount_idx: int, desc_idx: int) -> Optional[Dict]:
        """Parse a single data row into a transaction dict."""
        if len(row) <= max(date_idx, amount_idx, desc_idx):
            return None  # Row too short
        
        # Parse date
        date_str = row[date_idx].strip()
        parsed_date = self._parse_date(date_str)
        if not parsed_date:
            raise ValueError(f"Invalid date format: {date_str}")
        
        # Parse amount
        amount_str = row[amount_idx].strip()
        amount = self._parse_amount(amount_str)
        if amount is None:
            raise ValueError(f"Invalid amount: {amount_str}")
        
        # Parse description
        description = row[desc_idx].strip() if desc_idx < len(row) else "Unknown"
        if not description:
            description = "Unknown"
        
        return {
            "date": parsed_date,
            "name": description,
            "amount": amount,
        }
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format."""
        if not date_str:
            return None
        
        for fmt in self.DATE_FORMATS:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float, handling various formats."""
        if not amount_str:
            return None
        
        # Remove currency symbols, commas, spaces
        cleaned = re.sub(r'[£$€¥₹,\s]', '', amount_str)
        
        # Handle parentheses for negative amounts (e.g., accounting format)
        if '(' in cleaned and ')' in cleaned:
            cleaned = '-' + cleaned.replace('(', '').replace(')', '')
        
        try:
            return float(cleaned)
        except ValueError:
            return None


def parse_uploaded_csv(csv_path: str, date_col: Optional[str] = None,
                      amount_col: Optional[str] = None,
                      description_col: Optional[str] = None) -> List[Dict]:
    """
    Convenience function to parse an uploaded CSV file.
    
    Args:
        csv_path: Path to CSV file
        date_col: Optional specific column name for date
        amount_col: Optional specific column name for amount
        description_col: Optional specific column name for description
        
    Returns:
        List of transaction dicts with keys: date, name, amount
    """
    parser = CSVParser(csv_path=csv_path)
    return parser.parse(date_col, amount_col, description_col)
