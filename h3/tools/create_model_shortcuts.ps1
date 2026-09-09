[CmdletBinding()]
param()

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$shortcutDirectory = Join-Path $repoRoot 'MODEL_SHORTCUTS'

$shortcuts = @(
    [pscustomobject]@{ Name = 'DOWNLOAD_H3_MODELS'; Target = 'E:\Data\Models\StableDiffusion\minimaxH3'; Description = 'Preferred H3 diffusion model and text encoder library' }
    [pscustomobject]@{ Name = 'DOWNLOAD_H3_LORA'; Target = 'D:\Models\Lora\minimaxH3'; Description = 'Preferred H3 LoRA library' }
    [pscustomobject]@{ Name = 'H3_VAE'; Target = 'E:\Data\Models\VAE\minimaxH3'; Description = 'H3-specific VAE library' }
    [pscustomobject]@{ Name = 'SHARED_CHECKPOINTS'; Target = 'E:\Data\Models\StableDiffusion'; Description = 'Shared checkpoint library' }
    [pscustomobject]@{ Name = 'SHARED_LORA'; Target = 'D:\Models\Lora'; Description = 'Shared LoRA library' }
    [pscustomobject]@{ Name = 'SHARED_VAE'; Target = 'E:\Data\Models\VAE'; Description = 'Shared VAE library' }
    [pscustomobject]@{ Name = 'SHARED_CONTROLNET'; Target = 'E:\Data\Models\ControlNet'; Description = 'Shared ControlNet library' }
    [pscustomobject]@{ Name = 'SHARED_EMBEDDINGS'; Target = 'E:\Data\Models\Embeddings'; Description = 'Shared embeddings library' }
    [pscustomobject]@{ Name = 'SHARED_UPSCALER'; Target = 'E:\Data\Models\ESRGAN'; Description = 'Shared upscaler library' }
    [pscustomobject]@{ Name = 'EASYREFORGE_CHECKPOINTS'; Target = 'E:\EasyReforge\Model\Stable-diffusion'; Description = 'EasyReforge alternate checkpoint library' }
    [pscustomobject]@{ Name = 'EASYREFORGE_LORA'; Target = 'E:\EasyReforge\Model\Lora'; Description = 'EasyReforge alternate LoRA library' }
    [pscustomobject]@{ Name = 'EASYREFORGE_VAE'; Target = 'E:\EasyReforge\Model\VAE'; Description = 'EasyReforge alternate VAE library' }
    [pscustomobject]@{ Name = 'EASYREFORGE_CONTROLNET'; Target = 'E:\EasyReforge\Model\ControlNet'; Description = 'EasyReforge alternate ControlNet library' }
    [pscustomobject]@{ Name = 'EASYREFORGE_UPSCALER'; Target = 'E:\EasyReforge\Model\ESRGAN'; Description = 'EasyReforge alternate upscaler library' }
)

New-Item -ItemType Directory -Path $shortcutDirectory -Force | Out-Null
$shell = New-Object -ComObject WScript.Shell
try {
    foreach ($definition in $shortcuts) {
        $target = [System.IO.Path]::GetFullPath($definition.Target)
        if (-not (Test-Path -LiteralPath $target -PathType Container)) {
            throw "Shortcut target does not exist: $target"
        }

        $shortcutPath = Join-Path $shortcutDirectory ($definition.Name + '.lnk')
        $shortcut = $shell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $target
        $shortcut.WorkingDirectory = $target
        $shortcut.WindowStyle = 1
        $shortcut.Description = $definition.Description
        $shortcut.Save()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($shortcut) | Out-Null
        Write-Output "Created $shortcutPath -> $target"
    }
}
finally {
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($shell) | Out-Null
}
