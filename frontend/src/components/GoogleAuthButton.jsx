import { useEffect, useRef } from 'react'

const GOOGLE_CLIENT_ID = (import.meta.env.VITE_GOOGLE_CLIENT_ID || '').trim()
const GOOGLE_SCRIPT_SRC = 'https://accounts.google.com/gsi/client'
const GOOGLE_PLACEHOLDER_CLIENT_IDS = new Set(['', 'your-google-client-id'])

let googleScriptPromise

function loadGoogleScript() {
    if (window.google?.accounts?.id) {
        return Promise.resolve(window.google)
    }

    if (!googleScriptPromise) {
        googleScriptPromise = new Promise((resolve, reject) => {
            const existingScript = document.querySelector(`script[src="${GOOGLE_SCRIPT_SRC}"]`)

            if (existingScript) {
                existingScript.addEventListener('load', () => resolve(window.google), { once: true })
                existingScript.addEventListener('error', () => reject(new Error('Failed to load Google Sign-In')), { once: true })
                return
            }

            const script = document.createElement('script')
            script.src = GOOGLE_SCRIPT_SRC
            script.async = true
            script.defer = true
            script.onload = () => resolve(window.google)
            script.onerror = () => reject(new Error('Failed to load Google Sign-In'))
            document.head.appendChild(script)
        })
    }

    return googleScriptPromise
}

export function isGoogleClientConfigured() {
    return !GOOGLE_PLACEHOLDER_CLIENT_IDS.has(GOOGLE_CLIENT_ID)
}

export default function GoogleAuthButton({ mode, loading, onCredential, onError }) {
    const containerRef = useRef(null)

    useEffect(() => {
        if (!isGoogleClientConfigured() || !containerRef.current) {
            return undefined
        }

        let cancelled = false

        loadGoogleScript()
            .then((google) => {
                if (cancelled || !containerRef.current || !google?.accounts?.id) {
                    return
                }

                const buttonWidth = Math.max(220, Math.floor(containerRef.current.offsetWidth || 360))

                containerRef.current.innerHTML = ''
                google.accounts.id.initialize({
                    client_id: GOOGLE_CLIENT_ID,
                    callback: onCredential,
                })
                google.accounts.id.renderButton(containerRef.current, {
                    theme: 'filled_black',
                    size: 'large',
                    width: buttonWidth,
                    text: mode === 'signup' ? 'signup_with' : 'signin_with',
                    shape: 'pill',
                })
            })
            .catch((error) => {
                if (!cancelled) {
                    onError?.(error)
                }
            })

        return () => {
            cancelled = true
            if (containerRef.current) {
                containerRef.current.innerHTML = ''
            }
        }
    }, [mode, onCredential, onError])

    if (!isGoogleClientConfigured()) {
        return null
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center gap-2 py-3 text-sm text-gray-400 min-h-[44px]">
                <div className="spinner" />
                {mode === 'signup' ? 'Signing up with Google…' : 'Signing in with Google…'}
            </div>
        )
    }

    return <div ref={containerRef} className="w-full flex justify-center min-h-[44px]" />
}