import { useEffect, useMemo, useState } from 'react'
import Navbar from '../components/Navbar'
import api from '../api/axios'
import RoadmapTimeline from '../components/RoadmapTimeline'
import { InternshipListSkeleton } from '../components/Skeleton'

const DEFAULT_FILTERS = {
    sector: '',
    domain: '',
    location: '',
}

function InternshipListCard({ internship }) {
    const [expanded, setExpanded] = useState(false)
    const roadmap = internship.learning_roadmap || []
    const hasAI = Boolean(internship.reasoning)

    return (
        <article className="glass-card p-5">
            <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-3">
                <div>
                    <h3 className="text-lg font-semibold text-white">{internship.title}</h3>
                    <p className="text-sm text-gray-300 mt-1">{internship.company}</p>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs">
                        <span className="px-2.5 py-1 rounded-full bg-white/10 border border-white/20 text-gray-200">{internship.sector || 'General'}</span>
                        <span className="px-2.5 py-1 rounded-full bg-white/10 border border-white/20 text-gray-200">{internship.domain || 'N/A'}</span>
                        <span className="px-2.5 py-1 rounded-full bg-white/10 border border-white/20 text-gray-200">{internship.location || 'N/A'}</span>
                    </div>
                </div>

                <div className="text-sm text-gray-300 lg:text-right space-y-1">
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

            <div className="mt-4 flex justify-end">
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

export default function InternshipsPage() {
    const [internships, setInternships] = useState([])
    const [filters, setFilters] = useState(DEFAULT_FILTERS)
    const [page, setPage] = useState(1)
    const [meta, setMeta] = useState({
        total: 0,
        page: 1,
        page_size: 10,
        total_pages: 1,
        has_prev: false,
        has_next: false,
    })
    const [available, setAvailable] = useState({
        sectors: [],
        domains: [],
        locations: [],
    })
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    // Scraper search state
    const [searchLocation, setSearchLocation] = useState('')
    const [scraping, setScraping] = useState(false)
    const [scrapeResult, setScrapeResult] = useState(null)

    const activeFilterCount = useMemo(
        () => Object.values(filters).filter(Boolean).length,
        [filters],
    )

    const loadInternships = async (selectedFilters = filters, selectedPage = page) => {
        setLoading(true)
        setError('')
        try {
            const params = {}
            if (selectedFilters.sector) params.sector = selectedFilters.sector
            if (selectedFilters.domain) params.domain = selectedFilters.domain
            if (selectedFilters.location) params.location = selectedFilters.location
            params.include_ai = true
            params.page = selectedPage
            params.page_size = 10

            const { data } = await api.get('/internships', { params })
            setInternships(data.data.internships || [])
            setAvailable(data.data.filters?.available || { sectors: [], domains: [], locations: [] })
            setMeta(data.data.meta || {
                total: 0,
                page: 1,
                page_size: 10,
                total_pages: 1,
                has_prev: false,
                has_next: false,
            })
            setPage(data.data.meta?.page || selectedPage)
        } catch (err) {
            setError(err.response?.data?.message || err.response?.data?.errors || 'Could not load internships.')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        loadInternships(DEFAULT_FILTERS, 1)
    }, []) // eslint-disable-line

    const applyFilters = () => {
        setPage(1)
        loadInternships(filters, 1)
    }

    const resetFilters = () => {
        setFilters(DEFAULT_FILTERS)
        setPage(1)
        loadInternships(DEFAULT_FILTERS, 1)
    }

    const goToPage = (nextPage) => {
        loadInternships(filters, nextPage)
    }

    const searchNewInternships = async () => {
        setScraping(true)
        setScrapeResult(null)
        try {
            const { data } = await api.post('/scraper/trigger', { location: searchLocation })
            setScrapeResult({
                success: true,
                inserted: data.data.total_inserted,
                updated: data.data.total_updated,
                location: data.data.location,
            })
            // Reload the list to show newly scraped internships
            loadInternships(DEFAULT_FILTERS, 1)
        } catch (err) {
            setScrapeResult({
                success: false,
                message: err.response?.data?.message || 'Scraping failed. Please try again.',
            })
        } finally {
            setScraping(false)
        }
    }

    return (
        <div className="min-h-screen flex flex-col">
            <Navbar />

            <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-6">
                {/* Search for new internships */}
                <section className="glass-card p-6">
                    <p className="section-label mb-2">Search New Internships</p>
                    <h2 className="text-xl font-bold text-white mb-1">Find internships in a specific location</h2>
                    <p className="text-sm text-gray-400 mb-4">
                        Enter a city, state, or country to search for new internships. This fetches fresh listings from external sources.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3">
                        <input
                            type="text"
                            className="form-input flex-1"
                            placeholder="e.g. New York, India, London, Remote…"
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
                        <select
                            className="form-input"
                            value={filters.sector}
                            onChange={(e) => setFilters((prev) => ({ ...prev, sector: e.target.value }))}
                        >
                            <option value="">All sectors</option>
                            {available.sectors.map((item) => (
                                <option key={item} value={item}>{item}</option>
                            ))}
                        </select>

                        <select
                            className="form-input"
                            value={filters.domain}
                            onChange={(e) => setFilters((prev) => ({ ...prev, domain: e.target.value }))}
                        >
                            <option value="">All domains</option>
                            {available.domains.map((item) => (
                                <option key={item} value={item}>{item}</option>
                            ))}
                        </select>

                        <select
                            className="form-input"
                            value={filters.location}
                            onChange={(e) => setFilters((prev) => ({ ...prev, location: e.target.value }))}
                        >
                            <option value="">All locations</option>
                            {available.locations.map((item) => (
                                <option key={item} value={item}>{item}</option>
                            ))}
                        </select>
                    </div>

                    <div className="mt-4 flex gap-3">
                        <button type="button" onClick={applyFilters} className="btn-primary">Apply filters</button>
                        <button type="button" onClick={resetFilters} className="btn-secondary">Reset</button>
                    </div>
                </section>

                {loading && (
                    <section className="space-y-4">
                        {Array.from({ length: 3 }).map((_, i) => (
                            <InternshipListSkeleton key={i} />
                        ))}
                    </section>
                )}

                {!loading && error && (
                    <section className="bg-rose-500/10 border border-rose-500/30 text-rose-300 px-5 py-4 rounded-2xl">
                        {error}
                    </section>
                )}

                {!loading && !error && internships.length === 0 && (
                    <section className="glass-card p-12 text-center animate-fade-in">
                        <div className="text-5xl mb-4">🔍</div>
                        <h2 className="text-white text-lg font-semibold mb-2">No internships found</h2>
                        <p className="text-gray-400 text-sm mb-5">No results match your current filters.</p>
                        <button
                            type="button"
                            onClick={resetFilters}
                            className="btn-secondary !py-2 !px-5 text-sm"
                        >
                            Clear all filters
                        </button>
                    </section>
                )}

                {!loading && !error && internships.length > 0 && (
                    <section className="space-y-4">
                        <div className="flex items-center justify-between gap-3">
                            <p className="text-sm text-gray-400">
                                Showing {internships.length} of {meta.total} internships
                            </p>
                            <p className="text-xs text-gray-500">
                                Page {meta.page} of {meta.total_pages}
                            </p>
                        </div>
                        {internships.map((internship) => (
                            <InternshipListCard key={internship._id} internship={internship} />
                        ))}
                        <div className="flex items-center justify-center gap-3 pt-2">
                            <button
                                type="button"
                                className="btn-secondary !py-2 !px-4 text-sm"
                                disabled={!meta.has_prev || loading}
                                onClick={() => goToPage(meta.page - 1)}
                            >
                                Previous
                            </button>
                            <span className="text-sm text-gray-400 min-w-[110px] text-center">
                                {meta.page} / {meta.total_pages}
                            </span>
                            <button
                                type="button"
                                className="btn-secondary !py-2 !px-4 text-sm"
                                disabled={!meta.has_next || loading}
                                onClick={() => goToPage(meta.page + 1)}
                            >
                                Next
                            </button>
                        </div>
                    </section>
                )}
            </main>
        </div>
    )
}
