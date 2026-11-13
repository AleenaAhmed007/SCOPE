# Phase 09 — RAG Document Retrieval

## 1. Objective

Build a Retrieval-Augmented Generation (RAG) system that retrieves relevant supply chain evidence from documents and provides grounded answers with source citations.

The RAG module will support the SCOPE agentic AI workflow.

## 2. Business Problem

Supply chain disruption analysis may require information from:

- Supplier contracts
- Service Level Agreements (SLAs)
- Procurement policies
- Shipping policies
- Compliance documents
- Operational reports
- Approved supply chain guidelines

The system should retrieve relevant evidence before generating an answer.

It must not invent document facts or citations.

## 3. RAG Architecture

The pipeline:

1. Document ingestion
2. Text extraction
3. Document cleaning
4. Chunking
5. Metadata assignment
6. Embedding generation
7. Vector indexing
8. Keyword retrieval
9. Hybrid retrieval
10. Reranking, if justified
11. Context construction
12. Grounded answer generation
13. Citation validation

## 4. Document Ingestion

Support relevant formats:

- PDF
- DOCX
- TXT
- Markdown

Suggested libraries:

- PyMuPDF
- python-docx
- LangChain document loaders, if useful

For each document, capture:

- Document ID
- File name
- Document type
- Source
- Version
- Upload timestamp
- Page number, where available
- Document status

Do not treat synthetic documents as real supplier contracts or official policies.

If synthetic documents are used for development, label them clearly as synthetic.

## 5. Chunking

Implement configurable chunking.

Suggested initial configuration:

- Chunk size: approximately 800 tokens
- Overlap: approximately 120 tokens

These are starting values, not fixed requirements.

Preserve:

- Document ID
- Page number
- Section heading
- Chunk ID
- Source reference

Avoid splitting important tables or policy sections in a way that destroys their meaning.

## 6. Embeddings and Vector Storage

Generate embeddings using a selected embedding model.

Preferred vector storage:

- PostgreSQL
- pgvector extension

Alternative:

- FAISS as a separate vector index, with document metadata stored in PostgreSQL.

Do not create an SQLite vector database.

Store document and chunk metadata in PostgreSQL.

## 7. Retrieval Strategy

Implement:

### Vector retrieval

Retrieve semantically similar chunks using embeddings.

### Keyword retrieval

Use PostgreSQL full-text search or a suitable BM25 implementation.

### Hybrid retrieval

Combine vector and keyword results.

Reciprocal Rank Fusion (RRF) may be used to merge rankings.

### Optional reranking

Use a cross-encoder reranker only if it improves retrieval quality.

Record retrieval configuration and scores.

## 8. Context and Answer Generation

Construct a context containing:

- Retrieved text
- Document title
- Page number
- Document version
- Source identifier

The answer-generation prompt must instruct the LLM to:

- Use retrieved evidence.
- Avoid unsupported factual claims.
- Clearly identify missing evidence.
- Cite sources for material document-based claims.
- Distinguish assumptions from verified information.

## 9. Citation Format

Use a consistent citation format.

Example:

`[Source: Supplier_SLA.pdf, Page 12, Document ID: DOC-001]`

Every citation must refer to an actual retrieved document chunk.

Do not generate page numbers or source names that are not present in document metadata.

## 10. RAG Evaluation

Create a small evaluation dataset with:

- Questions
- Expected relevant documents
- Expected relevant pages or chunks
- Reference answers, where available

Evaluate:

- Recall@k
- Precision@k
- MRR
- Citation correctness
- Answer groundedness
- Retrieval latency

Do not report fabricated evaluation results.

## 11. PostgreSQL Requirements

PostgreSQL is mandatory.

Use:

- PostgreSQL
- SQLAlchemy
- Alembic
- psycopg
- pgvector, where supported

Suggested tables:

- `documents`
- `document_versions`
- `document_chunks`
- `document_embeddings`
- `rag_queries`
- `retrieval_results`

If using pgvector, configure the vector column and indexes through PostgreSQL migrations.

If using FAISS, persist the index separately and maintain its document/chunk mapping in PostgreSQL.

No SQLite.

## 12. Suggested Folder Structure

```text
backend/
  rag/
    ingestion/
      loaders.py
      extract.py
      metadata.py

    chunking/
      splitter.py

    embeddings/
      generator.py

    retrieval/
      vector_search.py
      keyword_search.py
      hybrid_search.py
      reranker.py

    generation/
      prompts.py
      answer.py
      citations.py

    evaluation/
      dataset.py
      metrics.py
      evaluate.py

tests/
  test_ingestion.py
  test_chunking.py
  test_retrieval.py
  test_citations.py
```

## 13. Expected Outputs

- Document ingestion pipeline
- Chunking pipeline
- Embedding generation
- Vector retrieval
- Keyword retrieval
- Hybrid retrieval
- Grounded answer generation
- Source citations
- RAG evaluation report
- PostgreSQL document metadata

## 14. Acceptance Criteria

- Supported documents can be ingested.
- Document metadata is preserved.
- Chunks retain source and page references where available.
- Embeddings can be generated and retrieved.
- Hybrid retrieval is implemented or a documented reason is provided for another strategy.
- Answers use retrieved evidence.
- Unsupported claims are identified.
- Citations resolve to actual source documents.
- RAG evaluation metrics are generated from a real evaluation set.
- PostgreSQL stores document and retrieval metadata.
- No SQLite dependency exists.

## 15. Cursor AI Prompt

You are implementing Phase 09 of the SCOPE project.

Build a production-oriented Retrieval-Augmented Generation system for supply chain documents.

Requirements:

1. Inspect the existing repository and database configuration.
2. Support PDF, DOCX, TXT, and Markdown ingestion.
3. Extract text and preserve document IDs, filenames, page numbers, headings, versions, and source metadata where available.
4. Clearly label synthetic documents.
5. Implement configurable text chunking with overlap.
6. Generate embeddings using a configurable embedding model.
7. Use PostgreSQL with pgvector as the preferred vector store.
8. If pgvector is unavailable, use FAISS as a separate vector index and store all document metadata and mappings in PostgreSQL.
9. Implement vector retrieval.
10. Implement keyword retrieval using PostgreSQL full-text search or a suitable BM25 implementation.
11. Implement hybrid retrieval using Reciprocal Rank Fusion where appropriate.
12. Add optional reranking only when justified.
13. Generate answers using retrieved context only for document-grounded claims.
14. Preserve source, page, and document-version citations.
15. Do not fabricate citations, page numbers, or document facts.
16. Clearly report when evidence is insufficient.
17. Build a RAG evaluation dataset and calculate Recall@k, Precision@k, MRR, citation correctness, and latency where applicable.
18. Save retrieval configuration and evaluation results.
19. Add tests for ingestion, chunking, metadata, retrieval, and citation resolution.
20. Use PostgreSQL only for relational persistence.
21. Use SQLAlchemy, Alembic, and psycopg.
22. Never use SQLite or SQLite fallback.
23. Read secrets and database credentials from environment variables.
24. Document setup, ingestion, indexing, querying, and evaluation commands.
25. Do not fabricate evaluation results.

Inspect the repository before coding. Explain planned file changes, implement the module, and run the tests.

## 16. Definition of Done

RAG can ingest documents, retrieve relevant evidence, generate grounded answers with valid citations, and persist document and retrieval metadata in PostgreSQL.
