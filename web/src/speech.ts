import { Lang } from './i18n'

const LOCALE: Record<Lang, string> = { en: 'en-GB', de: 'de-DE' }

/** Prefer natural/neural voices when the browser offers them. */
function bestVoice(lang: Lang): SpeechSynthesisVoice | null {
  const voices = window.speechSynthesis?.getVoices?.() ?? []
  const want = LOCALE[lang]
  const same = voices.filter(
    (v) => v.lang === want || v.lang.startsWith(want.split('-')[0]),
  )
  if (!same.length) return null
  const score = (v: SpeechSynthesisVoice) => {
    const n = v.name.toLowerCase()
    let s = v.lang === want ? 2 : 0
    if (/natural|neural|google|premium|enhanced|aria|marlene|anna|katja/.test(n)) s += 4
    if (v.localService) s += 1
    return s
  }
  return same.sort((a, b) => score(b) - score(a))[0]
}

/** Speak text in short sentences with the best available voice (ADR 0071). */
export function speak(text: string, lang: Lang, onEnd: () => void): () => void {
  const synth = window.speechSynthesis
  const segments = text
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter(Boolean)
  let cancelled = false
  const cancel = () => {
    cancelled = true
    synth.cancel()
  }
  const run = () => {
    const voice = bestVoice(lang)
    let i = 0
    const next = () => {
      if (cancelled) return
      if (i >= segments.length) {
        onEnd()
        return
      }
      const u = new SpeechSynthesisUtterance(segments[i++])
      u.lang = LOCALE[lang]
      if (voice) u.voice = voice
      u.rate = 0.98
      u.pitch = 1.0
      u.onend = next
      u.onerror = next
      synth.speak(u)
    }
    next()
  }
  // Never gate on the voice list: it loads asynchronously and may stay empty in
  // some browsers — speech still works without an explicit voice.
  run()
  return cancel
}
