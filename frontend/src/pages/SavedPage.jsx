import { useEffect, useState, useCallback } from 'react'
import Navbar from '../components/Navbar'
import api from '../api/axios'
import { useToast } from '../context/ToastContext'

function SavedCard({ internship, onUnsave, onPrep }) {
    const [toggling, setToggling] = useState(false)

    const handleUnsave = async () => {
        setToggling(true)
        try {
            await api.post(`/internships/${internship.id}/save`)
            onUnsave(internship.id)
        } catch {
            // parent will refresh
        } finally {
            setToggling(false)
        }
    }

    return (
        <article className="glass-card-hover p-5 space-y-3" id={`saved-card-${internship.id}`}>
            <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                    <h3 className="font-bold text-white text-base leading-tight truncate">{internship.title}</h3>
                    <p className="text-sm text-gray-400 mt-0.5">{internship.company}</p>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                        {[internship.domain, internship.location].filter(Boolean).map(tag => (
                            <span key={tag} className="text-xs px-2 py-0.5 rounded-full bg-white/10 border border-white/15 text-gray-300">
                                {tag}
                            </span>
                        ))}
                    </div>
                </div>

                {/* Star / unsave button */}
                <button
                    onClick={handleUnsave}
                    disabled={toggling}
                    title="Remove bookmark"
                    className="flex-shrink-0 text-2xl text-amber-400 hover:text-gray-500 transition-colors disabled:opacity-50"
                    id={`unsave-btn-${internship.id}`}
                >
                    {toggling ? '…' : '★'}
                </button>
            </div>

            {internship.description && (
                <p className="text-sm text-gray-400 leading-relaxed line-clamp-2">{internship.description}</p>
            )}

            {internship.required_skills?.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                    {internship.required_skills.slice(0, 6).map(s => (
                        <span key={s} className="text-xs px-2.5 py-1 rounded-full bg-brand-500/15 border border-brand-500/30 text-brand-200">
                            {s}
                        </span>
                    ))}
                </div>
            )}

            <div className="flex justify-between items-center pt-1 border-t border-white/5">
                <div className="text-xs text-gray-500 space-x-3">
                    {internship.stipend && <span>{internship.stipend}</span>}
                    {internship.duration && <span>{internship.duration}</span>}
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => onPrep(internship.id)}
                        className="btn-secondary !py-1.5 !px-3 text-xs"
                        id={`prep-btn-${internship.id}`}
                    >
                        🎤 Prep
                    </button>
                    {internship.apply_url && (
                        <a
                            href={internship.apply_url}
                            target="_blank"
                            rel="noreferrer"
                            className="btn-primary !py-1.5 !px-3 text-xs"
                        >
                            Apply ↗
                        </a>
                    )}
                </div>
            </div>
        </article>
    )
}

export default function SavedPage() {
    const toast  = useToast()
    const [internships, setInternships] = useState([])
    const [loading, setLoading]         = useState(true)

    const fetchSaved = useCallback(async () => {
        setLoading(true)
        try {
            const { data } = await api.get('/internships/saved')
            setInternships(data.data.internships || [])
        } catch {
            toast({ message: 'Could not load saved internships', type: 'error' })
        } finally {
            setLoading(false)
        }
    }, [toast])

    useEffect(() => { fetchSaved() }, [fetchSaved])

    const handleUnsave = (id) => {
        setInternships(prev => prev.filter(i => i.id !== id))
        toast({ message: 'Bookmark removed', type: 'info' })
    }

    const handlePrep = (id) => {
        window.location.href = `/interview-prep?id=${id}`
    }

    return (
        <div className="min-h-screen flex flex-col">
            <Navbar />
            <main className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-6">

                <div>
                    <p className="section-label mb-1">Saved Internships</p>
                    <h1 className="text-3xl font-bold text-white">Your Bookmarks</h1>
                    <p className="text-sm text-gray-400 mt-1">
                        Click ★ to remove a bookmark. Use{' '}
                        <a href="/internships" className="text-brand-400 hover:underline">Internships</a>{' '}
                        to discover and save more.
                    </p>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center h-64">
                        <div className="spinner" />
                    </div>
                ) : internships.length === 0 ? (
                    <div className="glass-card p-16 text-center animate-fade-in">
                        <div className="text-6xl mb-4">☆</div>
                        <h2 className="text-white text-lg font-semibold mb-2">No saved internships yet</h2>
                        <p className="text-gray-400 text-sm mb-6">
                            Browse the internships list and click ☆ to bookmark ones you like.
                        </p>
                        <a href="/internships" className="btn-primary">Browse Internships</a>
                    </div>
                ) : (
                    <div className="space-y-4">
                        <p className="text-sm text-gray-400">{internships.length} saved internship{internships.length !== 1 ? 's' : ''}</p>
                        {internships.map(i => (
                            <SavedCard
                                key={i.id}
                                internship={i}
                                onUnsave={handleUnsave}
                                onPrep={handlePrep}
                            />
                        ))}
                    </div>
                )}
            </main>
        </div>
    )
}
