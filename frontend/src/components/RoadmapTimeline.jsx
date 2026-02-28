export default function RoadmapTimeline({ roadmap = [] }) {
    if (!roadmap || roadmap.length === 0) {
        return (
            <p className="text-sm text-gray-500 italic">
                No learning gaps detected — you're well-qualified! 🎉
            </p>
        )
    }

    return (
        <div className="relative space-y-0">
            {/* Vertical line */}
            <div className="absolute left-3 top-2 bottom-2 w-px bg-gradient-to-b from-brand-500/60 via-violet-500/60 to-transparent" />

            {roadmap.map((step, i) => (
                <div key={i} className="flex gap-4 pb-5 last:pb-0 animate-slide-up" style={{ animationDelay: `${i * 80}ms` }}>
                    {/* Node */}
                    <div className="relative z-10 flex-shrink-0 w-6 h-6 mt-0.5 rounded-full bg-gradient-to-br from-brand-500 to-violet-500 flex items-center justify-center text-[10px] font-bold text-white shadow-md shadow-brand-500/30">
                        {i + 1}
                    </div>

                    {/* Content */}
                    <div className="flex-1 bg-white/5 border border-white/10 rounded-xl p-3">
                        <div className="flex items-start justify-between gap-2 mb-1">
                            <span className="text-sm font-semibold text-white">{step.skill}</span>
                            <span className="text-xs text-gray-500 whitespace-nowrap flex-shrink-0">
                                Week {step.week_start}–{step.week_end}
                            </span>
                        </div>
                        <p className="text-xs text-gray-400 leading-relaxed">{step.resource}</p>
                    </div>
                </div>
            ))}
        </div>
    )
}
