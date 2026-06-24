export function formatDuration(seconds?: number | null) {
  if (!seconds || Number.isNaN(seconds)) return "—";
  const minutes = Math.floor(seconds / 60);
  const remainder = Math.round(seconds % 60);
  return `${minutes}:${String(remainder).padStart(2, "0")}`;
}

export function formatBytes(bytes: number) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(units.length - 1, Math.floor(Math.log(bytes) / Math.log(1024)));
  return `${(bytes / 1024 ** index).toFixed(index > 1 ? 1 : 0)} ${units[index]}`;
}

export function confidenceLabel(value?: number | null) {
  if (value == null) return "Not analyzed";
  if (value >= 0.75) return "High confidence";
  if (value >= 0.5) return "Review suggested";
  return "Low confidence";
}
