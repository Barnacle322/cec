# Load environment variables from .env file
$env:_DATABASE_URL="sqlite:///db.sqlite"

if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*([^#].+?)\s*=\s*(.+)\s*$') {
            $varName = $matches[1]
            $varValue = $matches[2] -replace '^"(.*)"$','$1'
            [System.Environment]::SetEnvironmentVariable($varName, $varValue, "Process")
        }
    }
} else {
    Write-Host ".env file not found"
}

$env:FLASK_APP = "src/project"
$env:FLASK_DEBUG = "true"
flask run
