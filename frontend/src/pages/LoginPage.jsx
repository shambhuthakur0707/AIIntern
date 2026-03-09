import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID

export default function LoginPage() {
    const [form, setForm] = useState({ email: '', password: '' })
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const [googleLoading, setGoogleLoading] = useState(false)
    const { login } = useAuth()
    const navigate = useNavigate()

    const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        try {
            const { data } = await api.post('/auth/login', form)
            if (data.data.email_verified === false) {
                navigate('/verify-email', { state: { email: form.email } })
                return
            }
            login(data.data.token, data.data.user)
            navigate('/dashboard')
        } catch (err) {
            setError(err.response?.data?.message || 'Login failed. Please try again.')
        } finally {
            setLoading(false)
        }
    }

    // Initialize Google Sign-In
    useEffect(() => {
        if (!GOOGLE_CLIENT_ID) return
        const script = document.createElement('script')
        script.src = 'https://accounts.google.com/gsi/client'
        script.async = true
        script.defer = true
        script.onload = () => {
            window.google?.accounts.id.initialize({
                client_id: GOOGLE_CLIENT_ID,
                callback: handleGoogleResponse,
            })
            window.google?.accounts.id.renderButton(
                document.getElementById('google-signin-btn'),
                { theme: 'filled_black', size: 'large', width: '100%', text: 'signin_with', shape: 'pill' }
            )
        }
        document.head.appendChild(script)
        return () => { script.remove() }
    }, []) // eslint-disable-line

    const handleGoogleResponse = async (response) => {
        setError('')
        setGoogleLoading(true)
        try {
            const { data } = await api.post('/auth/google', { credential: response.credential })
            login(data.data.token, data.data.user)
            navigate('/dashboard')
        } catch (err) {
            setError(err.response?.data?.message || 'Google sign-in failed.')
        } finally {
            setGoogleLoading(false)
        }
    }

    return (
        <div className="animated-gradient min-h-screen flex items-center justify-center p-4">
            <div className="w-full max-w-md">

                {/* Logo */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500 to-violet-500 shadow-xl shadow-brand-500/30 mb-4">
                        <span className="text-2xl font-black text-white">AI</span>
                    </div>
                    <h1 className="text-3xl font-extrabold text-white">Welcome back</h1>
                    <p className="text-gray-400 mt-1.5">Sign in to your AIIntern account</p>
                </div>

                {/* Card */}
                <div className="glass-card p-8 shadow-2xl">
                    {error && (
                        <div className="mb-4 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm px-4 py-3 rounded-xl animate-fade-in">
                            {error}
                        </div>
                    )}

                    {/* Google Sign-In */}
                    {GOOGLE_CLIENT_ID && (
                        <>
                            <div className="mb-5">
                                {googleLoading ? (
                                    <div className="flex items-center justify-center gap-2 py-3 text-sm text-gray-400">
                                        <div className="spinner" /> Signing in with Google…
                                    </div>
                                ) : (
                                    <div id="google-signin-btn" className="flex justify-center" />
                                )}
                            </div>
                            <div className="flex items-center gap-3 mb-5">
                                <div className="flex-1 h-px bg-white/10" />
                                <span className="text-xs text-gray-500">or sign in with email</span>
                                <div className="flex-1 h-px bg-white/10" />
                            </div>
                        </>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5" id="login-form">
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1.5">Email</label>
                            <input
                                id="login-email"
                                type="email"
                                name="email"
                                value={form.email}
                                onChange={handleChange}
                                placeholder="aryan@example.com"
                                required
                                className="form-input"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1.5">Password</label>
                            <input
                                id="login-password"
                                type="password"
                                name="password"
                                value={form.password}
                                onChange={handleChange}
                                placeholder="••••••••"
                                required
                                className="form-input"
                            />
                        </div>

                        <button
                            id="login-submit"
                            type="submit"
                            disabled={loading}
                            className="btn-primary w-full flex items-center justify-center gap-2 mt-2"
                        >
                            {loading ? (
                                <><div className="spinner" />Signing in…</>
                            ) : (
                                'Sign In'
                            )}
                        </button>
                    </form>

                    <p className="mt-6 text-center text-sm text-gray-500">
                        Don't have an account?{' '}
                        <Link to="/register" className="text-brand-400 font-medium hover:text-brand-300 transition-colors">
                            Create one
                        </Link>
                    </p>

                    {/* Demo hint */}
                    <div className="mt-5 bg-brand-500/10 border border-brand-500/20 rounded-xl px-4 py-3">
                        <p className="text-xs text-gray-400 text-center">
                            <span className="text-brand-400 font-medium">Demo:</span>{' '}
                            aryan@example.com / Password1
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
