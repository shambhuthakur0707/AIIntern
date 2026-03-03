import { useState } from 'react'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const POPULAR_SKILLS = [
    'Python', 'JavaScript', 'React', 'Node.js', 'SQL', 'Machine Learning',
    'Data Analysis', 'Docker', 'AWS', 'Java', 'TensorFlow', 'Deep Learning',
    'Flutter', 'Kotlin', 'DevOps', 'TypeScript', 'FastAPI', 'Django',
]

const POPULAR_INTERESTS = [
    'Software Engineering', 'Data Science', 'AI / ML', 'Web Development',
    'Mobile Development', 'Cloud Computing', 'Cybersecurity', 'Product Management',
    'UI/UX Design', 'DevOps / SRE',
]

/**
 * OnboardingWizard — 3-step modal shown to new users with no skills.
 * Props:
 *   onClose: () => void   — called after completion or skip
 */
export default function OnboardingWizard({ onClose }) {
    const { user, updateUser } = useAuth()
    const toast = useToast()
    const [step, setStep] = useState(1)
    const [skills, setSkills] = useState([])
    const [skillInput, setSkillInput] = useState('')
    const [interests, setInterests] = useState([])
    const [saving, setSaving] = useState(false)

    const toggleListItem = (setter, list, item) => {
        setter(list.includes(item) ? list.filter((x) => x !== item) : [...list, item])
    }

    const addSkillFromInput = () => {
        const s = skillInput.trim()
        if (s && !skills.includes(s)) setSkills([...skills, s])
        setSkillInput('')
    }

    const handleAddSkillKey = (e) => {
        if (e.key === 'Enter') { e.preventDefault(); addSkillFromInput() }
    }

    const handleFinish = async () => {
        setSaving(true)
        try {
            await api.put('/auth/profile', {
                skills: [...(user?.skills ?? []), ...skills],
                interests,
            })
            updateUser((prev) => ({
                ...prev,
                skills: [...(prev?.skills ?? []), ...skills],
                interests,
            }))
            toast({ message: 'Profile setup complete! Run the AI agent to find matches.', type: 'success' })
        } catch {
            toast({ message: 'Could not save — you can update later from your profile.', type: 'warning' })
        } finally {
            setSaving(false)
            onClose()
        }
    }

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4"
            onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
        >
            <div className="glass-card w-full max-w-lg p-8 animate-fade-in">
                {/* Progress bar */}
                <div className="flex items-center gap-2 mb-8">
                    {[1, 2, 3].map((s) => (
                        <div
                            key={s}
                            className={`flex-1 h-1.5 rounded-full transition-colors duration-300 ${
                                s <= step ? 'bg-brand-500' : 'bg-white/10'
                            }`}
                        />
                    ))}
                </div>

                {/* Step 1 — Add skills */}
                {step === 1 && (
                    <div>
                        <h2 className="text-xl font-bold text-white mb-1">Add your skills</h2>
                        <p className="text-gray-400 text-sm mb-5">Pick from popular skills or type your own.</p>

                        <div className="flex gap-2 mb-4">
                            <input
                                className="input flex-1"
                                placeholder="Type a skill…"
                                value={skillInput}
                                onChange={(e) => setSkillInput(e.target.value)}
                                onKeyDown={handleAddSkillKey}
                            />
                            <button type="button" onClick={addSkillFromInput} className="btn-primary !py-2 !px-4 text-sm">
                                Add
                            </button>
                        </div>

                        <div className="flex flex-wrap gap-2 mb-4">
                            {POPULAR_SKILLS.map((s) => (
                                <button
                                    key={s}
                                    type="button"
                                    onClick={() => toggleListItem(setSkills, skills, s)}
                                    className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                                        skills.includes(s)
                                            ? 'border-brand-500 bg-brand-500/20 text-brand-300'
                                            : 'border-white/10 text-gray-400 hover:border-white/30 hover:text-white'
                                    }`}
                                >
                                    {skills.includes(s) ? '✓ ' : '+ '}{s}
                                </button>
                            ))}
                        </div>

                        {skills.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-2 mb-4">
                                {skills.map((s) => (
                                    <span
                                        key={s}
                                        className="inline-flex items-center gap-1 bg-brand-500/20 border border-brand-500/30 text-brand-300 text-xs px-2 py-0.5 rounded-full"
                                    >
                                        {s}
                                        <button
                                            type="button"
                                            onClick={() => setSkills(skills.filter((x) => x !== s))}
                                            className="hover:text-white"
                                        >×</button>
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Step 2 — Interests */}
                {step === 2 && (
                    <div>
                        <h2 className="text-xl font-bold text-white mb-1">Pick your interests</h2>
                        <p className="text-gray-400 text-sm mb-5">We'll prioritise matching internship domains.</p>

                        <div className="flex flex-wrap gap-2">
                            {POPULAR_INTERESTS.map((i) => (
                                <button
                                    key={i}
                                    type="button"
                                    onClick={() => toggleListItem(setInterests, interests, i)}
                                    className={`text-sm px-3 py-1.5 rounded-lg border transition-colors ${
                                        interests.includes(i)
                                            ? 'border-violet-500 bg-violet-500/20 text-violet-300'
                                            : 'border-white/10 text-gray-400 hover:border-white/30 hover:text-white'
                                    }`}
                                >
                                    {interests.includes(i) ? '✓ ' : ''}{i}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Step 3 — Ready */}
                {step === 3 && (
                    <div className="text-center py-4">
                        <div className="text-5xl mb-4">🚀</div>
                        <h2 className="text-xl font-bold text-white mb-2">You're all set!</h2>
                        <p className="text-gray-400 text-sm mb-1">
                            You've added <span className="text-white font-medium">{skills.length} skill{skills.length !== 1 ? 's' : ''}</span>
                            {interests.length > 0 && <> and <span className="text-white font-medium">{interests.length} interest{interests.length !== 1 ? 's' : ''}</span></>}.
                        </p>
                        <p className="text-gray-500 text-sm mt-2">
                            Click <span className="text-brand-400 font-medium">"Run AI Agent"</span> on the dashboard to see your personalized matches.
                        </p>
                    </div>
                )}

                {/* Navigation buttons */}
                <div className="flex items-center justify-between mt-8">
                    <button
                        type="button"
                        onClick={onClose}
                        className="text-sm text-gray-500 hover:text-gray-300 transition-colors"
                    >
                        Skip setup
                    </button>
                    <div className="flex gap-3">
                        {step > 1 && (
                            <button
                                type="button"
                                onClick={() => setStep((s) => s - 1)}
                                className="btn-secondary !py-2 !px-4 text-sm"
                            >
                                Back
                            </button>
                        )}
                        {step < 3 ? (
                            <button
                                type="button"
                                onClick={() => setStep((s) => s + 1)}
                                className="btn-primary !py-2 !px-5 text-sm"
                            >
                                Next →
                            </button>
                        ) : (
                            <button
                                type="button"
                                onClick={handleFinish}
                                disabled={saving}
                                className="btn-primary !py-2 !px-5 text-sm"
                            >
                                {saving ? 'Saving…' : 'Finish & Go!'}
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
