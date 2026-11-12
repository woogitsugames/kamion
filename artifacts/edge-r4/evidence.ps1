function Assert-EdgeEvidenceInputs {
    $evidence=Get-Content "$PSScriptRoot/evidence-inputs.json" -Raw|ConvertFrom-Json
    foreach($file in $evidence.files){
        if((Get-FileHash -LiteralPath $file.path -Algorithm SHA256).Hash -ne $file.sha256){
            throw "Frozen camera/reference input changed: $($file.path)"
        }
    }
}
