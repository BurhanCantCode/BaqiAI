"""Pakistani merchant names, spending categories, and PKR ranges for synthetic data."""

MERCHANTS = {
    "salary": ["JS Bank Salary Credit"],
    "rent": ["Monthly Rent Payment"],
    "utilities": [
        "K-Electric Bill",
        "SSGC Gas Bill",
        "PTCL Internet",
        "Jazz Monthly Package",
        "Zong Monthly Package",
    ],
    "groceries": [
        "Imtiaz Super Market",
        "Chase Up",
        "Metro Cash & Carry",
        "Al-Fatah Store",
        "Naheed Supermarket",
    ],
    "transport": [
        "Uber Pakistan",
        "Careem Ride",
        "InDrive",
        "PSO Fuel Station",
        "Shell Pakistan",
        "Total Parco Fuel",
    ],
    "food": [
        "Kababjees",
        "Kolachi Restaurant",
        "Kaybees",
        "Bundu Khan",
        "McDonald's PK",
        "KFC Pakistan",
        "Subway PK",
        "Foodpanda Order",
        "Cheetay Delivery",
    ],
    "entertainment": [
        "Netflix Subscription",
        "Cinepax Ticket",
        "Spotify Premium",
        "YouTube Premium",
        "Cue Studios",
    ],
    "shopping": [
        "Sapphire",
        "Khaadi",
        "Bonanza Satrangi",
        "Daraz.pk",
        "Junaid Jamshed",
        "Alkaram Studio",
        "Ideas by Gul Ahmed",
    ],
    "healthcare": [
        "Aga Khan Hospital",
        "Shaukat Khanum",
        "Dawaai.pk",
        "South City Hospital",
    ],
    "education": [
        "IBA Karachi Fee",
        "LUMS Fee",
        "Coursera Subscription",
        "Udemy Purchase",
    ],
}

# Per-transaction PKR ranges per category (min, max)
# Tuned so total monthly spending is ~80-90% of income, leaving 10-20% baqi
AMOUNT_RANGES = {
    "salary": (100000, 250000),
    "rent": (25000, 60000),
    "utilities": (1500, 4000),
    "groceries": (2000, 5000),
    "transport": (300, 1500),
    "food": (250, 1500),
    "entertainment": (300, 1200),
    "shopping": (800, 4000),
    "healthcare": (500, 4000),
    "education": (5000, 30000),
}

# Categories grouped by spending type
FIXED_CATEGORIES = {"rent", "utilities", "loan", "insurance"}
DISCRETIONARY_CATEGORIES = {"groceries", "transport", "healthcare", "education"}
WATERY_CATEGORIES = {"food", "entertainment", "shopping"}
