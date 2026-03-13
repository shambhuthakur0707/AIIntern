import { useCallback, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'
import GoogleAuthButton, { isGoogleClientConfigured } from '../components/GoogleAuthButton'

const SKILL_SUGGESTIONS = [
    'Python', 'JavaScript', 'React', 'Node.js', 'SQL', 'TensorFlow', 'PyTorch',
    'Machine Learning', 'Deep Learning', 'NLP', 'Data Analysis', 'Docker',
    'AWS', 'MongoDB', 'Git', 'Java', 'Scikit-learn', 'Pandas', 'NumPy',
    'Computer Vision', 'Flutter', 'Kotlin', 'REST API', 'DevOps', 'Kubernetes',
]

const PASSWORD_RULES = [
    { test: (p) => p.length >= 8, label: 'At least 8 characters' },
    { test: (p) => /[A-Z]/.test(p), label: 'One uppercase letter' },
    { test: (p) => /[a-z]/.test(p), label: 'One lowercase letter' },
    { test: (p) => /[0-9]/.test(p), label: 'One number' },
]

export default function RegisterPage() {
    const [form, setForm] = useState({
        name: '', email: '', password: '',
        education: '', experience_level: 'beginner',
        skills: [], interests: [],
    })
    const [skillInput, setSkillInput] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const [googleLoading, setGoogleLoading] = useState(false)
    const { login } = useAuth()
    const navigate = useNavigate()

    const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

    const addSkill = (skill) => {
        const s = skill.trim()
        if (s && !form.skills.includes(s)) {
            setForm({ ...form, skills: [...form.skills, s] })
        }
        setSkillInput('')
    }

    const removeSkill = (skill) => setForm({ ...form, skills: form.skills.filter((s) => s !== skill) })

    const passwordValid = PASSWORD_RULES.every((r) => r.test(form.password))

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        if (form.skills.length === 0) { setError('Please add at least one skill.'); return }
        if (!passwordValid) { setError('Please meet all password requirements.'); return }
        setLoading(true)
        try {
            const { data } = await api.post('/auth/register', {
                ...form,
                interests: form.skills.slice(0, 3),
            })
            login(data.data.token, data.data.user)
            navigate('/dashboard')
        } catch (err) {
            setError(err.response?.data?.message || 'Registration failed.')
        } finally {
            setLoading(false)
        }
    }

    const handleGoogleResponse = useCallback(async (response) => {
        setError('')
        setGoogleLoading(true)
        try {
            const { data } = await api.post('/auth/google', { credential: response.credential })
            login(data.data.token, data.data.user)
            navigate('/dashboard')
        } catch (err) {
            setError(err.response?.data?.message || 'Google sign-up failed.')
        } finally {
            setGoogleLoading(false)
        }
    }, [login, navigate])

    const handleGoogleScriptError = useCallback(() => {
        setError('Google Sign-In could not be loaded. Check your Google client ID setup.')
    }, [])

    return (
        <div className="animated-gradient min-h-screen flex items-center justify-center p-4 py-10">
            <div className="w-full max-w-lg">

                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500 to-violet-500 shadow-xl shadow-brand-500/30 mb-4">
                        <span className="text-2xl font-black text-white">AI</span>
                    </div>
                    <h1 className="text-3xl font-extrabold text-white">Create your profile</h1>
                    <p className="text-gray-400 mt-1.5">Let our AI find your perfect internship</p>
                </div>

                <div className="glass-card p-8 shadow-2xl">
                    {error && (
                        <div className="mb-4 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm px-4 py-3 rounded-xl">
                            {error}
                        </div>
                    )}

                    {/* Google Sign-Up */}
                    {isGoogleClientConfigured() && (
                        <>
                            <div className="mb-5">
                                <GoogleAuthButton
                                    mode="signup"
                                    loading={googleLoading}
                                    onCredential={handleGoogleResponse}
                                    onError={handleGoogleScriptError}
                                />
                            </div>
                            <div className="flex items-center gap-3 mb-5">
                                <div className="flex-1 h-px bg-white/10" />
                                <span className="text-xs text-gray-500">or register with email</span>
                                <div className="flex-1 h-px bg-white/10" />
                            </div>
                        </>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5" id="register-form">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1.5">Full Name</label>
                                <input id="reg-name" type="text" name="name" value={form.name} onChange={handleChange}
                                    placeholder="Aryan Sharma" required className="form-input" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1.5">Email</label>
                                <input id="reg-email" type="email" name="email" value={form.email} onChange={handleChange}
                                    placeholder="aryan@example.com" required className="form-input" />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1.5">Password</label>
                            <input id="reg-password" type="password" name="password" value={form.password} onChange={handleChange}
                                placeholder="Min. 8 characters" minLength={8} required className="form-input" />
                            {form.password && (
                                <div className="mt-2 space-y-1">
                                    {PASSWORD_RULES.map((rule) => (
                                        <div key={rule.label} className={`flex items-center gap-1.5 text-xs ${rule.test(form.password) ? 'text-emerald-400' : 'text-gray-500'}`}>
                                            <span>{rule.test(form.password) ? '✓' : '○'}</span>
                                            <span>{rule.label}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1.5">Education</label>
                            <input id="reg-education" type="text" name="education" value={form.education} onChange={handleChange}
                                placeholder="B.Tech CS, IIT Roorkee (3rd Year)" className="form-input" />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1.5">Experience Level</label>
                            <select id="reg-level" name="experience_level" value={form.experience_level}
                                onChange={handleChange} className="form-input bg-gray-900">
                                <option value="beginner">Beginner</option>
                                <option value="intermediate">Intermediate</option>
                                <option value="advanced">Advanced</option>
                            </select>
                        </div>

                        {/* Skills input */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1.5">
                                Your Skills <span className="text-gray-500">(type and press Enter)</span>
                            </label>
                            <div className="flex gap-2">
                                <input
                                    id="reg-skill-input"
                                    type="text"
                                    value={skillInput}
                                    onChange={(e) => setSkillInput(e.target.value)}
                                    onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addSkill(skillInput) } }}
                                    placeholder="e.g. Python"
                                    className="form-input flex-1"
                                />
                                <button type="button" onClick={() => addSkill(skillInput)}
                                    className="btn-secondary px-4 flex-shrink-0">Add</button>
                            </div>

                            {/* Quick suggestions */}
                            <div className="flex flex-wrap gap-1.5 mt-2">
                                {SKILL_SUGGESTIONS.filter(s => !form.skills.includes(s)).slice(0, 12).map((s) => (
                                    <button key={s} type="button" onClick={() => addSkill(s)}
                                        className="text-xs text-gray-500 hover:text-brand-400 border border-white/10 hover:border-brand-500/30 px-2 py-0.5 rounded-full transition-colors">
                                        + {s}
                                    </button>
                                ))}
                            </div>

                            {/* Selected skills */}
                            {form.skills.length > 0 && (
                                <div className="flex flex-wrap gap-1.5 mt-3">
                                    {form.skills.map((s) => (
                                        <span key={s} className="flex items-center gap-1 bg-brand-500/20 border border-brand-500/30 text-brand-300 text-xs px-2.5 py-1 rounded-full">
                                            {s}
                                            <button type="button" onClick={() => removeSkill(s)} className="text-brand-400 hover:text-white ml-0.5">×</button>
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>

                        <button id="reg-submit" type="submit" disabled={loading}
                            className="btn-primary w-full flex items-center justify-center gap-2 mt-2">
                            {loading ? <><div className="spinner" />Creating profile…</> : 'Create Profile & Get Matched'}
                        </button>
                    </form>

                    <p className="mt-5 text-center text-sm text-gray-500">
                        Already have an account?{' '}
                        <Link to="/login" className="text-brand-400 font-medium hover:text-brand-300 transition-colors">Sign in</Link>
                    </p>
                </div>
            </div>
        </div>
    )
}
