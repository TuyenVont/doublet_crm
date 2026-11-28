# Contact Center QA and integration

## Calls and recording demo

The Calls queue and Call Logs use the same Call Log and handling history. Managers can assign and transfer calls. The assignee can start, process a callback and resolve an assigned call. Create the callback twice from a missed call and verify that the same DoubleT Task is returned. Choose a due date when opening or reopening a task. A new task defaults to the end of the current day in the site timezone. Check that the date survives a handover. Review the customer link and the history with a manager and an assigned Sales User. An unrelated user should be unable to open the call or its private attachment.

Run `bench --site <qa-site> execute doublet_crm.calls_demo.seed_recording_demos` as Administrator to preview the two bundled demos. It reads both WAVs and the manifest from `demo_audio/DoubleT_Call_Demo_Audio`. For a bench with the assets in a separate directory, pass absolute `incoming_wav_path`, `outgoing_wav_path` and `manifest_path` values through `--kwargs`.

After verifying the target and the preview, run again with `--kwargs '{"preview_only":false,"confirmation":"<phrase from the preview>"}'`. Repeating the command reuses the two Call Logs and their private WAV and manifest Files. The fixed demo IDs and marker guard updates to existing demo rows. The Call Log duration is rounded to whole seconds and the end time uses the actual WAV length.

In **Call Logs**, find the **Calls Recording Demo Incoming** and **Calls Recording Demo Outgoing** customers. Play the WAV and select **View demo summary** to open the **AI Call Assistant**. The DEMO label identifies output loaded from the private manifest. Expand **Transcript**, review **Summary** and **Customer Needs**, then edit the suggested **Next Steps** before selecting **Save to Notes**. Reopen the call to see the saved text. The note also appears under the linked customer’s Notes.

Saving requires access to the call, its assistant, the linked customer and the existing Notes create or write permissions. A call has one follow-up note. The original customer link is retained if the call is subsequently relinked. Review the existing note before saving to a different customer. The shared note contains only the next steps explicitly saved by the employee.

The optional unique `DoubleT Note.source_call_log` field links the follow-up to its source. The release migration adds this field alongside the Zalo workflow schema. Existing Notes require no backfill.

### LIVE telephony and BeeKnoee

- Register an authenticated integration with the `Call Log API` role for `doublet_crm.api.create_call_log`. Map call ID, direction, outcome, start/end times, agent and caller/callee numbers from the vendor event. Use ISO 8601 timestamps with an offset. Use a stable `external_call_id` for retries. Confirm which vendor events are final and how late events and recording arrival are handled before enabling the webhook.
- Normalize phone numbers before matching. The Call Log can match a unique Lead or Contact; let an authorized handler choose the CRM record when matches are ambiguous. Test incoming, outgoing, missed and repeated events on QA with a vendor test account.
- Store recordings as private Files attached to the intended Call Log. Use a format recognized by both the app and the provider, with WAV PCM supported by the demo. The AI path accepts up to 25 MB and requires a readable, unambiguous private recording.
- Configure `doublet_beeknoee_api_key`, `doublet_beeknoee_base_url` (HTTPS), `doublet_beeknoee_stt_model` and `doublet_beeknoee_model` as protected site settings or their `DOUBLET_BEEKNOEE_*` environment equivalents. Verify that the credential can access both transcription and chat completion models. Configure the default queue worker and ensure authorization to send the recording to the provider.
- Generate or Regenerate on QA using a non-demo recording. Confirm Queued, Processing, Ready and Error states and assignee permissions after a handover. Missing credentials, a missing or ambiguous recording, a stopped worker, and provider/model errors require different checks. LIVE telephony and BeeKnoee require their own evidence.

## Zalo OA MOCK

1. As a System Manager on QA, POST `doublet_crm.zalo_oa.receive_mock_text` with a synthetic `oa_id`, `external_user_id`, unique `external_message_id`, `content`, and ISO 8601 `sent_at` with an offset. Replay the same event and compare the returned conversation/message IDs.
2. Open **Contact Center → Inbox**. Find the new conversation by external user ID. It starts in **Waiting** as **Unidentified Customer**. Use **Link Customer** to search Lead or Contact and verify the CRM record ID, OA and Zalo user before saving, or **Create Lead** with an account that has Lead create permission. Existing Lead links remain on their historical threads. Record tabs show the same history, subject to CRM and conversation permissions.
3. Assign the conversation. Sign in as the assignee, accept and save a mock reply. Check **First response**, the Needs reply/Replied filter and the record tab. First response is measured from the first inbound in the initial exchange. Consecutive inbound messages keep the same outstanding start time until an outbound reply. Missing timestamps can leave durations blank. In **Needs reply**, known waits are ordered oldest first.
4. Transfer the conversation as Manager with a reason. Verify the previous assignee loses access, the new assignee can accept, and the handling history shows actor, assignees, reason and time. Resolve the conversation and verify that a newer inbound event reopens it. Switch the handling status filter independently of the reply filter.
5. Repeat on a narrow viewport. Use **Conversations** to return to the list and **Customer details** to inspect the selected CRM record. The Inbox header and composer identify the flow as MOCK.

A Sales User sees assigned conversations only. A Sales Manager or System Manager can monitor and assign them. Editing the customer link requires read access to the selected CRM record. Changing an existing link requires a manager and a reason. Both mock reply endpoints accept `request_id`; clients must reuse that value and the same text when retrying an ambiguous response. The web composer supplies it automatically.

### LIVE Zalo OA

- Register the app and OA, authorize the message scopes, and keep OA credentials and token renewal in protected server settings. Subscribe the OA to the appropriate events. Confirm the signing procedure, replay checks, delivery policies and outbound messaging eligibility against [Zalo for Developers](https://developers.zalo.me/docs).
- Add a separate verified inbound webhook and outbound delivery integration before enabling LIVE. Bind announcements to the authenticated OA. Map a conversation by source, OA ID and external user ID. Deduplicate inbound by source, OA and external message ID. Link the CRM record explicitly. A live outbound implementation needs a durable send request key and provider delivery state so a timeout can be reconciled before retrying.
- On QA, verify signature rejection, invalid and expired tokens, token renewal, retry after disconnect, cross-OA isolation and provider-confirmed delivery. The current Inbox persists simulated replies to shared history. Live Zalo delivery has not been exercised here.

## Migration and rollback

The Zalo schema adds optional fields on DoubleT Conversation and adds the DoubleT Conversation Event audit DocType. Historical messages and Lead links need no backfill. An unset handling status reads as Waiting. Existing unassigned threads enter the manager queue and become visible to a Sales User on assignment. Existing site Custom DocPerm rules should be checked for the two Zalo DocTypes.

Before release, use a separate QA database and asset volume to verify full migration and run the backend and browser scenarios. Back up the target database, public and private files and protected site configuration. Check the backup checksums and the previous source/build revision. Restore the matching database, files and assets together on rollback. If users have processed real work after the upgrade, preserve a separate post-change backup and reconcile those records before restoring an older database. A rollback drill on QA is required before approving a production release.

### Docker release rehearsal

Use a production snapshot on an isolated QA database. Confirm that the restored site's database host belongs to QA, pause its scheduler and mute email before starting it. Run full `bench --site <qa-site> migrate` with the exact candidate source. Compare counts and hashes for pre-existing columns on business tables and compare attachment hashes before creating test fixtures. Restore the verified pre-migration backup into a separate QA schema and validate that it opens with the previous source and its matching assets.

Build the reviewed source revision in a staging directory. Package the generated `doublet_crm/public/frontend` and `doublet_crm/www/doublet_crm.html` with the same backend and `demo_audio` directory. Record the commit SHA and generated entrypoint hashes. For a production cutover, confirm both the Python import and the asset link resolve via the selected release directory. Use the existing Docker bench cutover procedure to stop accepting writes, check active jobs and take or revalidate the final backup before moving the app link. Start service only when schema, code and assets match.
