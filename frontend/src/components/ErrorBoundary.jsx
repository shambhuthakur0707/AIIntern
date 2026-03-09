import React from 'react'

export default class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props)
        this.state = { hasError: false, error: null }
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error }
    }

    componentDidCatch(error, errorInfo) {
        console.error('React ErrorBoundary caught:', error, errorInfo)
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
                    <div className="text-center max-w-md">
                        <div className="text-6xl mb-4">⚠️</div>
                        <h1 className="text-2xl font-bold text-white mb-2">Something went wrong</h1>
                        <p className="text-gray-400 mb-6 text-sm">
                            An unexpected error occurred. Please refresh the page to try again.
                        </p>
                        <button
                            onClick={() => window.location.reload()}
                            className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-6 py-2.5 rounded-xl transition-colors"
                        >
                            Refresh Page
                        </button>
                    </div>
                </div>
            )
        }
        return this.props.children
    }
}
