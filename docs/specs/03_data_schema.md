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
    "table_html": null
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
    "caption": "Table 1. Learning paradigms."
  }
}
```

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

MVP text ingestion supports local `.txt` files and text-based `.pdf` files.

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

Supported M2 methods:

* `bm25`: lexical BM25 compatible with `rank-bm25` behavior, implemented without model or network dependencies;
* `dense`: fake deterministic hashing vectors with cosine similarity;
* `fusion`: reciprocal rank fusion over BM25 and dense results;
* `reranked`: mock reranking over fused candidates.

Failure fallback:

* empty corpora return empty result lists;
* non-positive `top_k` returns an empty result list;
* dense retrieval does not download models, use GPU, require API keys, or access the network.
