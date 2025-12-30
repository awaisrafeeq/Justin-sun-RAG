# 📅 RAG Chatbot Project - Consolidated Roadmap (Sunday Off)

This roadmap merges the **Old** and **New** timelines and fixes the gaps found in the New timeline:

- The New timeline was missing **Day 6 (Chunking + Vector Storage for Podcasts)**.
- The Generation phase had a mismatch where **Day 13 (Content Generation)** was missing/unclear.

This version enforces **Sunday OFF**.

---

## ⚠️ Note on Deadline
The original plan targets **7 January 2025**, but enforcing **Sunday OFF** shifts the schedule.
This consolidated plan finishes on **9 January 2025**.

---

## ✅ Day-by-Day Plan (Sunday Off)

### Week 1

#### Day 1 — 24 December (Tuesday) ✅
**Goal:** Project Setup & Environment
- [x] Create project folder structure
- [x] Create `requirements.txt`
- [x] Setup virtual environment
- [x] Create `.env.example`
- [x] Setup Docker + `docker-compose.yml`
- [x] Configure PostgreSQL + Redis + Qdrant containers
- [x] Create FastAPI app + config + `/health` endpoint

#### Day 2 — 25 December (Wednesday) ✅
**Goal:** Database Setup
- [x] Create SQLAlchemy models: `rss_feeds`, `episodes`, `documents`
- [x] Setup Alembic + initial migration
- [x] Create DB session/connection handling
- [x] Basic CRUD scaffolding
- [x] Confirm DB tables created

#### Day 3 — 26 December (Thursday) ✅
**Goal:** Docling + Embeddings + Worker Baseline
- [x] Install/configure Docling (PDF + ASR)
- [x] Validate Docling PDF processing with sample PDF
- [x] Validate Docling ASR with sample audio
- [x] Setup embeddings wrapper (OpenAI)
- [x] Setup Celery with Redis + basic task structure
- [x] Setup logging baseline

#### Day 4 — 27 December (Friday) ✅
**Goal:** RSS Parser + Feed Management
- [x] Implement RSS feed parsing (`feedparser`)
- [x] Extract episode fields (title, guid, audio_url, published_at)
- [x] Handle different RSS formats
- [x] Implement feed existence check in DB
- [x] Implement GUID comparison logic (new episodes only)
- [x] API endpoints:
  - [x] `POST /feeds`
  - [x] `GET /feeds`
  - [x] `GET /feeds/{id}/episodes`

#### Day 5 — 28 December (Saturday) ✅
**Goal:** Audio Download + Transcription
- [x] Implement audio download (streaming)
- [x] Temporary storage / cleanup strategy
- [x] Integrate Docling ASR
- [x] Extract timestamps
- [x] Error handling + retries readiness
- [x] Test short + long episodes

#### Sunday OFF — 29 December (Sunday)
- No feature work
- Optional light tasks:
  - Cleanup/refactor
  - Add tests
  - Update docs

---

### Week 2

#### Day 6 — 30 December (Monday) ✅
**Goal:** Chunking + Vector Storage for Podcasts (RESTORED)
- [x] Implement transcript chunking (token/length based) + overlap
- [x] Preserve timestamps in chunks
- [x] Generate embeddings (batch)
- [x] Store chunks in Qdrant with rich metadata
- [x] Store `chunk_ids` back in Postgres episode record
- [x] Validate end-to-end: RSS → Audio → Transcript → Chunks → Vectors

#### Day 7 — 31 December (Tuesday) ✅
**Goal:** Background Processing + Incremental Updates
- [x] Celery task for episode processing (basic setup exists)
- [x] Queue processing + retries
- [x] Progress/status tracking
- [x] Test incremental update:
  - [x] First run processes all
  - [x] Second run only processes new episodes
- [x] Verify no duplicate episodes in Postgres
- [x] Verify no duplicate vectors in Qdrant

#### Day 8 — 1 January (Wednesday)
**Goal:** PDF Processing with Docling
- Implement PDF upload endpoint
- Save uploaded file temporarily
- Process PDF with Docling
- Extract text + tables + OCR (if scanned)
- Implement file hash for duplicate detection
- Store document record in Postgres

#### Day 9 — 2 January (Thursday)
**Goal:** Metadata Extraction + Document Classification
- Setup Claude client
- Document classification (cv/report/article/other)
- CV metadata extraction (name, skills, experience, education)
- General doc metadata extraction (title, author, topics, summary)
- Store metadata (JSONB) in Postgres

#### Day 10 — 3 January (Friday)
**Goal:** PDF Chunking + Vector Storage
- Chunk PDF content + preserve structure
- Add rich metadata (doc_type, extracted_name, section)
- Generate embeddings
- Store in Qdrant
- Store `chunk_ids` on document record
- Document endpoints:
  - `POST /documents/upload`
  - `GET /documents`
  - `GET /documents/{id}`

#### Day 11 — 4 January (Saturday)
**Goal:** Semantic Search + Disambiguation
- Implement query embedding
- Implement vector search with relevance threshold
- Metadata filters (source_type, doc_type, etc.)
- Disambiguation logic (multiple entities)
- Context builder (context window limits)

#### Sunday OFF — 5 January (Sunday)
- No feature work
- Optional light tasks:
  - Integration test runs
  - Fix small bugs

---

### Week 3

#### Day 12 — 6 January (Monday)
**Goal:** Chat Endpoint + Query Handler
- Implement query handler flow:
  - Embed query
  - Vector search
  - Relevance check
  - Disambiguation
  - Build context
- `POST /chat` endpoint
- `POST /search` endpoint
- Return sources + KB vs Web indication

#### Day 13 — 7 January (Tuesday)
**Goal:** Content Generation (RESTORED)
- Generators + prompts:
  - Interview questions (CV)
  - Episode brief (podcast)
  - Summary generator
- Generation endpoints:
  - `POST /generate/interview-questions`
  - `POST /generate/episode-brief`
  - `POST /generate/summary`
- Error handling + tests

#### Day 14 — 8 January (Wednesday)
**Goal:** Web Search Fallback + Integration
- Setup Tavily client
- Web search function + cleaning/parsing
- Fallback logic:
  - If KB score < threshold → web
  - If no KB results → web
- Hybrid response + attribution

#### Day 15 — 9 January (Thursday)
**Goal:** Final Testing + Deployment
- End-to-end testing:
  - RSS ingestion + incremental
  - PDF upload + processing
  - Chat + search
  - Disambiguation
  - Content generation
  - Web fallback
- Fix critical bugs
- Update README + env template
- Deployment + verify production endpoints
- Prepare demo

---

## ✅ Milestones
- **M1 (Foundation):** Day 1–3 (✅ Mostly Complete)
- **M2 (RSS Pipeline):** Day 4–7 (⚠️ Partially Complete)
- **M3 (PDF Pipeline):** Day 8–10 (❌ Not Started)
- **M4 (Retrieval):** Day 11–12
- **M5 (Generation + Web):** Day 13–14
- **M6 (Launch):** Day 15
