# WF-06 — Recording → AI Call Summary → Note

[← Danh sách workflow](README.md) · [Feature 1](../features/contact-center/CALLS.md) · [Feature 2](../features/activities/NOTES_TIMELINE.md)

- **Scenario/Actors:** authorized handler requests Generate/Regenerate, worker calls BeeKnoee, employee reviews next steps.
- **Preconditions/Input/Output:** one readable private recording ≤25 MB, protected provider config; output AI Summary and optional one Note.
- **Modules/permissions:** M10/M08; call scope, File access and Note create/write.
- **Exceptions/result:** missing/ambiguous recording, rate/budget limit, worker/provider error and relink require explicit states; never auto-publish unreviewed text.
- **Status:** DEMO path/source implemented; real provider and recording acceptance pending.

```mermaid
sequenceDiagram
  actor S as Sales
  participant A as AI Summary API
  participant W as Queue Worker
  participant P as BeeKnoee
  participant N as DoubleT Note
  S->>A: Generate(call)
  A->>W: enqueue source_key
  W->>P: transcription + analysis
  P-->>W: transcript/summary/needs/steps
  W-->>A: Ready/Error
  S->>A: review + Save next steps
  A->>N: upsert unique source_call_log
```

<a id="wf-07"></a>
