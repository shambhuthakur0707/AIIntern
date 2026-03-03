/** Animated shimmer skeleton block */
export function SkeletonBlock({ className = '' }) {
    return (
        <div className={`bg-white/5 rounded-xl animate-pulse ${className}`} />
    )
}

/** Full internship card skeleton */
export function InternshipCardSkeleton() {
    return (
        <div className="glass-card p-5 space-y-4 animate-pulse">
            <div className="flex items-start gap-3">
                <SkeletonBlock className="w-9 h-9 rounded-xl flex-shrink-0" />
                <div className="flex-1 space-y-2">
                    <SkeletonBlock className="h-4 w-3/5" />
                    <SkeletonBlock className="h-3 w-2/5" />
                </div>
                <div className="hidden sm:flex flex-col gap-1 items-end">
                    <SkeletonBlock className="h-3 w-20" />
                    <SkeletonBlock className="h-3 w-16" />
                </div>
            </div>
            <SkeletonBlock className="h-2 w-full rounded-full" />
            <div className="space-y-1.5">
                <SkeletonBlock className="h-3 w-1/4" />
                <SkeletonBlock className="h-3 w-full" />
                <SkeletonBlock className="h-3 w-4/5" />
            </div>
            <div className="flex gap-2">
                <SkeletonBlock className="h-6 w-16 rounded-full" />
                <SkeletonBlock className="h-6 w-20 rounded-full" />
                <SkeletonBlock className="h-6 w-14 rounded-full" />
            </div>
        </div>
    )
}

/** Smaller card skeleton for Internships page */
export function InternshipListSkeleton() {
    return (
        <div className="glass-card p-5 animate-pulse space-y-3">
            <div className="flex justify-between gap-4">
                <div className="space-y-2 flex-1">
                    <SkeletonBlock className="h-4 w-2/5" />
                    <SkeletonBlock className="h-3 w-1/4" />
                    <div className="flex gap-2 mt-1">
                        <SkeletonBlock className="h-5 w-16 rounded-full" />
                        <SkeletonBlock className="h-5 w-20 rounded-full" />
                    </div>
                </div>
                <div className="space-y-1.5 items-end hidden sm:flex flex-col">
                    <SkeletonBlock className="h-3 w-24" />
                    <SkeletonBlock className="h-3 w-20" />
                </div>
            </div>
            <SkeletonBlock className="h-3 w-full" />
            <SkeletonBlock className="h-3 w-3/4" />
        </div>
    )
}
