// Smoke tests for KvgDbLocation.cs. Run: dotnet run --project packages/dotnet/KvgDbLocation/tests
// Exit code 1 on any failure. Includes a real two-process check of InstanceLock and a real
// SQLite WAL database to back the "close connections / ClearAllPools before relocating" rule.
using System.Diagnostics;
using System.Globalization;
using Kvg.Standards;
using Microsoft.Data.Sqlite;

if (args.Length == 2 && args[0] == "--hold")
{
    // Child process: hold the instance lock until killed.
    using var held = InstanceLock.TryAcquire(args[1]);
    Console.WriteLine(held is null ? "FAILED" : "HELD");
    Console.Out.Flush();
    Thread.Sleep(TimeSpan.FromSeconds(60));
    return 0;
}

int failures = 0;
void Check(bool ok, string what)
{
    Console.WriteLine((ok ? "ok   " : "FAIL ") + what);
    if (!ok) failures++;
}
string Temp(string name) => Path.Combine(Path.GetTempPath(), "kvgdb-" + Guid.NewGuid().ToString("N")[..8], name);

// --- defaults, relocate, adopt, reset ------------------------------------------------
{
    var dir = Path.GetDirectoryName(Temp("x"))!;
    var loc = new DbLocation(dir, "app.db");
    Check(loc.GetEffectiveDbPath() == Path.Combine(dir, "app.db"), "default path is under the data dir");
    Check(loc.IsUsingDefaultLocation(), "first run uses the default location");
    Check(!loc.IsConfiguredPathMissing(), "first run: configured path is not 'missing'");

    Directory.CreateDirectory(dir);
    File.WriteAllText(loc.GetDefaultDbPath(), "DATA-1");

    var moved = Temp("synced/app.db");
    loc.SetDbPath(moved);
    Check(File.ReadAllText(moved) == "DATA-1", "relocate copies the current database to the new path");
    Check(File.Exists(loc.GetDefaultDbPath()), "relocate leaves the original in place");
    Check(!File.Exists(moved + ".partial"), "relocate leaves no .partial file behind");
    Check(new DbLocation(dir, "app.db").GetEffectiveDbPath() == Path.GetFullPath(moved), "override persists for a new instance");
    Check(!loc.IsUsingDefaultLocation(), "no longer using the default");

    var adopted = Temp("other/app.db");
    Directory.CreateDirectory(Path.GetDirectoryName(adopted)!);
    File.WriteAllText(adopted, "ALREADY-THERE");
    loc.SetDbPath(adopted);
    Check(File.ReadAllText(adopted) == "ALREADY-THERE", "an existing file at the new path is adopted untouched");

    File.Delete(adopted);
    Check(loc.IsConfiguredPathMissing(), "configured path deleted -> IsConfiguredPathMissing");

    // extra keys in the config must survive a set/reset
    var configPath = Path.Combine(dir, "db_location.json");
    var json = System.Text.Json.Nodes.JsonNode.Parse(File.ReadAllText(configPath))!.AsObject();
    json["other"] = "keep-me";
    File.WriteAllText(configPath, json.ToJsonString());
    loc.ResetToDefaultDbPath();
    Check(loc.IsUsingDefaultLocation() && loc.GetEffectiveDbPath() == loc.GetDefaultDbPath(), "reset returns to the default");
    Check(File.ReadAllText(configPath).Contains("keep-me"), "unrelated config keys survive a reset");

    File.WriteAllText(configPath, "{ not json");
    Check(loc.IsUsingDefaultLocation(), "a corrupt config file falls back to the default");
}

// --- data directories and file size ---------------------------------------------------
{
    var packaged = DbLocation.ResolveDataDirectory("MyApp", isDevelopment: false);
    var dev = DbLocation.ResolveDataDirectory("MyApp", isDevelopment: true);
    Check(packaged != dev && dev.EndsWith("MyApp-dev"), "dev and packaged data directories differ");

    var inv = CultureInfo.InvariantCulture;
    Check(FileSize.Format(842L * 1024, inv) == "842 KB", "842 KB");
    Check(FileSize.Format((long)(4.1 * 1024 * 1024), inv) == "4.1 MB", "4.1 MB");
    Check(FileSize.Format((long)(1.3 * 1024 * 1024 * 1024), inv) == "1.3 GB", "1.3 GB");
    Check(FileSize.Format(0, inv) == "0 KB", "0 bytes");
}

// --- instance lock: same process, then a real second process -------------------------
{
    var dir = Path.GetDirectoryName(Temp("x"))!;
    var first = InstanceLock.TryAcquire(dir);
    Check(first is not null, "first copy acquires the lock");
    Check(InstanceLock.TryAcquire(dir) is null, "second copy in the same process is refused");
    first!.Dispose();
    var again = InstanceLock.TryAcquire(dir);
    Check(again is not null, "lock can be re-acquired after release");
    again!.Dispose();

    var host = Environment.ProcessPath!;
    var psi = new ProcessStartInfo(host) { RedirectStandardOutput = true, UseShellExecute = false };
    if (Path.GetFileNameWithoutExtension(host) == "dotnet") psi.ArgumentList.Add(Environment.GetCommandLineArgs()[0]);
    psi.ArgumentList.Add("--hold"); psi.ArgumentList.Add(dir);
    using var child = Process.Start(psi)!;
    var line = child.StandardOutput.ReadLine();
    Check(line == "HELD", "child process acquired the lock");
    Check(InstanceLock.TryAcquire(dir) is null, "this process is refused while another process holds it");
    child.Kill(); child.WaitForExit();
    var afterKill = InstanceLock.TryAcquire(dir);
    Check(afterKill is not null, "lock is free again after the holder is killed (crash-safe)");
    afterKill?.Dispose();
}

// --- relocating a real SQLite database in WAL mode ------------------------------------
{
    var dir = Path.GetDirectoryName(Temp("x"))!;
    var loc = new DbLocation(dir, "app.db");
    Directory.CreateDirectory(dir);
    var cs = $"Data Source={loc.GetDefaultDbPath()}";
    using (var c = new SqliteConnection(cs))
    {
        c.Open();
        new SqliteCommand("PRAGMA journal_mode=WAL; CREATE TABLE t(x); INSERT INTO t VALUES (1),(2),(3);", c).ExecuteNonQuery();
    } // connection closed, but the pool still holds the file open

    // Informational: what a copy taken *before* releasing the pool actually contains.
    var naive = Temp("naive/app.db");
    Directory.CreateDirectory(Path.GetDirectoryName(naive)!);
    File.Copy(loc.GetDefaultDbPath(), naive);
    string naiveResult;
    try { naiveResult = $"{CountRows(naive)} of 3 rows"; }
    catch (SqliteException e) { naiveResult = "unreadable (" + e.Message + ")"; }
    Console.WriteLine($"info a copy taken before ClearAllPools: {naiveResult}");

    SqliteConnection.ClearAllPools();
    var target = Temp("synced/app.db");
    loc.SetDbPath(target);
    Check(CountRows(target) == 3, "after ClearAllPools, a relocated WAL database has all its rows");
}

static int CountRows(string path)
{
    using var c = new SqliteConnection($"Data Source={path};Pooling=False");
    c.Open();
    return Convert.ToInt32(new SqliteCommand("SELECT COUNT(*) FROM t", c).ExecuteScalar());
}

Console.WriteLine(failures == 0 ? "ALL OK" : $"{failures} FAILURES");
return failures == 0 ? 0 : 1;
