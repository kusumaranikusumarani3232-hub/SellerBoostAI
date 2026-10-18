"""
CSV import/export utilities for bulk listing operations.
"""
import csv
import io
import json
from typing import List, Dict, Any

from ..models.schemas import ProductInput, BulkImportItem, BulkImportPreviewResponse, ListingOutput

# CSV template columns
CSV_COLUMNS = [
    "name", "category", "features", "materials", "target_customer",
    "platform", "tone", "language", "brand", "price", "dimensions",
    "care_instructions", "custom_notes"
]

PLATFORM_OPTIONS = {"etsy", "shopify", "amazon", "ebay", "instagram", "general"}
TONE_OPTIONS = {"artisanal", "premium", "friendly", "concise", "bold", "professional"}


def generate_csv_template() -> str:
    """Generate a blank CSV template string with headers and an example row."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    writer.writerow({
        "name": "Lavender Dreams Hand-Poured Soy Candle",
        "category": "Home & Living",
        "features": "hand-poured; 100% natural soy wax; cotton wick; lavender essential oil; 40-hour burn time",
        "materials": "Natural soy wax, cotton wick, lavender essential oil blend",
        "target_customer": "Home decor enthusiasts, gift shoppers",
        "platform": "etsy",
        "tone": "artisanal",
        "language": "en",
        "brand": "Willow & Bloom",
        "price": "24.99",
        "dimensions": "3 x 3 x 4 inches",
        "care_instructions": "Trim wick to 1/4 inch before each burn",
        "custom_notes": "",
    })
    return output.getvalue()


def parse_csv_content(csv_text: str) -> BulkImportPreviewResponse:
    """Parse CSV text into validated product items with per-row errors."""
    reader = csv.DictReader(io.StringIO(csv_text))
    items: List[BulkImportItem] = []

    for row_num, row in enumerate(reader, start=2):  # Row 1 is header
        errors: List[str] = []
        raw_row: Dict[str, Any] = dict(row)

        name = (row.get("name") or "").strip()
        if not name or len(name) < 2:
            errors.append("Product name is required (min 2 characters)")

        platform = (row.get("platform") or "etsy").strip().lower()
        if platform not in PLATFORM_OPTIONS:
            errors.append(f"Invalid platform '{platform}'. Options: {', '.join(sorted(PLATFORM_OPTIONS))}")
            platform = "etsy"

        tone = (row.get("tone") or "artisanal").strip().lower()
        if tone not in TONE_OPTIONS:
            errors.append(f"Invalid tone '{tone}'. Options: {', '.join(sorted(TONE_OPTIONS))}")
            tone = "artisanal"

        # Parse features (semicolon-separated)
        features_raw = (row.get("features") or "").strip()
        features = [f.strip() for f in features_raw.split(";") if f.strip()] if features_raw else []

        # Parse price
        price = None
        price_str = (row.get("price") or "").strip()
        if price_str:
            try:
                price = float(price_str)
                if price < 0:
                    errors.append("Price must be non-negative")
                    price = None
            except ValueError:
                errors.append(f"Invalid price '{price_str}' — must be a number")

        product_data = None
        if not errors:
            try:
                product_data = ProductInput(
                    name=name,
                    category=(row.get("category") or "General").strip(),
                    features=features,
                    materials=(row.get("materials") or "").strip() or None,
                    target_customer=(row.get("target_customer") or "").strip() or None,
                    platform=platform,
                    tone=tone,
                    language=(row.get("language") or "en").strip(),
                    brand=(row.get("brand") or "").strip() or None,
                    price=price,
                    dimensions=(row.get("dimensions") or "").strip() or None,
                    care_instructions=(row.get("care_instructions") or "").strip() or None,
                    custom_notes=(row.get("custom_notes") or "").strip() or None,
                )
            except Exception as e:
                errors.append(f"Validation error: {str(e)}")

        items.append(BulkImportItem(
            row_number=row_num,
            valid=len(errors) == 0,
            errors=errors,
            product_data=product_data,
            raw_row=raw_row,
        ))

    valid_count = sum(1 for i in items if i.valid)
    return BulkImportPreviewResponse(
        total_rows=len(items),
        valid_rows=valid_count,
        invalid_rows=len(items) - valid_count,
        items=items,
    )


def export_listings_csv(products_with_listings: List[Dict[str, Any]]) -> str:
    """Export products and their generated listings to a CSV string."""
    fieldnames = [
        "product_name", "category", "platform", "tone", "language", "brand", "price",
        "title_1", "title_2", "title_3",
        "description", "short_description",
        "benefits", "keywords", "tags", "call_to_action",
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for item in products_with_listings:
        product = item.get("product", {})
        listing = item.get("listing", {})

        titles = listing.get("titles", [])
        row = {
            "product_name": product.get("name", ""),
            "category": product.get("category", ""),
            "platform": product.get("platform", ""),
            "tone": product.get("tone", ""),
            "language": product.get("language", ""),
            "brand": product.get("brand", ""),
            "price": product.get("price", ""),
            "title_1": titles[0].get("title", "") if len(titles) > 0 else "",
            "title_2": titles[1].get("title", "") if len(titles) > 1 else "",
            "title_3": titles[2].get("title", "") if len(titles) > 2 else "",
            "description": listing.get("description", ""),
            "short_description": listing.get("short_description", ""),
            "benefits": "; ".join(listing.get("benefits", [])),
            "keywords": "; ".join(listing.get("keywords", [])),
            "tags": "; ".join(listing.get("tags", [])),
            "call_to_action": listing.get("call_to_action", ""),
        }
        writer.writerow(row)

    return output.getvalue()
