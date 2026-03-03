import { useEffect, useRef } from 'react'

function scoreColor(score) {
    if (score >= 75) return 'from-emerald-500 to-teal-400'
    if (score >= 50) return 'from-brand-500 to-cyan-400'
    if (score >= 25) return 'from-amber-500 to-orange-400'
    return 'from-rose-600 to-rose-400'
}

export default function ProgressBar({ score, animated = true }) {
    const barRef = useRef(null)
    const safeScore = Number.isFinite(Number(score)) ? Number(score) : 0

    useEffect(() => {
        if (!barRef.current) return
        // Start from 0, animate to score
        barRef.current.style.width = '0%'
        const t = setTimeout(() => {
            barRef.current.style.width = `${Math.min(Math.max(safeScore, 0), 100)}%`
        }, 100)
        return () => clearTimeout(t)
    }, [safeScore])

    return (
        <div className="space-y-1.5">
            <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400 font-medium">Match Score</span>
                <span className={`text-sm font-bold bg-gradient-to-r ${scoreColor(safeScore)} bg-clip-text text-transparent`}>
                    {safeScore.toFixed(1)}%
                </span>
            </div>
            <div className="progress-track">
                <div
                    ref={barRef}
                    className={`h-full rounded-full bg-gradient-to-r ${scoreColor(safeScore)} transition-all duration-1000 ease-out`}
                    style={{ width: '0%' }}
                />
            </div>
        </div>
    )
}
