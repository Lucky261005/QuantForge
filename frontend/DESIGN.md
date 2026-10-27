# QuantForge design

## Brief
- Subject: QuantForge, a research and backtesting platform for NSE/BSE equities and indices.
- Audience: retail quants, students and small research desks in India who code or think in rules.
- Job: get a visitor to open the demo desk or create an account; inside the app, read numbers fast.
- Scope: the marketing site (home, 404, auth) gets the full treatment; the app
  (dashboard, backtests, etc.) is re-skinned through the shared tokens, fonts and shell.
- Assumptions: no real customers, no performance claims. Every number on the public site is
  either a product fact (17 indicators, 21 strategies, 124 tests) or computed from the backend's
  own charge model (`backend/app/backtesting/charges.py`).

## Concepts
| | Idea | Anchor | Signature | O/F/Fe/P |
|---|---|---|---|---|
| A. Place | The home page is one NSE session: scrolling runs the clock from pre-open 09:00 to the 15:30 close, each section is a time of day | NSE cash-market hours, IST | a vertical session rail draws the day's price path and ticks the IST timecode as you scroll | 4 / 5 / 4 / 2 |
| B. Material | The page is a contract note: every claim is a line item that settles into a net figure | the Indian charge model the engine implements | rows print in and a gross figure shrinks to net | 4 / 4 / 5 / 2 |
| C. Formal | Everything is a ticker board: one line of condensed caps per idea | exchange LED boards | lines flip like split-flap boards | 3 / 3 / 4 / 4 |

Pick A: it structures the whole page (and the app's market clock), and B survives as the
midday section, where the contract note is real math. The 404 steals from A: a market holiday.

## Concept card
```
Idea:        Test a strategy the way a trading day runs: from pre-open to the close.
Metaphor:    one NSE trading session, 09:00 to 15:30 IST.
Signature:   the midday contract note: charge rows print in and settle on the ₹222.21 total.
Emotion:     the calm focus of the minutes before the bell.
Motion verb: tick. Things advance in short, exact steps, like a price on a tape.
Screenshot:  the contract note settling on ₹222.21.
```

## System
- Palette "Ledger" (dark is the default on first visit; light via the toggle):
  - light: ground `#F1F3EF` cool paper, surfaces `#FFFFFF`, ink `#13201B` green-black, muted `#57615C`,
    lines ink at 12%, accent petrol `#0B5F6B` (ledger ink). Accent only for primary action, links,
    focus and the session tick.
  - dark: ground `#0E1517` petrol-black, surfaces `#151D20`, ink `#E6ECE9`, muted `#98A39F`, accent `#47BEC3`.
  - up `#19703D` / `#45C27A`, down `#B6312A` / `#EC6A5E`: only for real market direction, kept clear of the petrol accent.
- Type: Archivo at normal width. Display is weight 600, tracking -0.03em, leading 1.0, and capped:
  hero and closing 2.5 to 4.75rem, section headings 1.875 to 2.75rem, auth headings 1.875rem.
  Body 16px. Geist Mono for numbers, times and tickers, tabular.
- Grid: 12 columns, 24 px gutter, 16 px side gutter on phones. Section rhythm varies: poster hero, index list, two-column note,
  word wall, closing poster.
- Shape: 8 px radius on panels and buttons.
- Motion: one ease (`power3.out` / `cubic-bezier(.2,.7,.2,1)`), 0.5 s for type, 0.25 s for UI.
  Hover on primary targets: the label ticks up one line (inner span roll). Buttons invert to label color.
- Idle state: the IST clock in the nav ticks every second (real information); the instrument tape scrolls.
- Reduced motion: no Lenis, no scrub, no tape movement; all text visible.

## Genericness test
- The old site was a centered hero over a purple-blue mesh with glass cards and a fake
  ₹28 lakh equity curve. All three removed; the fake numbers are replaced by the real charge
  computation.
- Three equal feature cards became a timed index list, because the pipeline is a real sequence.

## Changes
- The session rail (desktop timeline and phone tape) was removed at the owner's request.
