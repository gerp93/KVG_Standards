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

## "Vibe install" mode

For apps that don't want a real package dependency (one-off scripts,
prototypes), VisualAssault also supports an AI-driven "vibe install" —
fetching `themes/THEMES.md` and transcribing one theme into a native file.
This has no version concept at all and will drift every time it's re-run
against a newer VisualAssault. Fine for throwaway/prototype work; not for
anything that will get a real release pipeline from this repo.
