import { useEffect, useState, useCallback } from 'react'
import Navbar from '../components/Navbar'
import api from '../api/axios'
import { useToast } from '../context/ToastContext'

function daysUntil(iso) {
    if (!iso) return null
    const diff = new Date(iso) - new Date()
    return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

function DeadlineBar({ days, deadline }) {
    // 0–30 day window; bar fills left to right as deadline approaches
    const MAX_DAYS = 30
    const clamped  = Math.max(0, Math.min(days ?? MAX_DAYS, MAX_DAYS))
    // Progress = (MAX_DAYS - remaining) / MAX_DAYS → 100% when 0 days left
    const pct = Math.round(((MAX_DAYS - clamped) / MAX_DAYS) * 100)

    const barColor =
        (days ?? MAX_DAYS) <= 1  ? 'bg-rose-500'   :
        (days ?? MAX_DAYS) <= 3  ? 'bg-amber-500'  :
        (days ?? MAX_DAYS) <= 7  ? 'bg-yellow-400' :
        'bg-emerald-500'

    const textColor =
        (days ?? MAX_DAYS) <= 1  ? 'text-rose-400'   :
        (days ?? MAX_DAYS) <= 3  ? 'text-amber-400'  :
        (days ?? MAX_DAYS) <= 7  ? 'text-yellow-400' :
        'text-emerald-400'

    return (
        <div className="space-y-1.5 w-full">
            <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                <div
                    className={`h-full rounded-full transition-all duration-700 ${barColor}`}
                    style={{ width: `${pct}%` }}
                />
            </div>
            <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">
                    {deadline ? new Date(deadline).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'}
                </span>
                <span className={`font-semibold ${textColor}`}>
                    {days === null ? 'No deadline' :
                     days < 0     ? 'Overdue' :
                     days === 0   ? 'Due today!' :
                     `${days} day${days !== 1 ? 's' : ''} left`}
                </span>
            </div>
        </div>
    )
}

const STATUS_COLOR = {
    saved:     'bg-slate-500/20 text-slate-300 border-slate-500/30',
    applied:   'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
    interview: 'bg-violet-500/20 text-violet-300 border-violet-500/30',
    final:     'bg-amber-500/20 text-amber-300 border-amber-500/30',
}

const STATUS_LABEL = { saved: 'Saved', applied: 'Applied', interview: 'Interview', final: 'Final' }

export default function DeadlinesPage() {
    const toast  = useToast()
    const [apps, setApps]       = useState([])
    const [loading, setLoading] = useState(true)
    const [sortAsc, setSortAsc] = useState(true)
    const [alertedFired, setAlertedFired] = useState(false)

    const fetchApps = useCallback(async () => {
        setLoading(true)
        try {
            const { data } = await api.get('/applications')
            setApps(data.data.applications || [])
        } catch {
            toast({ message: 'Could not load deadlines', type: 'error' })
        } finally {
            setLoading(false)
        }
    }, [toast])

    useEffect(() => { fetchApps() }, [fetchApps])

    // Fire urgent alerts once after first load
    useEffect(() => {
        if (alertedFired || apps.length === 0) return
        const urgent = apps.filter(a => {
            const d = daysUntil(a.deadline)
            return d !== null && d <= 3
        })
        if (urgent.length > 0) {
            urgent.forEach(a => {
                const days = daysUntil(a.deadline)
                toast({
                    message: `⚡ "${a.title}" deadline in ${days <= 0 ? 'under a day' : `${days} day${days !== 1 ? 's' : ''}`}!`,
                    type: 'warning',
                    duration: 6000,
                })
            })
        }
        setAlertedFired(true)
    }, [apps, alertedFired, toast])

    // Only show apps that have a deadline
    const withDeadline = apps.filter(a => a.deadline)
    withDeadline.sort((a, b) => {
        const da = daysUntil(a.deadline) ?? 9999
        const db_ = daysUntil(b.deadline) ?? 9999
        return sortAsc ? da - db_ : db_ - da
    })

    return (
        <div className="min-h-screen flex flex-col">
            <Navbar />
            <main className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-6">

                <div className="flex items-end justify-between gap-4 flex-wrap">
                    <div>
                        <p className="section-label mb-1">Deadlines</p>
                        <h1 className="text-3xl font-bold text-white">Upcoming Deadlines</h1>
                        <p className="text-sm text-gray-400 mt-1">
                            {withDeadline.length} application{withDeadline.length !== 1 ? 's' : ''} with deadlines
                        </p>
                    </div>
                    <button
                        className="btn-secondary !py-2 !px-4 text-sm flex items-center gap-2"
                        onClick={() => setSortAsc(v => !v)}
                        id="sort-toggle-btn"
                    >
                        <span>{sortAsc ? '↑' : '↓'}</span>
                        {sortAsc ? 'Soonest first' : 'Latest first'}
                    </button>
                </div>

                {/* Urgent alert banner */}
                {withDeadline.filter(a => (daysUntil(a.deadline) ?? 99) <= 3).length > 0 && (
                    <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl px-5 py-4 text-amber-300 text-sm flex items-start gap-3">
                        <span className="text-xl flex-shrink-0">⚡</span>
                        <div>
                            <p className="font-semibold">Urgent deadlines!</p>
                            <p className="text-amber-400/80 mt-0.5">
                                You have {withDeadline.filter(a => (daysUntil(a.deadline) ?? 99) <= 3).length} application{withDeadline.filter(a => (daysUntil(a.deadline) ?? 99) <= 3).length !== 1 ? 's' : ''} due within 3 days. Don't miss them!
                            </p>
                        </div>
                    </div>
                )}

                {loading ? (
                    <div className="flex items-center justify-center h-64">
                        <div className="spinner" />
                    </div>
                ) : withDeadline.length === 0 ? (
                    <div className="glass-card p-16 text-center animate-fade-in">
                        <div className="text-5xl mb-4">📅</div>
                        <h2 className="text-white text-lg font-semibold mb-2">No deadlines set</h2>
                        <p className="text-gray-400 text-sm mb-5">
                            Add deadline dates when adding internships to your tracker.
                        </p>
                        <a href="/tracker" className="btn-primary">Open Tracker</a>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {withDeadline.map(app => {
                            const days = daysUntil(app.deadline)
                            return (
                                <article
                                    key={app.id}
                                    className="glass-card p-5 space-y-3"
                                    id={`deadline-card-${app.id}`}
                                >
                                    <div className="flex items-start justify-between gap-4 flex-wrap">
                                        <div className="min-w-0">
                                            <h3 className="font-semibold text-white">{app.title}</h3>
                                            <p className="text-sm text-gray-400">{app.company}</p>
                                        </div>
                                        <span className={`text-xs px-3 py-1 rounded-full border flex-shrink-0 ${STATUS_COLOR[app.status] || STATUS_COLOR.saved}`}>
                                            {STATUS_LABEL[app.status] || app.status}
                                        </span>
                                    </div>

                                    <DeadlineBar days={days} deadline={app.deadline} />

                                    {app.notes && (
                                        <p className="text-xs text-gray-500 italic">{app.notes}</p>
                                    )}
                                </article>
                            )
                        })}
                    </div>
                )}
            </main>
        </div>
    )
}
