import { useEffect, useRef } from 'react'
import { STRINGS, type Lang } from '../i18n'

/** The help dialog has one interactive control. Keep Tab inside and return focus to its opener. */
export function IntroDialog({ lang, onClose }: { lang: Lang; onClose: () => void }) {
  const s = STRINGS[lang]
  const close = useRef<HTMLButtonElement>(null)
  const callback = useRef(onClose)
  callback.current = onClose
  useEffect(() => {
    const opener = document.activeElement
    close.current?.focus()
    const keys = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { event.preventDefault(); callback.current() }
      if (event.key === 'Tab') { event.preventDefault(); close.current?.focus() }
    }
    document.addEventListener('keydown', keys)
    return () => {
      document.removeEventListener('keydown', keys)
      if (opener instanceof HTMLElement && opener.isConnected) opener.focus()
    }
  }, [])
  return <div className="intro-backdrop">
    <div className="intro-card" role="dialog" aria-modal="true" aria-labelledby="intro-title">
      <h2 id="intro-title">{s.introTitle}</h2>
      <ul className="intro-lights">
        {s.introLights.map(([icon, text]) => <li key={text}>
          <span aria-hidden="true">{icon}</span><span>{text}</span>
        </li>)}
      </ul><p>{s.introPick}</p><p>{s.introListen}</p>
      <button ref={close} type="button" className="big-button" onClick={onClose}>{s.introDone}</button>
    </div>
  </div>
}
