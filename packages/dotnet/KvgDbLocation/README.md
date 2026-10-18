# KvgDbLocation

A user-configurable SQLite file location for .NET desktop apps (Avalonia), plus the
instance-isolation pieces from [`db-location-versioning.md`](../../../db-location-versioning.md).
Mirrors [`packages/python/kvg_dblocation`](../../python/kvg_dblocation) and Sweeper's
`src/main/dbLocation.ts`: default path, optional override, copy-on-relocate, reset.

**One source file, no dependencies, not published to NuGet.** You copy
[`KvgDbLocation.cs`](KvgDbLocation.cs) into your app from a KVG_Standards tag with
`scripts/update-kvg-dblocation.sh <tag>` (template: `templates/update-kvg-dblocation.sh`),
which stamps the source tag into the file. Fix bugs here, then re-run the script; never
patch the vendored copy. Publishing it as a NuGet package is future work.

## What's in it

| | |
|---|---|
| `DbLocation` | default / effective / configured path, `SetDbPath` (copy-on-relocate), `ResetToDefaultDbPath`, `IsConfiguredPathMissing`, `GetDbFileSizeBytes` |
| `DbLocation.ResolveDataDirectory(app, isDevelopment)` | `%LOCALAPPDATA%\app` / `~/.local/share/app`; a development run gets `app-dev` so it can never share a database with an installed copy |
| `InstanceLock.TryAcquire(dir)` | exclusive file lock: only one copy of the app per data folder; released by the OS if the process crashes |
| `FileSize.Format(bytes)` | `842 KB`, `4.1 MB`, `1.3 GB` for the Settings UI |

## Wiring

```csharp
// Program.Main, before any window or database access
VelopackApp.Build().Run();                                      // (updater wiring; see dotnet-avalonia.md)
bool isDev = !new UpdateManager(new GithubSource(...)).IsInstalled;  // or any "not an installed build" test
var dataDir = DbLocation.ResolveDataDirectory("KVGuzzler", isDev);

using var instance = InstanceLock.TryAcquire(dataDir);
if (instance is null) return;                                   // another copy is running

var dbLocation = new DbLocation(dataDir, "kvguzzler.db");
if (dbLocation.IsConfiguredPathMissing())
{
    // The user chose a custom location and it is gone (drive unplugged, synced folder
    // not mounted). Do NOT create a fresh database - ask: Quit, or use the default.
}
var connection = new SqliteConnection($"Data Source={dbLocation.GetEffectiveDbPath()}");
```

Settings UI: show the current path **and its size** (`FileSize.Format(dbLocation.GetDbFileSizeBytes()!.Value)`),
with "choose an existing file" (`SetDbPath` adopts it as-is), "choose a new location"
(`SetDbPath` copies the current database there), "reset to default", then **restart the app**
(an open connection cannot be re-pointed).

## Before relocating: close everything

`SetDbPath` copies the file, so no connection may still hold it. With
`Microsoft.Data.Sqlite` that means closing your connections **and** calling
`SqliteConnection.ClearAllPools()`: the pool keeps the file open, and in WAL mode (the
recommended mode) recent writes live in the `-wal` file until the last connection
closes and checkpoints. The smoke tests measure this: a copy taken before releasing
the pool of a WAL database was unreadable (`no such table`), because everything was
still in the WAL.

## Verifying

```bash
dotnet run --project packages/dotnet/KvgDbLocation/tests
```

Covers defaults, copy-on-relocate, adopt-existing, reset, corrupt config, the missing-path
guard, dev/packaged separation, the file-size format, the instance lock (same process
**and a real second process**, including after the holder is killed), and relocating a
real WAL database. Exit code 1 on any failure. Verified on .NET 10, Linux.
