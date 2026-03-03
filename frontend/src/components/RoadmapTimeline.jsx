function normalizeStep(step, index) {
    // New backend shape: { week, focus, tasks[] }
    if (step && typeof step === 'object' && ('focus' in step || 'tasks' in step)) {
        return {
            title: step.focus ?? `Week ${step.week ?? index + 1}`,
            subtitle: Array.isArray(step.tasks) ? step.tasks.join(' | ') : '',
            weekLabel: `Week ${step.week ?? index + 1}`,
        }
    }

    // Legacy frontend shape: { skill, week_start, week_end, resource }
    return {
        title: step?.skill ?? `Week ${index + 1}`,
        subtitle: step?.resource ?? '',
        weekLabel: `Week ${step?.week_start ?? index + 1}-${step?.week_end ?? index + 1}`,
    }
}

export default function RoadmapTimeline({ roadmap = [] }) {
    if (!roadmap || roadmap.length === 0) {
        return (
            <p className="text-sm text-gray-500 italic">
                No learning gaps detected. You are well-qualified.
            </p>
        )
    }

    return (
        <div className="relative space-y-0">
            <div className="absolute left-3 top-2 bottom-2 w-px bg-gradient-to-b from-brand-500/60 via-violet-500/60 to-transparent" />

            {roadmap.map((rawStep, i) => {
                const step = normalizeStep(rawStep, i)
                return (
                    <div key={i} className="flex gap-4 pb-5 last:pb-0 animate-slide-up" style={{ animationDelay: `${i * 80}ms` }}>
                        <div className="relative z-10 flex-shrink-0 w-6 h-6 mt-0.5 rounded-full bg-gradient-to-br from-brand-500 to-violet-500 flex items-center justify-center text-[10px] font-bold text-white shadow-md shadow-brand-500/30">
                            {i + 1}
                        </div>

                        <div className="flex-1 bg-white/5 border border-white/10 rounded-xl p-3">
                            <div className="flex items-start justify-between gap-2 mb-1">
                                <span className="text-sm font-semibold text-white">{step.title}</span>
                                <span className="text-xs text-gray-500 whitespace-nowrap flex-shrink-0">
                                    {step.weekLabel}
                                </span>
                            </div>
                            <p className="text-xs text-gray-400 leading-relaxed">{step.subtitle}</p>
                        </div>
                    </div>
                )
            })}
        </div>
    )
}

