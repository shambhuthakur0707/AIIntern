import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function navClassName({ isActive }) {
    return `text-sm font-medium transition-colors ${isActive ? 'text-white' : 'text-gray-400 hover:text-white'}`
}

export default function Navbar() {
    const { user, logout } = useAuth()
    const navigate = useNavigate()

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    return (
        <header className="sticky top-0 z-50 border-b border-white/10 bg-gray-950/80 backdrop-blur-md">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16 gap-4">
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
                            <NavLink to="/dashboard" className={navClassName}>Dashboard</NavLink>
                            <NavLink to="/internships" className={navClassName}>Internships</NavLink>
                        </nav>
                    </div>

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
                            className="text-sm text-gray-400 hover:text-white transition-colors font-medium"
                            id="logout-btn"
                        >
                            Sign out
                        </button>
                    </div>
                </div>
            </div>
        </header>
    )
}
