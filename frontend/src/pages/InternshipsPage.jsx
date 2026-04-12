import { useEffect, useMemo, useState, useCallback } from 'react'
import Navbar from '../components/Navbar'
import api from '../api/axios'
import RoadmapTimeline from '../components/RoadmapTimeline'
import { InternshipListSkeleton } from '../components/Skeleton'
import { useToast } from '../context/ToastContext'
import { useAuth } from '../context/AuthContext'

const DEFAULT_FILTERS = {
    sector: '',
    domain: '',
    location: '',
}

// ── Add-to-Tracker inline modal ───────────────────────────────────────────────
function TrackerModal({ internship, onClose, onAdded }) {
    const toast  = useToast()
    const today  = new Date().toISOString().split('T')[0]
    const [deadline, setDeadline] = useState('')
    const [notes, setNotes]       = useState('')
    const [saving, setSaving]     = useState(false)

    const handleAdd = async (e) => {
        e.preventDefault()
        setSaving(true)
        try {
            await api.post('/applications', {
                internship_id: internship._id,
                status: 'saved',
                deadline: deadline || undefined,
                notes,
            })
            toast({ message: `"${internship.title}" added to Tracker!`, type: 'success' })
            onAdded(internship._id)
            onClose()
        } catch (err) {
            const msg = err.response?.data?.message || 'Could not add to tracker'
            // Already tracked is a 200 — treat as success
            if (err.response?.status === 200) {
                toast({ message: 'Already in your Tracker', type: 'info' })
                onAdded(internship._id)
                onClose()
            } else {
                toast({ message: msg, type: 'error' })
            }
        } finally {
            setSaving(false)
        }
    }

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)' }}
            onClick={onClose}
        >
            <div
                className="glass-card w-full max-w-md p-6 space-y-5 animate-slide-up"
                onClick={e => e.stopPropagation()}
            >
                <div className="flex items-start justify-between">
                    <div>
                        <h3 className="font-bold text-white text-lg leading-tight">{internship.title}</h3>
                        <p className="text-sm text-gray-400">{internship.company}</p>
                    </div>
                    <button onClick={onClose} className="text-gray-500 hover:text-white text-xl transition-colors">✕</button>
                </div>

                <form onSubmit={handleAdd} className="space-y-4">
                    <div>
                        <label className="section-label mb-1.5 block">Application Deadline (optional)</label>
                        <input
                            type="date"
                            className="form-input"
                            value={deadline}
                            min={today}
                            onChange={e => setDeadline(e.target.value)}
                            id="tracker-deadline-input"
                        />
                    </div>
                    <div>
                        <label className="section-label mb-1.5 block">Notes (optional)</label>
                        <textarea
                            className="form-input resize-none text-sm"
                            rows={3}
                            placeholder="e.g. referral contact, interview round info…"
                            value={notes}
                            maxLength={500}
                            onChange={e => setNotes(e.target.value)}
                            id="tracker-notes-input"
                        />
                    </div>
                    <div className="flex gap-3 pt-1">
                        <button
                            type="submit"
                            disabled={saving}
                            className="btn-primary flex-1"
                            id="tracker-add-btn"
                        >
                            {saving ? 'Adding…' : '📋 Add to Tracker'}
                        </button>
                        <button type="button" onClick={onClose} className="btn-secondary !px-4">
                            Cancel
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

// ── Internship list card ─────────────────────────────────────────────────────
function InternshipListCard({ internship, savedIds, onSaveToggle, onOpenTracker }) {
    const [expanded, setExpanded]   = useState(false)
    const [toggling, setToggling]   = useState(false)
    const toast   = useToast()
    const roadmap = internship.learning_roadmap || []
    const hasAI   = Boolean(internship.reasoning)
    const isSaved = savedIds.has(internship._id)

    const handleSave = async () => {
        setToggling(true)
        try {
            const { data } = await api.post(`/internships/${internship._id}/save`)
            onSaveToggle(internship._id, data.data.saved)
            toast({
                message: data.data.saved ? '★ Bookmarked!' : '☆ Bookmark removed',
                type: data.data.saved ? 'success' : 'info',
            })
        } catch {
            toast({ message: 'Could not update bookmark', type: 'error' })
        } finally {
            setToggling(false)
        }
    }

    return (
        <article className="glass-card p-5" id={`internship-${internship._id}`}>
            <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-3">
                <div>
                    <div className="flex items-start gap-2">
                        <h3 className="text-lg font-semibold text-white flex-1">{internship.title}</h3>
                        {/* Bookmark toggle */}
                        <button
                            onClick={handleSave}
                            disabled={toggling}
                            title={isSaved ? 'Remove bookmark' : 'Bookmark this internship'}
                            className={`flex-shrink-0 text-xl transition-all duration-200 disabled:opacity-50 hover:scale-110 ${
                                isSaved ? 'text-amber-400' : 'text-gray-600 hover:text-amber-400'
                            }`}
                            id={`save-btn-${internship._id}`}
                        >
                            {toggling ? '…' : isSaved ? '★' : '☆'}
                        </button>
                    </div>
                    <p className="text-sm text-gray-300 mt-1">{internship.company}</p>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs">
                        <span className="px-2.5 py-1 rounded-full bg-white/10 border border-white/20 text-gray-200">{internship.sector || 'General'}</span>
                        <span className="px-2.5 py-1 rounded-full bg-white/10 border border-white/20 text-gray-200">{internship.domain || 'N/A'}</span>
                        <span className="px-2.5 py-1 rounded-full bg-white/10 border border-white/20 text-gray-200">{internship.location || 'N/A'}</span>
                    </div>
                </div>

                <div className="text-sm text-gray-300 lg:text-right space-y-1 flex-shrink-0">
                    <p><span className="text-gray-500">Stipend:</span> {internship.stipend || 'Not listed'}</p>
                    <p><span className="text-gray-500">Duration:</span> {internship.duration || 'Not listed'}</p>
                    <p><span className="text-gray-500">Openings:</span> {internship.openings ?? 0}</p>
                </div>
            </div>

            <p className="mt-4 text-sm text-gray-400 leading-relaxed">
                {internship.description || 'No description provided.'}
            </p>

            {internship.required_skills?.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                    {internship.required_skills.map((skill) => (
                        <span key={`${internship._id}-${skill}`} className="text-xs px-2.5 py-1 rounded-full bg-brand-500/15 border border-brand-500/30 text-brand-200">
                            {skill}
                        </span>
                    ))}
                </div>
            )}

            {hasAI && (
                <div className="mt-4 space-y-3">
                    <div className="bg-brand-500/5 border border-brand-500/20 rounded-xl p-3">
                        <p className="section-label mb-1.5">AI Reasoning</p>
                        <p className="text-sm text-gray-300 leading-relaxed">{internship.reasoning}</p>
                    </div>

                    <div className="text-xs text-gray-400 flex flex-wrap gap-3">
                        <span>Match: {Number(internship.weighted_score || 0).toFixed(1)}%</span>
                        <span>Confidence: {Number(internship.confidence_score || 0).toFixed(1)}%</span>
                        <span>{internship.fallback_used ? 'Fallback analysis' : 'LLM analysis'}</span>
                    </div>

                    {roadmap.length > 0 && (
                        <div>
                            <button
                                type="button"
                                onClick={() => setExpanded((v) => !v)}
                                className="w-full text-left"
                            >
                                <div className="flex items-center justify-between text-sm font-medium text-gray-400 hover:text-white transition-colors">
                                    <span>Learning Roadmap ({roadmap.length} weeks)</span>
                                    <svg className={`w-4 h-4 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                </div>
                            </button>
                            {expanded && (
                                <div className="pt-2">
                                    <RoadmapTimeline roadmap={roadmap} />
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Action row */}
            <div className="mt-4 flex flex-wrap items-center justify-end gap-2">
                <button
                    type="button"
                    onClick={() => onOpenTracker(internship)}
                    className="btn-secondary !py-2 !px-4 text-sm"
                    id={`tracker-btn-${internship._id}`}
                >
                    📋 Track
                </button>
                <a
                    href={`/interview-prep?id=${internship._id}`}
                    className="btn-secondary !py-2 !px-4 text-sm"
                    id={`prep-link-${internship._id}`}
                >
                    🎤 Prep
                </a>
                <a
                    href={internship.apply_url}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-primary !py-2 !px-4 text-sm"
                >
                    Apply now
                </a>
            </div>
        </article>
    )
}


// ── Main page ────────────────────────────────────────────────────────────────
export default function InternshipsPage() {
    const toast = useToast()
    const { user } = useAuth()

    const [internships, setInternships] = useState([])
    const [filters, setFilters]         = useState(DEFAULT_FILTERS)
    const [page, setPage]               = useState(1)
    const [meta, setMeta]               = useState({
        total: 0, page: 1, page_size: 10, total_pages: 1, has_prev: false, has_next: false,
    })
    const [available, setAvailable] = useState({ sectors: [], domains: [], locations: [] })
    const [loading, setLoading]     = useState(true)
    const [error, setError]         = useState('')

    // Save state — set of saved internship IDs
    const [savedIds, setSavedIds]   = useState(new Set())

    // Tracker modal
    const [trackerTarget, setTrackerTarget] = useState(null)
    const [trackedIds, setTrackedIds]       = useState(new Set())

    // Scraper state
    const [searchLocation, setSearchLocation] = useState('')
    const [scraping, setScraping]             = useState(false)
    const [scrapeResult, setScrapeResult]     = useState(null)

    const activeFilterCount = useMemo(
        () => Object.values(filters).filter(Boolean).length,
        [filters],
    )

    // Load saved IDs on mount from user context (already fetched at login)
    useEffect(() => {
        if (user?.saved_internships) {
            setSavedIds(new Set(user.saved_internships))
        }
    }, [user])

    const loadInternships = useCallback(async (selectedFilters = filters, selectedPage = page) => {
        setLoading(true)
        setError('')
        try {
            const params = {}
            if (selectedFilters.sector)   params.sector   = selectedFilters.sector
            if (selectedFilters.domain)   params.domain   = selectedFilters.domain
            if (selectedFilters.location) params.location = selectedFilters.location
            params.include_ai = true
            params.page       = selectedPage
            params.page_size  = 10

            const { data } = await api.get('/internships', { params })
            setInternships(data.data.internships || [])
            setAvailable(data.data.filters?.available || { sectors: [], domains: [], locations: [] })
            setMeta(data.data.meta || { total: 0, page: 1, page_size: 10, total_pages: 1, has_prev: false, has_next: false })
            setPage(data.data.meta?.page || selectedPage)
        } catch (err) {
            setError(err.response?.data?.message || err.response?.data?.errors || 'Could not load internships.')
        } finally {
            setLoading(false)
        }
    }, [filters, page]) // eslint-disable-line

    useEffect(() => { loadInternships(DEFAULT_FILTERS, 1) }, []) // eslint-disable-line

    const applyFilters  = () => { setPage(1); loadInternships(filters, 1) }
    const resetFilters  = () => { setFilters(DEFAULT_FILTERS); setPage(1); loadInternships(DEFAULT_FILTERS, 1) }
    const goToPage      = (nextPage) => loadInternships(filters, nextPage)

    const handleSaveToggle = (id, saved) => {
        setSavedIds(prev => {
            const next = new Set(prev)
            saved ? next.add(id) : next.delete(id)
            return next
        })
    }

    const handleTrackerAdded = (id) => {
        setTrackedIds(prev => new Set(prev).add(id))
    }

    const searchNewInternships = async () => {
        setScraping(true)
        setScrapeResult(null)
        try {
            const { data } = await api.post('/scraper/trigger', { location: searchLocation })
            setScrapeResult({ success: true, inserted: data.data.total_inserted, updated: data.data.total_updated, location: data.data.location })
            loadInternships(DEFAULT_FILTERS, 1)
        } catch (err) {
            setScrapeResult({ success: false, message: err.response?.data?.message || 'Scraping failed. Please try again.' })
        } finally {
            setScraping(false)
        }
    }

    return (
        <div className="min-h-screen flex flex-col">
            <Navbar />

            {/* Tracker modal */}
            {trackerTarget && (
                <TrackerModal
                    internship={trackerTarget}
                    onClose={() => setTrackerTarget(null)}
                    onAdded={handleTrackerAdded}
                />
            )}

            <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-6">
                {/* Search for new internships */}
                <section className="glass-card p-6">
                    <p className="section-label mb-2">Search New Internships</p>
                    <h2 className="text-xl font-bold text-white mb-1">Find internships in India (state-wise)</h2>
                    <p className="text-sm text-gray-400 mb-4">
                        Sources: Adzuna and Apify (LinkedIn + ATS actors). Enter an India city/state (for example: Bengaluru, Karnataka, Maharashtra, Delhi). Global listings are ignored.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3">
                        <input
                            type="text"
                            className="form-input flex-1"
                            placeholder="e.g. Bengaluru, Karnataka, Maharashtra, Delhi"
                            value={searchLocation}
                            onChange={(e) => setSearchLocation(e.target.value)}
                            maxLength={100}
                            disabled={scraping}
                        />
                        <button
                            type="button"
                            className="btn-primary !py-2.5 !px-6 text-sm whitespace-nowrap"
                            onClick={searchNewInternships}
                            disabled={scraping}
                        >
                            {scraping ? (
                                <span className="flex items-center gap-2">
                                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                    Searching…
                                </span>
                            ) : 'Search internships'}
                        </button>
                    </div>
                    {scrapeResult && (
                        <div className={`mt-3 text-sm px-4 py-3 rounded-xl border ${
                            scrapeResult.success
                                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                                : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                        }`}>
                            {scrapeResult.success
                                ? `Found ${scrapeResult.inserted} new and updated ${scrapeResult.updated} existing internships for "${scrapeResult.location}".`
                                : scrapeResult.message}
                        </div>
                    )}
                </section>

                {/* Filters */}
                <section className="glass-card p-6">
                    <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
                        <div>
                            <p className="section-label mb-2">Internship Explorer</p>
                            <h1 className="text-2xl font-bold text-white">Browse and filter internships</h1>
                            <p className="text-sm text-gray-400 mt-1">Filter by sector, domain, and location.</p>
                        </div>
                        <span className="text-xs text-gray-400 border border-white/10 rounded-full px-3 py-1 w-fit">
                            Active filters: {activeFilterCount}
                        </span>
                    </div>

                    <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-3">
                        <select className="form-input" value={filters.sector} onChange={(e) => setFilters((prev) => ({ ...prev, sector: e.target.value }))}>
                            <option value="">All sectors</option>
                            {available.sectors.map((item) => <option key={item} value={item}>{item}</option>)}
                        </select>
                        <select className="form-input" value={filters.domain} onChange={(e) => setFilters((prev) => ({ ...prev, domain: e.target.value }))}>
                            <option value="">All domains</option>
                            {available.domains.map((item) => <option key={item} value={item}>{item}</option>)}
                        </select>
                        <select className="form-input" value={filters.location} onChange={(e) => setFilters((prev) => ({ ...prev, location: e.target.value }))}>
                            <option value="">All locations</option>
                            {available.locations.map((item) => <option key={item} value={item}>{item}</option>)}
                        </select>
                    </div>

                    <div className="mt-4 flex gap-3">
                        <button type="button" onClick={applyFilters} className="btn-primary">Apply filters</button>
                        <button type="button" onClick={resetFilters} className="btn-secondary">Reset</button>
                    </div>
                </section>

                {loading && (
                    <section className="space-y-4">
                        {Array.from({ length: 3 }).map((_, i) => <InternshipListSkeleton key={i} />)}
                    </section>
                )}

                {!loading && error && (
                    <section className="bg-rose-500/10 border border-rose-500/30 text-rose-300 px-5 py-4 rounded-2xl">{error}</section>
                )}

                {!loading && !error && internships.length === 0 && (
                    <section className="glass-card p-12 text-center animate-fade-in">
                        <div className="text-5xl mb-4">🔍</div>
                        <h2 className="text-white text-lg font-semibold mb-2">No internships found</h2>
                        <p className="text-gray-400 text-sm mb-5">No results match your current filters.</p>
                        <button type="button" onClick={resetFilters} className="btn-secondary !py-2 !px-5 text-sm">Clear all filters</button>
                    </section>
                )}

                {!loading && !error && internships.length > 0 && (
                    <section className="space-y-4">
                        <div className="flex items-center justify-between gap-3">
                            <p className="text-sm text-gray-400">Showing {internships.length} of {meta.total} internships</p>
                            <p className="text-xs text-gray-500">Page {meta.page} of {meta.total_pages}</p>
                        </div>
                        {internships.map((internship) => (
                            <InternshipListCard
                                key={internship._id}
                                internship={internship}
                                savedIds={savedIds}
                                onSaveToggle={handleSaveToggle}
                                onOpenTracker={setTrackerTarget}
                            />
                        ))}
                        <div className="flex items-center justify-center gap-3 pt-2">
                            <button type="button" className="btn-secondary !py-2 !px-4 text-sm" disabled={!meta.has_prev || loading} onClick={() => goToPage(meta.page - 1)}>Previous</button>
                            <span className="text-sm text-gray-400 min-w-[110px] text-center">{meta.page} / {meta.total_pages}</span>
                            <button type="button" className="btn-secondary !py-2 !px-4 text-sm" disabled={!meta.has_next || loading} onClick={() => goToPage(meta.page + 1)}>Next</button>
                        </div>
                    </section>
                )}
            </main>
        </div>
    )
}
