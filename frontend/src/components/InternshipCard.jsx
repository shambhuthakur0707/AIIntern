import { useState } from 'react'
import ProgressBar from './ProgressBar'
import SkillBadge from './SkillBadge'
import RoadmapTimeline from './RoadmapTimeline'

export default function InternshipCard({ rec, index }) {
    const [expanded, setExpanded] = useState(false)

    const rankColors = ['from-yellow-400 to-amber-500', 'from-gray-300 to-gray-400', 'from-amber-600 to-yellow-700']
    const rankColor = rankColors[index] ?? 'from-brand-500 to-violet-500'

    return (
        <div className="glass-card-hover animate-slide-up p-5 space-y-4" style={{ animationDelay: `${index * 100}ms` }} id={`internship-card-${index}`}>

            {/* Header row */}
            <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                    {/* Rank badge */}
                    <div className={`flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br ${rankColor} flex items-center justify-center text-sm font-extrabold text-white shadow-md`}>
                        #{rec.rank}
                    </div>
                    <div>
                        <h3 className="font-bold text-white text-base leading-tight">{rec.internship_title}</h3>
                        <p className="text-sm text-gray-400">{rec.company} · <span className="text-brand-400">{rec.domain}</span></p>
                    </div>
                </div>
                {/* Meta */}
                <div className="hidden sm:flex flex-col items-end gap-1 text-xs text-gray-500 flex-shrink-0">
                    <span>💰 {rec.stipend}</span>
                    <span>📅 {rec.duration}</span>
                    <span>📍 {rec.location}</span>
                </div>
            </div>

            {/* Progress bar */}
            <ProgressBar score={rec.match_score} />

            {/* AI Reasoning */}
            <div className="bg-brand-500/5 border border-brand-500/20 rounded-xl p-3">
                <p className="section-label mb-1.5">🤖 AI Reasoning</p>
                <p className="text-sm text-gray-300 leading-relaxed">{rec.reasoning}</p>
            </div>

            {/* Missing skills */}
            {rec.missing_skills?.length > 0 && (
                <div>
                    <p className="section-label mb-2">⚡ Skill Gaps</p>
                    <div className="flex flex-wrap gap-1.5">
                        {rec.missing_skills.map((s) => (
                            <SkillBadge key={s} skill={s} size="xs" />
                        ))}
                    </div>
                </div>
            )}

            {/* Recommendation summary */}
            <div className="flex items-start gap-2 text-sm text-emerald-400">
                <span className="mt-0.5 flex-shrink-0">✅</span>
                <span>{rec.recommendation_summary}</span>
            </div>

            {/* Expandable roadmap */}
            <button
                onClick={() => setExpanded((e) => !e)}
                className="w-full text-left"
                id={`roadmap-toggle-${index}`}
            >
                <div className="flex items-center justify-between text-sm font-medium text-gray-400 hover:text-white transition-colors">
                    <span>📚 Learning Roadmap ({rec.total_learning_weeks ?? 0} weeks)</span>
                    <svg className={`w-4 h-4 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                </div>
            </button>

            {expanded && (
                <div className="pt-2 animate-fade-in">
                    <RoadmapTimeline roadmap={rec.roadmap} />
                </div>
            )}
        </div>
    )
}
