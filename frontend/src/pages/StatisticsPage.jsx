import { useState, useEffect, useMemo } from 'react'
import {
    PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer, LineChart, Line, ComposedChart,
    RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts'
import Navbar from '../components/Navbar'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

// ---------- Stat Card Component ----------
function StatCard({ label, value, subtext, icon, color, size = 'medium' }) {
    const sizeClass = size === 'large' ? 'p-6' : 'p-4'
    const textSize = size === 'large' ? 'text-3xl' : 'text-2xl'
    const iconSize = size === 'large' ? 'w-14 h-14' : 'w-12 h-12'

    return (
        <div className="bg-white/5 border border-white/10 rounded-2xl hover:border-white/20 transition-colors">
            <div className={`${sizeClass} flex items-start gap-4`}>
                <div className={`${iconSize} rounded-xl flex items-center justify-center text-2xl shrink-0 ${color}`}>
                    {icon}
                </div>
                <div className="flex-1">
                    <p className={`${textSize} font-extrabold text-white leading-tight`}>{value}</p>
                    <p className="text-xs text-gray-400 mt-1 font-medium">{label}</p>
                    {subtext && <p className="text-xs text-gray-600 mt-1">{subtext}</p>}
                </div>
            </div>
        </div>
    )
}

// ---------- Progress Bar Component ----------
function ProgressBar({ label, value, max = 100, color = 'bg-indigo-500' }) {
    const percentage = (value / max) * 100

    return (
        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-300 font-medium">{label}</span>
                <span className="text-sm font-bold text-white">{value}%</span>
            </div>
            <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                <div
                    className={`h-full ${color} transition-all duration-500`}
                    style={{ width: `${percentage}%` }}
                />
            </div>
        </div>
    )
}

// ---------- Skills Radar Chart Component ----------
function SkillsRadarChart({ topMatched, topMissing }) {
    const data = useMemo(() => {
        // Create a map of all skills with their proficiency levels
        const skillMap = {}

        // Add matched skills (available)
        topMatched.forEach(([skill, count]) => {
            skillMap[skill] = skillMap[skill] || { skill, matched: 0, missing: 0 }
            skillMap[skill].matched = count
        })

        // Add missing skills (required)
        topMissing.forEach(([skill, count]) => {
            skillMap[skill] = skillMap[skill] || { skill, matched: 0, missing: 0 }
            skillMap[skill].missing = count
        })

        // Combine both lists and take top 8 skills total
        return Object.values(skillMap)
            .sort((a, b) => (b.matched + b.missing) - (a.matched + a.missing))
            .slice(0, 8)
    }, [topMatched, topMissing])

    if (data.length === 0) {
        return (
            <div className="bg-white/5 border border-white/10 rounded-2xl p-8 text-center">
                <p className="text-gray-500">No skill data available</p>
            </div>
        )
    }

    return (
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
            <h3 className="text-sm font-bold text-white mb-4">📊 Available vs Required Skills</h3>
            <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <PolarGrid stroke="rgba(255,255,255,0.1)" />
                    <PolarAngleAxis dataKey="skill" tick={{ fontSize: 10, fill: '#9ca3af' }} />
                    <PolarRadiusAxis angle={90} domain={[0, 'auto']} tick={{ fill: '#6b7280', fontSize: 9 }} />
                    <Radar name="Your Skills" dataKey="matched" stroke="#10b981" fill="#10b981" fillOpacity={0.6} />
                    <Radar name="Required Skills" dataKey="missing" stroke="#ef4444" fill="#ef4444" fillOpacity={0.6} />
                    <Tooltip 
                        contentStyle={{ 
                            background: '#1f2937', 
                            border: '1px solid rgba(255,255,255,0.1)', 
                            borderRadius: 8, 
                            color: '#e5e7eb' 
                        }} 
                        labelStyle={{ color: '#f9fafb', fontWeight: 600 }}
                    />
                    <Legend wrapperStyle={{ fontSize: 11, color: '#9ca3af' }} />
                </RadarChart>
            </ResponsiveContainer>
            <div className="mt-4 grid grid-cols-2 gap-4 text-xs">
                <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3">
                    <p className="text-green-400 font-bold">✓ Your Skills</p>
                    <p className="text-gray-400 mt-1">Skills you already have</p>
                </div>
                <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                    <p className="text-red-400 font-bold">✗ Required Skills</p>
                    <p className="text-gray-400 mt-1">Skills to learn</p>
                </div>
            </div>
        </div>
    )
}

// ---------- Profile Completion Ring ----------
function CompletionRing({ percentage }) {
    const r = 50
    const circ = 2 * Math.PI * r
    const offset = circ - (Math.min(percentage, 100) / 100) * circ
    const color = percentage >= 80 ? '#10b981' : percentage >= 60 ? '#6366f1' : '#f59e0b'

    return (
        <div className="relative flex flex-col items-center justify-center">
            <svg width="120" height="120" viewBox="0 0 120 120" className="-rotate-90">
                <circle cx="60" cy="60" r={r} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="10" />
                <circle
                    cx="60" cy="60" r={r} fill="none" stroke={color} strokeWidth="10"
                    strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
                    style={{ transition: 'stroke-dashoffset 1s ease-out' }}
                />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-extrabold text-white">{percentage}%</span>
                <span className="text-xs text-gray-500 mt-1">Complete</span>
            </div>
        </div>
    )
}

// ---------- Main Statistics Page ----------
export default function StatisticsPage() {
    const { user } = useAuth()
    const toast = useToast()
    const [stats, setStats] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const { data } = await api.get('/statistics')
                setStats(data.data)
            } catch (err) {
                const msg = err.response?.data?.message || 'Failed to load statistics'
                toast({ message: msg, type: 'error' })
            } finally {
                setLoading(false)
            }
        }

        fetchStats()
    }, [])

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950">
                <Navbar />
                <div className="max-w-6xl mx-auto px-4 py-12">
                    <div className="animate-pulse space-y-4">
                        {[...Array(5)].map((_, i) => (
                            <div key={i} className="h-20 bg-white/5 rounded-xl" />
                        ))}
                    </div>
                </div>
            </div>
        )
    }

    if (!stats) {
        return (
            <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950">
                <Navbar />
                <div className="max-w-6xl mx-auto px-4 py-12">
                    <p className="text-gray-400 text-center">Could not load statistics</p>
                </div>
            </div>
        )
    }

    const matchStats = stats.match_stats || {}
    const profileComplete = stats.profile_completeness || 0
    const topMatched = matchStats.top_skills_matched || []
    const topMissing = matchStats.top_skills_missing || []

    return (
        <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950">
            <Navbar />

            <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
                {/* Header */}
                <div>
                    <h1 className="text-4xl font-bold text-white mb-2">Your Statistics</h1>
                    <p className="text-gray-400">Track your profile progress and matching performance</p>
                </div>

                {/* Profile Completeness Section */}
                <section className="space-y-4">
                    <h2 className="text-xl font-bold text-white">Profile Completeness</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-8 flex items-center justify-center">
                            <CompletionRing percentage={profileComplete} />
                        </div>

                        <div className="space-y-3">
                            <ProgressBar label="Overall Completion" value={profileComplete} color="bg-indigo-500" />

                            <div className="grid grid-cols-2 gap-3">
                                <StatCard
                                    label="Skills"
                                    value={stats.skills_count}
                                    icon="🎯"
                                    color="text-indigo-400"
                                    size="small"
                                />
                                <StatCard
                                    label="Interests"
                                    value={stats.interests_count}
                                    icon="⭐"
                                    color="text-amber-400"
                                    size="small"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-3 text-xs">
                                <div className="bg-white/5 border border-white/10 rounded-xl p-3 text-center">
                                    <p className="text-gray-400 mb-1">Experience</p>
                                    <p className="font-bold text-white">{stats.experience_level}</p>
                                </div>
                                <div className="bg-white/5 border border-white/10 rounded-xl p-3 text-center">
                                    <p className="text-gray-400 mb-1">Education</p>
                                    <p className="font-bold text-white">{stats.education}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Profile Links Section */}
                <section className="space-y-4">
                    <h2 className="text-xl font-bold text-white">Profile Links</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <StatCard
                            label="Resume"
                            value={stats.has_resume ? '✓ Added' : '✗ Missing'}
                            icon={stats.has_resume ? '📄' : '−'}
                            color={stats.has_resume ? 'bg-green-500/20 text-green-400' : 'bg-gray-600/20 text-gray-400'}
                        />
                        <StatCard
                            label="LinkedIn"
                            value={stats.has_linkedin ? '✓ Linked' : '✗ Not linked'}
                            icon={stats.has_linkedin ? '💼' : '−'}
                            color={stats.has_linkedin ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-600/20 text-gray-400'}
                        />
                        <StatCard
                            label="GitHub"
                            value={stats.has_github ? '✓ Linked' : '✗ Not linked'}
                            icon={stats.has_github ? '🐙' : '−'}
                            color={stats.has_github ? 'bg-purple-500/20 text-purple-400' : 'bg-gray-600/20 text-gray-400'}
                        />
                    </div>
                </section>

                {/* Matching Performance Section */}
                {matchStats.total_matches > 0 && (
                    <section className="space-y-4">
                        <h2 className="text-xl font-bold text-white">Matching Performance</h2>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <StatCard
                                label="Total Matches"
                                value={matchStats.total_matches}
                                icon="🎁"
                                color="bg-indigo-500/20 text-indigo-400"
                            />
                            <StatCard
                                label="Average Confidence"
                                value={`${matchStats.avg_confidence}%`}
                                icon="📊"
                                color="bg-emerald-500/20 text-emerald-400"
                            />
                            {matchStats.best_match && (
                                <div className="bg-gradient-to-br from-indigo-500/10 to-violet-500/10 border border-indigo-500/30 rounded-2xl p-4">
                                    <div className="text-xs text-gray-400 mb-1">🏆 Best Match</div>
                                    <p className="font-bold text-white text-sm leading-tight mb-1">{matchStats.best_match.title}</p>
                                    <p className="text-xs text-gray-500">{matchStats.best_match.company}</p>
                                    <p className="text-xs text-indigo-400 font-bold mt-2">{matchStats.best_match.confidence}% match</p>
                                </div>
                            )}
                        </div>
                    </section>
                )}

                {/* Skills Analysis Section */}
                {(topMatched.length > 0 || topMissing.length > 0) && (
                    <section className="space-y-4">
                        <h2 className="text-xl font-bold text-white">Skills Visualization</h2>
                        <SkillsRadarChart topMatched={topMatched} topMissing={topMissing} />
                    </section>
                )}

                {/* No Data Message */}
                {matchStats.total_matches === 0 && (
                    <section className="bg-white/5 border border-white/10 rounded-2xl p-8 text-center">
                        <div className="text-4xl mb-3">📊</div>
                        <p className="text-gray-400 mb-4">Run the matching agent to see your performance statistics</p>
                        <a href="/dashboard" className="btn-primary inline-flex items-center gap-2">
                            Go to Dashboard →
                        </a>
                    </section>
                )}
            </div>
        </div>
    )
}
