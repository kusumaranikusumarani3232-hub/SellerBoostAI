# ⚡ SellerBoost AI — Open-Weight AI E-Commerce Listing Assistant

> **Created for the Hacktoberfest DEV Side Hustle Challenge & Best Use of Backboard Challenge.**
> Empowers small online sellers, handmade creators, and marketplace entrepreneurs with open-weight AI to generate search-optimized, platform-tailored product listings in seconds.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178c6.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-6-646cff.svg)](https://vitejs.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v4-38bdf8.svg)](https://tailwindcss.com/)
[![Backboard](https://img.shields.io/badge/AI-Backboard%20SDK-8b5cf6.svg)](https://backboard.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🌟 Overview & Product Vision

Small business owners, handmade artisans, and marketplace sellers spend hours writing product descriptions, researching tags, adhering to marketplace rules, and formatting copy for multiple platforms.

**SellerBoost AI** solves this by combining **open-weight AI models** (Meta Llama 3.1 8B, Qwen 2.5 72B) via **Backboard** with automated quality checks and multi-platform packaging:

- 🎯 **3 Search-Optimized Titles**: Formatted with character counts and strategic focus (SEO, brand, descriptive).
- 📝 **Rich Product Descriptions**: Engaging storytelling, benefit bullet points, and high-converting calls-to-action.
- 🏷️ **Keywords & 13 Tags**: High-intent search terms tailored for discovery algorithms.
- 🛍️ **Platform-Specific Presets**:
  - **Etsy**: 13 tags limit, materials list, handmade story.
  - **Amazon**: 5 key feature bullets, backend search terms, standard product description.
  - **Shopify**: SEO meta title, meta description, HTML content, headline, CTA.
  - **eBay**: Formatted description, item specifics key-value pairs.
  - **Instagram / Social**: Viral hook, caption, relevant hashtags, CTA.
- 🔍 **Quality Auditor**: Real-time score (0–100) checking title length, keyword richness, readability grade (Flesch Reading Ease), and prohibited claim flags.
- 🪄 **Plain-Language Refinement**: Converse with the AI assistant to adjust tone, shorten copy, translate to languages like Hindi or Spanish, or highlight specific materials.
- 📦 **Bulk CSV Processing**: Import CSV catalogues, validate row-by-row, batch generate listings, and export results.
- 📚 **Product Library**: Full persistence via SQLite to store, search, duplicate, edit, and export saved listings.
- 💳 **Backboard Credit Protection**: Transparent tracking of token consumption, latency, and estimated cost against promo credit.

---

## 🏗️ Architecture

```
SellerBoost AI/
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── api/routes.py     # REST API endpoints
│   │   ├── core/config.py    # Environment settings & cost rates
│   │   ├── database/db.py    # aiosqlite asynchronous SQLite storage
│   │   ├── models/schemas.py # Pydantic v2 data models
│   │   └── services/
│   │       ├── ai_provider.py    # Backboard, Ollama, & Mock AI providers
│   │       ├── listing_service.py # Generation, refinement, & quality audit
│   │       └── csv_utils.py      # CSV parser, validation & template builder
│   ├── tests/test_api.py     # Pytest test suite (100% pass)
│   ├── main.py               # FastAPI entry point & lifespan
│   └── requirements.txt      # Python dependencies
│
├── frontend/                 # React 19 + TypeScript + Vite + Tailwind CSS v4
│   ├── src/
│   │   ├── components/       # Layout, ProductForm, ListingWorkspace, QualityPanel,
│   │   │                     # ModelStatusBadge, CopyButton, LoadingSpinner
│   │   ├── pages/            # Dashboard, CreateListing, ProductLibrary, BulkImport
│   │   ├── lib/              # api.ts (Axios client), utils.ts (formatting)
│   │   ├── types/            # TypeScript interfaces matching backend schemas
│   │   ├── App.tsx & main.tsx# Router & Toast providers
│   │   └── index.css         # Modern dark-mode design system
│   ├── package.json
│   └── vite.config.ts        # Vite build & backend proxy (/api -> :8000)
│
├── .env.example              # Environment variables template
└── README.md
```

---

## 🤖 Open-Weight AI & Backboard Integration

SellerBoost AI is built specifically around **open-weight foundation models** rather than closed APIs, preserving sovereignty, cost transparency, and privacy for small merchants.

### Providers Supported:
1. **Backboard (`AI_PROVIDER=backboard`)**:
   - Uses `backboard-sdk` to connect to **Meta Llama 3.1 8B Instruct** (`meta-llama/llama-3.1-8b-instruct`) and **Qwen 2.5 72B** (`qwen/qwen-2.5-72b-instruct`) via OpenRouter.
   - Preserves multi-turn state via Backboard assistant threads for conversational listing refinement.
   - Tracks input/output token usage and calculates costs to protect promo credits.
2. **Ollama (`AI_PROVIDER=ollama`)**:
   - Seamless local execution without internet dependency via local Ollama instances (`http://localhost:11434`).
3. **Demo / Mock Provider (`AI_PROVIDER=mock`)**:
   - Instant, zero-cost deterministic mock generator with rich synthetic listings and instant latency for testing and demos.

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** and **npm**
- (Optional) **Backboard API Key** from [Backboard.io](https://app.backboard.io/dashboard)

### 1. Clone & Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and enter your Backboard API Key:
# BACKBOARD_API_KEY=your_key_here
```

### 2. Backend Setup & Run

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run server (starts on http://127.0.0.1:8000)
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup & Run

```bash
cd frontend

# Install packages
npm install

# Start Vite dev server (starts on http://localhost:5173)
npm run dev
```

Open your browser at **`http://localhost:5173`**.

---

## 🧪 Running Automated Tests

A comprehensive automated test suite validates the entire stack:

```bash
cd backend
python -m pytest tests/test_api.py -v
```

**Results:**
- ✅ `test_health_check`
- ✅ `test_model_status`
- ✅ `test_sample_products`
- ✅ `test_generate_and_refine_listing` (Includes AI generation, quality scoring & conversational refinement)
- ✅ `test_products_crud_and_save_with_listing` (SQLite persistence, duplicate, update, delete)
- ✅ `test_bulk_csv_workflow` (Template download, validation preview, batch generation)

### Production Build Verification

```bash
cd frontend
npm run build
```
Builds cleanly with strict TypeScript compilation (`tsc -b`) and asset optimization.

---

## 🏆 Hacktoberfest & Backboard Challenge Highlights

| Criteria | Implementation in SellerBoost AI |
|---|---|
| **Real Utility for Side Hustles** | Solves the #1 time sink for solo online sellers: writing SEO-rich, compliant, multi-platform listings and social promos. |
| **Open-Weight AI Priority** | Powered by Llama 3.1 8B Instruct and Qwen 2.5 72B via Backboard SDK. |
| **Conversational Memory** | Uses Backboard thread state to refine descriptions seamlessly ("Make it sound more luxury", "Translate to Hindi"). |
| **Credit Safety & Tracking** | Live credit tracking badge monitors tokens, estimated cost, and remaining credit. |
| **No Mock-Only UI** | Fully functional asynchronous FastAPI backend, SQLite persistence, and complete frontend UI. |
| **Batch Production** | Bulk CSV studio allows merchants to import their existing spreadsheets and generate catalog listings in bulk. |

---

## 📄 License

MIT License. Built with passion for open-weight AI and independent creators.
