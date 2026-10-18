"""
Rule-based quality auditor for product listings.
Checks title lengths, missing details, unsupported claims, readability, and SEO basics.
No fake statistics — only transparent, explainable heuristic rules.
"""
import re
import math
from typing import List
from ..models.schemas import (
    ProductInput, ListingOutput, QualityReport,
    QualityAuditItem, ReadabilityStats
)

# Platform-specific title character limits
TITLE_LIMITS = {
    "etsy": 140,
    "amazon": 200,
    "shopify": 70,
    "ebay": 80,
    "instagram": 100,
    "general": 150,
}

# Words/phrases that should NOT appear unless explicitly in product source data
UNSUPPORTED_CLAIM_PATTERNS = [
    r"\bFDA\s+approved\b",
    r"\b100%\s+cure\b",
    r"\bmiracle\b",
    r"\bguaranteed\s+(results?|sales?|weight\s+loss)\b",
    r"\b#1\s+(best|selling|rated)\b",
    r"\bbest\s*seller\b",
    r"\bclinically\s+proven\b",
    r"\bmedically\s+approved\b",
    r"\bcertified\s+organic\b",  # only if not in product.features/materials
    r"\bpatented\b",
]


def _count_syllables(word: str) -> int:
    """Approximate syllable count for English words."""
    word = word.lower().strip()
    if len(word) <= 3:
        return 1
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


def _compute_readability(text: str) -> ReadabilityStats:
    """Compute Flesch reading ease and basic stats."""
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    words = text.split()
    sentence_count = max(len(sentences), 1)
    word_count = len(words)
    syllable_count = sum(_count_syllables(w) for w in words)
    
    avg_words = word_count / sentence_count
    avg_syllables = syllable_count / max(word_count, 1)
    
    # Flesch Reading Ease: 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
    reading_ease = 206.835 - (1.015 * avg_words) - (84.6 * avg_syllables)
    reading_ease = max(0, min(100, round(reading_ease, 1)))
    
    if reading_ease >= 80:
        level = "Very Easy (6th grade)"
    elif reading_ease >= 60:
        level = "Standard (8th-9th grade)"
    elif reading_ease >= 40:
        level = "Somewhat Difficult (10th-12th grade)"
    elif reading_ease >= 20:
        level = "Difficult (College level)"
    else:
        level = "Very Difficult (Professional)"
    
    return ReadabilityStats(
        word_count=word_count,
        sentence_count=sentence_count,
        avg_words_per_sentence=round(avg_words, 1),
        reading_ease_score=reading_ease,
        reading_level=level,
    )


def audit_listing(product: ProductInput, listing: ListingOutput) -> QualityReport:
    """Run all quality checks and return a comprehensive report."""
    items: List[QualityAuditItem] = []
    
    # --- Title checks ---
    platform_limit = TITLE_LIMITS.get(product.platform, 150)
    for i, title_alt in enumerate(listing.titles):
        tid = f"title_length_{i}"
        if title_alt.char_count > platform_limit:
            items.append(QualityAuditItem(
                id=tid, category="title", title=f"Title {i+1} Length",
                passed=False, severity="warning",
                message=f"Title '{title_alt.title[:40]}...' is {title_alt.char_count} chars, exceeding {product.platform} limit of {platform_limit}.",
                suggestion=f"Shorten to {platform_limit} characters or fewer."
            ))
        else:
            items.append(QualityAuditItem(
                id=tid, category="title", title=f"Title {i+1} Length",
                passed=True, severity="info",
                message=f"Title {i+1} is {title_alt.char_count} chars — within {product.platform} limit."
            ))
    
    # --- Missing details checks ---
    if not product.materials:
        items.append(QualityAuditItem(
            id="missing_materials", category="details", title="Materials Not Specified",
            passed=False, severity="warning",
            message="No materials or ingredients specified. Buyers value knowing what a product is made of.",
            suggestion="Add materials in the product form for richer listings."
        ))
    else:
        items.append(QualityAuditItem(
            id="materials_present", category="details", title="Materials Specified",
            passed=True, severity="info",
            message="Materials information is included."
        ))
    
    if not product.dimensions:
        items.append(QualityAuditItem(
            id="missing_dimensions", category="details", title="Dimensions Not Specified",
            passed=False, severity="info",
            message="No product dimensions provided. Size info helps reduce returns.",
            suggestion="Add dimensions (e.g., '5 x 3 x 2 inches') to improve buyer confidence."
        ))
    
    if not product.care_instructions:
        items.append(QualityAuditItem(
            id="missing_care", category="details", title="Care Instructions Missing",
            passed=False, severity="info",
            message="No care instructions provided.",
            suggestion="Add washing, storage, or maintenance instructions."
        ))
    
    if not product.target_customer:
        items.append(QualityAuditItem(
            id="missing_target", category="details", title="Target Customer Not Defined",
            passed=False, severity="info",
            message="No target audience specified. Defining your ideal buyer helps AI write more targeted copy.",
            suggestion="Describe who this product is for (e.g., 'new mothers', 'home office workers')."
        ))
    
    # --- Unsupported claims ---
    # Build a set of facts from the product
    product_facts = " ".join([
        product.name, product.category,
        " ".join(product.features or []),
        product.materials or "",
        product.custom_notes or "",
    ]).lower()
    
    all_generated_text = " ".join([
        listing.description,
        listing.short_description,
        listing.call_to_action,
        " ".join(listing.benefits),
    ])
    
    for pattern in UNSUPPORTED_CLAIM_PATTERNS:
        matches = re.findall(pattern, all_generated_text, re.IGNORECASE)
        for match in matches:
            # Check if the claim exists in the original product facts
            if not re.search(pattern, product_facts, re.IGNORECASE):
                items.append(QualityAuditItem(
                    id=f"claim_{match.replace(' ', '_').lower()[:30]}",
                    category="compliance",
                    title="Potential Unsupported Claim",
                    passed=False, severity="critical",
                    message=f"Found '{match}' in generated content but not in your product details.",
                    suggestion="Remove or verify this claim. Only include certifications and claims you can substantiate."
                ))
    
    if not any(i.category == "compliance" for i in items):
        items.append(QualityAuditItem(
            id="claims_clean", category="compliance", title="No Unsupported Claims Detected",
            passed=True, severity="info",
            message="No potentially unsupported claims were found in the generated content."
        ))
    
    # --- SEO checks ---
    if len(listing.keywords) < 5:
        items.append(QualityAuditItem(
            id="few_keywords", category="seo", title="Few Keywords Generated",
            passed=False, severity="warning",
            message=f"Only {len(listing.keywords)} keywords generated. More keywords improve discoverability.",
            suggestion="Aim for 10-15 relevant keywords."
        ))
    else:
        items.append(QualityAuditItem(
            id="keywords_ok", category="seo", title="Keywords Count",
            passed=True, severity="info",
            message=f"{len(listing.keywords)} keywords generated."
        ))
    
    # Check if product name appears in description
    name_words = [w.lower() for w in product.name.split() if len(w) > 3]
    desc_lower = listing.description.lower()
    name_in_desc = any(w in desc_lower for w in name_words)
    items.append(QualityAuditItem(
        id="name_in_desc", category="seo", title="Product Name in Description",
        passed=name_in_desc, severity="warning" if not name_in_desc else "info",
        message="Product name appears in description." if name_in_desc else "Product name keywords not found in description.",
        suggestion=None if name_in_desc else "Include key product name words in the description for SEO."
    ))
    
    # Etsy 13 tags check
    if product.platform == "etsy":
        etsy_preset = getattr(listing.platform_presets, "etsy", None) if listing.platform_presets else None
        etsy_tags = getattr(etsy_preset, "tags_13", []) if etsy_preset else []
        if len(etsy_tags) != 13:
            items.append(QualityAuditItem(
                id="etsy_tags", category="seo", title="Etsy Tag Count",
                passed=False, severity="warning",
                message=f"Etsy allows exactly 13 tags but {len(etsy_tags)} were generated.",
                suggestion="Adjust to exactly 13 tags."
            ))
        else:
            items.append(QualityAuditItem(
                id="etsy_tags", category="seo", title="Etsy Tag Count",
                passed=True, severity="info",
                message="Exactly 13 Etsy tags generated."
            ))

        long_tags = [t for t in etsy_tags if len(t) > 20]
        if long_tags:
            tag_details = [f"'{t}' ({len(t)} chars)" for t in long_tags]
            items.append(QualityAuditItem(
                id="etsy_tag_length", category="seo", title="Etsy Tag Length",
                passed=False, severity="warning",
                message=f"{len(long_tags)} tag(s) exceed Etsy's 20-character limit: {', '.join(tag_details)}.",
                suggestion=f"Shorten exceeding tags to 20 characters or fewer: {', '.join(f'\"{t}\"' for t in long_tags)}."
            ))
        else:
            items.append(QualityAuditItem(
                id="etsy_tag_length", category="seo", title="Etsy Tag Length",
                passed=True, severity="info",
                message="All Etsy tags are within the 20-character limit."
            ))
    
    # --- Readability ---
    readability = _compute_readability(listing.description)
    items.append(QualityAuditItem(
        id="readability", category="readability", title="Description Readability",
        passed=readability.reading_ease_score >= 40,
        severity="info" if readability.reading_ease_score >= 40 else "warning",
        message=f"Flesch Reading Ease: {readability.reading_ease_score} ({readability.reading_level}). {readability.word_count} words, {readability.sentence_count} sentences.",
        suggestion=None if readability.reading_ease_score >= 40 else "Consider shorter sentences and simpler words to improve readability."
    ))
    
    # --- Description length ---
    if readability.word_count < 50:
        items.append(QualityAuditItem(
            id="desc_short", category="details", title="Short Description",
            passed=False, severity="warning",
            message=f"Description is only {readability.word_count} words. Aim for 100-250 words.",
            suggestion="Expand the description with more product details and use cases."
        ))
    elif readability.word_count > 400:
        items.append(QualityAuditItem(
            id="desc_long", category="details", title="Long Description",
            passed=False, severity="info",
            message=f"Description is {readability.word_count} words. Some platforms work best under 300 words.",
            suggestion="Consider trimming for conciseness."
        ))
    
    # --- Score calculation ---
    total_checks = len(items)
    passed_checks = sum(1 for i in items if i.passed)
    critical_fails = sum(1 for i in items if not i.passed and i.severity == "critical")
    warning_fails = sum(1 for i in items if not i.passed and i.severity == "warning")
    
    score = round(100 * passed_checks / max(total_checks, 1))
    score = max(0, score - (critical_fails * 10) - (warning_fails * 3))
    score = max(0, min(100, score))
    
    if score >= 85:
        grade = "A — Excellent"
    elif score >= 70:
        grade = "B — Good"
    elif score >= 55:
        grade = "C — Needs Improvement"
    elif score >= 40:
        grade = "D — Poor"
    else:
        grade = "F — Significant Issues"
    
    compliance_notes = []
    if any(not i.passed and i.severity == "critical" for i in items):
        compliance_notes.append("⚠️ Critical compliance issues detected. Review flagged claims before publishing.")
    compliance_notes.append("Quality scores are heuristic-based and do not predict sales or search rankings.")
    
    return QualityReport(
        overall_score=score,
        grade=grade,
        passed_checks=passed_checks,
        total_checks=total_checks,
        items=items,
        readability=readability,
        compliance_notes=compliance_notes,
    )
