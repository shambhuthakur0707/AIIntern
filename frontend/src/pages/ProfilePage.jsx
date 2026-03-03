import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const EDUCATION_OPTIONS = [
    'High School',
    'Associate\'s Degree',
    'Bachelor\'s Degree',
    'Master\'s Degree',
    'PhD',
    'Bootcamp / Self-taught',
    'Other',
]

const EXPERIENCE_OPTIONS = ['Beginner', 'Intermediate', 'Advanced']

export default function ProfilePage() {
    const { user, updateUser } = useAuth()
    const toast = useToast()

    const [form, setForm] = useState({
        name: '',
        email: '',
        education: '',
        experience_level: '',
        linkedin_url: '',
        github_url: '',
        portfolio_url: '',
        location: '',
        bio: '',
    })
    const [saving, setSaving] = useState(false)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        api.get('/auth/me')
            .then(({ data }) => {
                const u = data.data?.user ?? data.user ?? data
                setForm({
                    name: u.name ?? '',
                    email: u.email ?? '',
                    education: u.education ?? '',
                    experience_level: u.experience_level ?? '',
                    linkedin_url: u.linkedin_url ?? '',
                    github_url: u.github_url ?? '',
                    portfolio_url: u.portfolio_url ?? '',
                    location: u.location ?? '',
                    bio: u.bio ?? '',
                })
            })
            .catch(() => {
                toast({ message: 'Could not load your profile.', type: 'error' })
            })
            .finally(() => setLoading(false))
    }, [])

    const handleChange = (e) => {
        const { name, value } = e.target
        setForm((prev) => ({ ...prev, [name]: value }))
    }

    const handleSave = async (e) => {
        e.preventDefault()
        setSaving(true)
        try {
            const { data } = await api.put('/auth/profile', form)
            if (updateUser) updateUser({ ...(user ?? {}), ...data.user })
            toast({ message: 'Profile saved successfully!', type: 'success' })
        } catch (err) {
            const msg = err?.response?.data?.error ?? 'Failed to save profile.'
            toast({ message: msg, type: 'error' })
        } finally {
            setSaving(false)
        }
    }

    return (
        <div className="min-h-screen text-gray-900" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 40%, #f093fb 100%)' }}>
            {/* Decorative blobs */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
                <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full opacity-30" style={{ background: 'radial-gradient(circle, #a78bfa, transparent)' }} />
                <div className="absolute top-1/2 -right-40 w-80 h-80 rounded-full opacity-20" style={{ background: 'radial-gradient(circle, #818cf8, transparent)' }} />
                <div className="absolute bottom-0 left-1/3 w-72 h-72 rounded-full opacity-25" style={{ background: 'radial-gradient(circle, #f9a8d4, transparent)' }} />
            </div>
            <Navbar />
            <main className="relative max-w-2xl mx-auto px-4 py-10">
                <h1 className="text-3xl font-bold mb-1 text-white drop-shadow">Your Profile</h1>
                <p className="text-white/70 text-sm mb-8">
                    Keep your profile up-to-date for better internship matches.
                </p>

                {loading ? (
                    <div className="glass-card p-8 animate-pulse space-y-4">
                        {Array.from({ length: 5 }).map((_, i) => (
                            <div key={i} className="h-10 bg-white/5 rounded-lg" />
                        ))}
                    </div>
                ) : (
                    <form onSubmit={handleSave} className="bg-white/90 backdrop-blur-md rounded-2xl shadow-2xl p-8 space-y-5">
                        {/* Name */}
                        <label className="block">
                            <span className="text-sm text-gray-600 mb-1 block">Full Name</span>
                            <input
                                name="name"
                                value={form.name}
                                onChange={handleChange}
                                className="input w-full"
                                placeholder="Jane Doe"
                            />
                        </label>

                        {/* Email (read-only) */}
                        <label className="block">
                            <span className="text-sm text-gray-600 mb-1 block">Email</span>
                            <input
                                name="email"
                                value={form.email}
                                readOnly
                                className="input w-full opacity-60 cursor-not-allowed"
                            />
                        </label>

                        {/* Education */}
                        <label className="block">
                            <span className="text-sm text-gray-600 mb-1 block">Education Level</span>
                            <select
                                name="education"
                                value={form.education}
                                onChange={handleChange}
                                className="input w-full"
                            >
                                <option value="">Select…</option>
                                {EDUCATION_OPTIONS.map((o) => (
                                    <option key={o} value={o}>{o}</option>
                                ))}
                            </select>
                        </label>

                        {/* Experience level */}
                        <label className="block">
                            <span className="text-sm text-gray-600 mb-1 block">Experience Level</span>
                            <div className="flex gap-3 mt-1">
                                {EXPERIENCE_OPTIONS.map((o) => (
                                    <button
                                        key={o}
                                        type="button"
                                        onClick={() => setForm((prev) => ({ ...prev, experience_level: o }))}
                                        className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors ${
                                            form.experience_level === o
                                                ? 'border-brand-500 bg-brand-500/20 text-brand-600'
                                                : 'border-gray-300 bg-gray-50 text-gray-600 hover:border-gray-400'
                                        }`}
                                    >
                                        {o}
                                    </button>
                                ))}
                            </div>
                        </label>

                        {/* Location */}
                        <label className="block">
                            <span className="text-sm text-gray-600 mb-1 block">Location</span>
                            <input
                                name="location"
                                value={form.location}
                                onChange={handleChange}
                                className="input w-full"
                                placeholder="e.g. New York, USA"
                            />
                        </label>

                        {/* Bio */}
                        <label className="block">
                            <span className="text-sm text-gray-600 mb-1 block">Short Bio</span>
                            <textarea
                                name="bio"
                                value={form.bio}
                                onChange={handleChange}
                                rows={3}
                                className="input w-full resize-none"
                                placeholder="Tell us a bit about yourself…"
                            />
                        </label>

                        {/* LinkedIn */}
                        <label className="block">
                            <span className="text-sm text-gray-600 mb-1 block">LinkedIn URL</span>
                            <input
                                name="linkedin_url"
                                value={form.linkedin_url}
                                onChange={handleChange}
                                className="input w-full"
                                placeholder="https://linkedin.com/in/username"
                            />
                        </label>

                        {/* GitHub */}
                        <label className="block">
                            <span className="text-sm text-gray-600 mb-1 block">GitHub URL</span>
                            <input
                                name="github_url"
                                value={form.github_url}
                                onChange={handleChange}
                                className="input w-full"
                                placeholder="https://github.com/username"
                            />
                        </label>

                        {/* Portfolio */}
                        <label className="block">
                            <span className="text-sm text-gray-600 mb-1 block">Portfolio / Website</span>
                            <input
                                name="portfolio_url"
                                value={form.portfolio_url}
                                onChange={handleChange}
                                className="input w-full"
                                placeholder="https://yourportfolio.com"
                            />
                        </label>

                        <button
                            type="submit"
                            disabled={saving}
                            className="btn-primary w-full !mt-2"
                        >
                            {saving ? 'Saving…' : 'Save Profile'}
                        </button>
                    </form>
                )}
            </main>
        </div>
    )
}
