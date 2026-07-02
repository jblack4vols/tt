# Incident Response Addendum — AI Tools

**Policy owner:** [Security Officer]
**Companion to:** TriStar PT HIPAA Incident Response Plan
**Effective date:** [Date]

## 1. Triggering events
Treat the following as security incidents requiring immediate response:
- A plugin or AI tool sending PHI to an unauthorized destination.
- Suspected exfiltration via a malicious or compromised plugin.
- API key, token, or secret disclosed in a prompt, log, or commit.
- Unauthorized installation of a plugin or marketplace.
- AI tool used without a BAA on data the user believed was de-identified but was not.
- Bulk download or query of PHI by an AI tool outside normal patterns.

## 2. Immediate response (within 1 hour)
1. **Contain.** Disconnect the affected device from the network. Revoke the user's API tokens, SSO sessions, and GitHub access.
2. **Preserve evidence.** Capture local Claude Code logs (`~/.claude/`), OTel collector logs, GitHub audit log, EDR telemetry, and the user's recent shell history. Do not wipe the laptop.
3. **Notify.** Alert the Privacy Officer and Security Officer. Open a numbered incident in the IR tracker.

## 3. Investigation (within 24 hours)
- Determine which records were potentially exposed (use audit logs, not memory).
- Identify whether the recipient was an entity with a BAA (e.g., Anthropic) or an unauthorized third party.
- Confirm whether the data sent met the HIPAA Safe Harbor de-identification standard. If yes, this is likely not a breach.
- Document findings in the incident record.

## 4. Breach analysis
Apply the four-factor risk assessment from 45 CFR §164.402:
1. Nature and extent of PHI involved.
2. The unauthorized recipient.
3. Whether PHI was actually acquired or viewed.
4. Extent to which risk has been mitigated.

If the analysis shows a low probability of compromise is **not** demonstrable, treat as a reportable breach.

## 5. Notification obligations
- < 500 individuals affected: notify affected individuals within 60 days; log for annual HHS submission.
- ≥ 500 individuals affected: notify HHS and prominent media outlets within 60 days.
- Notify business associates and the Anthropic security contact if their tooling was involved.

## 6. Post-incident
- Root cause analysis within 14 days.
- Update the Acceptable Use Policy or Plugin Development Standard if controls failed.
- Add detection rule to OTel/SIEM to catch the same pattern faster next time.
- Workforce retraining if the cause was user error.

## 7. Tabletop exercises
Run a tabletop scenario annually using one of these prompts:
- "A contractor pasted a 1,000-row export from our EMR into ChatGPT free tier."
- "An npm dependency in a billing plugin was compromised and exfiltrated audit logs."
- "A developer pushed a `.env` file with the EMR API key to a public GitHub fork."
