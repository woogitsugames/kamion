# Gemini CLI z osobnym profilem (drugie konto Google, wlasciciel 27.11).
# Logowanie trzymane w pliku w profilu $GeminiHome (keytar nie jest zainstalowany),
# wiec nie miesza sie z Antigravity (Menedzer poswiadczen, gemini:antigravity).
# Uzycie: pwsh scripts/cli-jobs/gemini2.ps1 [argumenty gemini]   (bez argumentow = interaktywnie / logowanie)
$GeminiHome = 'C:\Users\matma\gemini2'
New-Item -ItemType Directory -Force "$GeminiHome\AppData\Roaming", "$GeminiHome\AppData\Local" | Out-Null
$env:USERPROFILE = $GeminiHome
$env:HOME = $GeminiHome
$env:APPDATA = "$GeminiHome\AppData\Roaming"
$env:LOCALAPPDATA = "$GeminiHome\AppData\Local"
$env:GEMINI_CLI_HOME = $GeminiHome
& 'C:\Program Files\nodejs\node.exe' 'C:\Users\matma\AppData\Roaming\npm\node_modules\@google\gemini-cli\bundle\gemini.js' @args
exit $LASTEXITCODE
