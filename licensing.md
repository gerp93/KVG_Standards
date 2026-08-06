# Licensing

Every active app repo should carry a `LICENSE` file, same as it should carry
theming and a release pipeline — this isn't optional polish, it's part of
what "aligned to the standard" means.

## The default: AGPL-3.0

**GNU Affero General Public License v3.0.** Copyleft, and specifically the
network-use clause (a modified version run as a network service must still
offer its source) — the strongest copyleft option commonly available.
Default to it for every new repo.

## But check dependencies first

AGPL-3.0 is the default, not a rule applied blindly. Before adding it (or
before it's safe to assume an existing repo's choice is fine), check what
the repo actually depends on:

- **Permissive licenses (MIT, BSD, Apache-2.0, HPND, etc.) are always fine.**
  They don't restrict what license the combined work can carry, so a repo
  full of MIT/BSD/Apache dependencies has no obstacle to AGPL-3.0.
- **LGPL is fine as a dependency.** It's designed specifically to permit
  linking/importing from software under any license — that's the point of
  the "Lesser" GPL. (Example: KVGroove depends on `pygame`, which is LGPL.)
- **GPL-2.0-or-later is fine.** The "or later" clause is what makes it
  combinable with a GPLv3-family (including AGPLv3) work — plain
  **GPL-2.0-only**, without the "or later" grant, is not compatible with
  GPLv3/AGPLv3 and would block AGPL-3.0 for that repo. Check which one a
  GPL'd dependency actually uses; don't assume. (Example: KVGroove depends
  on `mutagen`, confirmed `GPL-2.0-or-later` — fine.)
- **Anything else — a source-available/non-commercial license, a
  GPL-2.0-only dependency, a proprietary SDK, etc. — is a real blocker.**
  Don't force AGPL-3.0 onto a repo where a dependency's license doesn't
  allow it. Flag it and pick a compatible alternative (a more permissive
  license for that repo, or replacing the dependency) case by case, and
  document why that repo differs from the default.

How to check a Python dependency's actual license (don't guess from the
package name or reputation):

```bash
pip download --no-deps -d /tmp/lic_check <package>
python3 -c "
import zipfile
z = zipfile.ZipFile('/tmp/lic_check/<wheel-file>.whl')
meta = [n for n in z.namelist() if n.endswith('METADATA')][0]
print(z.read(meta).decode())
" | grep -i license
```

For Go/JS dependencies, check `go.mod`'s resolved modules or
`package.json`'s dependency tree against their published `LICENSE` files —
the same "permissive/LGPL/GPL-or-later is fine, anything else needs a
look" triage applies.

## Current state (as of this audit)

All 10 active app repos plus VisualAssault, checked against their actual
dependency trees — no license-incompatible dependency found anywhere, so
AGPL-3.0 applies cleanly across the board:

| Repo | License |
|---|---|
| KVGrainy | AGPL-3.0 |
| KVGroove | AGPL-3.0 (deps checked: `pygame` LGPL, `mutagen` GPL-2.0-or-later — both fine) |
| KVG_Converter | AGPL-3.0 |
| KVGenius | AGPL-3.0 (ML deps — torch, transformers, diffusers, accelerate, safetensors, peft, bitsandbytes, flask, flet — are BSD/Apache-2.0/MIT) |
| KVGauge | AGPL-3.0 |
| gameshell-deploy | AGPL-3.0 (Wails + Go deps are MIT/BSD) |
| Sweeper | AGPL-3.0 (Electron + npm deps are MIT) |
| gameshell-framework | AGPL-3.0 |
| card-judge | AGPL-3.0 |
| timeline-trivia | AGPL-3.0 |
| VisualAssault | AGPL-3.0 |
| KVG_Standards | AGPL-3.0 |

## Adding a new consumer repo

Copy an existing repo's `LICENSE` file (they're all identical AGPL-3.0
boilerplate) — don't hand-type it. Check the new repo's dependency tree
against the rules above first if it pulls in anything unusual.

## Re-checking

Dependency licenses aren't permanently settled — a new dependency (or a
major version bump that changes one) could introduce an incompatibility
later. Worth a glance during the periodic audit pass (see `app-standards`
skill's audit workflow), not just once at repo creation.
