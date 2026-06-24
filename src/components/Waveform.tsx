export function Waveform({ values = [] }: { values?: number[] }) {
  const bars = values.length
    ? values.slice(0, 64)
    : Array.from({ length: 48 }, (_, index) => 0.2 + ((index * 17) % 10) / 12);

  return (
    <div className="waveform" aria-label="Track energy curve">
      {bars.map((value, index) => (
        <span
          key={`${index}-${value}`}
          style={{ height: `${Math.max(10, Math.min(100, Math.abs(value) * 100))}%` }}
        />
      ))}
    </div>
  );
}
