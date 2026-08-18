# 0002 — Structured lookup prefers the earliest accession, not the latest

**Status:** accepted

## Context

The same financial fact appears in several filings. Columbia's FY2023 net
income is in the FY2023 10-K as `348,700,000`, and again in a 2026 filing as
a rounded `349,000,000`. SEC promotes the rounded one into its normalized
`CY2023` frame.

Two obvious rules both give the wrong answer against hand-verified ground
truth: "trust the most recent filing" returns the rounded figure, and "trust
SEC's normalized frame" returns the same rounded figure.

(The related bug where all three comparative years shared one period label
is a separate matter, written up in `../engineering-notes.md`.)

## Decision

`structured_lookup.py` selects the **earliest** accession that reports the
fact — the original as-filed figure — and returns the accession number
alongside the value.

## Alternatives considered

- **Latest accession.** Rejected: fails the verified ground truth on the
  rounding case above.
- **SEC's normalized frame where one exists.** Rejected for the same reason,
  and it has no answer for facts SEC never assigned a frame to.
- **Return every reported value and let the caller choose.** Rejected as a
  non-decision. The router's whole claim is that a factual question gets one
  exact number with no model call; handing back a list moves the judgement
  onto a user who has less context than the system does.

## Consequences

**Accepted downside, and it is a real one.** A genuine restatement is also
filed later than the original. This rule returns the superseded figure for
one — the wrong answer, confidently, in exactly the case where being wrong
matters most for due diligence.

**Mitigation, not a fix.** Every structured answer carries the accession
number it came from, so a user can see which filing reported the number and
go check it. That converts a silent error into a visible provenance trail;
it does not prevent the error.

**When I would revisit this.** The current corpus contains no restatement I
know of, so I have optimised for the case I can verify. If one turns up, the
right answer is probably to detect disagreement between accessions and
surface both with their dates, rather than to flip the preference.
