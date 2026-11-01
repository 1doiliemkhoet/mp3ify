# Creates a new repository and pushes the mp3ify source to GitHub.
# No tokens are stored or read by this script: gh handles authentication.
param(
    [ValidateSet('Private', 'Public')]
    [string]$Visibility = 'Private'
)

$ErrorActionPreference = 'Stop'
$owner = '1doiliemkhoet'
$repo = 'mp3ify'
$fullName = "$owner/$repo"

foreach ($tool in @('git', 'gh')) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Error "Missing $tool. Install Git for Windows and GitHub CLI before running this script."
        exit 1
    }
}

& gh auth status *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'GitHub CLI is not authenticated. Run: gh auth login' -ForegroundColor Yellow
    exit 1
}

$login = (& gh api user --jq '.login' 2>$null | Select-Object -First 1)
if ($LASTEXITCODE -ne 0 -or $login -ne $owner) {
    Write-Error "Signed in as '$login'; expected '$owner'. Use 'gh auth switch' or 'gh auth login' to select the right account."
    exit 1
}

# Never overwrite or push to an existing GitHub repository unexpectedly.
& gh repo view $fullName --json name *> $null
if ($LASTEXITCODE -eq 0) {
    Write-Error "https://github.com/$fullName already exists. No code was pushed."
    exit 1
}

Set-Location $PSScriptRoot
if (-not (Test-Path '.git')) {
    & git init -b main
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

& git add -- mp3ify.py mp3ify.cmd install.cmd build-exe.cmd README.md tests/test_cli.py .gitignore .github/workflows/tests.yml publish-github.ps1 publish-github.cmd
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    & git commit -m 'feat: release mp3ify v1.0.1'
    if ($LASTEXITCODE -ne 0) {
        Write-Error 'Git commit failed. Configure git user.name and user.email, then retry.'
        exit 1
    }
}

$visibilityFlag = if ($Visibility -eq 'Public') { '--public' } else { '--private' }
& gh repo create $fullName $visibilityFlag --source . --remote origin --push
if ($LASTEXITCODE -ne 0) {
    Write-Error 'GitHub repository creation or push failed; review the message above.'
    exit $LASTEXITCODE
}
Write-Host "Uploaded: https://github.com/$fullName" -ForegroundColor Green
