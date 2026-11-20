# Demo GIF capture script

The README demo is currently a **static preview** (`assets/demo.svg`) of a real audit run. This file explains how to record the real animated GIF (`assets/demo.gif`) to replace it. Do not fake a GIF with a still image or a slideshow.

## What to record

One command, one result — the same real run shown in the static preview:

```bash
python3 cookie_security_checker.py https://github.com
```

Expected content: score 84/100, grade B, 3 findings. If GitHub's live cookies change, re-run and use the fresh output; do not edit the numbers by hand.

## Recording setup

- Terminal size: **100 columns x 28 rows**
- Theme: any dark theme with a readable monospace font (for example, JetBrains Mono or Cascadia Code, 14pt)
- Length: **under 15 seconds** (type the command, wait for the result, hold 2 seconds, stop)
- Clear the terminal first (`clear`) so the recording starts clean

## Option A: asciinema + agg (recommended, Linux/macOS)

```bash
pip install asciinema
asciinema rec -c "python3 cookie_security_checker.py https://github.com" demo.cast
# Convert the recording to a GIF (agg: https://github.com/asciinema/agg)
agg demo.cast assets/demo.gif
```

## Option B: VHS (scripted, reproducible)

Save this as `demo.tape` and run `vhs demo.tape`:

```text
Output assets/demo.gif
Set Shell "bash"
Set FontSize 14
Set Width 1000
Set Height 560
Set Theme "Dracula"
Hide
Type "python3 cookie_security_checker.py https://github.com"
Enter
Sleep 3s
Show
```

## Option C: ScreenToGif (Windows)

Record the terminal window with [ScreenToGif](https://www.screentogif.com/), trim to the command and its output, and export as GIF.

## Optimizing under 5 MB

```bash
gifsicle -O3 --colors 128 assets/demo.gif -o assets/demo.gif
```

If it is still over 5 MB, shorten the hold time at the end, reduce the terminal to 80x24, or drop the frame rate in the recorder settings. Never crop out the score line or the findings to save space.

## After recording

1. Save the GIF as `assets/demo.gif` (PNG/GIF files cannot be pushed through the GitHub connector — upload it through the GitHub website).
2. In `README.md`, replace the static preview image with `![Demo](assets/demo.gif)` and remove the "static preview" note.
3. Delete `assets/demo.svg` only after the GIF is live and rendering.
