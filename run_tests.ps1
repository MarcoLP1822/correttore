# run_tests.ps1 - Script PowerShell per eseguire i test
# 
# Usage:
#   .\run_tests.ps1              # Esegue tutti i test
#   .\run_tests.ps1 unit         # Solo test unitari
#   .\run_tests.ps1 integration  # Solo test di integrazione
#   .\run_tests.ps1 performance  # Solo test di performance
#   .\run_tests.ps1 coverage     # Test con coverage report

param(
    [Parameter(Position=0)]
    [ValidateSet('all', 'unit', 'integration', 'performance', 'coverage', 'fast', 'quick')]
    [string]$TestType = 'all'
)

# Colori per output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-Host "`n$('='*60)" -ForegroundColor Cyan

# Determina il comando pytest da eseguire
$pytestCmd = @("pytest")

switch ($TestType) {
    'unit' {
        Write-ColorOutput Yellow "🧪 Eseguendo TEST UNITARI..."
        $pytestCmd += "tests/unit/", "-m", "unit or not integration and not performance"
    }
    'integration' {
        Write-ColorOutput Yellow "🔗 Eseguendo TEST DI INTEGRAZIONE..."
        $pytestCmd += "tests/integration/", "-m", "integration"
    }
    'performance' {
        Write-ColorOutput Yellow "⚡ Eseguendo TEST DI PERFORMANCE..."
        $pytestCmd += "tests/performance/", "-m", "performance"
    }
    'coverage' {
        Write-ColorOutput Yellow "📊 Eseguendo test con COVERAGE..."
        $pytestCmd += "--cov=correttore", "--cov-report=html", "--cov-report=term-missing", "tests/"
    }
    'fast' {
        Write-ColorOutput Yellow "🚀 Eseguendo TEST VELOCI (no API, no slow)..."
        $pytestCmd += "tests/", "-m", "not slow and not api"
    }
    'quick' {
        Write-ColorOutput Yellow "⚡ Eseguendo QUICK TEST (stop al primo errore)..."
        $pytestCmd += "tests/unit/", "-x"
    }
    'all' {
        Write-ColorOutput Yellow "🎯 Eseguendo TUTTI I TEST..."
        $pytestCmd += "tests/"
    }
}

Write-Host "$('='*60)`n" -ForegroundColor Cyan

# Esegui i test
& $pytestCmd[0] $pytestCmd[1..($pytestCmd.Length-1)]
$exitCode = $LASTEXITCODE

# Messaggio finale
Write-Host "`n$('='*60)" -ForegroundColor Cyan
if ($exitCode -eq 0) {
    Write-ColorOutput Green "✅ TUTTI I TEST SONO PASSATI!"
    if ($TestType -eq 'coverage') {
        Write-Host "`n📊 Report coverage disponibile in: htmlcov\index.html" -ForegroundColor Cyan
    }
} else {
    Write-ColorOutput Red "❌ ALCUNI TEST SONO FALLITI (exit code: $exitCode)"
}
Write-Host "$('='*60)`n" -ForegroundColor Cyan

exit $exitCode
