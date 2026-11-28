import { useEffect, useId, useRef, useState } from 'react'
import type { Lang } from '../i18n'
import { speak } from '../speech'
const T = {
  en: { read: 'Listen: read field summary', stop: 'Stop reading field summary', choose: 'Choose a field to read', hint: 'Tap the speaker to hear this field.', unavailable: 'Read-aloud is unavailable in this browser.', failed: 'Read-aloud could not start. You can still read the field information.' },
  de: { read: 'Vorlesen: Feldzusammenfassung', stop: 'Vorlesen der Feldzusammenfassung stoppen', choose: 'Ein Feld zum Vorlesen auswählen', hint: 'Zum Vorlesen dieses Feldes auf den Lautsprecher tippen.', unavailable: 'Vorlesen ist in diesem Browser nicht verfügbar.', failed: 'Vorlesen konnte nicht starten. Die Feldinformationen bleiben lesbar.' },
}
export function ReadFieldButton({ text, lang, identity, context }: { text: string | null; lang: Lang; identity: string; context?: string }) {
  const hintId = useId()
  const t = T[lang]
  const [speaking, setSpeaking] = useState(false)
  const [failed, setFailed] = useState(false)
  const stop = useRef<(() => void) | null>(null)
  const available = typeof window.speechSynthesis?.speak === 'function' && typeof SpeechSynthesisUtterance !== 'undefined'
  useEffect(() => {
    stop.current?.(); stop.current = null; setSpeaking(false); setFailed(false)
    return () => { stop.current?.(); stop.current = null }
  }, [text, lang, identity])
  useEffect(() => {
    const cancel = () => { stop.current?.(); stop.current = null; setSpeaking(false) }
    window.addEventListener('cropews-stop-reading', cancel)
    return () => window.removeEventListener('cropews-stop-reading', cancel)
  }, [])
  const baseLabel = !available ? t.unavailable : !text ? t.choose : speaking ? t.stop : t.read
  const label = context ? `${context}: ${baseLabel}` : baseLabel
  return <div className="upper-read-control">
    <button type="button" className="upper-read-button" aria-label={label} aria-describedby={hintId} aria-pressed={speaking} title={label} disabled={!available || !text} onClick={() => {
      if (speaking) { stop.current?.(); stop.current = null; setSpeaking(false); return }
      if (!text) return
      try {
        window.dispatchEvent(new Event('cropews-stop-reading')); setFailed(false); setSpeaking(true); window.speechSynthesis.cancel()
        stop.current = speak(text, lang, () => { stop.current = null; setSpeaking(false) })
      } catch { setSpeaking(false); setFailed(true) }
    }}><span aria-hidden="true">{speaking ? '■' : '🔊'}</span></button>
    <span id={hintId} className="speaker-hint" role="status">{!available ? t.unavailable : failed ? t.failed : t.hint}</span>
  </div>
}
