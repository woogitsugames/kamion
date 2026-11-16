# Runs pure-logic NUnit test classes from the scratch-compiled Game.Tests.EditMode.dll by reflection (no Unity editor).
# Only tests that do not call native Unity code can run here.
param([string[]]$Classes = @('Game.Tests.MenuInputGateTests'), [string[]]$Skip = @())
$out = Join-Path $PSScriptRoot 'csc_out_1300b0aE.dag1'
$dirs = @(
    $out,
    'C:\Program Files\Unity\Hub\Editor\6000.3.28f1\Editor\Data\Managed\UnityEngine',
    'C:\Program Files\Unity\Hub\Editor\6000.3.28f1\Editor\Data\Managed',
    'C:\Users\matma\Documents\Claude\kamion\game\Library\PackageCache\com.unity.ext.nunit@d8c07649098d\net40\unity-custom',
    'C:\Users\matma\Documents\Claude\kamion\game\Library\ScriptAssemblies'
)
$resolver = [System.ResolveEventHandler] {
    param($s, $e)
    $n = ([System.Reflection.AssemblyName]$e.Name).Name
    foreach ($d in $dirs) {
        $p = Join-Path $d "$n.dll"
        if (Test-Path $p) { return [System.Reflection.Assembly]::LoadFrom($p) }
    }
    return $null
}
[System.AppDomain]::CurrentDomain.add_AssemblyResolve($resolver)
$asm = [System.Reflection.Assembly]::LoadFrom((Join-Path $out 'Game.Tests.EditMode.dll'))
$pass = 0; $fail = 0
foreach ($cn in $Classes) {
    $t = $asm.GetType($cn, $true)
    foreach ($m in $t.GetMethods([System.Reflection.BindingFlags]'Public,Instance,DeclaredOnly')) {
        $isTest = $false
        foreach ($a in $m.GetCustomAttributesData()) { if ($a.AttributeType.Name -eq 'TestAttribute') { $isTest = $true } }
        if (-not $isTest) { continue }
        if ($Skip -contains $m.Name) { "SKIP $cn.$($m.Name)"; continue }
        $o = [Activator]::CreateInstance($t)
        try { [void]$m.Invoke($o, $null); $pass++; "PASS $cn.$($m.Name)" }
        catch {
            $fail++
            $ex = $_.Exception; while ($ex.InnerException) { $ex = $ex.InnerException }
            "FAIL $cn.$($m.Name): $($ex.GetType().Name): $($ex.Message)"
        }
    }
}
"TOTAL pass=$pass fail=$fail"
