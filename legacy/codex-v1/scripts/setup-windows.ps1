# Windows setup only. Review SETUP.md before running. No application/data edits.
# Compatible with Windows PowerShell 5.1 and PowerShell 7+.
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# Check native exits explicitly, consistently across PowerShell versions.
$PSNativeCommandUseErrorActionPreference = $false
$root = Split-Path -Parent $PSScriptRoot
$protectedHashes = @{}
$originalDbOverride = [Environment]::GetEnvironmentVariable('F1_ERAS_DB_PATH', 'Process')
$exitCode = 1
$locationPushed = $false

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    Write-Host "`n> $Program $($Arguments -join ' ')"
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed (exit $LASTEXITCODE): $Program $($Arguments -join ' ')"
    }
}

function Refresh-ProcessPath {
    # Add newly registered paths only to this process; preserve custom PATH entries.
    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$env:Path;$machinePath;$userPath"
}

function Find-Tool {
    param([string]$Name)
    $command = Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($command) { return $command.Source }
    return $null
}

function Install-MissingTool {
    param([string]$PackageId, [string]$Version)
    $winget = Find-Tool 'winget.exe'
    if (-not $winget) {
        throw "Missing software ($PackageId) and winget is unavailable. Use the official installers under 'Manual Windows setup' in SETUP.md."
    }
    $installArguments = @('install', '--id', $PackageId, '--exact', '--source', 'winget')
    if ($Version) { $installArguments += @('--version', $Version) }
    # Leave installer/administrator/agreement prompts visible. No forced upgrade.
    Invoke-Checked $winget $installArguments | Out-Host
    Refresh-ProcessPath
}

function Require-Tool {
    param([string]$Name, [string]$PackageId, [string]$Version)
    $tool = Find-Tool $Name
    if (-not $tool) {
        Install-MissingTool $PackageId $Version
        $tool = Find-Tool $Name
    }
    if (-not $tool) {
        throw "$Name is still unavailable. Restart VS Code/PowerShell and follow SETUP.md before rerunning."
    }
    return $tool
}

function Find-CompatiblePython {
    # Ask the launcher for its Python 3, then try PATH Python. Ignore Store aliases.
    $candidates = @(
        @{ Name = 'py.exe'; Arguments = @('-3') },
        @{ Name = 'python.exe'; Arguments = @() }
    )
    foreach ($candidate in $candidates) {
        $program = Find-Tool $candidate.Name
        if (-not $program) { continue }
        if ($candidate.Name -eq 'python.exe' -and $program -match '\\WindowsApps\\') { continue }
        $probeArguments = @($candidate.Arguments) + @('-c',
            "import sys, sqlite3, venv; assert sys.version_info >= (3, 11); assert sys.version_info.releaselevel == 'final'; print(sys.executable)")
        try {
            $result = & $program @probeArguments 2>$null
            if ($LASTEXITCODE -eq 0 -and $result) { return ($result | Select-Object -Last 1).Trim() }
        } catch {
            # A missing interpreter, alias or incompatible version is not a usable candidate.
        }
    }
    return $null
}

try {
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
        throw 'This script requires Windows. See SETUP.md for manual macOS/Linux setup.'
    }
    if ($PSVersionTable.PSVersion -lt [version]'5.1') {
        throw 'PowerShell 5.1 or newer is required. See SETUP.md.'
    }
    Write-Host "F1 ERAs setup | PowerShell $($PSVersionTable.PSVersion) | Root: $root"
    Push-Location -LiteralPath $root
    $locationPushed = $true
    foreach ($path in @('apps/backend/pyproject.toml', 'apps/frontend/package.json',
            'apps/frontend/package-lock.json', 'data/f1db.db', '.vscode/extensions.json')) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Required repository file is missing: $path. Check the clone; see SETUP.md."
        }
    }
    # Refuse stale automation if runtime declarations change; never guess a new range.
    $backendConfig = Get-Content -LiteralPath 'apps/backend/pyproject.toml' -Raw
    $frontendConfig = Get-Content -LiteralPath 'apps/frontend/package.json' -Raw | ConvertFrom-Json
    $lockfile = Get-Content -LiteralPath 'apps/frontend/package-lock.json' -Raw | ConvertFrom-Json
    if ($backendConfig -notmatch '(?m)^requires-python\s*=\s*">=3\.11"\s*$' -or
            $frontendConfig.engines.node -ne '^24.15.0 || ^26.0.0' -or
            $lockfile.lockfileVersion -ne 3) {
        throw 'Runtime requirements/lockfile format differ from this setup baseline. Review SETUP.md and this script.'
    }
    foreach ($path in @('data/f1db.db', 'apps/backend/pyproject.toml',
            'apps/frontend/package.json', 'apps/frontend/package-lock.json')) {
        $protectedHashes[$path] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    }

    Refresh-ProcessPath
    $winget = Find-Tool 'winget.exe'
    if ($winget) { Invoke-Checked $winget @('--version') }
    else { Write-Host 'winget unavailable; existing prerequisites can still be used.' }
    $git = Require-Tool 'git.exe' 'Git.Git'
    Invoke-Checked $git @('--version')
    $gitRoot = (Invoke-Checked $git @('rev-parse', '--show-toplevel') | Out-String).Trim()
    if ([IO.Path]::GetFullPath($gitRoot) -ne [IO.Path]::GetFullPath($root)) {
        throw 'The script is not inside the expected repository root. See SETUP.md.'
    }
    $branch = (Invoke-Checked $git @('branch', '--show-current') | Out-String).Trim()
    Invoke-Checked $git @('status', '--short', '--branch')
    if ($branch -ne 'development/v1') {
        throw "Expected development/v1, found '$branch'. Preserve your work and select the branch deliberately; see SETUP.md."
    }
    $code = Require-Tool 'code.cmd' 'Microsoft.VisualStudioCode'
    Invoke-Checked $code @('--version')

    $python = Find-CompatiblePython
    if (-not $python) {
        # Python minor versions can coexist; do not remove an existing interpreter.
        Install-MissingTool 'Python.Python.3.14'
        $python = Find-CompatiblePython
    }
    if (-not $python) {
        throw 'No compatible Python was found. Restart the terminal or select Python explicitly via SETUP.md.'
    }
    Invoke-Checked $python @('--version')
    $node = Require-Tool 'node.exe' 'OpenJS.NodeJS.LTS' '24.15.0'
    Invoke-Checked $node @('--version')
    # Check the exact declared stable range without needing any downloaded package.
    Invoke-Checked $node @('-e', "const v = process.versions.node; const [a,b,c] = v.split('.').map(Number); if (v.includes('-') || !((a === 24 && (b > 15 || (b === 15 && c >= 0))) || a === 26)) { console.error('Incompatible Node ' + v + '; need ^24.15.0 || ^26.0.0. See SETUP.md.'); process.exit(1); }")
    $npm = Find-Tool 'npm.cmd'
    if (-not $npm) { throw 'npm.cmd is missing from the Node installation. Resolve it via SETUP.md; no automatic replacement.' }
    Invoke-Checked $npm @('--version')

    # Use the single normal VS Code recommendations list, without forcing updates.
    $extensions = @( (Get-Content -LiteralPath '.vscode/extensions.json' -Raw | ConvertFrom-Json).recommendations )
    $installed = @(Invoke-Checked $code @('--list-extensions'))
    foreach ($extension in $extensions) {
        if ($installed -contains $extension) { Write-Host "Extension already installed: $extension" }
        else { Invoke-Checked $code @('--install-extension', $extension) }
    }
    $installed = @(Invoke-Checked $code @('--list-extensions'))
    foreach ($extension in $extensions) {
        if ($installed -notcontains $extension) { throw "Extension verification failed: $extension. See SETUP.md." }
    }

    # Always use the project-local interpreter directly; activation is unnecessary.
    $venvPython = Join-Path $root '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath '.venv') {
        $venvDirectory = Get-Item -LiteralPath '.venv' -Force
        if ($venvDirectory.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw '.venv is a link/junction. Use a real project-local environment; see SETUP.md.'
        }
        if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
            throw 'Existing .venv is incomplete. Resolve it deliberately via SETUP.md; it will not be overwritten.'
        }
        Write-Host 'Reusing root .venv.'
    } else {
        Invoke-Checked $python @('-m', 'venv', '.venv')
    }
    Invoke-Checked $venvPython @('-c', "import pathlib, sys, sqlite3, venv; assert sys.version_info >= (3, 11); assert sys.version_info.releaselevel == 'final'; assert sys.prefix != sys.base_prefix; assert pathlib.Path(sys.prefix).resolve() == pathlib.Path('.venv').resolve(); print(sys.executable)")
    Invoke-Checked $venvPython @('-m', 'pip', '--version')
    Invoke-Checked $venvPython @('-m', 'pip', 'install', '-e', './apps/backend[test]')
    Invoke-Checked $npm @('--prefix', 'apps/frontend', 'ci')

    # Verify against the canonical tracked snapshot, not a session DB override.
    [Environment]::SetEnvironmentVariable('F1_ERAS_DB_PATH', $null, 'Process')
    Invoke-Checked $venvPython @('-m', 'ruff', 'check', '--no-cache', '--config',
        'apps/backend/pyproject.toml', 'apps/backend/src', 'apps/backend/tests')
    Invoke-Checked $venvPython @('-B', '-m', 'pytest', '-c', 'apps/backend/pyproject.toml',
        'apps/backend/tests', '-q', '-p', 'no:cacheprovider')
    Invoke-Checked $npm @('--prefix', 'apps/frontend', 'test')
    # package.json runs tsc --noEmit before vite build.
    Invoke-Checked $npm @('--prefix', 'apps/frontend', 'run', 'build')
    $diagnosticOutput = Invoke-Checked $venvPython @('-B', '-m', 'f1_eras.verification.diagnostic')
    $diagnosticJson = $diagnosticOutput -join "`n"
    Write-Host $diagnosticJson
    # Capture the parsed value first, then enumerate it consistently on 5.1 and 7+.
    $diagnostics = $diagnosticJson | ConvertFrom-Json
    $diagnostics = @($diagnostics)
    $years = @(2010, 2011, 2012, 2013)
    if ($diagnostics.Count -ne $years.Count) { throw 'Diagnostic did not return all four baseline seasons.' }
    foreach ($year in $years) {
        $seasonDiagnostics = @($diagnostics | Where-Object { $_.assessment.year -eq $year })
        if ($seasonDiagnostics.Count -ne 1) { throw "Missing/duplicate diagnostic assessment for $year." }
        $item = $seasonDiagnostics[0]
        if ($item.assessment.state -ne 'passed' -or $item.assessment.comparison -ne 'match' -or
                $item.assessment.trusted_for_normal_use -ne $true -or
                $item.f1db_award_difference_count -ne 0 -or $item.f1db_standing_difference_count -ne 0) {
            throw "Canonical trust/reconciliation failed for $year. Inspect the diagnostic; do not change data to make setup pass."
        }
    }
    Invoke-Checked $git @('diff', '--check')
    Invoke-Checked $git @('status', '--short', '--branch')
    Invoke-Checked $git @('diff')
    $exitCode = 0
} catch {
    Write-Host "`nSetup stopped: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Resolve the reported blocker using SETUP.md, then rerun. Existing work is preserved.'
} finally {
    # Also detect protected-file changes if an install/check fails. Never auto-revert.
    foreach ($path in $protectedHashes.Keys) {
        try {
            $absolutePath = Join-Path $root $path
            if ((Get-FileHash -LiteralPath $absolutePath -Algorithm SHA256).Hash -ne $protectedHashes[$path]) {
                $exitCode = 1
                Write-Host "Protected file changed: $path. Stop and review; it has not been reverted." -ForegroundColor Red
            }
        } catch {
            $exitCode = 1
            Write-Host "Could not verify protected file: $path. $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    [Environment]::SetEnvironmentVariable('F1_ERAS_DB_PATH', $originalDbOverride, 'Process')
    if ($locationPushed) { Pop-Location }
}

if ($exitCode -eq 0) {
    Write-Host "`nREADY FOR DEVELOPMENT" -ForegroundColor Green
    Write-Host 'Automated checks passed. Select .venv in VS Code, then start both services and complete the SETUP.md browser checklist.'
} else {
    Write-Host "`nSETUP INCOMPLETE - see the first error and SETUP.md." -ForegroundColor Red
}
exit $exitCode
