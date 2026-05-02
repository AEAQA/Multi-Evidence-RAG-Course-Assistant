# Evaluation Plan

## Goal

Evaluate how different retrieval strategies affect evidence retrieval quality, latency and final answer grounding.

## Retrieval methods to compare

```text
A. BM25-only
B. Dense-only
C. BM25 + Dense hybrid fusion
D. BM25 + Dense fusion + reranker
```

## Evaluation dataset

Create a small manually labeled dataset:

```text
data/eval/queries.jsonl
```

Each line:

```json
{"query_id": "q001", "query": "What is overfitting?", "relevant_chunk_ids": ["doc001_page003_text_0001"]}
```

Recommended size:

```text
10-30 queries for MVP
```

## Metrics

### Recall@k

Measures whether at least one relevant chunk appears in top-k.

Use:

```text
Recall@1
Recall@3
Recall@5
```

### MRR@k

Mean Reciprocal Rank measures how early the first relevant chunk appears.

Use:

```text
MRR@5
```

### NDCG@k

Normalized Discounted Cumulative Gain measures ranking quality.

Use:

```text
NDCG@5
```

### Latency

Record average retrieval latency for each method:

```text
latency_ms
```

### Optional cost

For API-enhanced mode, estimate:

```text
reranker_cost
llm_cost
asr_cost
vision_caption_cost
```

## Outputs

Evaluation results should be saved to:

```text
reports/evaluation/retrieval_metrics.csv
reports/evaluation/latency_metrics.csv
reports/evaluation/error_cases.md
reports/figures/
```

## Visualizations

Generate:

* Recall@k comparison chart
* MRR/NDCG comparison chart
* latency comparison chart
* optional cost vs quality chart

## Error analysis

Include at least:

* 3 successful cases
* 3 failed or weak cases

For each case, discuss:

* query
* expected evidence
* retrieved evidence
* method behavior
* possible reason for success/failure
