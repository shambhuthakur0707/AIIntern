import { useState } from 'react'
import ProgressBar from './ProgressBar'
import SkillBadge from './SkillBadge'
import RoadmapTimeline from './RoadmapTimeline'

export default function InternshipCard({ rec, index }) {
    const [expanded, setExpanded] = useState(false)
    const [copied, setCopied] = useState(false)

    const copyRoadmap = () => {
        const roadmap = rec.roadmap ?? rec.learning_roadmap ?? []
        if (!roadmap.length) return
        const text = roadmap.map((step, i) =>
            `Week ${step.week ?? i + 1}: ${step.focus ?? ''}\n` +
            (Array.isArray(step.tasks) ? step.tasks.map((t) => `  • ${t}`).join('\n') : '')
        ).join('\n\n')
        navigator.clipboard.writeText(`${rec.title ?? rec.internship_title} — Learning Roadmap\n\n${text}`)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    const rank = rec.rank ?? index + 1
    const title = rec.internship_title ?? rec.title ?? 'Untitled'
    const matchScore = Number(rec.match_score ?? rec.weighted_score ?? 0)
    const roadmap = rec.roadmap ?? rec.learning_roadmap ?? []
    const recommendationSummary =
        rec.recommendation_summary ??
        rec.improvement_priority ??
        'Review the skill gap analysis and roadmap to improve your fit.'
    const workMode = rec.work_mode ?? (rec.is_remote ? 'Remote' : 'On-site/Hybrid')

    const rankColors = ['from-yellow-400 to-amber-500', 'from-gray-300 to-gray-400', 'from-amber-600 to-yellow-700']
    const rankColor = rankColors[index] ?? 'from-brand-500 to-violet-500'

    return (
        <div className="glass-card-hover animate-slide-up p-5 space-y-4" style={{ animationDelay: `${index * 100}ms` }} id={`internship-card-${index}`}>

            {/* Header row */}
            <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                    {/* Rank badge */}
                    <div className={`flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br ${rankColor} flex items-center justify-center text-sm font-extrabold text-white shadow-md`}>
                        #{rank}
                    </div>
                    <div>
                        <h3 className="font-bold text-white text-base leading-tight">{title}</h3>
                        <p className="text-sm text-gray-400">
                            {rec.company}
                            {rec.company && rec.domain ? <span className="mx-1 opacity-50">·</span> : null}
                            {rec.domain ? <span className="text-brand-400">{rec.domain}</span> : null}
                        </p>
                    </div>
                </div>
                {/* Meta */}
                <div className="hidden sm:flex flex-col items-end gap-1 text-xs text-gray-500 flex-shrink-0">
                    <span>{rec.stipend}</span>
                    <span>{rec.duration}</span>
                    <span>{rec.location}</span>
                    <span className={workMode === 'Remote' ? 'text-emerald-400' : 'text-gray-400'}>{workMode}</span>
                </div>
            </div>

            {/* Progress bar */}
            <ProgressBar score={matchScore} />

            {/* AI Reasoning */}
            <div className="bg-brand-500/5 border border-brand-500/20 rounded-xl p-3">
                <p className="section-label mb-1.5">AI Reasoning</p>
                <p className="text-sm text-gray-300 leading-relaxed">{rec.reasoning}</p>
            </div>

            {/* Missing skills */}
            {rec.missing_skills?.length > 0 && (
                <div>
                    <p className="section-label mb-2">Skill Gaps</p>
                    <div className="flex flex-wrap gap-1.5">
                        {rec.missing_skills.map((s) => (
                            <SkillBadge key={s} skill={s} size="xs" />
                        ))}
                    </div>
                </div>
            )}

            {/* Recommendation summary */}
            <div className="flex items-start gap-2 text-sm text-emerald-400 bg-emerald-500/5 border border-emerald-500/20 rounded-xl px-3 py-2.5">
                <span className="mt-0.5 flex-shrink-0">✓</span>
                <span>{recommendationSummary}</span>
            </div>

            {rec.apply_url && (
                <div className="flex justify-end">
                    <a
                        href={rec.apply_url}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-secondary !py-2 !px-4 text-sm"
                    >
                        Open application
                    </a>
                </div>
            )}

            {/* Expandable roadmap */}
            <div className="flex items-center justify-between gap-2">
                <button
                    onClick={() => setExpanded((e) => !e)}
                    className="flex-1 text-left"
                    id={`roadmap-toggle-${index}`}
                >
                    <div className="flex items-center justify-between text-sm font-medium text-gray-400 hover:text-white transition-colors">
                        <span>Learning Roadmap ({rec.total_learning_weeks ?? roadmap.length ?? 0} weeks)</span>
                        <svg className={`w-4 h-4 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                    </div>
                </button>
                {roadmap.length > 0 && (
                    <button
                        onClick={copyRoadmap}
                        title="Copy roadmap to clipboard"
                        className="flex-shrink-0 text-xs text-gray-500 hover:text-brand-400 border border-white/10 hover:border-brand-500/30 px-2 py-1 rounded-lg transition-colors"
                    >
                        {copied ? '✓ Copied' : '⎘ Copy'}
                    </button>
                )}
            </div>

            {expanded && (
                <div className="pt-2 animate-fade-in">
                    <RoadmapTimeline roadmap={roadmap} />
                </div>
            )}
        </div>
    )
}

