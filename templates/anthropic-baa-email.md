# Anthropic BAA request — email draft

Send to: **sales@anthropic.com**
Subject: **BAA request — TriStar PT (HIPAA covered entity, outpatient PT)**

Optional CC: your account executive if you have one assigned.

---

## Email body

> Hi Anthropic team,
>
> I'm [Your Name], [your title] at TriStar PT, an outpatient physical
> therapy group operating eight clinics across [state(s)]. We're a HIPAA
> covered entity and would like to start the Business Associate Agreement
> process so we can use Claude on protected health information.
>
> **What we'd like to do with Claude:**
>
> - **Internal developer tooling via Claude Code** (Enterprise plan): a small
>   engineering team is building internal plugins for billing audits, KPI
>   reporting, and EMR data quality. Some of these will read claim-line and
>   visit-level data that contains PHI.
> - **Workforce productivity via Claude.ai** (Enterprise plan): clinical and
>   administrative staff using Claude for drafting policies, training
>   materials, denial-letter analysis, and similar non-clinical work. Some
>   of this incidentally touches PHI (e.g. a denied-claim narrative).
> - **Possible future API integration**: lightweight tools and automations
>   driven through the Anthropic API.
>
> **Estimated scale (year 1):**
> - Claude Code seats: ~[N] developers / contractors
> - Claude.ai seats: ~[M] clinical/administrative staff
> - API usage: small but non-zero (internal automations)
>
> **Decision timeframe:** we'd like to have BAA, plan, and provisioning in
> place within [X] weeks so we can start on real data instead of synthetic
> datasets.
>
> **Open questions for your team:**
>
> 1. Confirm BAA coverage scope — does Anthropic's standard BAA cover
>    Claude Code, Claude.ai (Team/Enterprise), and direct Anthropic API
>    usage on a single agreement?
> 2. What plan tier(s) are required for BAA eligibility on each surface?
> 3. Required disclosures or prerequisites from our side
>    (Privacy Officer contact, HIPAA risk assessment status, etc.).
> 4. Typical timeline from request to countersigned BAA.
> 5. Do you offer onboarding support for first-deployment HIPAA configurations
>    (managed-settings allowlists, audit-log exports, access reviews)?
>
> Happy to jump on a call. Best contacts on our side:
>
> - **Decision owner:** [Owner name], [title], [email]
> - **Privacy Officer:** [Privacy Officer name], [email]
> - **Technical lead:** [Engineering lead name], [email]
>
> Thanks,
>
> [Your Name]
> [Your title]
> TriStar PT
> [Phone]

---

## Substitution checklist

Replace before sending:

- [ ] `[Your Name]`, `[your title]`
- [ ] `[state(s)]` — primary operating state(s)
- [ ] `[N]` — Claude Code seat count
- [ ] `[M]` — Claude.ai seat count
- [ ] `[X]` — target weeks-to-execution
- [ ] Decision owner / Privacy Officer / Technical lead names + emails
- [ ] `[Phone]` — direct line

## What to do with the response

When Anthropic responds:

1. Forward the BAA draft to your healthcare attorney for review.
2. Once countersigned, file under `policies/baa/anthropic-<YYYY-MM-DD>.pdf`
   (the `policies/baa/` directory is intentionally not created in source —
   create it at sign-time as part of the records inventory).
3. Update the BAA section of `policies/01-acceptable-use-of-ai-coding-tools.md`
   with the executed date.
4. Coordinate with IT to flip `ANTHROPIC_BAA_SIGNED=true` in
   `config/managed-settings.json` and roll out via MDM.
5. Notify the workforce that PHI-touching surfaces are now permitted, with
   the standing reminder that the Acceptable Use Policy still applies.

## Talking-points reference (for follow-up calls)

If sales asks for context that didn't fit in the email, lead with these:

- **Operational scale:** 8 clinics, ~[total visits/week] visits, ~[therapist count] FTE.
- **EMR / PM system:** [vendor name].
- **Clearinghouse:** [vendor name].
- **Existing BAAs:** [count] (with EMR vendor, clearinghouse, billing, etc.).
- **Why now:** [the specific operational pain point that pushed this — e.g. denials, productivity reporting, or a recent audit finding].

Keep the first email short and focused on the ask. Save the operational
detail for follow-ups so they have what they need to scope the right plan.
