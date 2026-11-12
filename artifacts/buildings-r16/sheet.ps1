param([string]$Dir, [string]$Out, [string]$Pattern = 'r10_block_*', [int]$W = 640, [string]$Tile = '2x')
$files = Get-ChildItem "$Dir/1280/$Pattern.jpg" | ForEach-Object { $_.FullName }
magick montage @files -geometry "${W}x+4+4" -tile $Tile -label '%t' -pointsize 14 $Out
