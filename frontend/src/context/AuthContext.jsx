import { createContext, useContext, useState, useCallback } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
    const [token, setToken] = useState(() => localStorage.getItem('aiintern_token'))
    const [user, setUser] = useState(() => {
        try { return JSON.parse(localStorage.getItem('aiintern_user')) } catch { return null }
    })

    const login = useCallback((newToken, userData) => {
        localStorage.setItem('aiintern_token', newToken)
        localStorage.setItem('aiintern_user', JSON.stringify(userData))
        setToken(newToken)
        setUser(userData)
    }, [])

    const logout = useCallback(() => {
        localStorage.removeItem('aiintern_token')
        localStorage.removeItem('aiintern_user')
        setToken(null)
        setUser(null)
    }, [])

    const updateUser = useCallback((userData) => {
        localStorage.setItem('aiintern_user', JSON.stringify(userData))
        setUser(userData)
    }, [])

    return (
        <AuthContext.Provider value={{ token, user, login, logout, updateUser }}>
            {children}
        </AuthContext.Provider>
    )
}

export const useAuth = () => {
    const ctx = useContext(AuthContext)
    if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
    return ctx
}
