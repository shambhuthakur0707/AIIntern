import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import ErrorBoundary from './components/ErrorBoundary'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import InternshipsPage from './pages/InternshipsPage'
import ProfilePage from './pages/ProfilePage'
import StatisticsPage from './pages/StatisticsPage'
import TrackerPage from './pages/TrackerPage'
import SavedPage from './pages/SavedPage'
import DeadlinesPage from './pages/DeadlinesPage'
import InterviewPrepPage from './pages/InterviewPrepPage'

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
        <ErrorBoundary>
            <AuthProvider>
                <ToastProvider>
                    <BrowserRouter>
                        <Routes>
                            <Route path="/" element={<Navigate to="/dashboard" replace />} />
                            <Route path="/login"    element={<PublicRoute><LoginPage /></PublicRoute>} />
                            <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />

                            <Route path="/dashboard"    element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
                            <Route path="/internships"  element={<ProtectedRoute><InternshipsPage /></ProtectedRoute>} />
                            <Route path="/profile"      element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
                            <Route path="/statistics"   element={<ProtectedRoute><StatisticsPage /></ProtectedRoute>} />
                            <Route path="/tracker"      element={<ProtectedRoute><TrackerPage /></ProtectedRoute>} />
                            <Route path="/saved"        element={<ProtectedRoute><SavedPage /></ProtectedRoute>} />
                            <Route path="/deadlines"    element={<ProtectedRoute><DeadlinesPage /></ProtectedRoute>} />
                            <Route path="/interview-prep" element={<ProtectedRoute><InterviewPrepPage /></ProtectedRoute>} />

                            <Route path="*" element={<Navigate to="/" replace />} />
                        </Routes>
                    </BrowserRouter>
                </ToastProvider>
            </AuthProvider>
        </ErrorBoundary>
    )
}
