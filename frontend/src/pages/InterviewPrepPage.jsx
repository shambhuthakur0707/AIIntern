import { useEffect, useState, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import Navbar from '../components/Navbar'
import api from '../api/axios'
import { useToast } from '../context/ToastContext'

const TYPE_STYLES = {
    technical:   { chip: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',     icon: '⚙️' },
    behavioral:  { chip: 'bg-violet-500/20 text-violet-300 border-violet-500/30', icon: '🧠' },
    situational: { chip: 'bg-amber-500/20 text-amber-300 border-amber-500/30',   icon: '🎯' },
}

function QuestionCard({ q, index }) {
    const style = TYPE_STYLES[q.type] || TYPE_STYLES.situational

    return (
        // CSS 3D flip card — hover reveals tip on back
        <div
            className="relative h-52"
            style={{ perspective: '1000px' }}
            id={`question-card-${index}`}
        >
            <div
                className="relative w-full h-full transition-transform duration-500 ease-in-out"
                style={{ transformStyle: 'preserve-3d' }}
                // Tailwind can't do group-hover for transform-style, so we use inline JS toggle
                onMouseEnter={e => e.currentTarget.style.transform = 'rotateY(180deg)'}
                onMouseLeave={e => e.currentTarget.style.transform = 'rotateY(0deg)'}
            >
                {/* Front — question */}
                <div
                    className="absolute inset-0 glass-card p-5 flex flex-col justify-between"
                    style={{ backfaceVisibility: 'hidden', WebkitBackfaceVisibility: 'hidden' }}
                >
                    <div>
                        <div className="flex items-center justify-between mb-3">
                            <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${style.chip}`}>
                                {style.icon} {q.type}
                            </span>
                            <span className="text-xs text-gray-600 font-mono">#{index + 1}</span>
                        </div>
                        <p className="text-white font-medium leading-relaxed text-sm">{q.question}</p>
                    </div>
                    <p className="text-xs text-gray-600 mt-3">Hover to reveal coaching tip →</p>
                </div>

                {/* Back — coaching tip */}
                <div
                    className="absolute inset-0 rounded-2xl p-5 flex flex-col justify-between border"
                    style={{
                        backfaceVisibility: 'hidden',
                        WebkitBackfaceVisibility: 'hidden',
                        transform: 'rotateY(180deg)',
                        background: 'linear-gradient(135deg, rgba(20,184,166,0.12), rgba(124,58,237,0.12))',
                        borderColor: 'rgba(255,255,255,0.12)',
                    }}
                >
                    <div>
                        <p className="section-label mb-2">Coaching Tip</p>
                        <p className="text-sm text-gray-200 leading-relaxed">{q.tip}</p>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500 mt-3">
                        <span className={`px-2 py-0.5 rounded-full border text-xs ${style.chip}`}>{q.type}</span>
                        <span>← hover back to see question</span>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default function InterviewPrepPage() {
    const toast = useToast()
    const [searchParams] = useSearchParams()
    const internshipId   = searchParams.get('id')

    const [internship, setInternship]   = useState(null)
    const [questions, setQuestions]     = useState([])
    const [llmUsed, setLlmUsed]         = useState(false)
    const [loading, setLoading]         = useState(false)
    const [activeFilter, setFilter]     = useState('all')
    const [error, setError]             = useState('')

    const fetchPrep = useCallback(async (id) => {
        setLoading(true)
        setError('')
        try {
            const { data } = await api.post(`/internships/${id}/interview-prep`)
            setInternship(data.data.internship)
            setQuestions(data.data.questions || [])
            setLlmUsed(data.data.llm_used || false)
        } catch (err) {
            const msg = err.response?.data?.message || 'Could not load interview questions'
            setError(msg)
            toast({ message: msg, type: 'error' })
        } finally {
            setLoading(false)
        }
    }, [toast])

    useEffect(() => {
        if (internshipId) {
            fetchPrep(internshipId)
        }
    }, [internshipId, fetchPrep])

    const TYPES = ['all', 'technical', 'behavioral', 'situational']
    const filtered = activeFilter === 'all'
        ? questions
        : questions.filter(q => q.type === activeFilter)

    if (!internshipId) {
        return (
            <div className="min-h-screen flex flex-col">
                <Navbar />
                <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-16 text-center">
                    <div className="text-5xl mb-4">🎤</div>
                    <h1 className="text-2xl font-bold text-white mb-2">Interview Prep</h1>
                    <p className="text-gray-400 mb-6">
                        Open this page from an internship card to generate tailored questions.
                    </p>
                    <a href="/internships" className="btn-primary">Browse Internships</a>
                </main>
            </div>
        )
    }

    return (
        <div className="min-h-screen flex flex-col">
            <Navbar />
            <main className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">

                {/* Header */}
                <div>
                    <p className="section-label mb-1">Interview Prep</p>
                    {internship ? (
                        <>
                            <h1 className="text-3xl font-bold text-white">{internship.title}</h1>
                            <p className="text-gray-400 mt-1">
                                {internship.company}
                                {internship.domain ? ` · ${internship.domain}` : ''}
                            </p>
                        </>
                    ) : (
                        <h1 className="text-3xl font-bold text-white">Loading…</h1>
                    )}
                </div>

                {/* Skills used */}
                {internship?.required_skills?.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                        {internship.required_skills.map(s => (
                            <span key={s} className="text-xs px-2.5 py-1 rounded-full bg-brand-500/15 border border-brand-500/30 text-brand-200">
                                {s}
                            </span>
                        ))}
                    </div>
                )}

                {/* Source badge */}
                {!loading && questions.length > 0 && (
                    <div className="flex items-center gap-3">
                        <span className={`text-xs px-3 py-1.5 rounded-full border ${
                            llmUsed
                                ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300'
                                : 'bg-gray-700/40 border-white/10 text-gray-400'
                        }`}>
                            {llmUsed ? '✨ AI-generated questions' : '📋 Curated question bank'}
                        </span>
                        <button
                            onClick={() => fetchPrep(internshipId)}
                            className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
                            id="regenerate-btn"
                        >
                            ↺ Regenerate
                        </button>
                    </div>
                )}

                {/* Type filter chips */}
                {!loading && questions.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                        {TYPES.map(t => (
                            <button
                                key={t}
                                onClick={() => setFilter(t)}
                                className={`text-xs px-3 py-1.5 rounded-full border transition-all capitalize ${
                                    activeFilter === t
                                        ? 'bg-brand-500/30 border-brand-500/50 text-brand-200'
                                        : 'border-white/10 text-gray-500 hover:border-white/25 hover:text-gray-300'
                                }`}
                                id={`filter-${t}`}
                            >
                                {t === 'all' ? `All (${questions.length})` : `${TYPE_STYLES[t]?.icon} ${t} (${questions.filter(q => q.type === t).length})`}
                            </button>
                        ))}
                    </div>
                )}

                {/* Loading state */}
                {loading && (
                    <div className="flex flex-col items-center justify-center py-20 space-y-4">
                        <div className="spinner" style={{ width: 40, height: 40 }} />
                        <p className="text-gray-400 text-sm">Generating questions for {internship?.title ?? 'this role'}…</p>
                    </div>
                )}

                {/* Error */}
                {!loading && error && (
                    <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 px-5 py-4 rounded-2xl">
                        {error}
                    </div>
                )}

                {/* Question grid */}
                {!loading && filtered.length > 0 && (
                    <>
                        <p className="text-xs text-gray-600">Hover any card to flip it and reveal the coaching tip</p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                            {filtered.map((q, i) => (
                                <QuestionCard key={i} q={q} index={i} />
                            ))}
                        </div>
                    </>
                )}

            </main>
        </div>
    )
}
