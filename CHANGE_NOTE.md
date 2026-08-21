# CyberCrypt UI — Master Prompt Change Note

This note maps every code change back to the three named root-cause bugs
plus the structural mandates in the master prompt. Core engine, analysis,
presentation, viva, and the 54 unit tests were **not** touched.

---

## Bug 3 — `GlassCard._args` not bound to self  (hover AttributeError)

**Symptom.** Hovering any glass card raised `AttributeError` because
`_raise_card()` called `self._args(...)`, but `_args` was a local closure
inside `__init__` and was never stored on the instance.

**Fix — `cybercrypt/ui/widgets.py` (`GlassCard`).**
- Line ~126: store the closure — `self._args = _args`.
- Added `relocate(relx, rely, relwidth, relheight)` (line ~151) so a card
  can be moved/resized by resize handlers without re-creating it. It
  re-applies `place(**self._args(...))` to both shadow and panel.
- AST audit of the whole `ui/` tree for the same local-closure-used-as-
  `self.<name>` pattern came back clean.

**Verified.** The probe generates real `<Enter>`/`<Leave>` events on every
mapped widget across all screens at three window sizes — zero exceptions.

---

## Bug 2 — `x=0.63` instead of `relx=0.63` in decrypt  (columns overlap)

**Symptom.** `decrypt_screen.py` placed the keys/details/actions column
with `x=0.63`, which Tk interprets as 0.63 **pixels** — so the right
column sat on top of the left input column.

**Fix — `cybercrypt/ui/screens/decrypt_screen.py`.**
- `_relayout()` now places every card with `relx`/`rely`/`relwidth`/
  `relheight` fractions: left column `relx=0` (input 0.25 / pipeline 0.29
  / output 0.20 of width 0.60), right column `relx=0.63` (keys 0.46 /
  details 0.235 / actions 0.073 of width 0.37).
- A post-fix scan for `place(x=<float>)` across the whole `ui/` tree came
  back clean — every remaining `x=` is an integer pixel offset.

---

## Bug 1 — layout math on pre-`map` size  (4000% buttons, off-screen cards)

**Symptom.** `dashboard_screen.py` ran its layout at construction time,
dividing by `winfo_height()` which is **1** before the window is mapped.
Result: hero buttons computed at ~4000% height, stat cards at
`rely ≈ 150–200` (far below the screen).

**Fix — `cybercrypt/ui/screens/dashboard_screen.py`.**
- All positioning moved out of `_build_*` and into a `_relayout()` method
  bound to `<Configure>` (debounced via `after(16, ...)`).
- Guard: `if height < 100 or not self.winfo_ismapped(): return` — so the
  method no-ops until the window reports real geometry, then re-runs on
  every resize.
- Widgets are built once and stashed on `self` (`_encrypt_button`,
  `_about_button`, `_stat_cards`, `_pipeline_card`, `_layer_cards`), and
  `_relayout()` just re-places them.

**Same relayout pattern applied to** `encrypt_screen.py`,
`decrypt_screen.py`, and `presentation_screen.py` for consistency and
resize-correctness.

---

## Structural mandate — no pixel args that ctk re-scales

**Found during verification.** On high-DPI (1.5× here, root window
1920×1140 logical 1280×720), `CTkFrame.place()` multiplies pixel `x`/`y`
by the widget scaling factor. Passing a winfo-derived pixel (e.g.
`y=761`) placed the widget at 761×1.5 ≈ **1141** — off the bottom of
the 912-tpx-tall presentation control bar.

**Fix.**
- `dashboard_screen.py` `_relayout()`: `y=content_top` → `rely=content_top
  / height`; `x=round(0.205 * width)` → `relx=0.205`. Removed the now
  unused `width = self.winfo_width()` read.
- `presentation_screen.py` `_relayout()`: `y=bar_top` → `rely=bar_top /
  height`. The bar now lands exactly at screen bottom (761 + 151 = 912).
- `encrypt_screen.py` / `decrypt_screen.py` were already correct: they
  use `rely=(top + round(frac*height) + gap) / height`, where the scaling
  cancels in the ratio, plus plain `relx` fractions.

**Rule going forward.** Every `place()` call in `ui/` now uses only
`relx`/`rely`/`relwidth`/`relheight` (fractions 0–1). The only integer
pixel `x=`/`y=` remaining are inside fixed-aspect children (card
medallions, labels) where the value is a small constant that does not
derive from `winfo_height()`.

---

## Verification results

| Check | Result |
|---|---|
| `python -m compileall -q cybercrypt` | clean |
| `python -m pyflakes cybercrypt main.py run_tests.py tests` | clean |
| `python run_tests.py` (54 tests) | **54/54 OK** |
| UI probe — global exception trap, widget-tree geometry walk, real hovers, encrypt→decrypt round trip, analysis exports, presentation all-slides + autoplay, viva toggles, resize to 1180×760 and 1400×900 | **63/63 passed**, 0 trapped exceptions |
| smoke_phase3 (shortcuts / tooltips / round trip) | **25/25** |
| smoke_phase4 (analysis dashboard + exports) | **38/38** |
| smoke_phase5 (architecture + viva + guide) | **28/28** |
| Screenshots | saved to `ccp_shots_*` (every screen at default + min size) |

Engine, analysis, presentation, viva, and all tests are unchanged. Lazy
screen construction and the Ctrl+Enter / Ctrl+Shift+Enter / Ctrl+C
shortcuts are preserved (confirmed by smoke_phase3).
