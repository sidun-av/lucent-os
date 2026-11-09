<#
Lucent OS: join the installer ISO downloaded in parts, and check it.

Double-click join-lucent-iso.cmd in the folder with your downloads, or
right-click this file and choose "Run with PowerShell". Nothing to install:
it uses only what Windows 10 and 11 come with (Windows PowerShell 5.1).

The folder (default: the folder this script is in) holds what you downloaded
from the release page: lucent-os-<version>-<arch>.iso.001, .002, ... and
SHA256SUMS.

1. If cosign is installed, checks that SHA256SUMS was signed by Lucent OS's
   release workflow on GitHub (SHA256SUMS.sigstore.json).
2. Checks every part against SHA256SUMS while joining them, and names the
   ones to download again.
3. Checks the finished ISO against SHA256SUMS.
Nothing is deleted: the parts stay until you remove them.

This file is plain ASCII on purpose (Windows PowerShell 5.1 reads scripts
without a byte-order mark in the ANSI code page).
#>
param(
    [string]$Path = "",
    [switch]$NoPause
)

$ErrorActionPreference = "Stop"
$IdentityRegexp = '^https://github\.com/sidun-av/lucent-os/\.github/workflows/release\.yml@refs/(tags/v.+|heads/main)$'
$Issuer = "https://token.actions.githubusercontent.com"
$Guide = "https://github.com/sidun-av/lucent-os/blob/main/docs/install-usb.md"
$script:Partial = $null

function Close-Window([int]$Code) {
    if (-not $NoPause -and -not $env:LUCENT_NO_PAUSE) {
        Write-Host ""
        [void](Read-Host "Press Enter to close this window")
    }
    exit $Code
}

function Stop-WithProblem([string]$Message, [string[]]$Details = @()) {
    if ($script:Partial -and (Test-Path -LiteralPath $script:Partial)) {
        Remove-Item -LiteralPath $script:Partial -Force -ErrorAction SilentlyContinue
    }
    Write-Host ""
    Write-Host "Problem: $Message" -ForegroundColor Red
    foreach ($line in $Details) { Write-Host $line }
    Close-Window 1
}

function Format-GB([double]$Bytes) {
    return ("{0:N1} GB" -f ($Bytes / 1e9))
}

function ConvertTo-Hex([byte[]]$Bytes) {
    return ([System.BitConverter]::ToString($Bytes) -replace "-", "").ToLowerInvariant()
}

function Get-Sha256([string]$File) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $stream = [System.IO.File]::OpenRead($File)
    try { return ConvertTo-Hex $sha.ComputeHash($stream) }
    finally { $stream.Dispose(); $sha.Dispose() }
}

try {
    if (-not $Path) { $Path = $PSScriptRoot }
    if (-not $Path) { $Path = (Get-Location).Path }
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        Stop-WithProblem "Cannot open the folder $Path."
    }
    $Dir = (Resolve-Path -LiteralPath $Path).ProviderPath

    Write-Host "Lucent OS installer: joining and checking the downloaded parts in"
    Write-Host "  $Dir"
    Write-Host ""

    $SumsFile = Join-Path $Dir "SHA256SUMS"
    if (-not (Test-Path -LiteralPath $SumsFile -PathType Leaf)) {
        Stop-WithProblem "SHA256SUMS is missing from this folder." @(
            "Download SHA256SUMS from the same release page as the parts, put it next to them,",
            "and run this again.")
    }

    # name -> expected hash, in file order.
    $Sums = [ordered]@{}
    foreach ($line in [System.IO.File]::ReadAllLines($SumsFile)) {
        if ($line -match '^([0-9a-fA-F]{64}) [ *](.+?)\s*$') {
            $Sums[$Matches[2]] = $Matches[1].ToLowerInvariant()
        }
    }
    if ($Sums.Count -eq 0) {
        Stop-WithProblem "SHA256SUMS is empty or damaged. Download it again from the release page."
    }

    function Get-Parts([string]$Iso) {
        $pattern = '^' + [regex]::Escape($Iso) + '\.[0-9]{3}$'
        return @($Sums.Keys | Where-Object { $_ -match $pattern } | Sort-Object)
    }

    # The ISOs whose parts (or finished file) are in this folder.
    $Todo = @()
    foreach ($name in @($Sums.Keys)) {
        if ($name -notmatch '\.iso$') { continue }
        $here = Test-Path -LiteralPath (Join-Path $Dir $name) -PathType Leaf
        foreach ($p in (Get-Parts $name)) {
            if (Test-Path -LiteralPath (Join-Path $Dir $p) -PathType Leaf) { $here = $true }
        }
        if ($here) { $Todo += $name }
    }
    if ($Todo.Count -eq 0) {
        Stop-WithProblem "No ISO parts found in this folder." @(
            "Put the downloaded files (lucent-os-...iso.001, .002, ...) in the same folder as",
            "SHA256SUMS and this script, then run it again.")
    }

    # 1. The signature of SHA256SUMS.
    $Bundle = Join-Path $Dir "SHA256SUMS.sigstore.json"
    if (Test-Path -LiteralPath $Bundle -PathType Leaf) {
        $cosign = Get-Command cosign -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cosign) {
            Write-Host "Checking the signature of SHA256SUMS with cosign..."
            # cosign reports on stderr; Windows PowerShell 5.1 would turn that
            # into a terminating error under "Stop".
            $ErrorActionPreference = "Continue"
            $global:LASTEXITCODE = 0
            $null = & $cosign.Source verify-blob --bundle $Bundle `
                --certificate-identity-regexp $IdentityRegexp `
                --certificate-oidc-issuer $Issuer $SumsFile 2>&1
            $code = $LASTEXITCODE
            $ErrorActionPreference = "Stop"
            if ($code -ne 0) {
                Stop-WithProblem "The signature check failed: SHA256SUMS was not signed by Lucent OS's release workflow." @(
                    "Do not use these files. Download them again from",
                    "  https://github.com/sidun-av/lucent-os/releases")
            }
            Write-Host "Signature verified: SHA256SUMS was made by Lucent OS's release workflow on GitHub." -ForegroundColor Green
        } else {
            Write-Host "Note: the signature was not checked (cosign is not installed). The checksums"
            Write-Host "below still prove that every part arrived complete and undamaged."
        }
    } else {
        Write-Host "Note: SHA256SUMS.sigstore.json is not here, so the signature was not checked."
    }
    Write-Host ""

    $Buffer = New-Object byte[] (4MB)
    foreach ($iso in $Todo) {
        $want = $Sums[$iso]
        $parts = Get-Parts $iso
        $n = $parts.Count
        $isoPath = Join-Path $Dir $iso

        if (Test-Path -LiteralPath $isoPath -PathType Leaf) {
            Write-Host "Checking the finished $iso..."
            if ((Get-Sha256 $isoPath) -eq $want) {
                Write-Host "$iso is already joined and checked." -ForegroundColor Green
                Write-Host ""
                continue
            }
            Write-Host "The $iso here is incomplete or damaged; joining it again from the parts."
        }

        $missing = @($parts | Where-Object { -not (Test-Path -LiteralPath (Join-Path $Dir $_) -PathType Leaf) })
        if ($missing.Count -gt 0) {
            Stop-WithProblem "Some parts of $iso are missing:" (@($missing | ForEach-Object { "  - $_" }) + @(
                "Download them from the release page into this folder and run this again."))
        }

        $need = [int64]0
        foreach ($p in $parts) { $need += (Get-Item -LiteralPath (Join-Path $Dir $p)).Length }
        $drive = New-Object System.IO.DriveInfo ([System.IO.Path]::GetPathRoot($Dir))
        $free = [int64]$drive.AvailableFreeSpace
        if ($env:LUCENT_TEST_FREE_BYTES) { $free = [int64]$env:LUCENT_TEST_FREE_BYTES }
        if ($free -lt $need) {
            Stop-WithProblem ("Not enough free space to join ${iso}: it needs {0}, this drive has {1} free." -f (Format-GB $need), (Format-GB $free)) @(
                "Free up some space, or move the parts to a bigger drive, and run this again.")
        }
        if ($drive.DriveFormat -eq "FAT32" -or $drive.DriveFormat -eq "FAT") {
            Stop-WithProblem "This drive ($($drive.Name)) uses FAT32, which cannot hold files over 4 GB." @(
                "Move the parts and this script to a drive formatted as NTFS (for example",
                "your Downloads folder on C:) and run it again.")
        }

        # 2. One pass: check every part, join them and hash the whole ISO.
        $script:Partial = "$isoPath.partial"
        $whole = [System.Security.Cryptography.SHA256]::Create()
        $out = [System.IO.File]::Open($script:Partial, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write)
        $damaged = @()
        $done = [int64]0
        $lastShown = [int64]-1
        $writeError = $null
        try {
            for ($i = 0; $i -lt $n; $i++) {
                $p = $parts[$i]
                Write-Host ("Checking and joining part {0} of {1} ({2})..." -f ($i + 1), $n, $p)
                $sha = [System.Security.Cryptography.SHA256]::Create()
                $in = [System.IO.File]::OpenRead((Join-Path $Dir $p))
                try {
                    while (($read = $in.Read($Buffer, 0, $Buffer.Length)) -gt 0) {
                        [void]$sha.TransformBlock($Buffer, 0, $read, $null, 0)
                        if ($damaged.Count -eq 0) {
                            [void]$whole.TransformBlock($Buffer, 0, $read, $null, 0)
                            $out.Write($Buffer, 0, $read)
                        }
                        $done += $read
                        $pct = [int64](100 * $done / [math]::Max($need, 1))
                        if ($pct -ne $lastShown) {
                            Write-Progress -Activity "Joining $iso" -Status ("{0} of {1}" -f (Format-GB $done), (Format-GB $need)) -PercentComplete ([math]::Min($pct, 100))
                            $lastShown = $pct
                        }
                    }
                    [void]$sha.TransformFinalBlock($Buffer, 0, 0)
                    if ((ConvertTo-Hex $sha.Hash) -ne $Sums[$p]) { $damaged += $p }
                } finally {
                    $in.Dispose(); $sha.Dispose()
                }
            }
            [void]$whole.TransformFinalBlock($Buffer, 0, 0)
            $got = ConvertTo-Hex $whole.Hash
        } catch {
            $writeError = $_.Exception
        } finally {
            $out.Dispose(); $whole.Dispose()
            Write-Progress -Activity "Joining $iso" -Completed
        }
        if ($writeError) {
            while ($writeError.InnerException) { $writeError = $writeError.InnerException }
            Stop-WithProblem "Could not write $iso ($($writeError.Message))." @(
                "Is the drive full? Free up some space and run this again.")
        }

        if ($damaged.Count -gt 0) {
            Stop-WithProblem "Some parts of $iso are damaged (their checksum does not match SHA256SUMS):" (@($damaged | ForEach-Object { "  - $_" }) + @(
                "Download them again from the release page, replace the old ones, and run this again."))
        }
        if ($got -ne $want) {
            Stop-WithProblem "The joined $iso does not match SHA256SUMS, although every part did." @(
                "SHA256SUMS may be from a different release: download it again and run this again.")
        }
        Move-Item -LiteralPath $script:Partial -Destination $isoPath -Force
        $script:Partial = $null
        Write-Host ("Ready: {0} ({1}), checked against SHA256SUMS." -f $isoPath, (Format-GB $need)) -ForegroundColor Green
        Write-Host ("You can delete the {0} part files ({1}.001 ...) now." -f $n, $iso)
        Write-Host ""
    }

    Write-Host "Next: write the ISO to a USB stick (16 GB or larger), see"
    Write-Host "  $Guide"
    Close-Window 0
} catch {
    Stop-WithProblem "Something went wrong: $($_.Exception.Message)" @(
        "Please report it at https://github.com/sidun-av/lucent-os/issues")
}
