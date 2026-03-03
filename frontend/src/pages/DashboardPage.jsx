import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import InternshipCard from '../components/InternshipCard'
import SkillBadge from '../components/SkillBadge'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'

// Confidence ring around the score
function ConfidenceRing({ score }) {
    const radius = 40
    const circ = 2 * Math.PI * radius
    const offset = circ - (score / 100) * circ

    const color = score >= 70 ? '#10b981' : score >= 45 ? '#6366f1' : '#f59e0b'

    return (
        <div className="flex flex-col items-center gap-2">
            <svg width="100" height="100" viewBox="0 0 100 100" className="-rotate-90">
                <circle cx="50" cy="50" r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="8" />
                <circle cx="50" cy="50" r={radius} fill="none" stroke={color} strokeWidth="8"
                    strokeDasharray={circ} strokeDashoffset={offset}
                    strokeLinecap="round"
                    style={{ transition: 'stroke-dashoffset 1.5s ease-out' }} />
            </svg>
            <div className="absolute" style={{ marginTop: '-68px' }}>
                <p className="text-2xl font-extrabold text-white text-center">{score.toFixed(0)}%</p>
            </div>
            <p className="text-xs text-gray-500 font-medium -mt-1">Confidence</p>
        </div>
    )
}

export default function DashboardPage() {
    const { user, updateUser } = useAuth()
    const [matchResult, setMatchResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [dashLoading, setDashLoading] = useState(true)
    const [skillInput, setSkillInput] = useState('')
    const [profileBusy, setProfileBusy] = useState(false)
    const [profileMessage, setProfileMessage] = useState('')
    const [cvFile, setCvFile] = useState(null)
    const [profileLinks, setProfileLinks] = useState({
        linkedin_url: '',
        github_url: '',
    })

    // Load last result on mount
    useEffect(() => {
        api.get('/dashboard')
            .then(({ data }) => {
                if (data.data.match_result) setMatchResult(data.data.match_result)
                if (data.data.user) updateUser(data.data.user)
            })
            .catch(() => { })
            .finally(() => setDashLoading(false))
    }, []) // eslint-disable-line

    useEffect(() => {
        setProfileLinks({
            linkedin_url: user?.linkedin_url || '',
            github_url: user?.github_url || '',
        })
    }, [user?.linkedin_url, user?.github_url])

    const runAgent = async () => {
        setError('')
        setLoading(true)
        setMatchResult(null)
        try {
            const { data } = await api.post('/agent/match')
            setMatchResult(data.data.match_result)
            if (data.data.user) updateUser(data.data.user)
        } catch (err) {
            setError(
                err.response?.data?.errors ||
                err.response?.data?.message ||
                'Agent failed. Check backend logs and try again.'
            )
        } finally {
            setLoading(false)
        }
    }

    const handleAddSkill = async () => {
        const skill = skillInput.trim()
        if (!skill) return
        setProfileBusy(true)
        setError('')
        setProfileMessage('')
        try {
            const { data } = await api.patch('/profile/skills/add', { skill })
            updateUser(data.data.user)
            setSkillInput('')
            setProfileMessage(`Added skill: ${skill}`)
        } catch (err) {
            setError(err.response?.data?.message || 'Could not add skill.')
        } finally {
            setProfileBusy(false)
        }
    }

    const handleRemoveSkill = async (skill) => {
        setProfileBusy(true)
        setError('')
        setProfileMessage('')
        try {
            const { data } = await api.patch('/profile/skills/remove', { skill })
            updateUser(data.data.user)
            setProfileMessage(`Removed skill: ${skill}`)
        } catch (err) {
            setError(err.response?.data?.message || 'Could not remove skill.')
        } finally {
            setProfileBusy(false)
        }
    }

    const handleImportProfile = async () => {
        setProfileBusy(true)
        setError('')
        setProfileMessage('')
        try {
            const formData = new FormData()
            formData.append('linkedin_url', profileLinks.linkedin_url || '')
            formData.append('github_url', profileLinks.github_url || '')
            if (cvFile) formData.append('cv', cvFile)

            const { data } = await api.post('/profile/import', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            })
            updateUser(data.data.user)
            setCvFile(null)
            const importedCount = data.data.imported_skills?.length || 0
            setProfileMessage(`Profile updated. Imported ${importedCount} skills from CV/links.`)
        } catch (err) {
            setError(err.response?.data?.message || err.response?.data?.errors || 'Profile import failed.')
        } finally {
            setProfileBusy(false)
        }
    }

    const recs = matchResult?.recommendations ?? []
    const meta = matchResult?.meta ?? {}
    const avgConfidence = recs.length
        ? recs.reduce((sum, r) => sum + Number(r.confidence_score || 0), 0) / recs.length
        : 0
    const overallSummary =
        matchResult?.overall_ai_summary ||
        `Generated ${meta.returned ?? recs.length} recommendations from ${meta.passed_filter ?? 0} filtered internships.`

    return (
        <div className="min-h-screen flex flex-col">
            <Navbar />

            <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">

                {/* ── Hero / Profile section ── */}
                <section className="glass-card p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
                    <div className="flex items-center gap-4">
                        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-500 to-violet-500 flex items-center justify-center text-2xl font-black text-white shadow-xl shadow-brand-500/30 flex-shrink-0">
                            {user?.name?.[0]?.toUpperCase()}
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white">{user?.name}</h2>
                            <p className="text-sm text-gray-400">{user?.education || 'Student'}</p>
                            <p className="text-xs text-brand-400 font-medium mt-0.5 capitalize">{user?.experience_level} level</p>
                        </div>
                    </div>

                    {/* User skills */}
                    <div className="flex-1">
                        <p className="section-label mb-2">Your Skills</p>
                        <div className="flex flex-wrap gap-2">
                            {(user?.skills ?? []).map((s) => (
                                <span key={s} className="inline-flex items-center gap-1.5">
                                    <SkillBadge skill={s} />
                                    <button
                                        type="button"
                                        onClick={() => handleRemoveSkill(s)}
                                        disabled={profileBusy}
                                        className="text-xs text-gray-500 hover:text-rose-300"
                                        title={`Remove ${s}`}
                                    >
                                        x
                                    </button>
                                </span>
                            ))}
                        </div>
                        <div className="mt-3 flex gap-2">
                            <input
                                type="text"
                                value={skillInput}
                                onChange={(e) => setSkillInput(e.target.value)}
                                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleAddSkill() } }}
                                placeholder="Add a skill (e.g. TensorFlow)"
                                className="form-input flex-1"
                                disabled={profileBusy}
                            />
                            <button type="button" className="btn-secondary px-4" onClick={handleAddSkill} disabled={profileBusy}>
                                Add
                            </button>
                        </div>
                    </div>

                    {/* Run agent button */}
                    <div className="flex flex-col items-center gap-2 flex-shrink-0">
                        <button
                            id="run-agent-btn"
                            onClick={runAgent}
                            disabled={loading}
                            className="btn-primary flex items-center gap-2 min-w-[180px] justify-center"
                        >
                            {loading ? (
                                <><div className="spinner" />Agent thinking…</>
                            ) : (
                                <>
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                            d="M13 10V3L4 14h7v7l9-11h-7z" />
                                    </svg>
                                    Run AI Agent
                                </>
                            )}
                        </button>
                        {!loading && <p className="text-xs text-gray-600">~30-60 sec</p>}
                    </div>
                </section>

                <section className="glass-card p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-base font-semibold text-white">CV & Platform Import</h3>
                        <span className="text-xs text-gray-500">Imports skills to improve matching</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs text-gray-400 mb-1.5">LinkedIn URL</label>
                            <input
                                type="url"
                                className="form-input"
                                placeholder="https://www.linkedin.com/in/your-profile"
                                value={profileLinks.linkedin_url}
                                onChange={(e) => setProfileLinks((p) => ({ ...p, linkedin_url: e.target.value }))}
                                disabled={profileBusy}
                            />
                        </div>
                        <div>
                            <label className="block text-xs text-gray-400 mb-1.5">GitHub URL</label>
                            <input
                                type="url"
                                className="form-input"
                                placeholder="https://github.com/your-username"
                                value={profileLinks.github_url}
                                onChange={(e) => setProfileLinks((p) => ({ ...p, github_url: e.target.value }))}
                                disabled={profileBusy}
                            />
                        </div>
                    </div>

                    <div className="mt-4 flex flex-col sm:flex-row gap-3 sm:items-center">
                        <input
                            type="file"
                            accept=".txt,.md,.rtf"
                            onChange={(e) => setCvFile(e.target.files?.[0] || null)}
                            disabled={profileBusy}
                            className="text-sm text-gray-400"
                        />
                        <button
                            type="button"
                            className="btn-primary sm:w-auto w-full"
                            onClick={handleImportProfile}
                            disabled={profileBusy}
                        >
                            {profileBusy ? 'Saving profile...' : 'Save & Import'}
                        </button>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                        Supported CV formats: .txt, .md, .rtf
                        {user?.resume_filename ? ` | Last uploaded: ${user.resume_filename}` : ''}
                    </p>
                    {profileMessage && <p className="text-sm text-emerald-400 mt-3">{profileMessage}</p>}
                </section>

                {/* ── Loading state ── */}
                {loading && (
                    <div className="glass-card p-10 flex flex-col items-center gap-5 animate-pulse-slow" id="agent-loading">
                        <div className="relative">
                            <div className="w-16 h-16 rounded-full border-4 border-brand-500/30 border-t-brand-500 animate-spin" />
                            <div className="absolute inset-0 flex items-center justify-center text-2xl">🤖</div>
                        </div>
                        <div className="text-center">
                            <h3 className="text-lg font-semibold text-white">AI Agent is working…</h3>
                            <p className="text-sm text-gray-400 mt-1 max-w-sm">
                                Fetching internships → Computing match scores → Analyzing skill gaps → Generating roadmaps
                            </p>
                        </div>
                        <div className="flex gap-2">
                            {['Fetching DB', 'Scoring Skills', 'Gap Analysis', 'Ranking'].map((step, i) => (
                                <div key={step} className="text-xs bg-brand-500/20 border border-brand-500/30 text-brand-300 px-3 py-1 rounded-full"
                                    style={{ animationDelay: `${i * 400}ms` }}>
                                    {step}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* ── Error ── */}
                {error && (
                    <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 px-5 py-4 rounded-2xl animate-fade-in">
                        <p className="font-medium">⚠️ {error}</p>
                    </div>
                )}

                {/* ── Dashboard loading ── */}
                {dashLoading && !loading && (
                    <div className="text-center text-gray-600 py-12">Loading your profile…</div>
                )}

                {/* ── No results yet ── */}
                {!loading && !dashLoading && !matchResult && !error && (
                    <div className="glass-card p-12 text-center animate-fade-in" id="empty-state">
                        <div className="text-6xl mb-4">🚀</div>
                        <h3 className="text-xl font-bold text-white mb-2">Ready to find your internship?</h3>
                        <p className="text-gray-400 max-w-md mx-auto">
                            Click <span className="text-brand-400 font-medium">"Run AI Agent"</span> above. Our agentic AI will
                            analyze your profile, fetch internship listings, score each match, detect skill gaps, and generate
                            a personalized learning roadmap — all automatically.
                        </p>
                    </div>
                )}

                {/* ── Results ── */}
                {!loading && matchResult && (
                    <div className="space-y-6 animate-fade-in" id="results-section">

                        {/* Summary + Confidence */}
                        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {/* AI Summary */}
                            <div className="glass-card p-5 md:col-span-2">
                                <p className="section-label mb-3">🧠 AI Analysis Summary</p>
                                <p className="text-gray-300 leading-relaxed text-sm">{overallSummary}</p>
                            </div>

                            {/* Confidence ring */}
                            <div className="glass-card p-5 flex flex-col items-center justify-center gap-2 relative">
                                <p className="section-label mb-2">Match Confidence</p>
                                <div className="relative flex flex-col items-center">
                                    <ConfidenceRing score={matchResult.confidence_score ?? avgConfidence} />
                                </div>
                                <p className="text-xs text-gray-500 text-center mt-1">
                                    Based on your skills vs. all internship requirements
                                </p>
                            </div>
                        </section>

                        {/* Top 5 recommendations */}
                        <section>
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-bold text-white">
                                    🏆 Top {recs.length} Recommendations
                                </h2>
                                <span className="text-xs text-gray-500 bg-white/5 border border-white/10 px-3 py-1 rounded-full">
                                    Powered by Ollama + Flask Agent
                                </span>
                            </div>

                            <div className="space-y-4">
                                {recs.map((rec, i) => (
                                    <InternshipCard key={i} rec={rec} index={i} />
                                ))}
                            </div>
                        </section>
                    </div>
                )}

            </main>

            {/* Footer */}
            <footer className="border-t border-white/5 text-center py-4 text-xs text-gray-700">
                AIIntern — Agentic AI Internship Matcher · Built with LangChain, GPT-4o, Flask & React
            </footer>
        </div>
    )
}
