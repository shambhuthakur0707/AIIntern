const COLORS = [
    'bg-brand-500/20 text-brand-300 border border-brand-500/30',
    'bg-violet-500/20 text-violet-300 border border-violet-500/30',
    'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30',
    'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30',
    'bg-rose-500/20 text-rose-300 border border-rose-500/30',
    'bg-amber-500/20 text-amber-300 border border-amber-500/30',
]

function colorFor(skill) {
    let h = 0
    for (let i = 0; i < skill.length; i++) h = (h * 31 + skill.charCodeAt(i)) % COLORS.length
    return COLORS[Math.abs(h)]
}

export default function SkillBadge({ skill, size = 'sm' }) {
    return (
        <span className={`skill-badge ${colorFor(skill)} ${size === 'xs' ? 'text-[11px] px-2 py-0.5' : ''}`}>
            {skill}
        </span>
    )
}
