# Русификатор Dawson Oaks Trailer Park
#
# Установка одной командой (PowerShell):
#   irm https://raw.githubusercontent.com/demon3t/dawson_oaks_trailer_park_ru/main/install.ps1 | iex
# Удаление:
#   irm https://raw.githubusercontent.com/demon3t/dawson_oaks_trailer_park_ru/main/uninstall.ps1 | iex
#
# Запущенный из папки репозитория (install.bat) скрипт берёт патчи из patch/ рядом,
# а запущенный из интернета — скачивает их из репозитория.
param(
    [string]$GameDir = "",
    [switch]$Uninstall,
    [switch]$PauseAtEnd
)

$RepoRaw = "https://raw.githubusercontent.com/demon3t/dawson_oaks_trailer_park_ru/main"
$ScriptUrl = "$RepoRaw/install.ps1"

function Invoke-DawsonRu {
    param([string]$GameDir, [switch]$Uninstall, [string]$LocalRoot)

    $ErrorActionPreference = "Stop"
    $LanguageIndex = 10  # «Русский» — 11-й пункт в списке языков
    $UserSettings = Join-Path $env:USERPROFILE "AppData\LocalLow\Striped Panda Studios\Dawson Oaks Trailer Park\settings.json"
    $TempDir = $null

    if (-not ([System.Management.Automation.PSTypeName]"DawsonRuPatch").Type) {
        Add-Type @"
using System; using System.IO;
public static class DawsonRuPatch {
    public static byte[] Apply(byte[] old, byte[] patch) {
        if (patch.Length < 5 || System.Text.Encoding.ASCII.GetString(patch, 0, 5) != "DOTP1")
            throw new Exception("damaged patch file");
        var ms = new MemoryStream();
        int p = 5;
        while (p < patch.Length) {
            if (patch[p] == 1) {
                long o = BitConverter.ToInt64(patch, p + 1);
                int n = BitConverter.ToInt32(patch, p + 9);
                ms.Write(old, (int)o, n);
                p += 13;
            } else if (patch[p] == 2) {
                int n = BitConverter.ToInt32(patch, p + 1);
                ms.Write(patch, p + 5, n);
                p += 5 + n;
            } else throw new Exception("damaged patch file");
        }
        return ms.ToArray();
    }
}
"@
    }

    function Get-Sha([byte[]]$data) {
        $sha = [Security.Cryptography.SHA256]::Create()
        return ([BitConverter]::ToString($sha.ComputeHash($data)) -replace "-", "")
    }

    function Find-GameDir {
        $candidates = @()
        $steam = (Get-ItemProperty "HKCU:\Software\Valve\Steam" -ErrorAction SilentlyContinue).SteamPath
        if ($steam) {
            $candidates += Join-Path $steam "steamapps\common\Dawson Oaks Trailer Park"
            $vdf = Join-Path $steam "steamapps\libraryfolders.vdf"
            if (Test-Path $vdf) {
                foreach ($m in [regex]::Matches((Get-Content $vdf -Raw), '"path"\s+"([^"]+)"')) {
                    $candidates += Join-Path ($m.Groups[1].Value -replace '\\\\', '\') "steamapps\common\Dawson Oaks Trailer Park"
                }
            }
        }
        foreach ($c in $candidates) {
            if (Test-Path (Join-Path $c "GameAssembly.dll")) { return $c }
        }
        return $null
    }

    function Test-Writable([string]$dir) {
        $probe = Join-Path $dir ".dawson_ru_write_test"
        try { [IO.File]::WriteAllText($probe, "x"); Remove-Item $probe -Force; return $true }
        catch { return $false }
    }

    # Выставить язык в пользовательских настройках игры (если файл уже есть)
    function Set-UserLanguage([double]$value, [switch]$OnlyIfRussian) {
        if (-not (Test-Path $UserSettings)) { return }
        $text = [IO.File]::ReadAllText($UserSettings)
        $m = ([regex]'("language"\s*:\s*\{[^{}]*?"value"\s*:\s*)([0-9.]+)').Match($text)
        if (-not $m.Success) { return }
        if ($OnlyIfRussian -and [double]$m.Groups[2].Value -lt $LanguageIndex) { return }
        $g = $m.Groups[2]
        $text = $text.Substring(0, $g.Index) + $value.ToString("0.0", [Globalization.CultureInfo]::InvariantCulture) + $text.Substring($g.Index + $g.Length)
        [IO.File]::WriteAllText($UserSettings, $text, (New-Object Text.UTF8Encoding($false)))
    }

    try {
        if (-not $GameDir) { $GameDir = Find-GameDir }
        if (-not $GameDir -or -not (Test-Path (Join-Path $GameDir "GameAssembly.dll"))) {
            throw "Игра не найдена. Укажите путь к папке игры, например:`n  & ([scriptblock]::Create((irm $ScriptUrl))) -GameDir 'D:\SteamLibrary\steamapps\common\Dawson Oaks Trailer Park'"
        }
        Write-Host "Папка игры: $GameDir"
        if (Get-Process -Name "Dawson Oaks Trailer Park" -ErrorAction SilentlyContinue) {
            throw "Закройте игру и запустите снова."
        }

        # Нет прав на запись (например, игра в Program Files) — перезапуск от администратора
        if (-not (Test-Writable $GameDir)) {
            Write-Host "Нужны права администратора, сейчас появится запрос Windows..." -ForegroundColor Yellow
            $argsList = "-GameDir '$($GameDir -replace "'", "''")' -PauseAtEnd"
            if ($Uninstall) { $argsList += " -Uninstall" }
            if ($LocalRoot) {
                $cmd = "& '$((Join-Path $LocalRoot 'install.ps1') -replace "'", "''")' $argsList"
            } else {
                $cmd = "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; & ([scriptblock]::Create((irm '$ScriptUrl'))) $argsList"
            }
            Start-Process powershell -Verb RunAs -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $cmd)
            return
        }

        # Файлы патча: локальная папка patch/ или скачивание из репозитория
        if ($LocalRoot -and (Test-Path (Join-Path $LocalRoot "patch\manifest.json"))) {
            $PatchDir = Join-Path $LocalRoot "patch"
            $manifest = Get-Content (Join-Path $PatchDir "manifest.json") -Raw -Encoding UTF8 | ConvertFrom-Json
        } else {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            $TempDir = Join-Path $env:TEMP ("dawson_ru_" + [Guid]::NewGuid().ToString("N"))
            New-Item -ItemType Directory $TempDir | Out-Null
            $PatchDir = $TempDir
            $wc = New-Object Net.WebClient
            Write-Host "Загрузка файлов русификатора..."
            $wc.DownloadFile("$RepoRaw/patch/manifest.json", (Join-Path $PatchDir "manifest.json"))
            $manifest = Get-Content (Join-Path $PatchDir "manifest.json") -Raw -Encoding UTF8 | ConvertFrom-Json
            if (-not $Uninstall) {
                foreach ($f in $manifest.files) {
                    $wc.DownloadFile("$RepoRaw/patch/$($f.patch)", (Join-Path $PatchDir $f.patch))
                }
            }
        }

        if ($Uninstall) {
            foreach ($f in $manifest.files) {
                $target = Join-Path $GameDir $f.path
                $backup = "$target.bak"
                if (Test-Path $backup) {
                    Copy-Item $backup $target -Force
                    Remove-Item $backup
                    Write-Host "  восстановлен $($f.name)"
                }
            }
            Set-UserLanguage 0 -OnlyIfRussian
            Write-Host ""
            Write-Host "Русификатор удалён." -ForegroundColor Green
            return
        }

        # 1. Проверяем все файлы до каких-либо изменений
        $jobs = @()
        foreach ($f in $manifest.files) {
            $target = Join-Path $GameDir $f.path
            $backup = "$target.bak"
            if (-not (Test-Path $target)) { throw "Не найден файл игры: $($f.path)" }
            $cur = Get-Sha ([IO.File]::ReadAllBytes($target))
            if ($cur -eq $f.patched_sha256) { continue }  # уже установлено
            if ($cur -eq $f.original_sha256) { $source = $target }
            elseif ((Test-Path $backup) -and (Get-Sha ([IO.File]::ReadAllBytes($backup))) -eq $f.original_sha256) { $source = $backup }
            else {
                throw "Файл $($f.name) не подходит к этой версии русификатора. Скорее всего, игра обновилась — дождитесь обновления русификатора. (Если файлы игры повреждены — проверьте их целостность в Steam.)"
            }
            $jobs += @{ f = $f; target = $target; backup = $backup; source = $source }
        }

        # 2. Применяем патчи
        foreach ($j in $jobs) {
            $old = [IO.File]::ReadAllBytes($j.source)
            $new = [DawsonRuPatch]::Apply($old, [IO.File]::ReadAllBytes((Join-Path $PatchDir $j.f.patch)))
            if ((Get-Sha $new) -ne $j.f.patched_sha256) { throw "Ошибка при применении патча к $($j.f.name)" }
            if ($j.source -eq $j.target) { Copy-Item $j.target $j.backup -Force }
            [IO.File]::WriteAllBytes($j.target, $new)
            Write-Host "  обновлён $($j.f.name)"
        }

        Set-UserLanguage $LanguageIndex
        Write-Host ""
        if ($jobs.Count -eq 0) { Write-Host "Русификатор уже установлен." -ForegroundColor Green }
        else { Write-Host "Готово! Русский язык установлен." -ForegroundColor Green }
        Write-Host "Если игра запустится не на русском: Settings -> Game -> Language -> Русский."
    }
    catch {
        Write-Host ""
        Write-Host "ОШИБКА: $($_.Exception.Message)" -ForegroundColor Red
    }
    finally {
        if ($TempDir -and (Test-Path $TempDir)) { Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue }
    }
}

Invoke-DawsonRu -GameDir $GameDir -Uninstall:$Uninstall -LocalRoot $PSScriptRoot
if ($PauseAtEnd) { Write-Host ""; Read-Host "Нажмите Enter, чтобы закрыть окно" | Out-Null }
