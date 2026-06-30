'use client'

interface Props {
  t: number
  duration: number
  playing: boolean
  speed: number
  onSeek: (t: number) => void
  onTogglePlay: () => void
  onSpeed: (s: number) => void
  onStep: (delta: number) => void
}

function fmt(s: number): string {
  if (!isFinite(s) || s < 0) s = 0
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

export function Transport({ t, duration, playing, speed, onSeek, onTogglePlay, onSpeed, onStep }: Props) {
  const speeds = [0.5, 1, 1.5, 2]
  return (
    <div className="flex items-center gap-4 px-4 py-3 rounded-xl" style={{ border: '1.5px solid rgba(26,26,26,0.12)', background: 'rgba(26,26,26,0.03)' }}>
      <button
        onClick={() => onStep(-3)}
        className="rounded-md px-2 py-1 transition hover:bg-black/5"
        style={{ fontFamily: 'var(--font-mono), monospace', fontSize: '0.75rem', color: 'rgba(26,26,26,0.5)' }}
      >-3s</button>

      <button
        onClick={onTogglePlay}
        className="flex h-10 w-10 items-center justify-center rounded-full transition hover:scale-105 active:scale-95"
        style={{ background: '#1DB954', color: '#fff' }}
      >
        {playing ? (
          <svg width="12" height="14" viewBox="0 0 12 14" fill="currentColor"><rect x="0" y="0" width="3.5" height="14" rx="1"/><rect x="8.5" y="0" width="3.5" height="14" rx="1"/></svg>
        ) : (
          <svg width="12" height="14" viewBox="0 0 12 14" fill="currentColor"><path d="M0 0 L12 7 L0 14 Z"/></svg>
        )}
      </button>

      <button
        onClick={() => onStep(3)}
        className="rounded-md px-2 py-1 transition hover:bg-black/5"
        style={{ fontFamily: 'var(--font-mono), monospace', fontSize: '0.75rem', color: 'rgba(26,26,26,0.5)' }}
      >+3s</button>

      <div style={{ fontFamily: 'var(--font-mono), monospace', fontSize: '0.85rem', color: 'rgba(26,26,26,0.6)', marginLeft: 4 }}>
        <span style={{ color: '#1A1A1A', fontWeight: 600 }}>{fmt(t)}</span>
        <span style={{ margin: '0 4px', color: 'rgba(26,26,26,0.3)' }}>/</span>
        <span>{fmt(duration)}</span>
      </div>

      <div className="relative flex-1 mx-2">
        <input
          type="range"
          min={0}
          max={duration}
          step={0.05}
          value={t}
          onChange={(e) => onSeek(parseFloat(e.target.value))}
          className="video-range h-1.5 w-full cursor-pointer appearance-none rounded-full"
          style={{ background: 'rgba(26,26,26,0.12)' }}
        />
      </div>

      <div className="flex items-center gap-1">
        {speeds.map((s) => (
          <button
            key={s}
            onClick={() => onSpeed(s)}
            className="rounded-md px-2 py-1 transition"
            style={{
              fontFamily: 'var(--font-mono), monospace',
              fontSize: '0.75rem',
              background: speed === s ? 'rgba(26,26,26,0.1)' : 'transparent',
              color: speed === s ? '#1A1A1A' : 'rgba(26,26,26,0.4)',
            }}
          >{s}x</button>
        ))}
      </div>
    </div>
  )
}
