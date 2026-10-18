"""
FastAPI REST API routes for SellerBoost AI.
"""
import logging
import traceback
from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import PlainTextResponse

from ..models.schemas import (
    ProductInput, ListingOutput, RefineRequest,
    SavedProductRecord, ProductListResponse,
    BulkImportPreviewResponse, BulkGenerateRequest, BulkGenerateResponse,
    BulkGenerateItemResult, ModelStatusResponse,
)
from ..services.listing_service import generate_listing, refine_listing
from ..services.ai_provider import get_provider, SAMPLE_PRODUCTS
from ..services.csv_utils import generate_csv_template, parse_csv_content, export_listings_csv
from ..database.db import (
    save_product, get_product, list_products,
    delete_product, duplicate_product,
    get_usage_summary,
)
from ..core.config import settings

logger = logging.getLogger("sellerboost.api")

router = APIRouter(prefix="/api", tags=["SellerBoost AI"])


# ─── Health & Status ─────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """Basic health endpoint."""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@router.get("/model-status", response_model=ModelStatusResponse)
async def model_status():
    """Return current AI provider status, model info, and credit usage."""
    provider = get_provider()
    health = await provider.health_check()
    usage = await get_usage_summary()

    is_backboard = bool(settings.AI_PROVIDER == "backboard" and settings.BACKBOARD_API_KEY)
    is_ollama = bool(settings.AI_PROVIDER == "ollama")

    if is_backboard:
        active_model = settings.BACKBOARD_DEFAULT_MODEL
        display_name = "Meta Llama 3.1 8B Instruct (via Backboard + OpenRouter)"
        license_info = "Llama 3.1 Community License — open weights, commercial use permitted under 700M MAU"
        pricing = f"~${settings.INPUT_COST_PER_MILLION}/1M input, ~${settings.OUTPUT_COST_PER_MILLION}/1M output"
        context_limit = 128000
        prov_name = f"backboard/{settings.BACKBOARD_DEFAULT_PROVIDER}"
        notes = "Hosted inference via Backboard sovereign gateway routing through OpenRouter to open-weight Llama 3.1 8B."
        is_open_weight = True
    elif is_ollama:
        active_model = settings.OLLAMA_DEFAULT_MODEL
        display_name = f"{settings.OLLAMA_DEFAULT_MODEL} (Local Ollama)"
        license_info = "Varies by model — check model card"
        pricing = "$0.00 — fully local inference"
        context_limit = 32768
        prov_name = "ollama"
        notes = "100% offline local inference. No data sent to any cloud service."
        is_open_weight = True
    else:
        active_model = "sellerboost-demo-v1"
        display_name = "Demo Mode (Synthetic Responses)"
        license_info = "N/A — synthetic sample data only"
        pricing = "$0.00 — no inference"
        context_limit = 0
        prov_name = "mock"
        notes = "Demo mode active. Set BACKBOARD_API_KEY in .env for live open-weight AI inference."
        is_open_weight = False

    raw_status = health.get("status", "error")
    valid_statuses = {"healthy", "degraded", "demo_mode", "error"}
    health_status = raw_status if raw_status in valid_statuses else "error"

    estimated_used = usage.get("estimated_used_usd", 0.0)
    return ModelStatusResponse(
        provider=prov_name,
        active_model=active_model,
        display_name=display_name,
        license=license_info,
        is_open_weight=is_open_weight,
        context_limit=context_limit,
        pricing_per_1m_tokens=pricing,
        promo_credit_initial_usd=float(settings.INITIAL_PROMO_CREDIT_USD),
        estimated_used_usd=round(float(estimated_used), 6),
        estimated_remaining_usd=round(max(0.0, float(settings.INITIAL_PROMO_CREDIT_USD) - float(estimated_used)), 6),
        total_inferences=int(usage.get("total_inferences", 0)),
        latency_ms=health.get("latency_ms"),
        health_status=health_status,
        notes=notes,
    )


# ─── Sample Products ─────────────────────────────────────────────────────

@router.get("/samples")
async def get_sample_products():
    """Return sample products for demo exploration."""
    samples = []
    for key, data in SAMPLE_PRODUCTS.items():
        samples.append({"id": key, **data})
    return {"samples": samples}


# ─── Listing Generation ──────────────────────────────────────────────────

@router.post("/generate", response_model=ListingOutput)
async def generate_product_listing(product: ProductInput):
    """Generate a complete product listing from product details."""
    try:
        listing = await generate_listing(product)
        return listing
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Generation error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


@router.post("/refine", response_model=ListingOutput)
async def refine_product_listing(request: RefineRequest):
    """Refine an existing listing with plain-language instructions."""
    try:
        listing = await refine_listing(request)
        return listing
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Refinement error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"AI refinement failed: {str(e)}")


# ─── Saved Products ──────────────────────────────────────────────────────

@router.post("/products", response_model=SavedProductRecord)
async def create_product(product: ProductInput):
    """Save a new product to the library."""
    record = await save_product(product)
    return record


@router.post("/products/save-with-listing", response_model=SavedProductRecord)
async def save_product_with_listing(product: ProductInput, listing: Optional[ListingOutput] = None):
    """Save product and its generated listing together."""
    record = await save_product(product, listing)
    return record


@router.get("/products", response_model=ProductListResponse)
async def list_saved_products(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List saved products with optional search and filters."""
    total, products = await list_products(search, category, platform, limit, offset)
    return ProductListResponse(total=total, products=products)


@router.get("/products/{product_id}", response_model=SavedProductRecord)
async def get_saved_product(product_id: str):
    """Get a single saved product by ID."""
    record = await get_product(product_id)
    if not record:
        raise HTTPException(status_code=404, detail="Product not found")
    return record


@router.put("/products/{product_id}", response_model=SavedProductRecord)
async def update_saved_product(product_id: str, product: ProductInput):
    """Update an existing product."""
    existing = await get_product(product_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")
    record = await save_product(product, existing.listing, product_id=product_id)
    return record


@router.delete("/products/{product_id}")
async def delete_saved_product(product_id: str):
    """Delete a product and its listings."""
    deleted = await delete_product(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"status": "deleted", "id": product_id}


@router.post("/products/{product_id}/duplicate", response_model=SavedProductRecord)
async def duplicate_saved_product(product_id: str):
    """Duplicate an existing product."""
    record = await duplicate_product(product_id)
    if not record:
        raise HTTPException(status_code=404, detail="Product not found")
    return record


# ─── Bulk Operations ─────────────────────────────────────────────────────

@router.get("/bulk/template", response_class=PlainTextResponse)
async def download_csv_template():
    """Download a blank CSV template for bulk import."""
    template = generate_csv_template()
    return PlainTextResponse(
        content=template,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sellerboost_template.csv"}
    )


@router.post("/bulk/preview", response_model=BulkImportPreviewResponse)
async def preview_csv_import(file: UploadFile = File(...)):
    """Upload and validate a CSV file without generating listings."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    # Size limit: 5MB
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="CSV file exceeds 5MB limit")

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = content.decode("latin-1")
        except Exception:
            raise HTTPException(status_code=400, detail="Could not decode CSV file")

    preview = parse_csv_content(text)
    return preview


@router.post("/bulk/generate", response_model=BulkGenerateResponse)
async def bulk_generate_listings(request: BulkGenerateRequest):
    """Generate listings for multiple products."""
    results: List[BulkGenerateItemResult] = []

    for idx, product in enumerate(request.products):
        try:
            listing = await generate_listing(product)
            results.append(BulkGenerateItemResult(
                index=idx,
                product_name=product.name,
                category=product.category,
                platform=product.platform,
                status="success",
                listing=listing,
            ))
        except Exception as e:
            logger.error(f"Bulk generation failed for product {idx} '{product.name}': {e}")
            results.append(BulkGenerateItemResult(
                index=idx,
                product_name=product.name,
                category=product.category,
                platform=product.platform,
                status="error",
                error_message=str(e),
            ))

    succeeded = sum(1 for r in results if r.status == "success")
    return BulkGenerateResponse(
        total=len(results),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        results=results,
    )


@router.post("/bulk/export", response_class=PlainTextResponse)
async def export_listings_to_csv(data: List[dict]):
    """Export product listings to CSV."""
    csv_content = export_listings_csv(data)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sellerboost_listings_export.csv"}
    )
