#Requires -Version 5.1
# Start all Legal Multi-Agent System services (Windows PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "Starting Registry service on port 10000..."
$regJob = Start-Job -ScriptBlock { python -m registry }
Start-Sleep -Seconds 2

Write-Host "Starting Tax Agent on port 10102..."
$taxJob = Start-Job -ScriptBlock { python -m tax_agent }

Write-Host "Starting Compliance Agent on port 10103..."
$compJob = Start-Job -ScriptBlock { python -m compliance_agent }
Start-Sleep -Seconds 3

Write-Host "Starting Law Agent on port 10101..."
$lawJob = Start-Job -ScriptBlock { python -m law_agent }
Start-Sleep -Seconds 3

Write-Host "Starting Customer Agent on port 10100..."
$custJob = Start-Job -ScriptBlock { python -m customer_agent }

Write-Host ""
Write-Host "All services started:"
Write-Host "  Registry:         http://localhost:10000"
Write-Host "  Customer Agent:   http://localhost:10100"
Write-Host "  Law Agent:        http://localhost:10101"
Write-Host "  Tax Agent:        http://localhost:10102"
Write-Host "  Compliance Agent: http://localhost:10103"
Write-Host ""
Write-Host "Run test_client.py to send a query:"
Write-Host "  python test_client.py"
Write-Host ""
Write-Host "Press Ctrl+C to stop all services."

try {
    # Wait for any job to complete (they should run indefinitely)
    $completed = Wait-Job -Job @($regJob, $taxJob, $compJob, $lawJob, $custJob) -Any
    Write-Host "`nA service has stopped: $($completed.Name)"
    Receive-Job -Job $completed
}
finally {
    Write-Host "`nStopping all services..."
    Stop-Job -Job @($regJob, $taxJob, $compJob, $lawJob, $custJob)
    Remove-Job -Job @($regJob, $taxJob, $compJob, $lawJob, $custJob) -Force
}
