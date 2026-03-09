import { useState, useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'

export default function VerifyEmailPage() {
    const [otp, setOtp] = useState(['', '', '', '', '', ''])
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const [resendLoading, setResendLoading] = useState(false)
    const [resendCooldown, setResendCooldown] = useState(0)
    const [success, setSuccess] = useState(false)
    const inputRefs = useRef([])
    const navigate = useNavigate()
    const location = useLocation()
    const { user, updateUser } = useAuth()

    const email = location.state?.email || user?.email || ''

    useEffect(() => {
        if (!email) navigate('/login', { replace: true })
    }, [email, navigate])

    useEffect(() => {
        if (resendCooldown <= 0) return
        const timer = setInterval(() => setResendCooldown((c) => c - 1), 1000)
        return () => clearInterval(timer)
    }, [resendCooldown])

    useEffect(() => {
        inputRefs.current[0]?.focus()
    }, [])

    const handleChange = (index, value) => {
        if (value && !/^\d$/.test(value)) return
        const newOtp = [...otp]
        newOtp[index] = value
        setOtp(newOtp)
        if (value && index < 5) {
            inputRefs.current[index + 1]?.focus()
        }
    }

    const handleKeyDown = (index, e) => {
        if (e.key === 'Backspace' && !otp[index] && index > 0) {
            inputRefs.current[index - 1]?.focus()
        }
    }

    const handlePaste = (e) => {
        e.preventDefault()
        const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
        if (pasted.length === 6) {
            setOtp(pasted.split(''))
            inputRefs.current[5]?.focus()
        }
    }

    const handleVerify = async (e) => {
        e.preventDefault()
        const code = otp.join('')
        if (code.length !== 6) { setError('Please enter the 6-digit code'); return }

        setError('')
        setLoading(true)
        try {
            const { data } = await api.post('/auth/verify-email', { email, otp: code })
            if (data.data?.user) updateUser(data.data.user)
            setSuccess(true)
            setTimeout(() => navigate('/dashboard', { replace: true }), 1500)
        } catch (err) {
            setError(err.response?.data?.message || 'Verification failed. Try again.')
            setOtp(['', '', '', '', '', ''])
            inputRefs.current[0]?.focus()
        } finally {
            setLoading(false)
        }
    }

    const handleResend = async () => {
        setError('')
        setResendLoading(true)
        try {
            await api.post('/auth/resend-otp', { email })
            setResendCooldown(60)
        } catch (err) {
            setError(err.response?.data?.message || 'Could not resend OTP.')
        } finally {
            setResendLoading(false)
        }
    }

    return (
        <div className="animated-gradient min-h-screen flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500 to-violet-500 shadow-xl shadow-brand-500/30 mb-4">
                        <span className="text-2xl">✉️</span>
                    </div>
                    <h1 className="text-3xl font-extrabold text-white">Verify your email</h1>
                    <p className="text-gray-400 mt-1.5">
                        We sent a 6-digit code to <span className="text-brand-400 font-medium">{email}</span>
                    </p>
                </div>

                <div className="glass-card p-8 shadow-2xl">
                    {success && (
                        <div className="mb-4 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm px-4 py-3 rounded-xl animate-fade-in text-center">
                            ✓ Email verified! Redirecting…
                        </div>
                    )}

                    {error && (
                        <div className="mb-4 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm px-4 py-3 rounded-xl animate-fade-in">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleVerify}>
                        <div className="flex justify-center gap-3 mb-6">
                            {otp.map((digit, i) => (
                                <input
                                    key={i}
                                    ref={(el) => (inputRefs.current[i] = el)}
                                    type="text"
                                    inputMode="numeric"
                                    maxLength={1}
                                    value={digit}
                                    onChange={(e) => handleChange(i, e.target.value)}
                                    onKeyDown={(e) => handleKeyDown(i, e)}
                                    onPaste={i === 0 ? handlePaste : undefined}
                                    className="w-12 h-14 text-center text-2xl font-bold text-white bg-white/5 border border-white/20 rounded-xl focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition-colors"
                                    disabled={loading || success}
                                />
                            ))}
                        </div>

                        <button
                            type="submit"
                            disabled={loading || success || otp.join('').length !== 6}
                            className="btn-primary w-full flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <><div className="spinner" />Verifying…</>
                            ) : success ? (
                                '✓ Verified'
                            ) : (
                                'Verify Email'
                            )}
                        </button>
                    </form>

                    <div className="mt-5 text-center">
                        <p className="text-sm text-gray-500">
                            Didn't receive the code?{' '}
                            {resendCooldown > 0 ? (
                                <span className="text-gray-600">Resend in {resendCooldown}s</span>
                            ) : (
                                <button
                                    type="button"
                                    onClick={handleResend}
                                    disabled={resendLoading}
                                    className="text-brand-400 font-medium hover:text-brand-300 transition-colors"
                                >
                                    {resendLoading ? 'Sending…' : 'Resend OTP'}
                                </button>
                            )}
                        </p>
                    </div>

                    <div className="mt-4 text-center">
                        <button
                            type="button"
                            onClick={() => navigate('/login')}
                            className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
                        >
                            ← Back to login
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
