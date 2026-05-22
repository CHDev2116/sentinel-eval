# Demo assets (proposals & client decks)

Place **short GIF or MP4** recordings here for business READMEs and slide decks. **Bundled SVG previews work without any extra installs** — including on machines without Homebrew.

## Recommended recordings (~30 seconds each)

| File | Command / content | Audience message |
|------|-------------------|------------------|
| `sentinel-eval-smoke.gif` | `sentinel-eval --model llama3.1:latest --quiet` | Fast, local, no cloud upload |
| `sentinel-eval-full.gif` | `sentinel-eval --all --quiet` | Full golden run + summary lines |
| `release-gate-fail.gif` | `sentinel-eval --all --release-gate` (exit 1) | **Deploy blocked** when cases fail |
| `leaderboard.gif` | `sentinel-leaderboard` after register | Compare models before rollout |
| `expand-surfaces.gif` | `sentinel-eval --limit 5 --expand-surfaces` | Same attack, many packaging forms |

## How to record (no Homebrew required)

### Option A — Screen recording (simplest)

1. Run the demo in Terminal (dark theme, ~100 columns wide).
2. Record the window:
   - **macOS:** QuickTime → File → New Screen Recording, or **Shift+Cmd+5**
   - **Windows:** Win+G (Xbox Game Bar) or Snipping Tool video
   - **Linux:** GNOME Screenshot / OBS
3. Convert to GIF (optional) if you have **ffmpeg** anywhere on PATH:

```bash
ffmpeg -i recording.mov -vf "fps=12,scale=1280:-1:flags=lanczos" docs/demos/sentinel-eval-smoke.gif
```

### Option B — asciinema + agg (terminal → GIF)

Install tools via **pip** or your OS package manager — not only Homebrew:

```bash
# pip (works in project venv)
pip install asciinema
# agg: https://github.com/asciinema/agg — download release binary or:
pip install agg  # if available on your platform

asciinema rec /tmp/sentinel.cast
# run: sentinel-eval --model llama3.1:latest --quiet
# exit recording with Ctrl+D

agg /tmp/sentinel.cast docs/demos/sentinel-eval-smoke.gif --theme monokai
```

**Linux packages:** `sudo apt install asciinema` (agg may still be a binary download).

### Option C — Skip GIF for now

Use the **animated SVG previews** linked from [BUSINESS_README.md](../BUSINESS_README.md). Clients viewing GitHub or exported PDFs still see motion in many viewers.

Keep terminal font ≥14pt and dark background to match bundled previews.

## Bundled previews (no install required)

| Asset | Description |
|-------|-------------|
| [demo_run_animated.svg](demo_run_animated.svg) | Staged terminal smoke output |
| [attack_before_after.svg](attack_before_after.svg) | Missed vs caught injection |
| [leaderboard_preview.svg](leaderboard_preview.svg) | Model comparison bars |

## Architecture PNG (optional)

```bash
# From repo root — tries rsvg, Inkscape, macOS qlmanage, or Python cairosvg
./scripts/export_business_diagram.sh
```

**macOS without brew:**

```bash
qlmanage -t -s 2200 -o docs/diagrams docs/diagrams/architecture_business.svg
mv docs/diagrams/architecture_business.svg.png docs/diagrams/architecture_business.png
```

**Or** open `docs/diagrams/architecture_business.svg` in Chrome/Safari and screenshot, or import the SVG into Slides/PowerPoint (stays vector).

## Link from proposals

```markdown
![Smoke run](https://raw.githubusercontent.com/CHDev2116/sentinel-eval/main/docs/demos/sentinel-eval-smoke.gif)
```

Replace with your fork/org after publishing recordings.
