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

    // Phone
    const [phone, setPhone] = useState('')
    const [savingPhone, setSavingPhone] = useState(false)

    // Change password
    const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm_password: '' })
    const [savingPw, setSavingPw] = useState(false)

    // Change email
    const [newEmail, setNewEmail] = useState('')
    const [savingEmail, setSavingEmail] = useState(false)

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
                setPhone(u.phone ?? '')
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

    const handleSavePhone = async (e) => {
        e.preventDefault()
        setSavingPhone(true)
        try {
            await api.patch('/auth/phone', { phone })
            toast({ message: 'Phone number updated!', type: 'success' })
        } catch (err) {
            const msg = err?.response?.data?.message ?? err?.response?.data?.error ?? 'Failed to update phone.'
            toast({ message: msg, type: 'error' })
        } finally {
            setSavingPhone(false)
        }
    }

    const handleChangePassword = async (e) => {
        e.preventDefault()
        if (pwForm.new_password !== pwForm.confirm_password) {
            toast({ message: 'New passwords do not match.', type: 'error' })
            return
        }
        setSavingPw(true)
        try {
            await api.put('/auth/change-password', {
                current_password: pwForm.current_password,
                new_password: pwForm.new_password,
            })
            toast({ message: 'Password changed successfully!', type: 'success' })
            setPwForm({ current_password: '', new_password: '', confirm_password: '' })
        } catch (err) {
            const msg = err?.response?.data?.message ?? err?.response?.data?.error ?? 'Failed to change password.'
            toast({ message: msg, type: 'error' })
        } finally {
            setSavingPw(false)
        }
    }

    const handleChangeEmail = async (e) => {
        e.preventDefault()
        setSavingEmail(true)
        try {
            const { data } = await api.post('/auth/change-email', { new_email: newEmail })
            if (updateUser) updateUser({ ...(user ?? {}), ...data.data?.user })
            setForm((prev) => ({ ...prev, email: newEmail }))
            toast({ message: 'Email updated successfully!', type: 'success' })
            setNewEmail('')
        } catch (err) {
            const msg = err?.response?.data?.message ?? err?.response?.data?.error ?? 'Failed to update email.'
            toast({ message: msg, type: 'error' })
        } finally {
            setSavingEmail(false)
        }
    }

    const inputCls = 'w-full px-4 py-2.5 rounded-lg border border-gray-300 bg-white text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 transition'

    return (
        <div className="min-h-screen text-gray-900" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 40%, #f093fb 100%)' }}>
            {/* Decorative blobs */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
                <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full opacity-30" style={{ background: 'radial-gradient(circle, #a78bfa, transparent)' }} />
                <div className="absolute top-1/2 -right-40 w-80 h-80 rounded-full opacity-20" style={{ background: 'radial-gradient(circle, #818cf8, transparent)' }} />
                <div className="absolute bottom-0 left-1/3 w-72 h-72 rounded-full opacity-25" style={{ background: 'radial-gradient(circle, #f9a8d4, transparent)' }} />
            </div>
            <Navbar />
            <main className="relative max-w-2xl mx-auto px-4 py-10 space-y-8">
                <div>
                    <h1 className="text-3xl font-bold mb-1 text-white drop-shadow">Your Profile</h1>
                    <p className="text-white/70 text-sm">Keep your profile up-to-date for better internship matches.</p>
                </div>

                {loading ? (
                    <div className="bg-white/90 rounded-2xl p-8 animate-pulse space-y-4">
                        {Array.from({ length: 5 }).map((_, i) => (
                            <div key={i} className="h-10 bg-gray-100 rounded-lg" />
                        ))}
                    </div>
                ) : (
                    <>
                        {/* ── Profile Info ── */}
                        <form onSubmit={handleSave} className="bg-white/90 backdrop-blur-md rounded-2xl shadow-2xl p-8 space-y-5">
                            <h2 className="text-lg font-semibold text-gray-800 border-b pb-2">Profile Info</h2>

                            <label className="block">
                                <span className="text-sm text-gray-600 mb-1 block">Full Name</span>
                                <input name="name" value={form.name} onChange={handleChange} className={inputCls} placeholder="Jane Doe" />
                            </label>

                            <label className="block">
                                <span className="text-sm text-gray-600 mb-1 block">Email <span className="text-xs text-gray-400">(change below)</span></span>
                                <input name="email" value={form.email} readOnly className={`${inputCls} opacity-60 cursor-not-allowed bg-gray-50`} />
                            </label>

                            <label className="block">
                                <span className="text-sm text-gray-600 mb-1 block">Education Level</span>
                                <select name="education" value={form.education} onChange={handleChange} className={inputCls}>
                                    <option value="">Select…</option>
                                    {EDUCATION_OPTIONS.map((o) => <option key={o} value={o}>{o}</option>)}
                                </select>
                            </label>

                            <label className="block">
                                <span className="text-sm text-gray-600 mb-1 block">Experience Level</span>
                                <div className="flex gap-3 mt-1">
                                    {EXPERIENCE_OPTIONS.map((o) => (
                                        <button key={o} type="button"
                                            onClick={() => setForm((prev) => ({ ...prev, experience_level: o }))}
                                            className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors ${form.experience_level === o ? 'border-indigo-500 bg-indigo-50 text-indigo-700' : 'border-gray-300 bg-gray-50 text-gray-600 hover:border-gray-400'}`}>
                                            {o}
                                        </button>
                                    ))}
                                </div>
                            </label>

                            <label className="block">
                                <span className="text-sm text-gray-600 mb-1 block">Location</span>
                                <input name="location" value={form.location} onChange={handleChange} className={inputCls} placeholder="e.g. New York, USA" />
                            </label>

                            <label className="block">
                                <span className="text-sm text-gray-600 mb-1 block">Short Bio</span>
                                <textarea name="bio" value={form.bio} onChange={handleChange} rows={3} className={`${inputCls} resize-none`} placeholder="Tell us a bit about yourself…" />
                            </label>

                            <label className="block">
                                <span className="text-sm text-gray-600 mb-1 block">LinkedIn URL</span>
                                <input name="linkedin_url" value={form.linkedin_url} onChange={handleChange} className={inputCls} placeholder="https://linkedin.com/in/username" />
                            </label>

                            <label className="block">
                                <span className="text-sm text-gray-600 mb-1 block">GitHub URL</span>
                                <input name="github_url" value={form.github_url} onChange={handleChange} className={inputCls} placeholder="https://github.com/username" />
                            </label>

                            <label className="block">
                                <span className="text-sm text-gray-600 mb-1 block">Portfolio / Website</span>
                                <input name="portfolio_url" value={form.portfolio_url} onChange={handleChange} className={inputCls} placeholder="https://yourportfolio.com" />
                            </label>

                            <button type="submit" disabled={saving} className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition disabled:opacity-60">
                                {saving ? 'Saving…' : 'Save Profile'}
                            </button>
                        </form>

                        {/* ── Account Settings ── */}
                        <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-2xl p-8 space-y-8">
                            <h2 className="text-lg font-semibold text-gray-800 border-b pb-2">Account Settings</h2>

                            {/* Phone number */}
                            <form onSubmit={handleSavePhone} className="space-y-3">
                                <h3 className="text-sm font-semibold text-gray-700">Phone Number</h3>
                                <p className="text-xs text-gray-500">International format e.g. +919876543210</p>
                                <div className="flex gap-2">
                                    <input
                                        type="tel"
                                        value={phone}
                                        onChange={(e) => setPhone(e.target.value)}
                                        className={`${inputCls} flex-1`}
                                        placeholder="+919876543210"
                                    />
                                    <button type="submit" disabled={savingPhone || !phone.trim()} className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold transition disabled:opacity-60 whitespace-nowrap">
                                        {savingPhone ? 'Saving…' : 'Save'}
                                    </button>
                                </div>
                            </form>

                            <hr className="border-gray-200" />

                            {/* Change email */}
                            <div className="space-y-3">
                                <h3 className="text-sm font-semibold text-gray-700">Change Email</h3>
                                <form onSubmit={handleChangeEmail} className="flex gap-2">
                                    <input
                                        type="email"
                                        value={newEmail}
                                        onChange={(e) => setNewEmail(e.target.value)}
                                        className={`${inputCls} flex-1`}
                                        placeholder="new@email.com"
                                    />
                                    <button type="submit" disabled={savingEmail || !newEmail.trim()} className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold transition disabled:opacity-60 whitespace-nowrap">
                                        {savingEmail ? 'Updating…' : 'Update'}
                                    </button>
                                </form>
                            </div>

                            <hr className="border-gray-200" />

                            {/* Change password */}
                            <form onSubmit={handleChangePassword} className="space-y-3">
                                <h3 className="text-sm font-semibold text-gray-700">Change Password</h3>
                                <p className="text-xs text-gray-500">Min 8 characters with uppercase, lowercase, and a number.</p>
                                <label className="block">
                                    <span className="text-xs text-gray-500 mb-1 block">Current Password</span>
                                    <input
                                        type="password"
                                        value={pwForm.current_password}
                                        onChange={(e) => setPwForm((p) => ({ ...p, current_password: e.target.value }))}
                                        className={inputCls}
                                        placeholder="••••••••"
                                    />
                                </label>
                                <label className="block">
                                    <span className="text-xs text-gray-500 mb-1 block">New Password</span>
                                    <input
                                        type="password"
                                        value={pwForm.new_password}
                                        onChange={(e) => setPwForm((p) => ({ ...p, new_password: e.target.value }))}
                                        className={inputCls}
                                        placeholder="••••••••"
                                    />
                                </label>
                                <label className="block">
                                    <span className="text-xs text-gray-500 mb-1 block">Confirm New Password</span>
                                    <input
                                        type="password"
                                        value={pwForm.confirm_password}
                                        onChange={(e) => setPwForm((p) => ({ ...p, confirm_password: e.target.value }))}
                                        className={inputCls}
                                        placeholder="••••••••"
                                    />
                                </label>
                                <button
                                    type="submit"
                                    disabled={savingPw || !pwForm.current_password || !pwForm.new_password || !pwForm.confirm_password}
                                    className="w-full py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold text-sm transition disabled:opacity-60"
                                >
                                    {savingPw ? 'Changing…' : 'Change Password'}
                                </button>
                            </form>
                        </div>
                    </>
                )}
            </main>
        </div>
    )
}
