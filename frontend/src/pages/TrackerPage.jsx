import { useEffect, useState, useCallback } from 'react'
import Navbar from '../components/Navbar'
import api from '../api/axios'
import { useToast } from '../context/ToastContext'

const COLUMNS = [
    { id: 'saved',     label: 'Saved',     icon: '🔖', color: 'from-slate-500 to-slate-600' },
    { id: 'applied',   label: 'Applied',   icon: '📤', color: 'from-brand-600 to-cyan-600'  },
    { id: 'interview', label: 'Interview',  icon: '🎤', color: 'from-violet-600 to-purple-600' },
    { id: 'final',     label: 'Offer / Rejected', icon: '🏁', color: 'from-amber-500 to-orange-500' },
]

const STATUS_ORDER = ['saved', 'applied', 'interview', 'final']

function daysUntil(iso) {
    if (!iso) return null
    const diff = new Date(iso) - new Date()
    return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

function urgencyClass(days) {
    if (days === null) return 'text-gray-500'
    if (days <= 1)  return 'text-rose-400'
    if (days <= 3)  return 'text-amber-400'
    if (days <= 7)  return 'text-yellow-400'
    return 'text-emerald-400'
}

function urgencyBg(days) {
    if (days === null) return 'bg-gray-700/40'
    if (days <= 1)  return 'bg-rose-500/20 border-rose-500/40'
    if (days <= 3)  return 'bg-amber-500/20 border-amber-500/40'
    if (days <= 7)  return 'bg-yellow-500/20 border-yellow-500/40'
    return 'bg-emerald-500/20 border-emerald-500/40'
}

function ApplicationCard({ app, onMove, onOutcome, onDelete }) {
    const days = daysUntil(app.deadline)
    const idx  = STATUS_ORDER.indexOf(app.status)
    const canMoveBack    = idx > 0
    const canMoveForward = idx < STATUS_ORDER.length - 1

    return (
        <div className="glass-card p-4 space-y-3 group" id={`app-card-${app.id}`}>
            {/* Title & company */}
            <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                    <h4 className="font-semibold text-white text-sm leading-tight truncate">{app.title}</h4>
                    <p className="text-xs text-gray-400 truncate">{app.company}</p>
                </div>
                <button
                    onClick={() => onDelete(app.id)}
                    className="flex-shrink-0 opacity-0 group-hover:opacity-100 text-gray-600 hover:text-rose-400 transition-all text-xs"
                    title="Remove"
                >✕</button>
            </div>

            {/* Deadline badge */}
            {app.deadline && (
                <div className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border ${urgencyBg(days)}`}>
                    <span>📅</span>
                    <span className={urgencyClass(days)}>
                        {days === null ? '—' : days < 0 ? 'Overdue' : days === 0 ? 'Due today' : `${days}d left`}
                    </span>
                </div>
            )}

            {/* Notes snippet */}
            {app.notes && (
                <p className="text-xs text-gray-500 italic leading-relaxed line-clamp-2">{app.notes}</p>
            )}

            {/* Final column — Offer / Rejected toggles */}
            {app.status === 'final' && (
                <div className="flex gap-2 pt-1">
                    <button
                        onClick={() => onOutcome(app.id, app.outcome === 'offer' ? null : 'offer')}
                        className={`flex-1 text-xs py-1.5 rounded-lg border transition-all ${
                            app.outcome === 'offer'
                                ? 'bg-emerald-500/30 border-emerald-500/50 text-emerald-300'
                                : 'border-white/10 text-gray-500 hover:border-emerald-500/40 hover:text-emerald-400'
                        }`}
                    >✓ Offer</button>
                    <button
                        onClick={() => onOutcome(app.id, app.outcome === 'rejected' ? null : 'rejected')}
                        className={`flex-1 text-xs py-1.5 rounded-lg border transition-all ${
                            app.outcome === 'rejected'
                                ? 'bg-rose-500/30 border-rose-500/50 text-rose-300'
                                : 'border-white/10 text-gray-500 hover:border-rose-500/40 hover:text-rose-400'
                        }`}
                    >✕ Rejected</button>
                </div>
            )}

            {/* Move arrows */}
            <div className="flex items-center justify-between pt-1 border-t border-white/5">
                <button
                    disabled={!canMoveBack}
                    onClick={() => onMove(app.id, STATUS_ORDER[idx - 1])}
                    className="flex items-center gap-1 text-xs text-gray-500 hover:text-white disabled:opacity-25 disabled:cursor-not-allowed transition-colors"
                >
                    ← Back
                </button>
                {app.apply_url && (
                    <a
                        href={app.apply_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
                    >Apply ↗</a>
                )}
                <button
                    disabled={!canMoveForward}
                    onClick={() => onMove(app.id, STATUS_ORDER[idx + 1])}
                    className="flex items-center gap-1 text-xs text-gray-500 hover:text-white disabled:opacity-25 disabled:cursor-not-allowed transition-colors"
                >
                    Next →
                </button>
            </div>
        </div>
    )
}

export default function TrackerPage() {
    const toast = useToast()
    const [applications, setApplications] = useState([])
    const [loading, setLoading]   = useState(true)

    const fetchApps = useCallback(async () => {
        try {
            const { data } = await api.get('/applications')
            setApplications(data.data.applications || [])
        } catch {
            toast({ message: 'Could not load tracker', type: 'error' })
        } finally {
            setLoading(false)
        }
    }, [toast])

    useEffect(() => { fetchApps() }, [fetchApps])

    const moveCard = async (id, newStatus) => {
        // Optimistic update
        setApplications(prev =>
            prev.map(a => a.id === id ? { ...a, status: newStatus } : a)
        )
        try {
            await api.patch(`/applications/${id}`, { status: newStatus })
        } catch {
            toast({ message: 'Failed to move card, refreshing…', type: 'error' })
            fetchApps()
        }
    }

    const setOutcome = async (id, outcome) => {
        setApplications(prev =>
            prev.map(a => a.id === id ? { ...a, outcome } : a)
        )
        try {
            await api.patch(`/applications/${id}`, { outcome })
            toast({ message: outcome ? `Marked as ${outcome}!` : 'Outcome cleared', type: 'success' })
        } catch {
            toast({ message: 'Failed to update outcome', type: 'error' })
            fetchApps()
        }
    }

    const deleteCard = async (id) => {
        setApplications(prev => prev.filter(a => a.id !== id))
        try {
            await api.delete(`/applications/${id}`)
            toast({ message: 'Application removed', type: 'info' })
        } catch {
            toast({ message: 'Failed to remove', type: 'error' })
            fetchApps()
        }
    }

    const byStatus = (status) => applications.filter(a => a.status === status)

    return (
        <div className="min-h-screen flex flex-col">
            <Navbar />
            <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">

                {/* Header */}
                <div className="mb-8">
                    <p className="section-label mb-1">Application Tracker</p>
                    <h1 className="text-3xl font-bold text-white">
                        Your Kanban Board{' '}
                        <span className="text-gray-500 text-lg font-normal">
                            ({applications.length} applications)
                        </span>
                    </h1>
                    <p className="text-sm text-gray-400 mt-1">
                        Use the ← → buttons on each card to advance its stage. Add internships from the{' '}
                        <a href="/internships" className="text-brand-400 hover:underline">Internships</a> page.
                    </p>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center h-64">
                        <div className="spinner" />
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5">
                        {COLUMNS.map(col => {
                            const cards = byStatus(col.id)
                            return (
                                <div key={col.id} className="flex flex-col gap-3" id={`column-${col.id}`}>
                                    {/* Column header */}
                                    <div className={`flex items-center justify-between px-4 py-2.5 rounded-xl bg-gradient-to-r ${col.color} bg-opacity-20`}>
                                        <div className="flex items-center gap-2">
                                            <span>{col.icon}</span>
                                            <span className="text-sm font-semibold text-white">{col.label}</span>
                                        </div>
                                        <span className="text-xs bg-white/20 text-white px-2 py-0.5 rounded-full font-medium">
                                            {cards.length}
                                        </span>
                                    </div>

                                    {/* Cards */}
                                    {cards.length === 0 ? (
                                        <div className="glass-card p-6 text-center text-gray-600 text-xs border-dashed">
                                            {col.id === 'saved' ? 'Add from Internships →' : 'No cards here yet'}
                                        </div>
                                    ) : (
                                        cards.map(app => (
                                            <ApplicationCard
                                                key={app.id}
                                                app={app}
                                                onMove={moveCard}
                                                onOutcome={setOutcome}
                                                onDelete={deleteCard}
                                            />
                                        ))
                                    )}
                                </div>
                            )
                        })}
                    </div>
                )}
            </main>
        </div>
    )
}
