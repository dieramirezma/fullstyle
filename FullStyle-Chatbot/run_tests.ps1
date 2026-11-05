$env:PYTHONPATH = "."

# Display introduction
Write-Host "`n===== FullStyle Chatbot Test Runner =====" -ForegroundColor Cyan
Write-Host "This script helps you run tests for the FullStyle Chatbot`n"

function Show-Menu {
    Write-Host "Available Test Options:" -ForegroundColor Green
    Write-Host "1. Run All Tests"
    Write-Host "2. Run Unit Tests Only"
    Write-Host "3. Run Integration Tests Only"
    Write-Host "4. Exit"
    Write-Host
}

function Run-AllTests {
    Write-Host "`nRunning all tests..." -ForegroundColor Yellow
    python -m pytest -v
}

function Run-UnitTests {
    Write-Host "`nRunning unit tests..." -ForegroundColor Yellow
    python -m pytest -v tests/unit/
}

function Run-IntegrationTests {
    Write-Host "`nRunning integration tests..." -ForegroundColor Yellow
    python -m pytest -v tests/integration/
}

function Run-TestConnection {
    Write-Host "`nRunning backend connection test..." -ForegroundColor Yellow
    python -m tests.manual.test_connection_script
}

function Run-TestChatbot {
    Write-Host "`nRunning chatbot query test..." -ForegroundColor Yellow
    python -m tests.manual.test_chatbot_script
}

# Main loop
$choice = 0
while ($choice -ne 6) {
    Show-Menu
    $choice = Read-Host "Enter your choice (1-4)"

    switch ($choice) {
        1 { Run-AllTests }
        2 { Run-UnitTests }
        3 { Run-IntegrationTests }
        4 { Write-Host "`nExiting...`n" -ForegroundColor Cyan }
        default { Write-Host "`nInvalid choice. Please enter a number between 1 and 4.`n" -ForegroundColor Red }
    }

    if ($choice -ne 4) {
        Write-Host "`nPress Enter to continue..."
        Read-Host
    }
}
