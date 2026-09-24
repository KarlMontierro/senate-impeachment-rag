# Senate Impeachment Records — Data Source

## Purpose

This document describes the public Philippine Senate source that will be
used to construct the impeachment-record corpus for the RAG system.

## Primary Source

The project uses publicly available impeachment records from the official
Philippine Senate website.

### Senate Impeachment Documents

Official source:

https://senate.gov.ph/services/impeachment-documents

This page serves as the primary starting point for discovering impeachment
documents for the project.

## Initial Record Types

The project plan defines the initial corpus as:

- Prosecution PDFs
- Defense PDFs
- Court issuances
- Senate journals
- Memoranda
- Other relevant PDFs available in the Senate archive

## Initial Metadata

The crawler should attempt to identify:

- title
- category
- document date
- source URL
- document/file URL
- filename

## Source Investigation Checklist

- [ ] Identify the page structure
- [ ] Identify document categories
- [ ] Identify document listing structure
- [ ] Determine URL patterns
- [ ] Determine pagination behavior
- [ ] Determine date format
- [ ] Determine filename patterns
- [ ] Identify PDF links
- [ ] Identify video/audio links
- [ ] Determine how categories can be classified

## Crawler Output

The crawler should initially produce document metadata without downloading
the complete corpus.

Expected fields:

```text
title
category
document_date
source_url
file_url
filename


### Initial Access Test

On September 24, 2026, the source was tested using Python `requests`.

Result:

- HTTP status: `403 Forbidden`
- Content type: `text/html; charset=UTF-8`
- Response size: approximately 5.8 KB

The official page is accessible through a normal web browser, but direct
retrieval using the initial Python HTTP client was denied.

The crawler implementation will therefore be investigated further before
automated discovery is finalized.