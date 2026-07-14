# Arctellis Design System

The visual and verbal brand system for Arctellis. Teal grounds every surface; azure carries the single live signal; the north-pointing chevron and monospace figures do the rest.

## Contents

| Section | Covers |
|---|---|
| **01 Colour** | Teal-led palette, copyable hex values, "azure = live signal only" usage rules |
| **02 Typography** | Hanken Grotesk + JetBrains Mono specimens, weights, full type scale |
| **03 Logo** | Primary + reversed lockups, the mark, clear space, minimum sizes, misuse |
| **04 Iconography** | Chevron construction (path + gradient) and the motif in use |
| **05 Voice & Tone** | Principles, do/don't examples (UK English, no em-dashes), signature lines |

## Core palette

| Token | Hex | Use |
|---|---|---|
| `--teal-ink` | `#1F4A57` | Primary, CTAs, logo base |
| `--ink` | `#14323D` | Headings, strongest text |
| `--azure` | `#34A6EB` | Live signal, active states, checks — one element per view |
| `--ground` | `#F6F8F8` | Page background |
| `--surface-2` | `#EEF3F3` | Alternating section surface |
| `--border` | `#DCE5E5` | Hairline rules |
| `--body` | `#46585D` | Body copy |

**Type:** Hanken Grotesk (display + body, 400–800) · JetBrains Mono (figures, labels, eyebrows).

## Repository layout

```
.
├── index.html                     # Built standalone — open directly in any browser, works offline
├── src/
│   ├── Arctellis Design System.dc.html   # Editable source (Design Component)
│   ├── support.js                 # DC runtime
│   └── assets/                    # Logo lockups (light + reversed)
└── README.md
```

## Usage

- **View it:** open `index.html` in a browser. No build step, no server.
- **Edit it:** the source of truth is `src/Arctellis Design System.dc.html`. After editing, regenerate `index.html` as a single self-contained file.
- **Copy values:** every colour chip in the Colour section copies its hex to the clipboard on click.

## Conventions

- UK English throughout.
- No em-dashes: use a comma or a full stop.
- Azure is a signal, never decoration. If it is everywhere, it means nothing.

---

Arctellis Design System · v1.0 · © 2026 TrustPredict Ltd
