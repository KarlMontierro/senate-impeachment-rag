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

**Day 2 — Database + Document Processing: In Progress**

### Day 1 Progress

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

### Day 2 Progress

- PostgreSQL 18 configured
- pgvector 0.8.6 installed and enabled
- `documents` table created
- `pages` table created
- Full PDF downloader implemented
- 88/88 PDF documents downloaded
- SHA-256 hashes calculated for downloaded documents
- PyMuPDF configured for PDF text extraction
- Tesseract OCR configured as a fallback for scanned PDFs
- Page-level extraction and OCR pipeline implemented
- `CR00261.pdf` successfully processed
- 93 pages extracted from `CR00261.pdf`
- 92 pages required OCR
- Page text successfully stored in PostgreSQL
- Full-corpus ingestion script implemented

The full 88-document corpus has been downloaded locally. Full-corpus
database ingestion and OCR quality verification are still in progress.

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

## Day 2 Corpus Snapshot

| Item | Count |
|---|---:|
| Total manifest records | 95 |
| PDF documents | 88 |
| Video files | 7 |
| PDFs downloaded | 88 |
| PDFs processed | 1 |
| Pages processed | 93 |
| Pages requiring OCR | 92 |

The full PDF corpus has been downloaded locally.

The current PostgreSQL ingestion test has successfully processed
`CR00261.pdf`. Full-corpus ingestion will process the remaining documents.

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

PyMuPDF

Tesseract OCR

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
│   ├── download_test.py
│   └── download_documents.py
│
├── document_processing/
│   └── PDF extraction and OCR
│
├── evaluation/
│   └── RAG evaluation
│
├── scripts/
│   └── ingest_documents.py
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

Generated document data, downloaded PDFs, environment files, virtual
environments, and Python cache files are excluded from Git.

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

The downloader also:

Uses streamed downloads
Validates HTTP responses
Checks PDF content type
Validates the downloaded PDF file
Calculates SHA-256 hashes
Skips already downloaded valid files
Stores documents according to their category
Uses temporary .part files during downloads
Full Corpus Download

The current manifest contains 88 PDF documents.

All 88 PDFs have been successfully downloaded.

The downloader initially completed 86 files, with one existing file and one
network timeout. The failed document was retried successfully without
redownloading the existing files.

Final download status:

Manifest PDFs:   88
Downloaded:      1
Already existed: 87
Failed:          0

The final local corpus therefore contains all 88 PDF documents.

Large PDF files are intentionally not committed to GitHub.

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

The current manifest contains:

95 total records
88 PDF records
7 video records

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

Database

The project uses PostgreSQL 18 with pgvector 0.8.6.

The database is currently being used to store document metadata and
page-level extracted text.

Documents

The documents table contains:

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

The pages table contains:

pages
├── id
├── document_id
├── page_number
└── text

The pages table references the corresponding document and enforces unique
document/page combinations.

Chunks

The chunks table is planned for Day 3:

chunks
├── id
├── document_id
├── page_id
├── chunk_index
├── text
└── embedding

Page-level storage is important because citations need to point back to the
specific page containing the retrieved information.

Document Processing

The document processing pipeline currently performs:

PDF
 │
 ▼
Page-by-Page Text Extraction
 │
 ├── Good Text
 │      │
 │      ▼
 │   Store Text
 │
 └── Poor / Missing Text
        │
        ▼
      OCR
        │
        ▼
    Store OCR Text

PyMuPDF is used for normal PDF text extraction.

Tesseract OCR is used when the extracted text does not meet the configured
quality threshold.

The current quality check evaluates extracted text based on minimum text
length and alphanumeric content.

Initial Processing Test

CR00261.pdf was used as the initial ingestion test document.

Results:

Pages extracted:        93
Pages requiring OCR:    92
Document status:         processed
Database document ID:   1

The first page contained extractable text, while the remaining pages were
primarily scanned/image-based and required OCR.

The resulting page text was successfully stored in PostgreSQL.

OCR output is retained as extracted source text rather than aggressively
rewriting or correcting OCR artifacts.

Full-Corpus Ingestion

The full-corpus ingestion script is:

scripts/ingest_documents.py

It is designed to:

Read the document manifest.
Identify PDF records.
Locate the corresponding local PDF.
Calculate the SHA-256 hash.
Extract text page-by-page.
Detect pages requiring OCR.
Run OCR when necessary.
Store document metadata in PostgreSQL.
Store page-level text in PostgreSQL.
Update the document processing status.

The full 88-document ingestion has not yet been completed.

The next ingestion step is to process the downloaded corpus and verify
extraction and OCR quality across the documents.

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

If the available records do not provide enough evidence to answer a
question, the system should state that the records do not provide sufficient
information rather than inventing an answer.

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

Future hosted-model integration must also avoid exposing API keys through
the frontend.

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

In Progress

 Build PostgreSQL database
 Configure pgvector
 Download all 88 PDFs
 Store document metadata
 Calculate SHA-256 hashes
 Extract PDF text page-by-page
 Add OCR fallback
 Store page text
 Implement full-corpus ingestion script
 Process the complete 88-document corpus
 Verify OCR/text extraction quality across the corpus
Day 3 — Chunking + Embeddings

Planned

 Implement page-aware chunking
 Generate embeddings
 Store embeddings in pgvector
 Implement semantic search
 Return document, page, text, similarity, and source URL
Day 4 — RAG Pipeline

Planned

 Query embedding
 Retrieve relevant chunks
 Reranking
 Context construction
 LLM integration
 Page-level citations
 Insufficient-evidence handling
Day 5 — React Interface

Planned

 Chat interface
 Source citations
 Document filters
 Document detail view
 Original document links
 Corpus information
Day 6 — Automatic Updates + Security

Planned

 Re-check Senate API
 Detect new documents
 Detect changed documents
 Compare URLs and SHA-256 hashes
 Add rate/context limits
 Security controls
 Prompt-injection handling
Day 7 — Evaluation

Planned

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
 Metadata is stored for the complete corpus
 Duplicate detection can be performed using SHA-256
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