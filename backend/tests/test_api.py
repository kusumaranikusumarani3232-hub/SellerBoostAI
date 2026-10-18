import pytest
import io
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest_asyncio
from main import app
from app.database.db import init_db


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    await init_db()


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


from app.core.config import settings
from app.models.schemas import ModelStatusResponse


@pytest.mark.asyncio
async def test_model_status():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/model-status")
    assert response.status_code == 200
    data = response.json()
    assert "provider" in data
    assert "active_model" in data
    assert "health_status" in data
    # Ensure is_open_weight is strictly a boolean
    assert "is_open_weight" in data
    assert isinstance(data["is_open_weight"], bool)
    assert not isinstance(data["is_open_weight"], str)
    assert data["is_open_weight"] is True
    # Ensure no API keys or secrets are leaked in response
    if settings.BACKBOARD_API_KEY:
        assert settings.BACKBOARD_API_KEY not in response.text
        assert data["is_open_weight"] != settings.BACKBOARD_API_KEY
    # Verify entire response validates against the schema
    validated = ModelStatusResponse(**data)
    assert validated.is_open_weight is True


@pytest.mark.asyncio
async def test_model_status_regression_mock_and_ollama(monkeypatch):
    """Regression test ensuring is_open_weight is strictly boolean across provider configurations."""
    # Test Mock / Demo configuration
    monkeypatch.setattr(settings, "AI_PROVIDER", "mock")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        mock_resp = await ac.get("/api/model-status")
    assert mock_resp.status_code == 200
    mock_data = mock_resp.json()
    assert mock_data["is_open_weight"] is False
    assert isinstance(mock_data["is_open_weight"], bool)
    assert mock_data["provider"] == "mock"
    ModelStatusResponse(**mock_data)

    # Test Ollama configuration
    monkeypatch.setattr(settings, "AI_PROVIDER", "ollama")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        ollama_resp = await ac.get("/api/model-status")
    assert ollama_resp.status_code == 200
    ollama_data = ollama_resp.json()
    assert ollama_data["is_open_weight"] is True
    assert isinstance(ollama_data["is_open_weight"], bool)
    assert ollama_data["provider"] == "ollama"
    ModelStatusResponse(**ollama_data)


@pytest.mark.asyncio
async def test_sample_products():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/samples")
    assert response.status_code == 200
    data = response.json()
    assert "samples" in data
    assert len(data["samples"]) >= 3
    first_sample = data["samples"][0]
    assert "name" in first_sample
    assert "category" in first_sample
    assert "platform" in first_sample


@pytest.mark.asyncio
async def test_generate_and_refine_listing():
    sample_product = {
        "name": "Handmade Olive Wood Cutting Board",
        "category": "Home & Kitchen",
        "features": [
            "Hand-carved from solid Mediterranean olive wood",
            "Unique natural wood grain patterns",
            "Finished with food-safe organic mineral oil",
            "Includes ergonomic thumb hole for hanging"
        ],
        "materials": "Mediterranean Olive Wood, Mineral Oil",
        "target_customer": "Culinary enthusiasts and home chefs",
        "platform": "etsy",
        "tone": "artisanal",
        "language": "en",
        "brand": "Timber & Grain",
        "price": 64.99,
        "dimensions": "14 x 8 x 0.8 inches",
        "care_instructions": "Hand wash with mild soap and dry immediately. Oil monthly."
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Generate listing
        gen_resp = await ac.post("/api/generate", json=sample_product)
        assert gen_resp.status_code == 200
        listing = gen_resp.json()
        assert len(listing["titles"]) >= 1
        assert len(listing["description"]) > 20
        assert len(listing["keywords"]) >= 1
        assert "quality_report" in listing
        assert listing["quality_report"]["overall_score"] > 0

        # Refine listing
        refine_payload = {
            "original_listing": listing,
            "product_data": sample_product,
            "instruction": "Emphasize organic food safety and premium holiday gift appeal"
        }
        ref_resp = await ac.post("/api/refine", json=refine_payload)
        assert ref_resp.status_code == 200
        refined = ref_resp.json()
        assert len(refined["description"]) > 0


@pytest.mark.asyncio
async def test_products_crud_and_save_with_listing():
    product_data = {
        "name": "Ceramic Matcha Whisk Holder",
        "category": "Home & Kitchen",
        "features": ["Glossy speckled glaze", "Preserves whisk shape"],
        "materials": "Ceramic",
        "platform": "etsy",
        "tone": "artisanal",
        "language": "en",
        "brand": "Zen Craft",
        "price": 22.0
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create
        create_resp = await ac.post("/api/products", json=product_data)
        assert create_resp.status_code == 200
        created = create_resp.json()
        pid = created["id"]
        assert created["product_data"]["name"] == product_data["name"]

        # Get
        get_resp = await ac.get(f"/api/products/{pid}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == pid

        # List
        list_resp = await ac.get("/api/products?search=Matcha")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 1

        # Duplicate
        dup_resp = await ac.post(f"/api/products/{pid}/duplicate")
        assert dup_resp.status_code == 200
        dup_id = dup_resp.json()["id"]
        assert dup_id != pid

        # Delete duplicate and original
        del_resp1 = await ac.delete(f"/api/products/{dup_id}")
        assert del_resp1.status_code == 200
        del_resp2 = await ac.delete(f"/api/products/{pid}")
        assert del_resp2.status_code == 200

        # Save with listing
        save_listing_payload = {
            "product": product_data,
            "listing": {
                "titles": [{"title": "Ceramic Matcha Whisk Holder", "char_count": 27, "focus": "Brand"}],
                "description": "Handcrafted whisk holder.",
                "short_description": "Keep your matcha whisk in perfect shape.",
                "benefits": ["Extends life of whisk", "Beautiful aesthetic"],
                "keywords": ["matcha", "tea whisk holder"],
                "tags": ["matcha", "ceramic"],
                "call_to_action": "Order today for tea rituals.",
                "platform_presets": {
                    "etsy": {"title": "Ceramic Whisk Holder", "tags_13": ["matcha"], "materials": ["ceramic"], "description": "Handmade"},
                    "amazon": {"title": "Ceramic Whisk Holder", "bullet_points": ["Point 1"], "product_description": "Desc", "search_terms": ["matcha"]},
                    "shopify": {"page_title": "Whisk Holder", "meta_description": "Meta", "headline": "Headline", "body_html_text": "<p>Body</p>", "feature_highlights": ["Highlight 1"], "call_to_action": "Buy Now"},
                    "ebay": {"title": "Whisk Holder", "item_specifics": {"Material": "Ceramic"}, "formatted_description": "Desc"},
                    "instagram": {"caption": "Tea time vibes", "hook": "Whisk care", "hashtags": ["#matcha"], "call_to_action": "Shop link in bio"}
                },
                "social_content": {
                    "launch_post": "Introducing our whisk holder!",
                    "instagram_caption": "Tea time",
                    "tiktok_reel_hook": "Stop ruining your matcha whisk!",
                    "hashtags": ["#matcha", "#tea"],
                    "call_to_action": "Link in bio"
                },
                "provider_used": "mock",
                "model_used": "sellerboost-demo-v1"
            }
        }
        swl_resp = await ac.post("/api/products/save-with-listing", json=save_listing_payload)
        assert swl_resp.status_code == 200
        swl_record = swl_resp.json()
        assert swl_record["listing"] is not None

        # Clean up
        await ac.delete(f"/api/products/{swl_record['id']}")


@pytest.mark.asyncio
async def test_bulk_csv_workflow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Download template
        tpl_resp = await ac.get("/api/bulk/template")
        assert tpl_resp.status_code == 200
        assert "text/csv" in tpl_resp.headers["content-type"]

        # Preview CSV upload
        csv_content = (
            "name,category,features,materials,target_customer,platform,tone,language,brand,price\n"
            "Handmade Leather Wallet,Accessories,Top-grain leather; 6 card slots,Leather,Men,etsy,artisanal,en,LeatherCo,45.0\n"
            ",Clothing,Missing name,,,,,,,\n"
        )
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        prev_resp = await ac.post("/api/bulk/preview", files=files)
        assert prev_resp.status_code == 200
        prev_data = prev_resp.json()
        assert prev_data["total_rows"] == 2
        assert prev_data["valid_rows"] == 1
        assert prev_data["invalid_rows"] == 1

        # Bulk generate listings
        valid_product = prev_data["items"][0]["product_data"]
        bulk_resp = await ac.post("/api/bulk/generate", json={"products": [valid_product]})
        assert bulk_resp.status_code == 200
        bulk_data = bulk_resp.json()
        assert bulk_data["total"] == 1
        assert bulk_data["succeeded"] == 1
        assert len(bulk_data["results"]) == 1
        assert bulk_data["results"][0]["status"] == "success"
        assert bulk_data["results"][0]["category"] == valid_product["category"]
        assert bulk_data["results"][0]["platform"] == valid_product["platform"]


@pytest.mark.asyncio
async def test_bulk_generate_and_export_three_products():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        csv_content = (
            "name,category,features,materials,target_customer,platform,tone,language,brand,price\n"
            "Handmade Leather Wallet,Accessories,Top-grain leather; 6 card slots,Leather,Men,etsy,artisanal,en,LeatherCo,45.0\n"
            "Wireless Noise-Cancelling Earbuds,Electronics,Active noise cancellation; Bluetooth 5.3,Silicone,Music lovers,amazon,premium,en,SoundWave,89.99\n"
            "Organic Matcha Green Tea,Food & Beverage,Ceremonial grade; 100% organic,Matcha powder,Tea lovers,shopify,friendly,en,ZenTea,29.95\n"
        )
        files = {"file": ("test3.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        prev_resp = await ac.post("/api/bulk/preview", files=files)
        assert prev_resp.status_code == 200
        prev_data = prev_resp.json()
        assert prev_data["total_rows"] == 3
        assert prev_data["valid_rows"] == 3

        products = [item["product_data"] for item in prev_data["items"]]
        bulk_resp = await ac.post("/api/bulk/generate", json={"products": products})
        assert bulk_resp.status_code == 200
        bulk_data = bulk_resp.json()
        assert bulk_data["total"] == 3
        assert bulk_data["succeeded"] == 3

        # Confirm category and platform are populated in the results
        expected_mappings = [
            ("Handmade Leather Wallet", "Accessories", "etsy"),
            ("Wireless Noise-Cancelling Earbuds", "Electronics", "amazon"),
            ("Organic Matcha Green Tea", "Food & Beverage", "shopify"),
        ]
        for i, (name, cat, plat) in enumerate(expected_mappings):
            res = bulk_data["results"][i]
            assert res["product_name"] == name
            assert res["category"] == cat
            assert res["platform"] == plat

        # Confirm CSV export formatting
        export_payload = [
            {"product": p, "listing": r["listing"]}
            for p, r in zip(products, bulk_data["results"])
        ]
        export_resp = await ac.post("/api/bulk/export", json=export_payload)
        assert export_resp.status_code == 200
        exported_csv = export_resp.text
        assert "Accessories" in exported_csv
        assert "Electronics" in exported_csv
        assert "Food & Beverage" in exported_csv


from app.services.quality_auditor import audit_listing
from app.models.schemas import (
    ProductInput, ListingOutput, TitleAlternative,
    PlatformPresets, EtsyPreset, AmazonPreset,
    ShopifyPreset, EbayPreset, InstagramPreset, SocialContent
)
from app.services.ai_provider import BackboardProvider


def _build_test_etsy_listing(tags: list[str]) -> tuple[ProductInput, ListingOutput]:
    product = ProductInput(
        name="Handmade Ceramic Mug",
        category="Home & Living",
        features=["Hand-thrown stoneware", "Food safe glaze"],
        materials="Stoneware Clay, Ceramic Glaze",
        platform="etsy",
        tone="artisanal",
        language="en",
    )
    listing = ListingOutput(
        titles=[TitleAlternative(title="Handmade Ceramic Mug", char_count=20, focus="Artisanal")],
        description="A beautiful handmade ceramic mug crafted with stoneware clay for daily use.",
        short_description="Handmade ceramic mug crafted with stoneware clay.",
        benefits=["Durable stoneware", "Artisan finish"],
        keywords=["ceramic mug", "coffee mug", "handmade pottery", "artisan cup", "pottery"],
        tags=tags,
        call_to_action="Order your handmade ceramic mug today!",
        platform_presets=PlatformPresets(
            etsy=EtsyPreset(
                title="Handmade Ceramic Mug | Artisan Stoneware",
                tags_13=tags,
                materials=["Stoneware Clay"],
                description="Storytelling Etsy description for handmade ceramic mug.",
            ),
            amazon=AmazonPreset(
                title="Ceramic Mug",
                bullet_points=["Handmade quality"],
                product_description="Description",
                search_terms=["ceramic mug"],
            ),
            shopify=ShopifyPreset(
                page_title="Ceramic Mug",
                meta_description="Meta",
                headline="Headline",
                body_html_text="Body",
                feature_highlights=["Feature"],
                call_to_action="Buy Now",
            ),
            ebay=EbayPreset(title="Ceramic Mug", item_specifics={}, formatted_description="Desc"),
            instagram=InstagramPreset(caption="Mug", hook="Hook", hashtags=["#mug"], call_to_action="Bio"),
        ),
        social_content=SocialContent(
            launch_post="Launch",
            instagram_caption="Caption",
            tiktok_reel_hook="Hook",
            hashtags=["#mug"],
            call_to_action="Bio",
        ),
        provider_used="backboard/openrouter",
        model_used=settings.BACKBOARD_DEFAULT_MODEL,
    )
    return product, listing


def test_etsy_tag_length_boundary_20_chars():
    """Tags with exactly 20 characters must be accepted as valid (boundary case: len == 20)."""
    tag_20_chars = "12345678901234567890"
    assert len(tag_20_chars) == 20
    tags = [tag_20_chars] * 13

    product, listing = _build_test_etsy_listing(tags)
    report = audit_listing(product, listing)

    tag_length_item = next((i for i in report.items if i.id == "etsy_tag_length"), None)
    assert tag_length_item is not None
    assert tag_length_item.passed is True
    assert tag_length_item.severity == "info"
    assert "within the 20-character limit" in tag_length_item.message

    tag_count_item = next((i for i in report.items if i.id == "etsy_tags"), None)
    assert tag_count_item is not None
    assert tag_count_item.passed is True
    assert "Exactly 13 Etsy tags" in tag_count_item.message


def test_etsy_tag_length_boundary_21_chars():
    """A tag with 21 characters must be flagged and accurately identified (boundary case: len == 21)."""
    tag_20_chars = "12345678901234567890"
    tag_21_chars = "123456789012345678901"
    assert len(tag_20_chars) == 20
    assert len(tag_21_chars) == 21

    # 12 valid 20-char tags and 1 exceeding 21-char tag
    tags = [tag_20_chars] * 12 + [tag_21_chars]
    product, listing = _build_test_etsy_listing(tags)
    report = audit_listing(product, listing)

    tag_length_item = next((i for i in report.items if i.id == "etsy_tag_length"), None)
    assert tag_length_item is not None
    assert tag_length_item.passed is False
    assert tag_length_item.severity == "warning"
    assert "1 tag(s) exceed Etsy's 20-character limit" in tag_length_item.message
    # Verify the offending tag is accurately identified by name and length
    assert f"'{tag_21_chars}' (21 chars)" in tag_length_item.message
    assert tag_21_chars in tag_length_item.suggestion
    # Verify the 20-char tag is NOT flagged
    assert f"'{tag_20_chars}'" not in tag_length_item.message


def test_etsy_tag_length_multiple_exceeding_tags():
    """Multiple exceeding tags must all be identified with their exact character counts."""
    tag_10 = "short-tag"             # 9 chars
    tag_20 = "exactly-twenty-chars"   # 20 chars
    tag_21 = "twenty-one-characters"  # 21 chars
    tag_28 = "this-is-a-twenty-eight-char"  # 26 chars -> let's make 28
    tag_28 = "twenty-eight-characters-long"  # 27 chars
    assert len(tag_20) == 20
    assert len(tag_21) == 21

    tags = [tag_10, tag_20, tag_21, tag_28] + ["valid-tag"] * 9
    assert len(tags) == 13

    product, listing = _build_test_etsy_listing(tags)
    report = audit_listing(product, listing)

    tag_length_item = next((i for i in report.items if i.id == "etsy_tag_length"), None)
    assert tag_length_item is not None
    assert tag_length_item.passed is False
    assert "2 tag(s) exceed Etsy's 20-character limit" in tag_length_item.message
    assert f"'{tag_21}' (21 chars)" in tag_length_item.message
    assert f"'{tag_28}' ({len(tag_28)} chars)" in tag_length_item.message
    assert f"'{tag_20}'" not in tag_length_item.message
    assert f"'{tag_10}'" not in tag_length_item.message


def test_etsy_tag_count_validation():
    """Etsy tag count must validate exactly 13 tags."""
    # 12 tags -> warning
    product12, listing12 = _build_test_etsy_listing(["tag"] * 12)
    report12 = audit_listing(product12, listing12)
    item12 = next(i for i in report12.items if i.id == "etsy_tags")
    assert item12.passed is False
    assert "12 were generated" in item12.message

    # 13 tags -> passed
    product13, listing13 = _build_test_etsy_listing(["tag"] * 13)
    report13 = audit_listing(product13, listing13)
    item13 = next(i for i in report13.items if i.id == "etsy_tags")
    assert item13.passed is True


@pytest.mark.asyncio
async def test_provider_and_exact_model_reporting():
    """Validate provider and exact model ID reporting, verifying open-weight compliance and zero key leaks."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/model-status")

    assert response.status_code == 200
    data = response.json()

    # Provider and model ID validation
    assert "backboard" in data["provider"].lower()
    assert data["active_model"] == settings.BACKBOARD_DEFAULT_MODEL
    assert data["active_model"] == "meta-llama/llama-3.1-8b-instruct"
    assert "Backboard" in data["display_name"]
    assert "Llama 3.1" in data["display_name"]

    # Open-weight license verification
    assert data["is_open_weight"] is True
    assert "Llama 3.1 Community License" in data["license"]
    assert "700M" in data["license"]

    # Strict privacy: never display or leak API keys
    if settings.BACKBOARD_API_KEY:
        assert settings.BACKBOARD_API_KEY not in response.text
        assert settings.BACKBOARD_API_KEY not in str(data)

    # Validate BackboardProvider health check namespace
    bp = BackboardProvider()
    assert "backboard" in bp.default_provider or f"backboard/{bp.default_provider}" == data["provider"]

