# ADR 0071: More natural read-aloud voices

- Status: accepted, 2026-11-04
- Context: the read-aloud button used a single `SpeechSynthesisUtterance` for the
  whole card at `rate 0.9` with no voice selection — the default voice read one
  long blob and sounded robotic in both English and German.
- Decision: a shared `web/src/speech.ts` helper now
  - picks the best matching voice (`getVoices()`), preferring
    natural/neural/Google/enhanced voices and the exact locale (`en-GB`/`de-DE`),
    waiting for `onvoiceschanged` when the list is not loaded yet;
  - splits the text into sentences and queues one utterance per sentence, so the
    browser produces natural pauses and resets prosody between clauses;
  - speaks at `rate 0.98` (near normal) with neutral pitch.
  `RiskCard` and `LiveCard` both use it, so winter cards and Live cards sound the
  same. No external TTS service: the app must work offline and free; on devices
  with better voices installed (Android Google voices, Windows natural voices)
  quality improves automatically.
- Consequences: utterances are chained via `onend`, so a card read is a queue of
  short utterances; cancelling still works through `speechSynthesis.cancel()`.
