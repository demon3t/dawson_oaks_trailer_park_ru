# Удаление русификатора Dawson Oaks Trailer Park одной командой (PowerShell):
#   irm https://raw.githubusercontent.com/demon3t/dawson_oaks_trailer_park_ru/main/uninstall.ps1 | iex
$local = if ($PSScriptRoot) { Join-Path $PSScriptRoot "install.ps1" } else { $null }
if ($local -and (Test-Path $local)) {
    & $local -Uninstall @args
} else {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    & ([scriptblock]::Create((irm "https://raw.githubusercontent.com/demon3t/dawson_oaks_trailer_park_ru/main/install.ps1"))) -Uninstall
}
