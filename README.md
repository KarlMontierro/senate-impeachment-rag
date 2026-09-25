# Philippine Senate Impeachment Records AI Assistant

A local retrieval-augmented generation (RAG) research assistant for publicly
available Philippine Senate impeachment records.

## Project Goal

The system collects public Philippine Senate impeachment records, processes
their contents, indexes the documents, and allows users to ask questions
about the records with page-level source citations.

The system is designed to provide neutral, source-grounded answers based on
the retrieved Senate records rather than unsupported model knowledge.

## Current Status

**Day 1 — Project Foundation + Data Acquisition: Completed**

Current progress:

- Project structure created
- Git and GitHub repository configured
- Official Senate impeachment document source identified
- Senate published-records API identified
- Document discovery crawler implemented
- Document manifest generated
- 95 records discovered
- 88 PDF documents discovered
- 7 video files discovered
- PDF download process verified
- SHA-256 file hashing verified
- First Senate PDF successfully downloaded and verified

## Official Data Source

Philippine Senate Impeachment Documents:

https://senate.gov.ph/services/impeachment-documents

The system uses the Senate's published-records endpoint for document
discovery:

https://senate.gov.ph/hq/impeachment/published

The API provides information such as:

- Case number
- Parties/categories
- Sections
- Document labels
- Filenames
- Document paths
- Video files

## Current Corpus

The currently discovered corpus contains:

| Category | PDFs | Videos |
|---|---:|---:|
| Prosecution | 24 | 7 |
| Defense | 19 | 0 |
| Court Issuances | 13 | 0 |
| Journal | 28 | 0 |
| Memoranda | 4 | 0 |
| **Total** | **88** | **7** |

The current implementation focuses on PDF documents.
Video processing is planned for a later phase.

## Architecture

Planned system architecture:

```text
Senate Website
      │
      ▼
Document Discovery API
      │
      ▼
Document Crawler
      │
      ▼
PDF Downloader
      │
      ▼
Document Processing
      │
      ├── Text Extraction
      ├── OCR Fallback
      └── Page Detection
      │
      ▼
Page-Aware Chunking
      │
      ▼
Embeddings
      │
      ▼
PostgreSQL + pgvector
      │
      ▼
FastAPI Backend
      │
      ├── Query Processing
      ├── Hybrid Retrieval
      ├── Reranking
      └── Context Building
      │
      ▼
LLM Provider
      │
      ▼
Answer + Page Citations
      │
      ▼
React Frontend
Planned Technology Stack
Backend
Python
FastAPI
PostgreSQL
pgvector
AI / RAG
Ollama
Qwen3 8B
nomic-embed-text
Embeddings
Semantic retrieval
Reranking
Frontend
React
Vite
Document Processing
Python PDF processing libraries
OCR
Page-aware text extraction
Development
Git
GitHub
VS Code
Local LLM Architecture

The project is designed to run locally during development.

The initial configuration uses:

LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3:8b
OLLAMA_URL=http://localhost:11434

The project will use a provider abstraction rather than calling Ollama
directly throughout the application.

This allows the local LLM to be replaced with a hosted model later without
rewriting the RAG pipeline.

Planned structure:

providers/
├── llm/
│   ├── base.py
│   ├── ollama.py
│   └── hosted.py
│
└── embeddings/
    ├── base.py
    ├── ollama.py
    └── hosted.py
Repository Structure
senate-impeachment-rag/
│
├── backend/
│   └── FastAPI application
│
├── frontend/
│   └── React + Vite application
│
├── crawler/
│   ├── inspect_source.py
│   ├── test_published_api.py
│   ├── discover_documents.py
│   └── download_test.py
│
├── document_processing/
│   └── PDF extraction and OCR
│
├── evaluation/
│   └── RAG evaluation
│
├── scripts/
│   └── Utility scripts
│
├── tests/
│   └── Automated tests
│
├── docs/
│   └── data-source.md
│
├── data/
│   └── Local document data
│
├── .env.example
├── .gitignore
├── README.md
└── docker-compose.yml
Document Acquisition

The crawler discovers documents from the Senate published-records API.

The API returns paths such as:

/uploads/impeachment/...

The actual browser-accessible PDF path uses:

/hq/uploads/impeachment/...

The downloader converts the API path into the accessible PDF URL before
downloading.

Example:

API path:

/uploads/impeachment/prosecution/articles_of_impeachment/CR00261.pdf

Download path:

/hq/uploads/impeachment/prosecution/articles_of_impeachment/CR00261.pdf
Document Manifest

The crawler generates:

data/document_manifest.json

The manifest stores document metadata including:

{
  "id": 1,
  "label": "CR00261",
  "filename": "CR00261.pdf",
  "category": "Prosecution",
  "category_slug": "prosecution",
  "section_id": 1,
  "section_title": "Articles of Impeachment",
  "file_type": "pdf",
  "source_url": "https://senate.gov.ph/hq/impeachment/published",
  "file_url": "https://senate.gov.ph/uploads/..."
}

Generated document data is excluded from Git through .gitignore.

Downloaded Documents

Downloaded documents are stored locally under:

data/documents/

with category-based folders:

data/
└── documents/
    ├── prosecution/
    ├── defense/
    ├── court_issuances/
    ├── journal/
    └── memoranda/

Large PDF files and generated document data are intentionally not committed
to GitHub.

File Integrity

Each downloaded document receives a SHA-256 hash.

Example:

CR00261.pdf

SHA-256:
3f38a43be1d8ae714a69ac635b02e68123cf99ed20c681a44d8fc88c15471341

The hash will later be used for duplicate detection and detecting whether a
previously downloaded document has changed.

RAG Pipeline

The planned RAG pipeline is:

User Question
      │
      ▼
Query Processing
      │
      ▼
Query Embedding
      │
      ▼
Document Retrieval
      │
      ├── Semantic Search
      └── Metadata / Keyword Search
      │
      ▼
Reranking
      │
      ▼
Context Builder
      │
      ▼
Local / Hosted LLM
      │
      ▼
Grounded Answer
      │
      ▼
Page-Level Citations

The system should answer using retrieved source material.

If the available records do not provide enough evidence to answer a question,
the system should state that the records do not provide sufficient
information rather than inventing an answer.

Database Design

The planned database contains:

Documents
documents
├── id
├── title
├── category
├── document_date
├── source_url
├── file_path
├── file_hash
├── file_size
├── status
├── created_at
└── updated_at
Pages
pages
├── id
├── document_id
├── page_number
└── text
Chunks
chunks
├── id
├── document_id
├── page_id
├── chunk_index
├── text
└── embedding

Page-level storage is important because citations need to point back to the
specific page containing the retrieved information.

Neutrality and Source Handling

The assistant is designed as a neutral research tool.

The system should:

Use retrieved Senate records as the primary evidence
Distinguish prosecution documents from defense documents
Distinguish court issuances from party arguments
Distinguish allegations and arguments from established facts
Avoid unsupported conclusions
Cite the source document and page
State when the available records do not answer a question

The assistant should not merge claims from different parties into a single
undifferentiated factual statement.

Security Considerations

The system should account for:

Prompt injection inside retrieved documents
Malicious or unexpected document content
Sensitive information contained in public records
Unbounded resource consumption
Excessively large queries
Arbitrary URL fetching
Arbitrary file uploads
Shell or code execution through user prompts

Retrieved document text should be treated as data, not as instructions to the
LLM or application.

Development Roadmap
Day 1 — Foundation + Data Acquisition

Completed

Project setup
Git/GitHub
Senate source investigation
API discovery
Document crawler
Document manifest
PDF download proof of concept
SHA-256 verification
Day 2 — Database + Document Processing

Next:

Build PostgreSQL database
Configure pgvector
Download all 88 PDFs
Store document metadata
Calculate SHA-256 hashes
Extract PDF text page-by-page
Add OCR fallback
Store page text
Day 3 — Chunking + Embeddings
Implement page-aware chunking
Generate embeddings
Store embeddings in pgvector
Implement semantic search
Return document, page, text, similarity, and source URL
Day 4 — RAG Pipeline
Query embedding
Retrieve relevant chunks
Reranking
Context construction
LLM integration
Page-level citations
Insufficient-evidence handling
Day 5 — React Interface
Chat interface
Source citations
Document filters
Document detail view
Original document links
Corpus information
Day 6 — Automatic Updates + Security
Re-check Senate API
Detect new documents
Detect changed documents
Compare URLs and SHA-256 hashes
Add rate/context limits
Security controls
Prompt-injection handling
Day 7 — Evaluation

Create approximately 30–50 evaluation questions covering:

Retrieval accuracy
Citation accuracy
Faithfulness
Answer completeness
Hallucination rate
Latency
Failure cases

Document the results and include them in the project README.

Phase 2

Potential future features:

Hybrid BM25 + semantic retrieval
Improved reranking
Video ingestion
Timeline browsing
Model benchmarking
Public deployment

These features are intentionally outside the initial MVP.

Definition of Done

The project will be considered complete when:

Data Acquisition
Senate documents can be discovered automatically
PDFs can be downloaded
Metadata is stored
Duplicate documents can be detected
Changed documents can be detected
Page text can be extracted
OCR is available for scanned documents
Retrieval
Embeddings are generated
pgvector stores embeddings
Relevant sources are retrieved
Retrieval results include page information
RAG
Questions can be answered using retrieved records
Answers are grounded in retrieved sources
Citations identify the relevant document and page
The system can indicate insufficient evidence
Application
FastAPI backend is functional
React frontend is functional
Users can search/chat with the corpus
Users can inspect sources
Users can open original Senate documents
Evaluation
Retrieval is evaluated
Citation accuracy is evaluated
Faithfulness is evaluated
Completeness is evaluated
Hallucination cases are documented
Latency is measured
Project Quality
Environment variables are documented
LLM providers are replaceable
GitHub repository is clean
README documents setup and architecture
Local development works from a fresh environment
Portfolio Description

Developed a continuously updated retrieval-augmented generation system for
publicly available Philippine Senate impeachment records using Python,
FastAPI, PostgreSQL/pgvector, local open-weight LLMs, and automated document
ingestion. Implemented semantic and metadata-based retrieval with page-level
source citations, enabling users to query prosecution, defense, court,
journal, and memorandum records.