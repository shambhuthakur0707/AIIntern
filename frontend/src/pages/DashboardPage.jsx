import { useState, useEffect, useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import Navbar from '../components/Navbar'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { InternshipCardSkeleton } from '../components/Skeleton'
import OnboardingWizard from '../components/OnboardingWizard'

const SKILL_SUGGESTIONS = [
    'Python', 'JavaScript', 'React', 'Node.js', 'SQL', 'TensorFlow', 'PyTorch',
    'Machine Learning', 'Deep Learning', 'NLP', 'Data Analysis', 'Docker',
    'AWS', 'MongoDB', 'Git', 'Java', 'Scikit-learn', 'Pandas', 'NumPy',
    'Computer Vision', 'Flutter', 'Kotlin', 'REST API', 'DevOps', 'Kubernetes',
    'TypeScript', 'GraphQL', 'PostgreSQL', 'Redis', 'Flask', 'FastAPI', 'Django',
]

// ---------- Stat Card ----------
function StatCard({ label, value, sub, icon, color }) {
    return (
        <div className="bg-white/5 border border-white/10 rounded-2xl p-5 flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl shrink-0 ${color}`}>{icon}</div>
            <div>
                <p className="text-2xl font-extrabold text-white leading-none">{value}</p>
                <p className="text-xs text-gray-400 mt-1 font-medium">{label}</p>
                {sub && <p className="text-xs text-gray-600 mt-0.5">{sub}</p>}
            </div>
        </div>
    )
}

// ---------- Confidence Arc ----------
function ConfidenceArc({ score }) {
    const r = 42, circ = 2 * Math.PI * r
    const offset = circ - (Math.min(score, 100) / 100) * circ
    const color = score >= 70 ? '#10b981' : score >= 45 ? '#6366f1' : '#f59e0b'
    return (
        <div className="relative flex flex-col items-center">
            <svg width="104" height="104" viewBox="0 0 104 104" className="-rotate-90">
                <circle cx="52" cy="52" r={r} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="9" />
                <circle cx="52" cy="52" r={r} fill="none" stroke={color} strokeWidth="9"
                    strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
                    style={{ transition: 'stroke-dashoffset 1.4s ease-out' }} />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl font-extrabold text-white leading-none">{score.toFixed(0)}%</span>
                <span className="text-[10px] text-gray-500 mt-0.5">Match</span>
            </div>
        </div>
    )
}

// ---------- Skills Gap Chart ----------
function SkillsGapChart({ recommendations }) {
    const data = useMemo(() => {
        const skillMap = {}
        recommendations.forEach((rec) => {
            const missing = rec.missing_skills ?? []
            const matched = rec.matched_skills ?? []
            missing.forEach(s => {
                if (!s) return
                const key = s.length > 14 ? s.slice(0, 13) + '…' : s
                skillMap[key] = skillMap[key] || { skill: key, marketDemand: 0, userHas: 0 }
                skillMap[key].marketDemand += 1
            })
            matched.forEach(s => {
                if (!s) return
                const key = s.length > 14 ? s.slice(0, 13) + '…' : s
                skillMap[key] = skillMap[key] || { skill: key, marketDemand: 0, userHas: 0 }
                skillMap[key].userHas += 1
                skillMap[key].marketDemand += 1
            })
        })
        return Object.values(skillMap).sort((a, b) => b.marketDemand - a.marketDemand).slice(0, 10)
    }, [recommendations])

    if (data.length === 0) return <p className="text-xs text-gray-600 text-center py-10">Run the agent to see skill data.</p>

    return (
        <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 30 }} barCategoryGap="30%">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="skill" tick={{ fill: '#9ca3af', fontSize: 10 }} angle={-35} textAnchor="end" interval={0} height={54} />
                <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} allowDecimals={false} />
                <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10, color: '#e5e7eb' }} labelStyle={{ color: '#f9fafb', fontWeight: 600 }} />
                <Legend wrapperStyle={{ fontSize: 11, color: '#9ca3af', paddingTop: 4 }} />
                <Bar dataKey="marketDemand" name="Market Demand" fill="#6366f1" radius={[4, 4, 0, 0]} />
                <Bar dataKey="userHas" name="You Have" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
        </ResponsiveContainer>
    )
}

// ---------- Recommendation Card ----------
function RecCard({ rec, index }) {
    const [open, setOpen] = useState(false)
    const [copied, setCopied] = useState(false)
    const roadmap = rec.learning_roadmap ?? []
    const score = Number(rec.confidence_score ?? 0).toFixed(0)
    const scoreBg = score >= 70 ? 'bg-emerald-500/15 border-emerald-500/30' : score >= 45 ? 'bg-indigo-500/15 border-indigo-500/30' : 'bg-amber-500/15 border-amber-500/30'
    const scoreText = score >= 70 ? 'text-emerald-400' : score >= 45 ? 'text-indigo-400' : 'text-amber-400'

    const copyRoadmap = () => {
        const text = roadmap.map((w, i) => `Week ${i + 1}: ${w.goal ?? w.topic ?? JSON.stringify(w)}`).join('\n')
        navigator.clipboard.writeText(text).then(() => { setCopied(true); setTimeout(() => setCopied(false), 2000) })
    }

    return (
        <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden hover:border-white/20 transition-colors">
            <div className="flex items-start justify-between gap-4 p-5">
                <div className="flex items-start gap-4 min-w-0">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center text-sm font-bold text-white shrink-0">#{index + 1}</div>
                    <div className="min-w-0">
                        <h3 className="font-bold text-white text-base leading-snug">{rec.internship_title ?? rec.title}</h3>
                        <p className="text-sm text-gray-400 mt-0.5">{rec.company ?? rec.internship_company ?? '—'}</p>
                        <div className="flex flex-wrap gap-1.5 mt-2">
                            {(rec.matched_skills ?? []).slice(0, 4).map(s => (
                                <span key={s} className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/15 border border-indigo-500/25 text-indigo-300">{s}</span>
                            ))}
                            {(rec.matched_skills ?? []).length > 4 && <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-gray-500">+{rec.matched_skills.length - 4} more</span>}
                        </div>
                    </div>
                </div>
                <div className={`text-center px-3 py-2 rounded-xl border shrink-0 ${scoreBg}`}>
                    <p className={`text-xl font-extrabold leading-none ${scoreText}`}>{score}%</p>
                    <p className="text-[10px] text-gray-500 mt-0.5">Confidence</p>
                </div>
            </div>

            {rec.reasoning && (
                <div className="px-5 pb-4">
                    <p className="text-xs text-gray-400 leading-relaxed border-l-2 border-indigo-500/50 pl-3">{rec.reasoning}</p>
                </div>
            )}

            {(rec.missing_skills ?? []).length > 0 && (
                <div className="px-5 pb-4 flex flex-wrap gap-1.5 items-center">
                    <span className="text-[10px] text-gray-500">Gaps:</span>
                    {rec.missing_skills.slice(0, 5).map(s => (
                        <span key={s} className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-300">{s}</span>
                    ))}
                </div>
            )}

            {roadmap.length > 0 && (
                <div className="border-t border-white/5">
                    <div className="flex items-center justify-between px-5 py-3">
                        <button type="button" onClick={() => setOpen(o => !o)} className="text-xs text-gray-400 hover:text-white transition-colors flex items-center gap-1">
                            📝 Roadmap ({roadmap.length} weeks)
                            <svg className={`w-3.5 h-3.5 transition-transform duration-200 ${open ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                        </button>
                        {open && <button type="button" onClick={copyRoadmap} className="text-[10px] text-gray-500 hover:text-gray-300">{copied ? '✓ Copied' : '⎘ Copy'}</button>}
                    </div>
                    {open && (
                        <div className="px-5 pb-4 space-y-2">
                            {roadmap.map((week, wi) => (
                                <div key={wi} className="flex gap-3 text-xs">
                                    <span className="shrink-0 w-14 text-indigo-400 font-medium">Week {wi + 1}</span>
                                    <span className="text-gray-400">{week.goal ?? week.topic ?? JSON.stringify(week)}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            <div className="px-5 py-3 border-t border-white/5 flex justify-end">
                <a href={rec.apply_url ?? '#'} target="_blank" rel="noreferrer"
                    className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-1.5 rounded-lg font-medium transition-colors">
                    Apply now →
                </a>
            </div>
        </div>
    )
}

// ================================================================
// Main Dashboard
// ================================================================
export default function DashboardPage() {
    const { user, updateUser } = useAuth()
    const toast = useToast()
    const [matchResult, setMatchResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [dashLoading, setDashLoading] = useState(true)
    const [skillInput, setSkillInput] = useState('')
    const [profileBusy, setProfileBusy] = useState(false)
    const [cvFile, setCvFile] = useState(null)
    const [profileLinks, setProfileLinks] = useState({ linkedin_url: '', github_url: '' })
    const [matchHistory, setMatchHistory] = useState(() => {
        try { return JSON.parse(localStorage.getItem('matchHistory') ?? '[]') } catch { return [] }
    })
    const [showOnboarding, setShowOnboarding] = useState(false)
    const [importOpen, setImportOpen] = useState(false)
    const [historyOpen, setHistoryOpen] = useState(false)

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
        const dismissed = localStorage.getItem('onboardingDone')
        if (!dismissed && user && (!user.skills || user.skills.length === 0)) setShowOnboarding(true)
    }, [user?.skills?.length]) // eslint-disable-line

    useEffect(() => {
        setProfileLinks({ linkedin_url: user?.linkedin_url || '', github_url: user?.github_url || '' })
    }, [user?.linkedin_url, user?.github_url])

    const runAgent = async () => {
        setError(''); setLoading(true); setMatchResult(null)
        try {
            const { data } = await api.post('/agent/match')
            setMatchResult(data.data.match_result)
            if (data.data.user) updateUser(data.data.user)
            const result = data.data.match_result
            const entry = {
                timestamp: new Date().toISOString(),
                confidence: result?.confidence_score ?? null,
                top_match: result?.recommendations?.[0]?.internship_title ?? 'Unknown',
            }
            setMatchHistory(prev => {
                const updated = [entry, ...prev].slice(0, 5)
                localStorage.setItem('matchHistory', JSON.stringify(updated))
                return updated
            })
        } catch (err) {
            const status = err.response?.status
            const serverMsg = err.response?.data?.errors || err.response?.data?.message
            if (status === 401) setError('Session expired. Please log out and log back in.')
            else if (serverMsg) setError(serverMsg)
            else if (err.code === 'ERR_NETWORK' || !err.response) setError('Cannot reach the backend. Make sure Flask is running on port 5000.')
            else setError(`Agent failed (HTTP ${status ?? 'unknown'}). Check backend logs.`)
        } finally { setLoading(false) }
    }

    const handleAddSkill = async () => {
        const skill = skillInput.trim(); if (!skill) return
        setProfileBusy(true)
        try {
            const { data } = await api.patch('/profile/skills/add', { skill })
            updateUser(data.data.user); setSkillInput('')
            toast({ message: `Added: ${skill}`, type: 'success' })
        } catch (err) { toast({ message: err.response?.data?.message || 'Could not add skill.', type: 'error' }) }
        finally { setProfileBusy(false) }
    }

    const handleRemoveSkill = async (skill) => {
        setProfileBusy(true)
        try {
            const { data } = await api.patch('/profile/skills/remove', { skill })
            updateUser(data.data.user); toast({ message: `Removed: ${skill}`, type: 'info' })
        } catch (err) { toast({ message: err.response?.data?.message || 'Could not remove.', type: 'error' }) }
        finally { setProfileBusy(false) }
    }

    const handleImportProfile = async () => {
        setProfileBusy(true)
        try {
            const formData = new FormData()
            formData.append('linkedin_url', profileLinks.linkedin_url || '')
            formData.append('github_url', profileLinks.github_url || '')
            if (cvFile) formData.append('cv', cvFile)
            const { data } = await api.post('/profile/import', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
            updateUser(data.data.user); setCvFile(null)
            const c = data.data.imported_skills?.length || 0
            toast({ message: `Imported ${c} skill${c !== 1 ? 's' : ''}.`, type: 'success' })
        } catch (err) { toast({ message: err.response?.data?.message || 'Import failed.', type: 'error' }) }
        finally { setProfileBusy(false) }
    }

    const recs = matchResult?.recommendations ?? []
    const meta = matchResult?.meta ?? {}
    const avgConf = recs.length ? recs.reduce((s, r) => s + Number(r.confidence_score || 0), 0) / recs.length : 0
    const confScore = matchResult?.confidence_score ?? avgConf
    const totalGaps = recs.reduce((s, r) => s + (r.missing_skills?.length ?? 0), 0)
    const skillsMatched = recs.reduce((s, r) => s + (r.matched_skills?.length ?? 0), 0)
    const overallSummary = matchResult?.overall_ai_summary || `Generated ${meta.returned ?? recs.length} recommendations from ${meta.passed_filter ?? 0} filtered internships.`
    const suggestions = SKILL_SUGGESTIONS.filter(
        s => !(user?.skills ?? []).map(x => x.toLowerCase()).includes(s.toLowerCase()) &&
            (skillInput === '' || s.toLowerCase().includes(skillInput.toLowerCase()))
    ).slice(0, 8)

    return (
        <div className="min-h-screen bg-gray-950 flex flex-col">
            <Navbar />

            {showOnboarding && (
                <OnboardingWizard onClose={() => { localStorage.setItem('onboardingDone', '1'); setShowOnboarding(false) }} />
            )}

            <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-6">

                {/* ── TOP ROW: Profile + Run Agent ── */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                    {/* Profile card */}
                    <div className="lg:col-span-2 bg-white/5 border border-white/10 rounded-2xl p-6">
                        <div className="flex items-center gap-4 mb-5">
                            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-2xl font-black text-white shrink-0">
                                {user?.name?.[0]?.toUpperCase()}
                            </div>
                            <div>
                                <h2 className="text-lg font-bold text-white">{user?.name}</h2>
                                <p className="text-sm text-gray-400">{user?.education || 'Student'} · <span className="capitalize text-indigo-400">{user?.experience_level || 'Beginner'}</span></p>
                            </div>
                        </div>

                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Your Skills</p>
                        <div className="flex flex-wrap gap-2 min-h-[32px]">
                            {(user?.skills ?? []).map(s => (
                                <span key={s} className="inline-flex items-center gap-1 text-xs bg-indigo-500/15 border border-indigo-500/25 text-indigo-300 px-2.5 py-1 rounded-full">
                                    {s}
                                    <button type="button" onClick={() => handleRemoveSkill(s)} disabled={profileBusy} className="hover:text-rose-300 ml-0.5 leading-none">×</button>
                                </span>
                            ))}
                            {(user?.skills ?? []).length === 0 && <span className="text-xs text-gray-600">No skills yet — add some below</span>}
                        </div>

                        <div className="mt-4 flex gap-2">
                            <input type="text" value={skillInput}
                                onChange={e => setSkillInput(e.target.value)}
                                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleAddSkill() } }}
                                placeholder="Add a skill…" className="form-input flex-1 !py-1.5 !text-sm" disabled={profileBusy} />
                            <button type="button" onClick={handleAddSkill} disabled={profileBusy}
                                className="text-sm bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-1.5 rounded-lg font-medium transition-colors">Add</button>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-1.5">
                            {suggestions.map(s => (
                                <button key={s} type="button" onClick={() => setSkillInput(s)} disabled={profileBusy}
                                    className="text-xs text-gray-500 hover:text-indigo-400 border border-white/10 hover:border-indigo-500/30 px-2 py-0.5 rounded-full transition-colors">
                                    + {s}
                                </button>
                            ))}
                        </div>

                        <button type="button" onClick={() => setImportOpen(o => !o)}
                            className="mt-4 text-xs text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1">
                            🔗 {importOpen ? 'Hide' : 'Show'} CV & Platform Import
                        </button>
                        {importOpen && (
                            <div className="mt-3 space-y-3 border-t border-white/5 pt-3">
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    <input type="url" className="form-input !py-1.5 !text-sm" placeholder="LinkedIn URL"
                                        value={profileLinks.linkedin_url} onChange={e => setProfileLinks(p => ({ ...p, linkedin_url: e.target.value }))} disabled={profileBusy} />
                                    <input type="url" className="form-input !py-1.5 !text-sm" placeholder="GitHub URL"
                                        value={profileLinks.github_url} onChange={e => setProfileLinks(p => ({ ...p, github_url: e.target.value }))} disabled={profileBusy} />
                                </div>
                                <div className="flex gap-3 items-center">
                                    <input type="file" accept=".txt,.md,.rtf" onChange={e => setCvFile(e.target.files?.[0] || null)} disabled={profileBusy} className="text-xs text-gray-400 flex-1" />
                                    <button type="button" onClick={handleImportProfile} disabled={profileBusy}
                                        className="text-xs bg-white/10 hover:bg-white/15 text-gray-300 border border-white/10 px-3 py-1.5 rounded-lg transition-colors shrink-0">
                                        {profileBusy ? 'Saving…' : 'Import'}
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Run Agent card */}
                    <div className="bg-gradient-to-br from-indigo-600/20 to-violet-600/20 border border-indigo-500/30 rounded-2xl p-6 flex flex-col items-center justify-center gap-4 text-center">
                        <div className="text-4xl">🤖</div>
                        <div>
                            <h3 className="text-base font-bold text-white">AI Internship Agent</h3>
                            <p className="text-xs text-gray-400 mt-1 max-w-[180px] mx-auto">Scores, ranks, and explains every match using AI</p>
                        </div>
                        <button id="run-agent-btn" onClick={runAgent} disabled={loading}
                            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white font-semibold py-2.5 rounded-xl transition-colors flex items-center justify-center gap-2">
                            {loading
                                ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Thinking…</>
                                : <><svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>Run AI Agent</>
                            }
                        </button>
                        {!loading && <p className="text-[10px] text-gray-600">Takes ~30–60 seconds</p>}
                    </div>
                </div>

                {/* ── Agent loading ── */}
                {loading && (
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-10 flex flex-col items-center gap-4">
                        <div className="relative">
                            <div className="w-14 h-14 rounded-full border-4 border-indigo-500/30 border-t-indigo-500 animate-spin" />
                            <div className="absolute inset-0 flex items-center justify-center text-xl">🤖</div>
                        </div>
                        <p className="text-sm font-semibold text-white">AI Agent is working…</p>
                        <p className="text-xs text-gray-500 max-w-xs text-center">Fetching internships → Scoring matches → Detecting skill gaps → Generating roadmaps</p>
                        <div className="flex gap-2 flex-wrap justify-center">
                            {['Fetching DB', 'Scoring Skills', 'Gap Analysis', 'Ranking'].map(step => (
                                <span key={step} className="text-[10px] bg-indigo-500/15 border border-indigo-500/25 text-indigo-300 px-3 py-1 rounded-full animate-pulse">{step}</span>
                            ))}
                        </div>
                    </div>
                )}

                {/* ── Error ── */}
                {error && <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 px-5 py-4 rounded-2xl text-sm">⚠️ {error}</div>}

                {/* ── Skeleton ── */}
                {dashLoading && !loading && (
                    <div className="space-y-4">{Array.from({ length: 3 }).map((_, i) => <InternshipCardSkeleton key={i} />)}</div>
                )}

                {/* ── Empty state ── */}
                {!loading && !dashLoading && !matchResult && !error && (
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-14 text-center">
                        <div className="text-5xl mb-4">🚀</div>
                        <h3 className="text-lg font-bold text-white mb-2">Ready to find your internship?</h3>
                        <p className="text-sm text-gray-500 max-w-sm mx-auto">
                            Click <span className="text-indigo-400 font-medium">"Run AI Agent"</span> above to get AI-powered ranked matches with personalised roadmaps.
                        </p>
                    </div>
                )}

                {/* ====== RESULTS ====== */}
                {!loading && matchResult && (
                    <div className="space-y-6 animate-fade-in">

                        {/* Stat cards */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <StatCard label="Match Confidence" value={`${confScore.toFixed(0)}%`} icon="🎯" color="bg-indigo-500/20" />
                            <StatCard label="Recommendations" value={recs.length} icon="🏆" color="bg-violet-500/20" sub={`from ${meta.passed_filter ?? 0} candidates`} />
                            <StatCard label="Skills Matched" value={skillsMatched} icon="✅" color="bg-emerald-500/20" />
                            <StatCard label="Skill Gaps Found" value={totalGaps} icon="📈" color="bg-amber-500/20" sub="across all matches" />
                        </div>

                        {/* Chart + Summary */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            <div className="lg:col-span-2 bg-white/5 border border-white/10 rounded-2xl p-6">
                                <div className="flex items-center justify-between mb-4">
                                    <div>
                                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Skills Gap Analysis</p>
                                        <h3 className="text-base font-bold text-white mt-0.5">Market Demand vs Your Skills</h3>
                                    </div>
                                    <div className="flex items-center gap-3 text-[10px] text-gray-500">
                                        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-indigo-500 inline-block" />Market</span>
                                        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 inline-block" />You Have</span>
                                    </div>
                                </div>
                                <SkillsGapChart recommendations={recs} />
                            </div>

                            <div className="flex flex-col gap-4">
                                <div className="bg-white/5 border border-white/10 rounded-2xl p-5 flex flex-col items-center gap-3">
                                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Overall Score</p>
                                    <ConfidenceArc score={confScore} />
                                    <p className="text-[10px] text-gray-600 text-center">Based on your skills vs. internship requirements</p>
                                </div>
                                <div className="flex-1 bg-white/5 border border-white/10 rounded-2xl p-5">
                                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">🧠 AI Summary</p>
                                    <p className="text-xs text-gray-400 leading-relaxed">{overallSummary}</p>
                                    {meta.model_used && (
                                        <p className="text-[10px] text-gray-600 mt-3 border-t border-white/5 pt-2">
                                            Model: <span className="text-indigo-400">{meta.model_used}</span>
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Match history */}
                        {matchHistory.length > 0 && (
                            <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
                                <button type="button" onClick={() => setHistoryOpen(o => !o)}
                                    className="flex items-center justify-between w-full text-sm font-medium text-gray-400 hover:text-white transition-colors">
                                    <span>📅 Match History ({matchHistory.length} run{matchHistory.length !== 1 ? 's' : ''})</span>
                                    <span className="text-xs">{historyOpen ? '▲' : '▼'}</span>
                                </button>
                                {historyOpen && (
                                    <ul className="mt-3 space-y-1.5">
                                        {matchHistory.map((h, i) => (
                                            <li key={i} className="flex items-center justify-between text-xs bg-white/5 rounded-lg px-3 py-2">
                                                <span className="text-gray-500">{new Date(h.timestamp).toLocaleString()}</span>
                                                <span className="text-gray-300 truncate max-w-[40%] mx-2">{h.top_match}</span>
                                                <span className="text-indigo-400 font-semibold shrink-0">{h.confidence != null ? `${Math.round(h.confidence * 100)}%` : 'N/A'}</span>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                        )}

                        {/* Recommendations */}
                        <div>
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-bold text-white">🏆 Top {recs.length} Recommendations</h2>
                                <span className="text-[10px] text-gray-600 border border-white/10 bg-white/5 px-3 py-1 rounded-full">
                                    Powered by {meta.model_used ?? 'AI'} · Flask Agent
                                </span>
                            </div>
                            <div className="space-y-4">
                                {recs.map((rec, i) => <RecCard key={i} rec={rec} index={i} />)}
                            </div>
                        </div>
                    </div>
                )}
            </main>

            <footer className="border-t border-white/5 text-center py-4 text-xs text-gray-700">
                AIIntern &middot; Agentic AI Internship Matcher &middot; Groq / Ollama &middot; Flask &middot; React
            </footer>
        </div>
    )
}
