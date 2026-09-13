# Speech And Timeline Procedure

Use this reference for text-to-speech requests, audio artifacts, caching, timing,
and synchronization with the final composition.

## Required Authority

Locate the accepted voice/provider capability, speech input contract, language
and pronunciation rules, cache identity, audio format, timeline schema, and
synchronization tolerance. Do not choose a voice or tolerance implicitly.

## Ordering Invariant

Generate or resolve the approved audio artifact, measure its actual duration,
then finalize the timeline before the final video render. Never infer duration
only from text length or provider estimates.

## Implementation Proof

- Validate the TTS request and map provider failures into accepted categories.
- Key cached audio with every accepted input that can change output.
- Record the voice/provider and relevant revision metadata.
- Measure audio duration using repository-approved tooling.
- Exercise silence, missing audio, invalid format, cache miss/hit, and changed
  narration when relevant.
- Compare rendered synchronization against the accepted tolerance.

Stop before external speech generation when capability, credentials, cost,
voice, cache ownership, audio format, or timing tolerance is unresolved.
