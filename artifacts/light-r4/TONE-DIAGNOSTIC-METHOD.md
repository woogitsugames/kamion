Przyczyna odrzucenia pierwszej planszy High, lokalna wersja Unity URP:
SingleCameraRequest w ProcessRenderRequests wywołuje RenderSingleCameraInternal. Ta ścieżka inicjuje CameraData i renderuje, ale nie wywołuje UpdateVolumeFramework. Zwykły Camera.Render przechodzi przez RenderCameraStack, gdzie UpdateVolumeFramework jest przed inicjalizacją CameraData.
To tłumaczy użycie domyślnego lub poprzedniego stosu gradingu w pierwszym laboratorium. Sama flaga renderPostProcessing=true nie potwierdza wybranego presetu. Pierwsze identyczne High nie dowodzi zgodności tonów ani błędu produktu.
Poprawiona diagnostyka używa dokładnie istniejącego RenderToPixels świata i dodatkowo porównuje rzeczywistą saturację oraz master(.1) VolumeStack z aktywnym runtime LookVolume. Kod lokalnego URP jest źródłem tej analizy, bez odwołania do innej wersji dokumentacji.
Po terminalnym końcu pipeline świata należy uruchomić run-tone-chart.ps1 -OutputName tone-chart-v2. Nie uruchamiać równoległego własnego Unity: main slot z owner gpt-light jest reentrant.
Pierwsze osiem PNG i192próbki środków zachowano jako dowód niewłaściwej metody. Nie używać ich do doboru produkcyjnych parametrów nocy lub korekcji Low.
