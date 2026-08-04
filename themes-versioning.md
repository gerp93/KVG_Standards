# Theme versioning

[VisualAssault](https://github.com/gerp93/VisualAssault) is the single
source of truth for color themes (`themes/THEMES.md`), with generated
packages for CSS, Tkinter, Flet, and Angular.

## The rule

**Consumers pin to a tag, never `@main`.**

```
# requirements.txt — wrong, silently picks up whatever VisualAssault's tip is:
visual-assault-tkinter @ git+https://github.com/gerp93/VisualAssault.git@main#subdirectory=packages/tkinter

# right — pinned to a released version:
visual-assault-tkinter @ git+https://github.com/gerp93/VisualAssault.git@v0.2.0#subdirectory=packages/tkinter
```

Same idea for npm/CSS/Angular consumers: point at a tagged ref or a
downloaded `releases/vX.Y.Z/*.zip`, not `main`.

## Bumping a theme dependency

1. Check VisualAssault's latest tag/release.
2. Update the pinned `@vX.Y.Z` in the consumer's dependency file in one
   commit, so the version bump is reviewable on its own (not bundled into
   an unrelated feature change).
3. Re-test the app's theme picker — VisualAssault's generator is
   deterministic from `THEMES.md`, but a version bump can still add/rename
   themes.

## Go / static-asset consumers (no package manager)

Go has no npm/pip-style git-subdirectory dependency mechanism, and CSS
consumed by a plain HTTP server isn't "installed" at all — so for
[gameshell-framework](https://github.com/gerp93/gameshell-framework) (which
serves `static/css/colors.css` to every Go game via its `/gs/` mount), the
tag-pinning principle is applied by **vendoring a pinned copy** instead:

- The theme color blocks in `colors.css` are a verbatim copy of
  VisualAssault's `packages/css/themes.css` at a specific tag, marked with a
  comment noting the source tag and "do not hand-edit."
- `scripts/update-visual-assault-css.sh <tag>` re-fetches that file from a
  given VisualAssault tag and splices it back in — the deliberate,
  reviewable equivalent of bumping a pinned version string.
- This is exactly the same failure mode as `@main` if skipped: gameshell-framework's
  vendored copy was found already stale (missing tokens VisualAssault added
  after `v0.1.0`) because it was a one-time copy-paste with no re-vendor
  step, not a pinned version anyone remembered to bump.

Any other Go (or plain static-HTML) consumer should follow the same
pattern: vendor a marked, tag-sourced copy plus a re-vendor script, never a
silent hand-copy.

## "Vibe install" mode

For apps that don't want a real package dependency (one-off scripts,
prototypes), VisualAssault also supports an AI-driven "vibe install" —
fetching `themes/THEMES.md` and transcribing one theme into a native file.
This has no version concept at all and will drift every time it's re-run
against a newer VisualAssault. Fine for throwaway/prototype work; not for
anything that will get a real release pipeline from this repo.
