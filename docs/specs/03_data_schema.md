# Data Schema

## Chunk type

Supported chunk types:

```text
text
image
table
```

## Base chunk schema

```json
{
  "chunk_id": "doc001_page003_text_0001",
  "doc_id": "doc001",
  "source_file": "lecture_1.pdf",
  "page": 3,
  "type": "text",
  "text": "The content used for retrieval and answer generation.",
  "metadata": {
    "section_title": null,
    "bbox": null,
    "image_path": null,
    "caption": null,
    "nearby_text": null,
    "table_html": null,
    "table_summary": null,
    "table_markdown": null,
    "cells": null
  }
}
```

## Text chunk

```json
{
  "chunk_id": "doc001_page003_text_0001",
  "doc_id": "doc001",
  "source_file": "lecture_1.pdf",
  "page": 3,
  "type": "text",
  "text": "Overfitting occurs when a model performs well on training data but poorly on unseen data.",
  "metadata": {
    "section_title": "Model Generalization"
  }
}
```

## Image chunk

```json
{
  "chunk_id": "doc001_page005_image_0001",
  "doc_id": "doc001",
  "source_file": "lecture_1.pdf",
  "page": 5,
  "type": "image",
  "text": "Figure showing a CNN architecture with convolution, pooling and fully connected layers.",
  "metadata": {
    "bbox": [50, 120, 500, 420],
    "image_path": "data/processed/images/doc001_p005_img001.png",
    "caption": "Figure 2. CNN architecture.",
    "nearby_text": "The figure below illustrates the structure of a convolutional neural network."
  }
}
```

## Table chunk

```json
{
  "chunk_id": "doc001_page007_table_0001",
  "doc_id": "doc001",
  "source_file": "lecture_1.pdf",
  "page": 7,
  "type": "table",
  "text": "Table comparing supervised learning, unsupervised learning and reinforcement learning.",
  "metadata": {
    "table_html": "<table>...</table>",
    "table_summary": "Learning type | Input | Objective | Supervised | labeled data | prediction",
    "table_markdown": "Learning type | Input | Objective\nSupervised | labeled data | prediction",
    "cells": [
      ["Learning type", "Input", "Objective"],
      ["Supervised", "labeled data", "prediction"]
    ],
    "caption": "Table 1. Learning paradigms."
  }
}
```

Stage 5B table evidence quality rules:

* Table chunks may be indexed for diagnostics, but only readable table chunks
  may become final cited evidence.
* A table chunk is invalid for `E1`/`E2`/`E3` if it has no
  `table_summary`, `table_markdown`, `table_html`, `cells`, `caption`,
  `nearby_text` or readable text preview.
* Placeholder previews such as `(no text preview)` and
  `Table extracted from PDF.` are invalid cited evidence.
* Very short, symbol-heavy, hash-heavy or internal-id-like table text is
  considered low quality and remains available only in diagnostics.
* Existing processed chunk caches may need re-ingestion to populate the newer
  `table_summary`, `table_markdown` and `cells` metadata fields.

## Retrieval result schema

```json
{
  "chunk_id": "doc001_page003_text_0001",
  "score": 0.87,
  "rank": 1,
  "method": "bm25",
  "chunk": {}
}
```

## Fused result schema

```json
{
  "chunk_id": "doc001_page003_text_0001",
  "bm25_rank": 2,
  "dense_rank": 1,
  "fusion_score": 0.0325,
  "chunk": {}
}
```

## Reranked result schema

```json
{
  "chunk_id": "doc001_page003_text_0001",
  "rerank_score": 0.94,
  "rank": 1,
  "chunk": {}
}
```

## Evaluation query schema

File:

```text
data/eval/queries.jsonl
```

Example:

```json
{"query_id": "q001", "query": "What is overfitting?", "relevant_chunk_ids": ["doc001_page003_text_0001"]}
```

## Milestone 1 ingestion contract

MVP text ingestion supports local `.txt`, `.md`, `.markdown` files and text-based `.pdf` files.

Loader output:

* `doc_id`
* `source_file`
* `page`
* `text`
* `metadata`

Failure fallback:

* missing paths raise `FileNotFoundError`;
* empty text files raise `ValueError`;
* PDFs with no extractable text raise `ValueError`;
* image/table extraction is deferred and must not be required for text ingestion tests.

## Milestone 2 retrieval contract

Retrieval baselines expose a shared result shape:

```json
{
  "chunk_id": "doc001_page003_text_0001",
  "score": 0.87,
  "rank": 1,
  "method": "bm25",
  "chunk": {}
}
```

## Uploaded document registry schema

Local uploaded demo documents are tracked in ignored local storage:

```text
data/processed/corpus_registry.json
```

Each record uses:

```json
{
  "doc_id": "abc123def456",
  "filename": "lecture_1.pdf",
  "stored_path": "data/processed/uploads/abc123def456_lecture_1.pdf",
  "chunk_count": 12,
  "type_counts": {
    "text": 10,
    "image": 1,
    "table": 1
  },
  "created_at": "2026-05-03T00:00:00+00:00"
}
```

The registry is metadata only. Retrieval always returns chunk-level results.

## UI evidence row contract

The right evidence panel renders scored chunk-level rows:

```json
{
  "rank": 1,
  "score": 2.0,
  "method": "reranked",
  "chunk_id": "doc001_page003_text_0001",
  "doc_id": "doc001",
  "source_file": "lecture_1.pdf",
  "page": 3,
  "type": "text",
  "preview": "Short text preview, caption, or table summary."
}
```

For final answer evidence, the scored source of truth is the top reranked
`RetrievalResult` list selected for answer generation.

Supported M2 methods:

* `bm25`: lexical BM25 compatible with `rank-bm25` behavior, implemented without model or network dependencies;
* `dense`: fake deterministic hashing vectors with cosine similarity;
* `fusion`: reciprocal rank fusion over BM25 and dense results;
* `reranked`: mock reranking over fused candidates.

Failure fallback:

* empty corpora return empty result lists;
* non-positive `top_k` returns an empty result list;
* dense retrieval does not download models, use GPU, require API keys, or access the network.

## Milestone 6 image-aware ingestion contract

Image-aware PDF ingestion adds a new chunk-level entrypoint:

```python
load_pdf_chunks(
    pdf_path,
    include_images=True,
    include_tables=True,
    image_output_dir="data/processed/images",
)
```

The original `load_pdf()` text-page contract remains unchanged.

Image chunks:

* use `type="image"`;
* store extracted image files under `metadata.image_path`;
* store page occurrence bounds under `metadata.bbox`;
* store nearby page text under `metadata.nearby_text`;
* store mock or fallback captions under `metadata.caption`;
* use caption plus nearby text as `text` so image chunks can enter BM25, dense, fusion, and reranked retrieval.

Table chunks:

* use `type="table"`;
* use lightweight PyMuPDF table detection only;
* store text fallback in `text`;
* store simple HTML fallback in `metadata.table_html`;
* may be absent when table detection is not available or no table is found.

Failure fallback:

* no images return an empty image chunk list;
* image save failure skips that image and continues;
* image output directory creation failure returns an empty image chunk list;
* caption failure stores `Image extracted from PDF.` and does not block ingestion;
* table detection failure returns an empty table chunk list;
* text extraction failure does not block image/table chunks;
* if text, image, and table extraction all produce no chunks, `load_pdf_chunks()` raises `ValueError`.


## Evidence intelligence query output contract

The Streamlit app-service query response includes stable evidence references
for product-like citation interaction. These fields extend the existing answer
and retrieval objects without changing retrieval algorithms.

Citation objects may include an optional `evidence_id`:

```json
{
  "evidence_id": "E1",
  "chunk_id": "doc001_page003_text_0001",
  "source_file": "lecture_1.pdf",
  "page": 3
}
```

Final evidence rows use:

```json
{
  "evidence_id": "E1",
  "chunk_id": "doc001_page003_text_0001",
  "doc_id": "doc001",
  "source_file": "lecture_1.pdf",
  "page": 3,
  "type": "text",
  "method": "reranked",
  "score": 0.87,
  "confidence": 0.465,
  "preview": "Short text preview, caption, or table summary.",
  "chunk": {}
}
```

Retrieval trace stages use:

```json
{
  "stage": "BM25",
  "result_count": 5,
  "top_score": 2.4,
  "latency_ms": 3.2,
  "confidence": 0.706
}
```

Required stages are:

```text
BM25
Dense
Fusion
Reranker
Final Evidence
```

The query response also includes a lightweight `scope` object with corpus name,
chunk count, source count and document count.
