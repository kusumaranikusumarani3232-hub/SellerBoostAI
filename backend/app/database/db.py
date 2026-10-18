import aiosqlite
import json
import uuid
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
from ..core.config import settings
from ..models.schemas import ProductInput, ListingOutput, SavedProductRecord

DB_PATH = settings.DATABASE_PATH

async def init_db():
    """Initialize SQLite database schemas."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                features TEXT NOT NULL,
                materials TEXT,
                target_customer TEXT,
                platform TEXT NOT NULL,
                tone TEXT NOT NULL,
                language TEXT NOT NULL,
                brand TEXT,
                price REAL,
                dimensions TEXT,
                care_instructions TEXT,
                custom_notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                listing_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS usage_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                estimated_cost_usd REAL DEFAULT 0.0
            );
        """)
        await db.commit()

async def save_product(product_data: ProductInput, listing: Optional[ListingOutput] = None, product_id: Optional[str] = None) -> SavedProductRecord:
    """Save or update product and optional listing."""
    now_iso = datetime.utcnow().isoformat()
    pid = product_id or str(uuid.uuid4())
    
    features_json = json.dumps(product_data.features)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if product exists
        cursor = await db.execute("SELECT id, created_at FROM products WHERE id = ?", (pid,))
        row = await cursor.fetchone()
        
        if row:
            created_at = row[1]
            await db.execute("""
                UPDATE products SET
                    name = ?, category = ?, features = ?, materials = ?,
                    target_customer = ?, platform = ?, tone = ?, language = ?,
                    brand = ?, price = ?, dimensions = ?, care_instructions = ?,
                    custom_notes = ?, updated_at = ?
                WHERE id = ?
            """, (
                product_data.name, product_data.category, features_json, product_data.materials,
                product_data.target_customer, product_data.platform, product_data.tone, product_data.language,
                product_data.brand, product_data.price, product_data.dimensions, product_data.care_instructions,
                product_data.custom_notes, now_iso, pid
            ))
        else:
            created_at = now_iso
            await db.execute("""
                INSERT INTO products (
                    id, name, category, features, materials, target_customer,
                    platform, tone, language, brand, price, dimensions,
                    care_instructions, custom_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pid, product_data.name, product_data.category, features_json, product_data.materials,
                product_data.target_customer, product_data.platform, product_data.tone, product_data.language,
                product_data.brand, product_data.price, product_data.dimensions,
                product_data.care_instructions, product_data.custom_notes, created_at, now_iso
            ))
        
        if listing:
            listing_json = json.dumps(listing.model_dump())
            lid = str(uuid.uuid4())
            # Replace existing listing for this product or insert new
            await db.execute("DELETE FROM listings WHERE product_id = ?", (pid,))
            await db.execute("""
                INSERT INTO listings (id, product_id, listing_data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (lid, pid, listing_json, created_at, now_iso))
            
        await db.commit()
        
    return SavedProductRecord(
        id=pid,
        product_data=product_data,
        listing=listing,
        created_at=created_at,
        updated_at=now_iso
    )

async def get_product(product_id: str) -> Optional[SavedProductRecord]:
    """Retrieve single product by ID with its latest listing."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT p.id, p.name, p.category, p.features, p.materials, p.target_customer,
                   p.platform, p.tone, p.language, p.brand, p.price, p.dimensions,
                   p.care_instructions, p.custom_notes, p.created_at, p.updated_at,
                   l.listing_data
            FROM products p
            LEFT JOIN listings l ON p.id = l.product_id
            WHERE p.id = ?
        """, (product_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        
        features_list = json.loads(row[3]) if row[3] else []
        prod = ProductInput(
            name=row[1],
            category=row[2],
            features=features_list,
            materials=row[4],
            target_customer=row[5],
            platform=row[6],
            tone=row[7],
            language=row[8],
            brand=row[9],
            price=row[10],
            dimensions=row[11],
            care_instructions=row[12],
            custom_notes=row[13]
        )
        
        listing_obj = None
        if row[16]:
            listing_dict = json.loads(row[16])
            listing_obj = ListingOutput.model_validate(listing_dict)
            
        return SavedProductRecord(
            id=row[0],
            product_data=prod,
            listing=listing_obj,
            created_at=row[14],
            updated_at=row[15]
        )

async def list_products(search: Optional[str] = None, category: Optional[str] = None, platform: Optional[str] = None, limit: int = 50, offset: int = 0) -> Tuple[int, List[SavedProductRecord]]:
    """List products with optional search and filters."""
    query = """
        SELECT p.id, p.name, p.category, p.features, p.materials, p.target_customer,
               p.platform, p.tone, p.language, p.brand, p.price, p.dimensions,
               p.care_instructions, p.custom_notes, p.created_at, p.updated_at,
               l.listing_data
        FROM products p
        LEFT JOIN listings l ON p.id = l.product_id
        WHERE 1=1
    """
    params: List[Any] = []
    
    if search:
        query += " AND (p.name LIKE ? OR p.brand LIKE ? OR p.materials LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])
    if category and category.lower() != "all":
        query += " AND p.category = ?"
        params.append(category)
    if platform and platform.lower() != "all":
        query += " AND p.platform = ?"
        params.append(platform)
        
    count_query = f"SELECT COUNT(*) FROM ({query})"
    
    async with aiosqlite.connect(DB_PATH) as db:
        c_cursor = await db.execute(count_query, params)
        total = (await c_cursor.fetchone())[0]
        
        query += " ORDER BY p.updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        
        results: List[SavedProductRecord] = []
        for r in rows:
            features = json.loads(r[3]) if r[3] else []
            prod = ProductInput(
                name=r[1],
                category=r[2],
                features=features,
                materials=r[4],
                target_customer=r[5],
                platform=r[6],
                tone=r[7],
                language=r[8],
                brand=r[9],
                price=r[10],
                dimensions=r[11],
                care_instructions=r[12],
                custom_notes=r[13]
            )
            listing_obj = None
            if r[16]:
                try:
                    listing_obj = ListingOutput.model_validate(json.loads(r[16]))
                except Exception:
                    pass
            results.append(SavedProductRecord(
                id=r[0],
                product_data=prod,
                listing=listing_obj,
                created_at=r[14],
                updated_at=r[15]
            ))
            
        return total, results

async def delete_product(product_id: str) -> bool:
    """Delete a product and its associated listings."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.execute("DELETE FROM listings WHERE product_id = ?", (product_id,))
        await db.commit()
        return cursor.rowcount > 0

async def duplicate_product(product_id: str) -> Optional[SavedProductRecord]:
    """Duplicate an existing product and its listing."""
    existing = await get_product(product_id)
    if not existing:
        return None
    
    new_data = existing.product_data.model_copy()
    new_data.name = f"{new_data.name} (Copy)"
    
    new_listing = None
    if existing.listing:
        new_listing = existing.listing.model_copy()
        
    return await save_product(new_data, new_listing)

async def record_usage(provider: str, model: str, prompt_tokens: int, completion_tokens: int, cost_usd: float):
    """Record token usage event for credit monitoring."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO usage_tracking (
                timestamp, provider, model, prompt_tokens, completion_tokens,
                total_tokens, estimated_cost_usd
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            provider,
            model,
            prompt_tokens,
            completion_tokens,
            prompt_tokens + completion_tokens,
            cost_usd
        ))
        await db.commit()

async def get_usage_summary() -> Dict[str, Any]:
    """Get aggregated token and cost usage."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT COUNT(*), COALESCE(SUM(total_tokens), 0), COALESCE(SUM(estimated_cost_usd), 0.0)
            FROM usage_tracking
        """)
        row = await cursor.fetchone()
        return {
            "total_inferences": row[0],
            "total_tokens": row[1],
            "estimated_used_usd": round(row[2], 6)
        }
