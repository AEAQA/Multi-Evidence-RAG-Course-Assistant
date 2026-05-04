export const methodDescriptions: Record<string, { title: string; how: string; strength: string }> = {
  bm25: {
    title: "BM25 - Lexical Retrieval",
    how: "Searches for exact keyword matches using term frequency and inverse document frequency. It behaves like a smarter Ctrl+F across the indexed materials.",
    strength: "Best when your question uses specific terms or acronyms that appear verbatim in the study materials."
  },
  dense: {
    title: "Dense - Semantic Retrieval",
    how: "Converts the question and chunks into vector embeddings, then finds chunks whose meaning is close even when the wording differs.",
    strength: "Best when you rephrase concepts in your own words or use synonyms."
  },
  fusion: {
    title: "Fusion - Hybrid Ranking",
    how: "Combines BM25 and Dense results with Reciprocal Rank Fusion so chunks ranked highly by either method rise to the top.",
    strength: "The safest default because it blends lexical and semantic signals."
  },
  reranked: {
    title: "Reranker - Precision Filter",
    how: "Reads each candidate with the question and reorders candidates by relevance before final evidence is selected.",
    strength: "Best for selecting the evidence used by the grounded answer."
  }
};

export function MethodHowItWorks({ method }: { method: string }) {
  const desc = methodDescriptions[method];
  if (!desc) return null;
  return (
    <details className="method-how-details">
      <summary>{desc.title}</summary>
      <p className="method-how-text">{desc.how}</p>
      <p className="method-how-strength"><strong>When to use:</strong> {desc.strength}</p>
    </details>
  );
}
