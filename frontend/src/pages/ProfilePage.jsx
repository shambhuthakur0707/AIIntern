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

    const inputCls = 'form-input'

    return (
        <div className="min-h-screen flex flex-col">
            <Navbar />
            <main className="flex-1 max-w-2xl mx-auto w-full px-4 sm:px-6 py-10 space-y-6">

                {/* Page header */}
                <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500 to-violet-600 flex items-center justify-center text-2xl font-black text-white shrink-0">
                        {(form.name || user?.name || '?')[0]?.toUpperCase()}
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white leading-tight">Your Profile</h1>
                        <p className="text-sm text-gray-400 mt-0.5">Keep your profile up-to-date for better internship matches.</p>
                    </div>
                </div>

                {loading ? (
                    <div className="glass-card p-8 animate-pulse space-y-4">
                        {Array.from({ length: 5 }).map((_, i) => (
                            <div key={i} className="h-10 bg-white/5 rounded-xl" />
                        ))}
                    </div>
                ) : (
                    <>
                        {/* ── Profile Info ── */}
                        <form onSubmit={handleSave} className="glass-card p-6 space-y-5">
                            <h2 className="text-base font-semibold text-white border-b border-white/10 pb-3">Profile Info</h2>

                            <label className="block">
                                <span className="text-sm font-medium text-gray-300 mb-1.5 block">Full Name</span>
                                <input name="name" value={form.name} onChange={handleChange} className={inputCls} placeholder="Jane Doe" />
                            </label>

                            <label className="block">
                                <span className="text-sm font-medium text-gray-300 mb-1.5 block">
                                    Email <span className="text-xs text-gray-500">(change below)</span>
                                </span>
                                <input name="email" value={form.email} readOnly className={`${inputCls} opacity-50 cursor-not-allowed`} />
                            </label>

                            <label className="block">
                                <span className="text-sm font-medium text-gray-300 mb-1.5 block">Education Level</span>
                                <select name="education" value={form.education} onChange={handleChange} className={inputCls}>
                                    <option value="">Select…</option>
                                    {EDUCATION_OPTIONS.map((o) => <option key={o} value={o}>{o}</option>)}
                                </select>
                            </label>

                            <label className="block">
                                <span className="text-sm font-medium text-gray-300 mb-1.5 block">Experience Level</span>
                                <div className="flex gap-2 mt-1">
                                    {EXPERIENCE_OPTIONS.map((o) => (
                                        <button key={o} type="button"
                                            onClick={() => setForm((prev) => ({ ...prev, experience_level: o }))}
                                            className={`flex-1 py-2 rounded-xl border text-sm font-medium transition-all duration-200 ${
                                                form.experience_level === o
                                                    ? 'border-brand-500/70 bg-brand-500/15 text-brand-300'
                                                    : 'border-white/10 bg-white/5 text-gray-400 hover:border-white/20 hover:text-gray-200'
                                            }`}>
                                            {o}
                                        </button>
                                    ))}
                                </div>
                            </label>

                            <label className="block">
                                <span className="text-sm font-medium text-gray-300 mb-1.5 block">Location</span>
                                <input name="location" value={form.location} onChange={handleChange} className={inputCls} placeholder="e.g. New York, USA" />
                            </label>

                            <label className="block">
                                <span className="text-sm font-medium text-gray-300 mb-1.5 block">Short Bio</span>
                                <textarea name="bio" value={form.bio} onChange={handleChange} rows={3} className={`${inputCls} resize-none`} placeholder="Tell us a bit about yourself…" />
                            </label>

                            <label className="block">
                                <span className="text-sm font-medium text-gray-300 mb-1.5 block">LinkedIn URL</span>
                                <input name="linkedin_url" value={form.linkedin_url} onChange={handleChange} className={inputCls} placeholder="https://linkedin.com/in/username" />
                            </label>

                            <label className="block">
                                <span className="text-sm font-medium text-gray-300 mb-1.5 block">GitHub URL</span>
                                <input name="github_url" value={form.github_url} onChange={handleChange} className={inputCls} placeholder="https://github.com/username" />
                            </label>

                            <label className="block">
                                <span className="text-sm font-medium text-gray-300 mb-1.5 block">Portfolio / Website</span>
                                <input name="portfolio_url" value={form.portfolio_url} onChange={handleChange} className={inputCls} placeholder="https://yourportfolio.com" />
                            </label>

                            <button type="submit" disabled={saving} className="btn-primary w-full flex items-center justify-center gap-2">
                                {saving ? <><div className="spinner" />Saving…</> : 'Save Profile'}
                            </button>
                        </form>

                        {/* ── Account Settings ── */}
                        <div className="glass-card p-6 space-y-6">
                            <h2 className="text-base font-semibold text-white border-b border-white/10 pb-3">Account Settings</h2>

                            {/* Phone number */}
                            <form onSubmit={handleSavePhone} className="space-y-3">
                                <div>
                                    <h3 className="text-sm font-semibold text-gray-200">Phone Number</h3>
                                    <p className="text-xs text-gray-500 mt-0.5">International format e.g. +919876543210</p>
                                </div>
                                <div className="flex gap-2">
                                    <input
                                        type="tel"
                                        value={phone}
                                        onChange={(e) => setPhone(e.target.value)}
                                        className={`${inputCls} flex-1`}
                                        placeholder="+919876543210"
                                    />
                                    <button type="submit" disabled={savingPhone || !phone.trim()} className="btn-primary !py-2.5 !px-5 whitespace-nowrap">
                                        {savingPhone ? 'Saving…' : 'Save'}
                                    </button>
                                </div>
                            </form>

                            <div className="h-px bg-white/10" />

                            {/* Change email */}
                            <div className="space-y-3">
                                <div>
                                    <h3 className="text-sm font-semibold text-gray-200">Change Email</h3>
                                </div>
                                <form onSubmit={handleChangeEmail} className="flex gap-2">
                                    <input
                                        type="email"
                                        value={newEmail}
                                        onChange={(e) => setNewEmail(e.target.value)}
                                        className={`${inputCls} flex-1`}
                                        placeholder="new@email.com"
                                    />
                                    <button type="submit" disabled={savingEmail || !newEmail.trim()} className="btn-primary !py-2.5 !px-5 whitespace-nowrap">
                                        {savingEmail ? 'Updating…' : 'Update'}
                                    </button>
                                </form>
                            </div>

                            <div className="h-px bg-white/10" />

                            {/* Change password */}
                            <form onSubmit={handleChangePassword} className="space-y-3">
                                <div>
                                    <h3 className="text-sm font-semibold text-gray-200">Change Password</h3>
                                    <p className="text-xs text-gray-500 mt-0.5">Min 8 characters with uppercase, lowercase, and a number.</p>
                                </div>
                                <label className="block">
                                    <span className="text-xs text-gray-400 mb-1 block">Current Password</span>
                                    <input
                                        type="password"
                                        value={pwForm.current_password}
                                        onChange={(e) => setPwForm((p) => ({ ...p, current_password: e.target.value }))}
                                        className={inputCls}
                                        placeholder="••••••••"
                                    />
                                </label>
                                <label className="block">
                                    <span className="text-xs text-gray-400 mb-1 block">New Password</span>
                                    <input
                                        type="password"
                                        value={pwForm.new_password}
                                        onChange={(e) => setPwForm((p) => ({ ...p, new_password: e.target.value }))}
                                        className={inputCls}
                                        placeholder="••••••••"
                                    />
                                </label>
                                <label className="block">
                                    <span className="text-xs text-gray-400 mb-1 block">Confirm New Password</span>
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
                                    className="w-full py-2.5 rounded-xl bg-rose-600/80 hover:bg-rose-600 border border-rose-500/30 text-white font-semibold text-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
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
