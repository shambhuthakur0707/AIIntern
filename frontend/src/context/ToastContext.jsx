import { createContext, useContext, useState, useCallback, useRef } from 'react'

const ToastContext = createContext(null)

let _id = 0

export function ToastProvider({ children }) {
    const [toasts, setToasts] = useState([])
    const timers = useRef({})

    const dismiss = useCallback((id) => {
        setToasts((prev) => prev.filter((t) => t.id !== id))
        clearTimeout(timers.current[id])
    }, [])

    const toast = useCallback(({ message, type = 'info', duration = 3500 }) => {
        const id = ++_id
        setToasts((prev) => [...prev.slice(-4), { id, message, type }])
        timers.current[id] = setTimeout(() => dismiss(id), duration)
        return id
    }, [dismiss])

    return (
        <ToastContext.Provider value={{ toast, dismiss }}>
            {children}
            {/* Portal: fixed to viewport bottom-right */}
            <div className="fixed bottom-5 right-5 z-[9999] flex flex-col gap-2 pointer-events-none">
                {toasts.map((t) => (
                    <div
                        key={t.id}
                        className={`pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-xl shadow-xl border text-sm
                            animate-slide-up backdrop-blur-md max-w-xs
                            ${t.type === 'success' ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300' : ''}
                            ${t.type === 'error'   ? 'bg-rose-500/20 border-rose-500/40 text-rose-300'     : ''}
                            ${t.type === 'info'    ? 'bg-brand-500/20 border-brand-500/40 text-brand-300'  : ''}
                            ${t.type === 'warning' ? 'bg-amber-500/20 border-amber-500/40 text-amber-300'  : ''}
                        `}
                    >
                        <span className="flex-shrink-0 mt-0.5">
                            {t.type === 'success' && '✓'}
                            {t.type === 'error'   && '⚠'}
                            {t.type === 'info'    && 'ℹ'}
                            {t.type === 'warning' && '⚡'}
                        </span>
                        <span className="flex-1 leading-snug">{t.message}</span>
                        <button
                            onClick={() => dismiss(t.id)}
                            className="flex-shrink-0 text-current opacity-50 hover:opacity-100 transition-opacity ml-1"
                        >
                            ×
                        </button>
                    </div>
                ))}
            </div>
        </ToastContext.Provider>
    )
}

export function useToast() {
    const ctx = useContext(ToastContext)
    if (!ctx) throw new Error('useToast must be used inside ToastProvider')
    return ctx.toast
}
