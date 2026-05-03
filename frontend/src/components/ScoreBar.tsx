export function ScoreBar({ value }: { value: number }) {
  const width = Math.max(3, Math.min(100, Number.isFinite(value) ? Math.abs(value) * 100 : 3));
  return (
    <div className="score-track" aria-hidden="true">
      <span style={{ width: `${width}%` }} />
    </div>
  );
}

export function formatScore(value: number): string {
  if (!Number.isFinite(value)) {
    return "0.000";
  }
  return value.toFixed(3);
}
