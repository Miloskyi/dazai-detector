export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 rounded-2xl bg-ink-800 px-4 py-3">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 animate-bounce rounded-full bg-accent-400"
          style={{ animationDelay: `${i * 120}ms` }}
        />
      ))}
    </div>
  );
}
