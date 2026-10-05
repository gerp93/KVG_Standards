# Electron application menu

Electron gives every app a default menu bar (File, Edit, View, Window,
Help) whether or not it's called for. Most of it doesn't apply to a
single-window, non-document app: **File** has nothing to open/save/print,
**Edit**'s Undo/Redo/Cut/Copy/Paste as menu-bar items duplicate what native
text inputs already do via keyboard shortcuts, and **Window** (Minimize/
Zoom/bring-all-to-front) is multi-window chrome for an app that only ever
has one window. Shipping that default isn't neutral — it's a discoverable
surface that answers nothing a user of the app actually needs, plus it
leaks dev-only items (Reload, Force Reload, Toggle DevTools) into shipped
builds unless explicitly excluded.

**The rule:** replace the default with an explicit
`Menu.buildFromTemplate([...])` (via `Menu.setApplicationMenu`) that keeps
only what the app actually uses. In practice that's usually just:

- **View** — `reload`/`forceReload`/`toggleDevTools` gated behind
  `!app.isPackaged` (so they exist in dev, vanish from shipped builds
  without a separate build-time branch), zoom in/out/reset, and
  `togglefullscreen`.
- **Help** — a link to the GitHub repo, a link to file an issue, and a
  disabled `Version X.Y.Z` line for at-a-glance support info. Add an
  in-app "Guides & FAQ" entry too if the app has one.
- **macOS only** — the conventional `{ role: 'about' }` / services / hide /
  quit app-name menu Electron expects as the first template entry on that
  platform (`process.platform === 'darwin'`). Don't ship this on
  Windows/Linux — it's a macOS UI convention, not a cross-platform one.

No File, Edit, or Window entries at all, unless the app genuinely needs
one (a real multi-document app would keep File; a real multi-window app
would keep Window). Removing Edit means losing the *menu-bar* discoverability
of Cut/Copy/Paste/Select All — recover that with a right-click context menu
instead (see below), not by keeping the Edit menu around just for that.

## Reference implementation

[gerp93/RolePlaymate](https://github.com/gerp93/RolePlaymate)'s
`src/main/main.ts` (`setupApplicationMenu`) is the origin of this pattern —
copy its shape rather than reinventing it:

- A `ZOOM_IN_ITEMS` array with three entries bound to the same handler
  (`CmdOrCtrl+=`, `CmdOrCtrl+Shift+=`, `CmdOrCtrl+numadd`) because
  Electron's built-in `zoomIn` role only binds the first accelerator —
  Ctrl/Cmd+Shift+= (the physical `+` key on most keyboards) and the numpad
  `+` need their own, `visible: false` so they don't show as duplicate
  menu rows.
- `isSafeExternalUrl` gating every `shell.openExternal` call (only
  `https:`/`http:` — a `file:` or shell-handler URL reaching that call
  would otherwise be opened by the OS with whatever application claims
  it).
- `attachContextMenu(win)` on the `context-menu` webContents event: builds
  a `Menu` from `params.isEditable`/`params.editFlags`
  (cut/copy/paste/selectAll, each only if that flag says it's actually
  available) plus spellcheck suggestions/`Add to dictionary` when
  `params.misspelledWord`/`params.dictionarySuggestions` are present. This
  is what makes dropping the Edit menu safe — right-click still reaches
  the same actions.

[gerp93/Bracketeer](https://github.com/gerp93/Bracketeer)'s
`src/main/menu.ts` is a second, minimal adopter (no in-app "Guides & FAQ"
entry, since it has no in-app help route) — a smaller reference if
RolePlaymate's chat/lorebook-specific surface area is more than you need to
read through.

## Violations to flag

- An Electron app repo with no `Menu.setApplicationMenu` call at all
  (running on Electron's default menu — check `src/main/main.ts` and any
  `src/main/menu.ts` for the call, not just for a `Menu` import).
- A custom menu that still includes File, Edit, or Window entries without
  a stated reason the app actually needs them (a comment or obvious
  document/multi-window feature justifying it).
- Dev-only items (`reload`/`forceReload`/`toggleDevTools`) present in a
  packaged build — these must be gated behind `!app.isPackaged`, not
  shipped unconditionally.
- An Edit menu kept around *solely* to expose Cut/Copy/Paste/Select All,
  instead of removing it and adding the right-click context menu.
- `shell.openExternal` called on a menu-click handler with no scheme
  check — same class of issue as the SSRF/local-file-open risk
  `isSafeExternalUrl` exists to prevent.

This is currently an Electron-only standard (RolePlaymate → Bracketeer).
Follow the "New tech stacks" process in the `app-standards` skill before
inventing an equivalent for another desktop stack (Tkinter/Flet/Wails) —
none of those currently ship a default menu bar as noisy as Electron's, so
it's not yet clear the same problem exists there.
