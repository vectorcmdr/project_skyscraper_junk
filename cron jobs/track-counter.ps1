$url = "https://project-skyscraper.com/wp-json/wp/v2/pages/551"
$out = "counter-history.txt"
$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
try {
    $resp = Invoke-RestMethod -Uri $url -ErrorAction Stop
    $val = $resp.content.rendered
    "$ts | $val" | Out-File -Append -FilePath $out
    Write-Host "$ts -> $val"
} catch {
    "$ts | ERROR: $_" | Out-File -Append -FilePath $out
}
