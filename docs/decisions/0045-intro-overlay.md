# ADR 0045: First-visit "How it works" overlay

Status: Accepted (US-48, Issue #103)

## Context
The illiterate-friendly goal: a first-time visitor sees a map of fields with no
idea what the colors mean. OneSoil/xarvio onboard with a guided first screen.

## Decision
- On the first visit (`localStorage` flag), a small dialog explains: the three
  lights, tap-a-field-or-list, and that the card reads everything aloud.
  EN/DE, plain words, one "Got it" button.
- A "?" chip in the header reopens it any time.
- Deliberately not a multi-step tour: three sentences, no arrows pointing at
  UI — the UI should be self-evident after one read.

## Consequences
- E2E suites set the seen-flag in `beforeEach`; the dialog has its own test.
