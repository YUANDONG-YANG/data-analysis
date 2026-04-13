function CodeSpans({ text }: { text: string }) {
  const parts = text.split(/(`[^`]+`)/g);
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith("`") && part.endsWith("`")) {
          return (
            <code
              key={i}
              className="rounded-md bg-canvas-subtle/80 px-1.5 py-0.5 font-mono text-[0.9em] text-accent-glow"
            >
              {part.slice(1, -1)}
            </code>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}

export function InlineText({ text }: { text: string }) {
  const segments = text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <>
      {segments.map((segment, i) => {
        if (segment.startsWith("**") && segment.endsWith("**")) {
          return (
            <strong key={i} className="font-semibold text-ink">
              {segment.slice(2, -2)}
            </strong>
          );
        }
        return <CodeSpans key={i} text={segment} />;
      })}
    </>
  );
}
