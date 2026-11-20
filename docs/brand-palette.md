# Brand palette

Original palette for Cookie Security Checker. Used by `assets/banner.svg`, `assets/logo.svg`, and `assets/demo.svg`.

| Role | Name | HEX | Used for |
| --- | --- | --- | --- |
| Primary | Deep navy | `#0B1F3A` | Backgrounds, headings on light surfaces |
| Accent | Teal | `#2DD4BF` | Highlights, links, shield and icon fills |
| Neutral (light) | Off-white | `#F8FAFC` | Text on dark backgrounds, light surfaces |
| Neutral (mid) | Slate | `#64748B` | Secondary text on light backgrounds |

Supporting dark shade (banner gradient only): `#0F2A4A`. Light tint of slate for small text on dark backgrounds: `#94A3B8`.

## WCAG AA contrast checks

Checked with the standard relative-luminance formula. AA requires 4.5:1 for normal text and 3.0:1 for large text.

| Pair | Ratio | AA normal text (4.5:1) | AA large text (3.0:1) |
| --- | --- | --- | --- |
| White `#FFFFFF` on primary `#0B1F3A` | 16.52:1 | Pass | Pass |
| Teal `#2DD4BF` on primary `#0B1F3A` | 8.87:1 | Pass | Pass |
| Primary `#0B1F3A` on off-white `#F8FAFC` | 15.79:1 | Pass | Pass |
| Slate `#64748B` on off-white `#F8FAFC` | 4.55:1 | Pass | Pass |
| White `#FFFFFF` on banner shade `#0F2A4A` | 14.48:1 | Pass | Pass |
| Teal `#2DD4BF` on banner shade `#0F2A4A` | 7.78:1 | Pass | Pass |
| Slate `#64748B` on white `#FFFFFF` | 4.76:1 | Pass | Pass |

All pairs pass WCAG AA for normal text. Do not use slate `#64748B` for small text on dark backgrounds — use the `#94A3B8` tint or off-white instead.
