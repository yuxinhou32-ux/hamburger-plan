# Hamburger Plan

**English** | [中文](README.zh-CN.md)

> Stack a new habit on something you already do every day.

A single-file PWA for habit stacking. Instead of scheduling habits at a clock time, it attaches them to events that already happen — after you get up, before lunch, after a shower. "Hamburger" is the metaphor: the fixed event is the bun, the new habit is the patty in between.

**Try it**: https://hamburger-plan.app.workbuddy.host/

Open it in Safari, then "Add to Home Screen" — it behaves like an installed app, no app store involved.

> **Which build this is**: this is the **standalone build**. Everything lives in your own browser's `localStorage`; there is no login and not a single byte is sent to any server. Consequently there is no cross-device sync — wiring one up means bringing your own backend. That is deliberate: a public online instance where anyone can sign up would bill every stranger's write to the owner.

---

## Why

Most habit apps share two flaws.

**They schedule by clock time.** "Meditate at 7:30 every morning" sounds precise, but at 7:30 you are usually doing something else, so you miss it, and the day is written off. People are bad at clock commitments and good at event cues.

**They grade you.** Streaks, completion rates, days-missed. Once you break a streak, the app becomes a place you avoid. Habits do not need a permanent record of failure — if you break one, you just pick it up again.

So the trade-off here is blunt: **event anchors instead of clock times, a record instead of a scorecard.**

## What it does

| You want to | How |
| --- | --- |
| Note the fixed events of your day | Add an **anchor**: getting up, lunch, walking in after work, showering. Pick weekdays, give a rough time (used only for ordering) |
| Attach a habit | When adding an item, choose which anchor it hangs behind; it shows up there every day |
| Do something several times a day | Type `8 cups` into "how many times a day" — it moves into a **habits** strip at the top of the Today screen, one tap per count |
| Check something off | Tap the right-hand strip of the card; no need to hit the 25px circle precisely (the whole card height counts) |
| Re-attach | Press and hold the card, drag it under another anchor; drag to "unassigned" to skip it today |
| Cheat on a busy day | Every item can carry a "minimum version" line — do only that |
| Delete | Swipe left in the overview screen, tap the red Delete |
| See how it went | Review screen: a month heat-grid (darker = more done), tap a day for details, then monthly totals for the year |
| Move to a new phone | Export a backup (`json`), restore it on the new device |
| Use offline | Add to Home Screen; the service worker caches the page, fonts and icons |

## Design decisions worth knowing

**Anchors never notify.** The real trigger is in your life — lunch, a shower — not in the notification tray. A scheduled push would quietly turn "follow the event" back into "follow the clock", which is what this app exists to avoid.

**Completed items move to a "done" section — except counted ones.** Ordinary items slide into a done area so the remaining list stays clean. But a habit counted eight times a day would have to be dragged back out eight times, so counted habits get their own strip at the top of Today and simply turn green in place when they hit the target.

**"How many times a day" is an optional field, not a second entity.** No new "habit" object, no "is this a habit or a task" switch: fill it in and the item is counted, leave it blank and it is a single check. The data model only gains `target: {times, unit}` plus a side table of daily counts; the shape of historical records is untouched.

**Counts, not completion rates.** The review screen answers "how many days this month did I do it", not "I hit 87% of my target". No streaks, no "you missed 4 days".

**The tap target is much larger than the circle.** A 25px circle demands precision; missing it by a few pixels opens the edit sheet, which is miserable on a phone. The rightmost fifth of the card, full card height, checks the box.

**Press and hold to drag.** The cards are a list first: 460ms of holding before dragging starts, so scrolling doesn't grab anything.

## Where the data lives

Entirely in the browser, in two keys:

- `hb_state` — the whole document (anchors, items, daily checks, notes)
- `hb_dirty` — a queue of pending timestamps, the hook left for a future sync layer; currently written but never consumed

Roughly 5 MB per origin, with a warning at 3 MB. Real usage is tiny: checking in costs a few dozen bytes a day, so ten years is around 100 KB — notes are what actually grows. A failed write (quota exceeded, private mode) surfaces a message instead of silently pretending the data was saved.

Because it is local-only, the data belongs to **this browser on this device**: a new phone sees nothing, another browser sees nothing, and clearing site data erases it. Hence export / import.

## Tech

- **Single file**: `index.html` (~2,900 lines of HTML, CSS and plain JavaScript — no framework, no dependencies, no build step)
- **PWA**: `manifest.webmanifest` + `sw.js`; network-first for navigations (so updates land), cache-first for fonts and icons
- **Self-hosted fonts**: every face is subset to the glyphs actually used and shipped as `woff2` in `fonts/`. No font CDN — behind a flaky network a CDN silently falls back to system fonts and you never notice
- **Animation**: checked cards slide to their new position with FLIP (measure, re-render, invert, release) rather than fading out

## Run locally

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

Service workers only run over `http(s)`, so opening the file directly with `file://` works but without offline caching.

## Layout

```
index.html              the whole app
sw.js                   service worker
manifest.webmanifest    PWA manifest
fonts/                  subset woff2 fonts
icons/                  icons
build_public.py         builds this public standalone copy from the main project
```

**`build_public.py`** exists because the development version will eventually gain cloud sync while this repository must stay cloud-free forever. So the copy is built, not hand-copied: it copies the files, rewrites the settings screen's sync row into standalone wording, then asserts there are no network calls, no external URLs and no local paths — and exits non-zero if any check fails.

## License

MIT — see [LICENSE](LICENSE).
