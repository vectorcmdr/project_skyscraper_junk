param([int]$Interval = 0)

$logFile = "anomaly-log.txt"
$homeUrl = "https://project-skyscraper.com/"
$restUrl = "https://project-skyscraper.com/wp-json/wp/v2/pages/551"

function Check {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $results = @{ ts = $ts }

    # Fetch rendered page + REST API concurrently
    $pageTask = Invoke-WebRequest -Uri $homeUrl -UseBasicParsing -TimeoutSec 15
    $restTask = Invoke-RestMethod -Uri $restUrl -TimeoutSec 15

    # Extract counter from rendered HTML
    if ($pageTask.Content -match '<strong>(\d+)</strong>\s*(Live|Inbound)\s+(Connection\s+)?Attempts') {
        $results.renderedNum = [int]$Matches[1]
        $results.renderedLabel = "$($Matches[2]) Attempts"
    } else {
        $results.renderedNum = $null
        $results.renderedLabel = "NOT FOUND"
    }

    # Extract counter from REST API
    if ($restTask.content.rendered -match '<strong>(\d+)</strong>\s*(.+?)</span>') {
        $results.restNum = [int]$Matches[1]
        $results.restLabel = $Matches[2]
    } else {
        $results.restNum = $null
        $results.restLabel = "NOT FOUND"
    }

    # Compare
    $anomaly = $false
    $diff = @()
    if ($results.renderedNum -ne $results.restNum) {
        $anomaly = $true
        $diff += "NUM: rendered=$($results.renderedNum) vs rest=$($results.restNum)"
    }
    if ($results.renderedLabel -ne $results.restLabel) {
        $anomaly = $true
        $diff += "TEXT: rendered='$($results.renderedLabel)' vs rest='$($results.restLabel)'"
    }

    if ($anomaly) {
        $line = "[$ts] ANOMALY - $($diff -join ' | ') | URL: $homeUrl"
    } else {
        $line = "[$ts] OK - rendered=$($results.renderedNum) rest=$($results.restNum) label='$($results.renderedLabel)'"
    }

    $line | Out-File -Append -FilePath $logFile
    Write-Host $line
}

Check

if ($Interval -gt 0) {
    while ($true) {
        Start-Sleep -Seconds $Interval
        Check
    }
}
