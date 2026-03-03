import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function navClassName({ isActive }) {
    return `text-sm font-medium transition-colors ${isActive ? 'text-white' : 'text-gray-400 hover:text-white'}`
}

const NAV_LINKS = [
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/internships', label: 'Internships' },
    { to: '/profile', label: 'Profile' },
]

export default function Navbar() {
    const { user, logout } = useAuth()
    const navigate = useNavigate()
    const [menuOpen, setMenuOpen] = useState(false)

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    return (
        <header className="sticky top-0 z-50 border-b border-white/10 bg-gray-950/80 backdrop-blur-md">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16 gap-4">
                    {/* Logo + desktop nav */}
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-violet-500 flex items-center justify-center text-white font-bold text-sm">
                                AI
                            </div>
                            <span className="font-bold text-lg tracking-tight">
                                <span className="gradient-text">AIIntern</span>
                            </span>
                        </div>

                        <nav className="hidden md:flex items-center gap-4">
                            {NAV_LINKS.map(({ to, label }) => (
                                <NavLink key={to} to={to} className={navClassName}>{label}</NavLink>
                            ))}
                        </nav>
                    </div>

                    {/* Right side — user chip + sign out + hamburger */}
                    <div className="flex items-center gap-4">
                        {user && (
                            <div className="hidden sm:flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-3 py-1.5">
                                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-brand-500 to-violet-500 flex items-center justify-center text-xs font-bold">
                                    {user.name?.[0]?.toUpperCase()}
                                </div>
                                <span className="text-sm text-gray-300 font-medium">{user.name}</span>
                            </div>
                        )}
                        <button
                            onClick={handleLogout}
                            className="hidden sm:block text-sm text-gray-400 hover:text-white transition-colors font-medium"
                            id="logout-btn"
                        >
                            Sign out
                        </button>

                        {/* Hamburger — mobile only */}
                        <button
                            onClick={() => setMenuOpen((o) => !o)}
                            className="md:hidden flex flex-col justify-center items-center w-8 h-8 gap-1.5 text-gray-400 hover:text-white transition-colors"
                            aria-label="Toggle menu"
                        >
                            <span className={`block w-5 h-0.5 bg-current transition-transform duration-200 ${menuOpen ? 'rotate-45 translate-y-2' : ''}`} />
                            <span className={`block w-5 h-0.5 bg-current transition-opacity duration-200 ${menuOpen ? 'opacity-0' : ''}`} />
                            <span className={`block w-5 h-0.5 bg-current transition-transform duration-200 ${menuOpen ? '-rotate-45 -translate-y-2' : ''}`} />
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile menu dropdown */}
            {menuOpen && (
                <div className="md:hidden border-t border-white/10 bg-gray-950/95 px-4 py-4 space-y-1 animate-fade-in">
                    {NAV_LINKS.map(({ to, label }) => (
                        <NavLink
                            key={to}
                            to={to}
                            onClick={() => setMenuOpen(false)}
                            className={({ isActive }) =>
                                `block px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                                    isActive
                                        ? 'bg-white/10 text-white'
                                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                                }`
                            }
                        >
                            {label}
                        </NavLink>
                    ))}
                    <hr className="border-white/10 my-2" />
                    {user && (
                        <p className="px-3 py-1 text-xs text-gray-500">Signed in as <span className="text-gray-300">{user.name}</span></p>
                    )}
                    <button
                        onClick={() => { setMenuOpen(false); handleLogout() }}
                        className="block w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-red-400 hover:bg-white/5 transition-colors"
                    >
                        Sign out
                    </button>
                </div>
            )}
        </header>
    )
}
