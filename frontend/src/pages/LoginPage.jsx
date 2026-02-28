import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
    const [form, setForm] = useState({ email: '', password: '' })
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const { login } = useAuth()
    const navigate = useNavigate()

    const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        try {
            const { data } = await api.post('/auth/login', form)
            login(data.data.token, data.data.user)
            navigate('/dashboard')
        } catch (err) {
            setError(err.response?.data?.message || 'Login failed. Please try again.')
        } finally {
            setLoading(false)
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
                            aryan@example.com / password123
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
