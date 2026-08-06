# 02c — Add Program UI

## Goal

A form to create a new authorized program (target + scope), so real targets
can be registered without editing seed.py or calling the API by hand.
`POST /programs` already exists from Phase 1 — this phase only adds the
missing UI on top of it.

## Deliverables

- `dashboard/app/programs/new/page.tsx` — form with fields:
  - **name** (text, required)
  - **base_url** (text, required — e.g. `https://acme.example`)
  - **in_scope_domains** (repeatable text input — start with one field and
    an "Add another domain" button, or a comma-separated input if simpler)
  - **scope_notes** (textarea, optional — e.g. "use test accounts only,
    do not impact availability")
- On submit: `POST /programs` with the above, then redirect to
  `/programs` on success.
- Add an "Add Program" button/link on the existing `programs/page.tsx`
  linking to this new page.
- Client-side validation: reject empty `name`/`base_url` before submit;
  show the backend's validation error message if the request fails
  (e.g. duplicate name).
- Match existing Tailwind styling conventions (per `02b`).

## A note on scope, not just UI

This form is the only place new scope gets defined, so whatever gets typed
into `in_scope_domains` becomes something the scanner is allowed to touch.
No code enforcement is needed here beyond normal form validation — this is
a reminder for whoever is using the form: only add domains you are actually
authorized to test.

## Out of scope for this phase

- Editing or deleting existing programs (fine to add later; not needed to
  unblock Phase 3)
- Any scope-format validation beyond "not empty" (e.g. matching against a
  real DNS check) — out of scope for a student project

## Done when

- A new program created through this form appears on `/programs`
- The same program is selectable in the Home page's scan-trigger dropdown
  without a page refresh issue (i.e. the dropdown re-fetches or the app
  navigates in a way that picks up the new data)
