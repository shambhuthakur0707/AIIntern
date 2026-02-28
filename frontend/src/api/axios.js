import axios from 'axios'

const api = axios.create({
    baseURL: '/api',
    headers: { 'Content-Type': 'application/json' },
    timeout: 120000, // 2 min — agent can take time
})

// Attach JWT on every request
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('aiintern_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
})

// Unified error response
api.interceptors.response.use(
    (res) => res,
    (err) => {
        if (err.response?.status === 401) {
            localStorage.removeItem('aiintern_token')
            localStorage.removeItem('aiintern_user')
            window.location.href = '/login'
        }
        return Promise.reject(err)
    }
)

export default api
