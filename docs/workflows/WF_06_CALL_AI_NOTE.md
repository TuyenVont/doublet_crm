# WF-06 — Recording → AI Call Summary → Note

[← Danh sách workflow](README.md) · [Feature 1](../features/contact-center/CALLS.md) · [Feature 2](../features/activities/NOTES_TIMELINE.md)

- **Scenario/Actors:** authorized handler opens a marked DEMO or requests LIVE Generate/Regenerate; employee reviews next steps.
- **Preconditions/Input/Output:** DEMO requires matching private manifest/recording and never calls provider; LIVE requires one readable private recording ≤25 MB plus protected provider config. Output is displayed summary and at most one linked Note.
- **Modules/permissions:** M10/M08; call scope, File access and Note create/write.
- **Exceptions/result:** missing/ambiguous/stale recording, rate/budget limit, worker/provider error, handover/relink và stale Note version require explicit states; never auto-publish unreviewed text. `source_call_log` prevents duplicate Notes.
- **Contract:** [BF-08 AI Summary → reviewed Note](../architecture/BUSINESS_FLOW_CONTRACT.md#bf-08--ai-summary--reviewed-note). Note giữ original source/customer provenance; không tự chuyển sang Company/Deal khi Call được relink.
- **Status:** DEMO and LIVE source branches implemented; automated test exists but was not run here. Real provider/recording/browser acceptance pending.

```mermaid
sequenceDiagram
  actor S as Sales
  participant A as AI Summary API
  participant W as Queue Worker
  participant P as BeeKnoee
  participant N as DoubleT Note
  alt marked DEMO
    S->>A: Open demo assistant
    A-->>S: manifest sample, no queue/provider
  else LIVE
    S->>A: Generate(call)
    A->>W: enqueue source_key
    W->>P: transcription + analysis
    P-->>W: transcript/summary/needs/steps
    W-->>A: Ready/Error
  end
  S->>A: review + Save next steps
  A->>N: upsert unique source_call_log
```
