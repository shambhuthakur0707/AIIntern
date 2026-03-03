import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import InternshipsPage from './pages/InternshipsPage'
import ProfilePage from './pages/ProfilePage'

function ProtectedRoute({ children }) {
    const { token } = useAuth()
    return token ? children : <Navigate to="/login" replace />
}

function PublicRoute({ children }) {
    const { token } = useAuth()
    return token ? <Navigate to="/dashboard" replace /> : children
}

export default function App() {
    return (
        <AuthProvider>
            <ToastProvider>
                <BrowserRouter>
                    <Routes>
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
                        <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
                        <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
                        <Route path="/internships" element={<ProtectedRoute><InternshipsPage /></ProtectedRoute>} />
                        <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                </BrowserRouter>
            </ToastProvider>
        </AuthProvider>
    )
}
