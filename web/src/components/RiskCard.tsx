import { useEffect, useState } from 'react'
import type { FieldRisk, HorizonRisk } from '../api'
import { reasonText, speechText, STRINGS, type Lang } from '../i18n'

const ICON = { green: '✓', amber: '!', red: '‼' } as const

function Light({ h, lang }: { h: HorizonRisk; lang: Lang }) {
  const s = STRINGS[lang]
  const why = h.level === 'green' ? [] : h.reasons
  return (
    <li className={`light light-${h.level}`} data-testid={`horizon-${h.days}`}>
      <span className="light-dot" aria-hidden="true">
        {ICON[h.level]}
      </span>
      <span className="light-text">
        <strong>{s.inDays(h.days)}</strong>
        <span>{s.level[h.level]}</span>
        {why.length > 0 && (
          <span className="light-why">{why.map((r) => reasonText(r, lang)).join(' · ')}</span>
        )}
      </span>
    </li>
  )
}

export function RiskCard({ risk, lang }: { risk: FieldRisk; lang: Lang }) {
  const s = STRINGS[lang]
  const [speaking, setSpeaking] = useState(false)
  const canSpeak = typeof window !== 'undefined' && 'speechSynthesis' in window

  useEffect(() => () => {
    if (canSpeak) window.speechSynthesis.cancel()
  }, [canSpeak, risk, lang])

  const toggleSpeech = () => {
    if (!canSpeak) return
    window.speechSynthesis.cancel()
    if (speaking) {
      setSpeaking(false)
      return
    }
    const u = new SpeechSynthesisUtterance(speechText(risk, lang))
    u.lang = lang === 'de' ? 'de-DE' : 'en-GB'
    u.rate = 0.9
    u.onend = () => setSpeaking(false)
    setSpeaking(true)
    window.speechSynthesis.speak(u)
  }

  return (
    <section className="card" aria-live="polite" aria-label={`${s.field} ${risk.district}`}>
      <ul className="lights">
        {risk.horizons.map((h) => (
          <Light key={h.days} h={h} lang={lang} />
        ))}
      </ul>
      {canSpeak && (
        <button type="button" className="big-button speak" onClick={toggleSpeech}>
          <span aria-hidden="true">{speaking ? '■' : '🔊'}</span> {speaking ? s.stop : s.listen}
        </button>
      )}
    </section>
  )
}
