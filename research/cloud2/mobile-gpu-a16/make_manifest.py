#!/usr/bin/env python3
"""Generuje manifest.csv pakietu R8 (mobile-gpu-a16).

Jeden wiersz = jeden fakt / liczba / technika / pozycja planu.
Uruchom z katalogu pakietu:  python3 -I make_manifest.py
Wpisy są ręcznie zredagowane (cytaty przepisane z otwartych dokumentów); skrypt tylko składa CSV i liczy sha256
plików z repo (ścieżki względem korzenia worktree).
"""
import csv
import hashlib
import os
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ACC = "2026-11-14"
REPO_SHA = "81c9bae"  # origin/main w chwili startu pakietu

COLS = ["id", "kategoria", "przedmiot", "wartość", "jednostka", "status", "metoda", "cytat", "url_źródła",
        "url_pliku", "licencja", "autor", "data_dostępu", "sha256", "lat", "lon", "kierunek_deg",
        "opis_co_widać", "duplikat_sha256", "uwagi",
        # kolumny pakietu R8
        "urządzenie", "strona_lub_sekcja", "plik_lokalny", "sha_stabilny", "zysk_ms_min", "zysk_ms_max",
        "ryzyko_wizualne", "weryfikacja"]

# --- źródła (url_źródła, url_pliku, plik lokalny, sha256, stabilny?, licencja, autor) ---
GI_G57 = "https://vulkan.gpuinfo.org/api/internal/reports.php?" + urllib.parse.urlencode([
    ("filter[devicename]", "Mali-G57 MC2"), ("draw", "1"), ("start", "0"), ("length", "100"),
    ("columns[0][data]", "id"), ("order[0][column]", "0"), ("order[0][dir]", "desc")])
GI_S926 = "https://vulkan.gpuinfo.org/api/internal/reports.php?" + urllib.parse.urlencode([
    ("filter[devicename]", "samsung SM-S926B"), ("filter[platform]", "android"), ("filter[age]", ""),
    ("filter[apiversion]", ""), ("filter[option]", ""), ("draw", "1"), ("start", "0"), ("length", "50"),
    ("columns[0][data]", "id"), ("order[0][column]", "0"), ("order[0][dir]", "desc")])
VKS = "https://raw.githubusercontent.com/KhronosGroup/Vulkan-Samples/b4fb432b80234e54cf7be7411f20b65494a5b0f5/samples/performance/"
S = {
    "MTK": ("https://www.mediatek.com/products/smartphones-2/mediatek-helio-g99",
            "https://www.mediatek.com/products/smartphones-2/mediatek-helio-g99", "mtk_g99.html",
            "5507c53c18df06a62917c5f2098e347a150f2c9c2adf7cd1fe90829203d19c7a", "nie",
            "© MediaTek — referencja (dane techniczne producenta)", "MediaTek"),
    "DS": ("https://documentation-service.arm.com/static/6659a973876c8d213b7870b5",
           "https://documentation-service.arm.com/static/6659a973876c8d213b7870b5", "arm_6659a973876c8d213b7870b5.pdf",
           "fae47a2fe98ab6f238248a0f88e7d817d7018746222cc0285b27845b755d4648", "tak",
           "© Arm Ltd. 2024 — referencja, nie redystrybuować", "Arm Ltd. (Arm GPU Datasheet)"),
    "BPG": ("https://developer.arm.com/documentation/101897",
            "https://documentation-service.arm.com/static/67a62b17091bfc3e0a947695", "arm_bpg_101897_i10.pdf",
            "9d54788e8c40aaf696bb52a7bae67d1022c0734481b658d1f4d171d91f30c890", "tak",
            "Arm Non-Confidential (Proprietary Notice) — referencja", "Arm Ltd. (101897_0304_10_en, Issue 10)"),
    "GI53265": ("https://vulkan.gpuinfo.org/displayreport.php?id=53265",
                "https://vulkan.gpuinfo.org/displayreport.php?id=53265", "gpuinfo_report_53265.html",
                "4e151651fa13fc849d02d74dce4579e226f3a0cd9c8d8116aaaf6311e4f650aa", "nie",
                "CC BY 4.0 (gpuinfo.org)", "Sascha Willems / zgłaszający"),
    "GI53260": ("https://vulkan.gpuinfo.org/displayreport.php?id=53260",
                "https://vulkan.gpuinfo.org/displayreport.php?id=53260", "gpuinfo_report_53260.html",
                "1fa8be4c214aaa76d9ce4d282fbcdd65cc4b12ab89489492c20d20378521dc91", "nie",
                "CC BY 4.0 (gpuinfo.org)", "Sascha Willems / zgłaszający"),
    "GI52490": ("https://vulkan.gpuinfo.org/displayreport.php?id=52490",
                "https://vulkan.gpuinfo.org/displayreport.php?id=52490", "gpuinfo_report_52490.html",
                "cb6a6c7051156c10151608e8d765abe7f6c150b76cb3f6f8551bcd992cb7ddbb", "nie",
                "CC BY 4.0 (gpuinfo.org)", "Sascha Willems / zgłaszający"),
    "GIL57": ("https://vulkan.gpuinfo.org/listreports.php?devicename=Mali-G57+MC2", GI_G57, "gpuinfo_reports_g57mc2.json",
              "54e74749464166aabd3670b01925e3172765b78301fcb7d09ace9eb6a64af2ac", "nie",
              "CC BY 4.0 (gpuinfo.org)", "Sascha Willems"),
    "GIL926": ("https://vulkan.gpuinfo.org/listreports.php?devicename=samsung+SM-S926B&platform=android", GI_S926,
               "gpuinfo_reports_s926b.json", "3f3629c091cfd3c3b22f84e0c90d32670757451dd6ae01b75c98e83338402731", "nie",
               "CC BY 4.0 (gpuinfo.org)", "Sascha Willems"),
    "EXY": ("https://semiconductor.samsung.com/processor/mobile-processor/exynos-2400/",
            "https://semiconductor.samsung.com/processor/mobile-processor/exynos-2400/", "samsung_exynos2400.html",
            "5d7ce2a51d4563987880c7b1c91f52e53d4fa9aebaad376e99bca49c7c1d2e3a", "nie",
            "© Samsung Electronics — referencja", "Samsung Semiconductor"),
    "GSM": ("https://www.gsmmaniak.pl/1463367/samsung-galaxy-s24-plus-w-polsce-z-procesorem-exynos-2400-na-100-procent/",
            "https://www.gsmmaniak.pl/1463367/samsung-galaxy-s24-plus-w-polsce-z-procesorem-exynos-2400-na-100-procent/",
            "gsmmaniak_s24plus_exynos.html", "63f86f640fe92af6d642ea82983fef948dd418620b22265751a0510b43041241", "nie",
            "© gsmManiaK — referencja (media, nie producent)", "gsmManiaK.pl"),
    "URPPERF": ("https://docs.unity3d.com/6000.3/Documentation/Manual/urp/configure-for-better-performance.html",
                "https://docs.unity3d.com/6000.3/Documentation/Manual/urp/configure-for-better-performance.html",
                "unity_urp_configure_perf.html", "d448845c4475a310282654c50136b58ca540983fee4b59c12e5e7c1ebab7c68d", "nie",
                "© Unity Technologies — referencja", "Unity Technologies"),
    "URPAA": ("https://docs.unity3d.com/6000.3/Documentation/Manual/urp/anti-aliasing.html",
              "https://docs.unity3d.com/6000.3/Documentation/Manual/urp/anti-aliasing.html", "unity_urp_anti-aliasing.html",
              "050625c8b0a903efb7f0788ff1935be9039f4651618fde37cf5e0b9ff784558c", "nie",
              "© Unity Technologies — referencja", "Unity Technologies"),
    "URPASSET": ("https://docs.unity3d.com/6000.3/Documentation/Manual/urp/universalrp-asset.html",
                 "https://docs.unity3d.com/6000.3/Documentation/Manual/urp/universalrp-asset.html",
                 "unity_urp_universalrp-asset.html", "f11107e6c325e7a8025d563300a56e6c093e93e120c834ff3063ab7d8c4568a2", "nie",
                 "© Unity Technologies — referencja", "Unity Technologies"),
    "UANDR": ("https://docs.unity3d.com/6000.3/Documentation/Manual/class-PlayerSettingsAndroid.html",
              "https://docs.unity3d.com/6000.3/Documentation/Manual/class-PlayerSettingsAndroid.html",
              "unity_android_player_settings.html", "0c9e8c31251bdd39d9c0d975b8a3ac57dcb2d1488e98390c0d3ec27ef78f0c6a", "nie",
              "© Unity Technologies — referencja", "Unity Technologies"),
    "UCSREF": ("https://github.com/Unity-Technologies/UnityCsReference/blob/cf583fbe6da6b9fb11e3a1ac03f23df4eb120e9b/Editor/Mono/PlayerSettingsAndroid.bindings.cs",
               "https://raw.githubusercontent.com/Unity-Technologies/UnityCsReference/cf583fbe6da6b9fb11e3a1ac03f23df4eb120e9b/Editor/Mono/PlayerSettingsAndroid.bindings.cs",
               "unitycsref_PlayerSettingsAndroid.bindings.cs", "bcbbc8a3dc51a86a7b91d6ca748cf87c7aab30aee6a4bda3f6accb44f5946e04", "tak",
               "Unity Reference-Only License — referencja", "Unity Technologies"),
    "UUM147578": ("https://issuetracker.unity3d.com/issues/rendering-corruption-on-arm-mali-gpu-when-using-shader-with-framebuffer-and-depthtexture-with-vulkan-api",
                  "https://issuetracker.unity.com/api/v1.0/issues/23555", "unity_issues/issue_23555.json",
                  "7cc44e3aaa4d6b425bff93f2708cfee1bfe9b698e1321adb48c0fdd2e3acb8dc", "nie",
                  "© Unity Technologies — referencja", "Unity QA"),
    "UUM137912": ("https://issuetracker.unity3d.com/issues/android-app-crashes-when-volume-depth-of-field-is-set-to-bokeh-while-using-vulkan-graphics-api",
                  "https://issuetracker.unity.com/api/v1.0/issues/7525", "unity_issues/issue_7525.json",
                  "ac186c2dd051e66d59a3c913b309d8c6acb63fe8ebdb7f7104c806a8487b35e4", "nie",
                  "© Unity Technologies — referencja", "Unity QA"),
    "UUM28518": ("https://issuetracker.unity3d.com/issues/android-libgles-mali-dot-so-crash",
                 "https://issuetracker.unity.com/api/v1.0/issues/18470", "unity_issues/issue_18470.json",
                 "3b948986cf5cf896bf633c59f9893d5d1984a897f3f7fe4df971e32094bfeda1", "nie",
                 "© Unity Technologies — referencja", "Unity QA"),
    "UUM107530": ("https://issuetracker.unity3d.com/issues/build-performance-deteriorates-on-certain-android-devices-when-graphics-api-is-set-to-vulkan-on-an-upgraded-project",
                  "https://issuetracker.unity.com/api/v1.0/issues/20394", "unity_issues/issue_20394.json",
                  "2fd4e2b96b3b9c1f05118745a1d90bceb88c0fbe469850630c9f1b8c3718863c", "nie",
                  "© Unity Technologies — referencja", "Unity QA"),
    "VKMSAA": ("https://github.com/KhronosGroup/Vulkan-Samples/blob/b4fb432b80234e54cf7be7411f20b65494a5b0f5/samples/performance/msaa/README.adoc",
               VKS + "msaa/README.adoc", "vksamples/msaa.adoc",
               "060fb21362f10730b5cf7c0b7c001064189e2ee194ed53e05df4705c02967f70", "tak", "Apache-2.0", "Khronos Group / Arm"),
    "VKRP": ("https://github.com/KhronosGroup/Vulkan-Samples/blob/b4fb432b80234e54cf7be7411f20b65494a5b0f5/samples/performance/render_passes/README.adoc",
             VKS + "render_passes/README.adoc", "vksamples/render_passes.adoc",
             "d2eb6b34587382f15623dad68dd65b8cf7997951c4020ebe7812054514956ad1", "tak", "Apache-2.0", "Khronos Group / Arm"),
    "VKSUB": ("https://github.com/KhronosGroup/Vulkan-Samples/blob/b4fb432b80234e54cf7be7411f20b65494a5b0f5/samples/performance/subpasses/README.adoc",
              VKS + "subpasses/README.adoc", "vksamples/subpasses.adoc",
              "e30404371cc46f3651bf50fba5da1973110197804a9639680e57abd7cd01466d", "tak", "Apache-2.0", "Khronos Group / Arm"),
    "QCOM": ("https://docs.qualcomm.com/doc/80-78185-2/topic/mobile_best_practices.html",
             "https://docs.qualcomm.com/bundle/publicresource/80-78185-2/topics/mobile_best_practices.md",
             "qcom_mobile_best_practices.md", "afc70f6a602cae8116109a863b5272f6acf865b32e1c828f7e21c5ca6e0be0dd", "nie",
             "© Qualcomm — referencja", "Qualcomm (Snapdragon Game Developer Guide 80-78185-2)"),
    "AGI": ("https://developer.android.com/agi/supported-devices", "https://developer.android.com/agi/supported-devices",
            "agi_supported.html", "7f3032ea53675994d6c3e640beb3e9691934b184327ac0be6ef4649e0d74a16b", "nie",
            "CC BY 4.0 (Android docs content license)", "Google"),
    "AMSI": ("https://learn.arm.com/install-guides/ams/", "https://learn.arm.com/install-guides/ams/",
             "learn_arm_ams_install.html", "672f4b1b9ec3bc819b205cd91c7257305a665b7f6fbaf3a4fb55c64729690d50", "nie",
             "© Arm — referencja", "Arm Learning Paths"),
    "AMSS": ("https://learn.arm.com/learning-paths/mobile-graphics-and-gaming/ams/setup_tasks/",
             "https://learn.arm.com/learning-paths/mobile-graphics-and-gaming/ams/setup_tasks/",
             "learn_arm_ams_setup_tasks.html", "21e46007e40969021b772dacc3cd9d57d0f1559b44ecc2b76de53546b77369c4", "nie",
             "© Arm — referencja", "Arm Learning Paths"),
    "HWC": ("https://github.com/ARM-software/libGPUCounters/blob/847a04a1597d132a3746e9c6374d3977cea89a6d/README.md",
            "https://raw.githubusercontent.com/ARM-software/libGPUCounters/847a04a1597d132a3746e9c6374d3977cea89a6d/README.md",
            "libgpucounters_README.md", "059db5293e079606aad591c2cb474c473c4206acf84037b95f0d1874ba69bb2d", "tak",
            "MIT", "Arm Ltd."),
}
# źródła w repo (ścieżka względem korzenia worktree)
R = {
    "DM": "docs/DEVICE_MATRIX.md", "PB": "docs/PERFORMANCE_BUDGETS.md",
    "A0013": "docs/adr/0013-foliage-shader-and-medium-msaa.md", "A0106": "docs/adr/0106-perf-low-a16-r1.md",
    "A0113": "docs/adr/0113-perf-low-a16-r2.md", "A0136": "docs/adr/0136-a16-gpu-regression-impostor-trim.md",
    "A0177": "docs/adr/0177-perf-p99-pso-refresh.md", "G3R": "docs/reports/REVIEW-2026-11-14-s20-gate3-phone.md",
    "URPLOW": "game/Assets/_Project/Rendering/Settings/URP_Low.asset",
    "QP": "game/Assets/_Project/Rendering/Resources/QualityProfile.asset",
    "PS": "game/ProjectSettings/ProjectSettings.asset", "PV": "game/ProjectSettings/ProjectVersion.txt",
    "MR": "game/Assets/_Project/Rendering/Settings/Mobile_Renderer.asset",
}

rows = []


def add(kat, przedmiot, wartosc, jedn, status, metoda, cytat, src, sekcja="", urz="", uwagi="",
        zmin="", zmax="", ryzyko="", weryf=""):
    r = dict.fromkeys(COLS, "")
    r.update({"kategoria": kat, "przedmiot": przedmiot, "wartość": wartosc, "jednostka": jedn, "status": status,
              "metoda": metoda, "cytat": cytat, "data_dostępu": ACC, "uwagi": uwagi, "urządzenie": urz,
              "strona_lub_sekcja": sekcja, "zysk_ms_min": zmin, "zysk_ms_max": zmax, "ryzyko_wizualne": ryzyko,
              "weryfikacja": weryf})
    if src in S:
        u, f, loc, sha, stab, lic, aut = S[src]
        r.update({"url_źródła": u, "url_pliku": f, "plik_lokalny": "files/" + loc, "sha256": sha,
                  "sha_stabilny": stab, "licencja": lic, "autor": aut})
    elif src in R:
        p = R[src]
        with open(os.path.join(REPO, p), "rb") as fh:
            sha = hashlib.sha256(fh.read()).hexdigest()
        r.update({"url_źródła": f"repo:{p}@{REPO_SHA}", "plik_lokalny": p, "sha256": sha, "sha_stabilny": "repo",
                  "licencja": "repo projektu (własne)", "autor": "zespół Kamion"})
    elif src:
        raise KeyError(src)
    rows.append(r)


# ===================== A. Sprzęt: Galaxy A16 / Helio G99 / Mali-G57 MC2 =====================
add("sprzęt", "Galaxy A16 testowy: model, SoC, GPU", "SM-A165F; MT6789 (Helio G99); Mali-G57 MC2", "", "SOURCED",
    "pomiar w repo (adb getprop, 2026-11-09) + GL_RENDERER",
    "Samsung Galaxy A16 | SM-A165F (a16nseea) | MediaTek MT6789 (Helio G99) | Mali-G57 MC2", "DM",
    "tabela Device matrix", "A16")
add("sprzęt", "Helio G99: typ GPU (producent SoC)", "Arm Mali-G57 MC2", "", "SOURCED", "strona producenta SoC",
    "GPU Type Arm Mali-G57 MC2", "MTK", "Specifications > Graphics & Video", "A16")
add("sprzęt", "Helio G99: pamięć", "LPDDR4X, 4266", "Mbps (max)", "SOURCED", "strona producenta SoC",
    "Memory Type LPDDR4X Max Memory Frequency 4266Mbps", "MTK", "Specifications > Memory & Storage", "A16",
    "ten sam tekst marketingowy: 'LPDDR4X memory up to 2,133MHz' (2133 MHz × DDR = 4266 Mbps)")
add("sprzęt", "Helio G99: CPU", "2× Cortex-A76 2,2 GHz + 6× Cortex-A55 2,0 GHz", "", "SOURCED", "strona producenta SoC",
    "2x Arm Cortex-A76 up to 2.2GHz 6x Arm Cortex-A55 up to 2.0GHz", "MTK", "Specifications > Processor", "A16")
add("sprzęt", "Helio G99: maksymalne taktowanie GPU", "brak w źródle producenta", "MHz", "UNVERIFIED",
    "strona MediaTek nie podaje zegara GPU; nie otwarto tablicy OPP jądra MT6789",
    "", "MTK", "Specifications", "A16",
    "potrzebne do przeliczenia ms -> cykle; odczytać na telefonie (devfreq/ged sysfs) albo licznik 'GPU active cycles' w Streamline",
    weryf="adb shell: odczyt bieżącej częstotliwości GPU podczas device-metrics (ścieżka sysfs zależna od jądra — UNVERIFIED)")
add("sprzęt", "Helio G99: szczytowe pasmo DRAM", "≈17,1 przy szynie 32-bit (2×16)", "GB/s", "UNVERIFIED",
    "obliczenie 4266 Mb/s × szerokość szyny / 8; szerokość szyny NIE jest podana przez MediaTek (założenie)",
    "Max Memory Frequency 4266Mbps", "MTK", "Specifications > Memory & Storage", "A16",
    "dla szyny 16-bit byłoby ≈8,5 GB/s; liczba tylko do rzędu wielkości")
add("sprzęt", "Mali-G57: architektura", "Valhall", "", "SOURCED", "Arm GPU Datasheet (2024), wiersz Architecture",
    "Architecture ... Valhall (kolumny Mali-G57 … Immortalis-G715)", "DS", "s.1 tabela Naming/Architecture", "A16")
add("sprzęt", "Mali-G57: jednostki arytmetyczne na rdzeń", "2", "na rdzeń", "SOURCED", "Arm GPU Datasheet, Core Config",
    "Arithmetic units … Mali-G57: 2", "DS", "s.2 Core Config", "A16")
add("sprzęt", "Mali-G57: szerokość warpa", "16", "wątków", "SOURCED", "Arm GPU Datasheet, Core Config",
    "Warp width … Mali-G57: 16", "DS", "s.2 Core Config", "A16", "gpuinfo 53265 też: subgroupSize 16")
add("sprzęt", "Mali-G57: operacje FP32 na cykl na rdzeń", "64", "ops/cykl/rdzeń", "SOURCED",
    "Arm GPU Datasheet, Core Config (FMA liczone jako 2 operacje — wg Arm)",
    "FP32 operations/cycle … Mali-G57: 64", "DS", "s.2 Core Config", "A16")
add("sprzęt", "Mali-G57: operacje FP16 na cykl na rdzeń", "128", "ops/cykl/rdzeń", "SOURCED",
    "Arm GPU Datasheet, Core Config", "FP16 operations/cycle … Mali-G57: 128", "DS", "s.2 Core Config", "A16",
    "FP16 = 2× przepustowość ALU względem FP32")
add("sprzęt", "Mali-G57: piksele i fragmenty na cykl na rdzeń", "2 / 2", "px/cykl/rdzeń", "SOURCED",
    "Arm GPU Datasheet, Core Config", "Fragments/cycle … 2; Pixels/cycle … 2 (kolumna Mali-G57)", "DS",
    "s.2 Core Config", "A16")
add("sprzęt", "Mali-G57: teksele (bilinear) na cykl na rdzeń", "4", "tekseli/cykl/rdzeń", "SOURCED",
    "Arm GPU Datasheet, Core Config + Texturing", "Texels/cycle … 4; Bilinear samples/cycle … 4 (Mali-G57)", "DS",
    "s.2 Core Config, Texturing", "A16")
add("sprzęt", "Mali-G57: pamięć tile na piksel", "256", "bit/piksel", "SOURCED", "Arm GPU Datasheet, Core Config",
    "Tile bits/pixel [2] … Mali-G57: 256", "DS", "s.2 Core Config + przypis 2", "A16",
    "RGBA8 × 4 próbki MSAA = 128 bit, mieści się; RGBA16F × 4 = 256 bit na granicy (przypis: '256 is recommendation')")
add("sprzęt", "Mali-G57: cache tekstur / load-store", "32K / 16K", "bajtów na rdzeń", "SOURCED",
    "Arm GPU Datasheet, Core Config", "Load/store cache size (bytes) 16K; Texture cache size (bytes) 32K (Mali-G57)",
    "DS", "s.2 Core Config", "A16")
add("sprzęt", "Mali-G57: wątki maks. / przy 33–64 rejestrach", "1024 / 512", "wątków na rdzeń", "SOURCED",
    "Arm GPU Datasheet, Valhall ISA Config", "Thread count (max) 1024 … Thread count with 33-64 work registers 512",
    "DS", "s.2 Valhall ISA Config", "A16", "shader > 32 rejestrów = połowa zajętości (gorsze ukrywanie opóźnień)")
add("sprzęt", "Mali-G57: koszt próbkowania głębi z porównaniem (shadow map)", "×2", "mnożnik cykli", "SOURCED",
    "Arm GPU Datasheet, Texturing", "Depth format with reference … Mali-G57: x2", "DS", "s.2 Texturing", "A16",
    "potwierdza BPG s.76: 'if there is a reference or comparison depth, then it is a 2x cost, for example Shadow Maps'")
add("sprzęt", "Mali-G57: koszt ASTC bez EXT_decode_mode", "×2", "mnożnik cykli", "SOURCED",
    "Arm GPU Datasheet, Texturing", "ASTC without EXT_decode_mode … Mali-G57: x2", "DS", "s.2 Texturing", "A16",
    "czy Unity włącza VK_EXT_astc_decode_mode — UNVERIFIED")
add("sprzęt", "Mali-G57: MSAA 2× w sprzęcie", "promowane do 4×", "", "SOURCED", "Arm GPU Datasheet, Core Features",
    "2xMSAA — Automatically promoted to 4xMSAA (Mali-G71 … Immortalis-G715)", "DS", "s.1 Core Features", "A16",
    "Low ma msaa: 2 → na G57 sprzętowo 4×. Repo: MSAA 2×→1× Δ 0 ms (ADR 0106), a 4× było droższe od 2× w lesie (ADR 0013) — sprzeczność do wyjaśnienia",
    weryf="RenderDoc for Arm GPUs / Frame Advisor: liczba próbek załącznika koloru na A16 przy msaa 2 i 4")
add("sprzęt", "Mali-G57: przyspieszone mieszanie FP16 / R11G11B10", "tak", "", "SOURCED", "Arm GPU Datasheet, Core Features",
    "FP16 / R11G11B10 accelerated blending [5] ✓ (od Mali-G57)", "DS", "s.1 Core Features + przypis 5", "A16",
    "przypis 5: 'All have float blending. Valhall adds hardware acceleration for standard blend operations'")
add("sprzęt", "Mali-G57: brak Fragment Prepass (HSR od G725)", "brak (tylko FPK + early ZS)", "", "SOURCED",
    "Arm BPG — Fragment Prepass dopiero od Mali-G725/Immortalis-G925",
    "From Mali-G725 and Immortalis-G925 onwards, there is a new feature called Fragment Prepass.", "BPG", "s.21", "A16",
    "na G57 kolejność rysowania i discard/A2C mają pełne znaczenie")
add("sprzęt", "Mali-G57 MC2: łącznie na cykl (2 rdzenie)", "4 px; 128 ops FP32; 256 ops FP16; 8 tekseli", "na cykl GPU",
    "ESTIMATED", "mnożenie wartości Arm na rdzeń × 2 rdzenie (MC2 z MediaTek)", "", "DS", "s.2", "A16",
    "przeliczenie na GFLOPS wymaga zegara GPU (UNVERIFIED): FP32 GFLOPS = 128 × f[GHz]")
add("sprzęt", "A16 Low: piksele renderu (2340×1080 × 0,75²)", "1 755 × 810 = 1 421 550", "px", "ESTIMATED",
    "obliczenie: ekran z DEVICE_MATRIX × renderScale 0,75 z URP_Low", "m_RenderScale: 0.75", "URPLOW", "", "A16",
    "ekran natywny 2340×1080 = 2 527 200 px (DEVICE_MATRIX: '1080×2340')")
add("sprzęt", "A16 Low: teoretyczny minimalny czas wypełnienia 1 warstwy pełnoekranowej", "1,42 Mpx / (4 px/cykl × f)",
    "ms", "ESTIMATED", "obliczenie z 4 px/cykl (MC2); przy f = 1,0 GHz ≈ 0,36 ms (render 0,75) i ≈ 0,63 ms (natywnie 2,53 Mpx)",
    "", "DS", "s.2", "A16", "f GPU UNVERIFIED — liczby tylko jako dolna granica rzędu wielkości dla przebiegów pełnoekranowych")

# ---- Vulkan (gpuinfo) A16 ----
add("vulkan", "SM-A165F (Android 17): wersja Vulkan / sterownik", "1.3.303 / 54.1.0", "", "SOURCED",
    "raport gpuinfo 53265, tabela Properties", "apiVersion 1.3.303; driverVersion 54.1.0; deviceName Mali-G57 MC2",
    "GI53265", "Properties", "A16")
add("vulkan", "SM-A165F (Android 14): wersja Vulkan / sterownik", "1.1.177 / 32.1.0", "", "SOURCED",
    "raport gpuinfo 53260", "apiVersion 1.1.177; driverVersion 32.1.0", "GI53260", "Properties", "A16",
    "repo DEVICE_MATRIX (Android 16): 'GPU confirmed Mali-G57 MC2, Vulkan 1.1' — sterownik zależy od firmware; sprawdzić na naszym telefonie",
    weryf="adb shell dumpsys gpu / vulkaninfo albo log Unity 'Vulkan API version' na A16")
add("vulkan", "SM-A165F: lista raportów w gpuinfo", "2 raporty SM-A165F (53265, 53260) wśród 396 raportów Mali-G57 MC2",
    "raportów", "SOURCED", "API listy raportów gpuinfo (filter devicename=Mali-G57 MC2); cytat = pola JSON id, device, driver, api, osversion zestawione",
    "\"recordsFiltered\":396 … SM-A165F … 54.1.0 … 1.3.303 … 17.0; SM-A165F … 32.1.0 … 1.1.177 … 14.0", "GIL57", "", "A16")
add("vulkan", "Mali-G57 MC2: maxImageDimension2D", "16384", "px", "SOURCED", "raport gpuinfo 53265, Limits",
    "maxImageDimension2D 16384", "GI53265", "Limits", "A16", "to samo w 53260")
add("vulkan", "Mali-G57 MC2: maxPerStageDescriptorSamplers / SampledImages / UniformBuffers / Resources",
    "8388608 (sterownik 54.1.0); 500000 (32.1.0)", "", "SOURCED", "raporty gpuinfo 53265 i 53260, Limits",
    "maxPerStageDescriptorSamplers 8388608 (53265); maxPerStageDescriptorSamplers 500000 (53260)", "GI53265", "Limits", "A16")
add("vulkan", "Mali-G57 MC2: maxBoundDescriptorSets", "7 (54.1.0); 4 (32.1.0)", "", "SOURCED",
    "raporty gpuinfo 53265 / 53260", "maxBoundDescriptorSets 7 (53265); maxBoundDescriptorSets 4 (53260)", "GI53265",
    "Limits", "A16", "4 zestawy = minimum, które URP/Unity muszą obsłużyć na starszych sterownikach")
add("vulkan", "Mali-G57 MC2: subgroup", "rozmiar 16; operacje basic vote arithmetic ballot shuffle shuffle(relative) clustered quad",
    "", "SOURCED", "raport gpuinfo 53265",
    "subgroupSize 16; subgroupSupportedOperations basic vote arithmetic ballot shuffle shuffle (relative) clustered quad partitioned_bit_nv",
    "GI53265", "Properties/Subgroup", "A16")
add("vulkan", "Mali-G57 MC2: FP16 / int16 / 16-bit storage", "shaderFloat16 true; shaderInt16 true; storageBuffer16BitAccess true",
    "", "SOURCED", "raport gpuinfo 53265, Features", "shaderFloat16 true; shaderInt16 true; storageBuffer16BitAccess true",
    "GI53265", "Features", "A16", "53260 (stary sterownik) też: shaderFloat16 true VK_KHR_shader_float16_int8")
add("vulkan", "Mali-G57 MC2: kompresja tekstur", "ASTC LDR true; ASTC HDR true; ETC2 true; BC false", "", "SOURCED",
    "raport gpuinfo 53265, Features",
    "textureCompressionASTC_LDR true; textureCompressionASTC_HDR true; textureCompressionETC2 true; textureCompressionBC false",
    "GI53265", "Features", "A16")
add("vulkan", "Mali-G57 MC2: maxSamplerAnisotropy", "16", "", "SOURCED", "raport gpuinfo 53265",
    "maxSamplerAnisotropy 16", "GI53265", "Limits", "A16")
add("vulkan", "Mali-G57 MC2: multiDrawIndirect / maxDrawIndirectCount", "false / 1", "", "SOURCED", "raport gpuinfo 53265",
    "multiDrawIndirect false; maxDrawIndirectCount 1", "GI53265", "Features/Limits", "A16",
    "ogranicza GPU-driven rendering (np. GPU Resident Drawer z multi-draw) na A16 — Low ma GRD wyłączony (m_GPUResidentDrawerMode: 0)")
add("vulkan", "Mali-G57 MC2: framebufferColorSampleCounts (jak wyświetla gpuinfo)", "1, 2, 4, 8, 16, 32, 64", "", "SOURCED",
    "raport gpuinfo 53265 (tekst strony)", "framebufferColorSampleCounts 1 , 2 , 4 , 8 , 16 , 32 , 64", "GI53265", "Limits",
    "A16", "UNVERIFIED interpretacja: Arm datasheet wymienia MSAA do 16×; wartości 32/64 to prawdopodobnie sposób wyświetlania maski — nie używać >4×")
add("vulkan", "Mali-G57 MC2: maxComputeWorkGroupInvocations", "512", "", "SOURCED", "raport gpuinfo 53265",
    "maxComputeWorkGroupInvocations 512", "GI53265", "Limits", "A16", "Xclipse 940: 1024")

# ---- S24+ ----
add("sprzęt", "Galaxy S24+ testowy: model, SoC, GPU", "SM-S926B; Exynos 2400 (s5e9945); Xclipse 940", "", "SOURCED",
    "pomiar w repo (adb getprop, ro.hardware.egl=samsung)",
    "Samsung Galaxy S24+ | SM-S926B (e2sxeea), serial RZCX60VE8ZY | Samsung Exynos 2400 (s5e9945) | Xclipse 940 (RDNA3-based; `ro.hardware.egl=samsung`)",
    "DM", "tabela Device matrix", "S24+", "rozstrzyga wariant dla NASZEGO telefonu niezależnie od rynku")
add("sprzęt", "SM-S926B w gpuinfo: GPU w raportach", "Xclipse 940 w 7 z 8 raportów (1 raport 'Mali-G78', id 37901 — anomalia)",
    "raportów", "SOURCED", "API listy raportów gpuinfo (filter devicename=samsung SM-S926B); cytat = pola JSON id, device, gpuname, driver, api, osversion zestawione",
    "52490 samsung SM-S926B Samsung Xclipse 940 25.3.3 1.3.304 17.0 … 37901 samsung SM-S926B Mali-G78 38.0.0 1.1.213 15.0",
    "GIL926", "", "S24+", "model 'B' (Europa/globalny) = Exynos; wariant Snapdragon/Adreno 750 ma inne oznaczenia modelu (UNVERIFIED, nie otwarto listy)")
add("sprzęt", "S24+ w Polsce: wariant SoC (media)", "Exynos 2400 (SM-S926B)", "", "SOURCED",
    "artykuł prasowy przed premierą (źródło wtórne; potwierdza pomiar z repo)",
    "w Europie, a co za tym idzie w Polsce, Samsung Galaxy S24+ (SM-S926B) otrzyma procesor Samsung Exynos 2400", "GSM",
    "treść artykułu", "S24+", "Samsung PL nie publikuje już specyfikacji S24 (strona przekierowuje na S26) — sprawdzono 2026-11-14")
add("sprzęt", "Exynos 2400: GPU", "Xclipse 940, AMD RDNA 3, 'hexa-core GPU', sprzętowy ray tracing", "", "SOURCED",
    "strona producenta SoC",
    "The Exynos 2400 features an Xclipse 940 GPU, built on AMD RDNA™ 3 architecture … deca-core CPU and hexa-core GPU",
    "EXY", "sekcje Gaming/Performance", "S24+")
add("vulkan", "SM-S926B (Android 17): wersja Vulkan / sterownik", "1.3.304 / 25.3.3", "", "SOURCED", "raport gpuinfo 52490",
    "apiVersion 1.3.304; driverVersion 25.3.3; deviceName Samsung Xclipse 940", "GI52490", "Properties", "S24+")
add("vulkan", "Xclipse 940: subgroup", "64 (min 32, max 64)", "wątków", "SOURCED", "raport gpuinfo 52490",
    "subgroupSize 64; minSubgroupSize 32; maxSubgroupSize 64", "GI52490", "Subgroup", "S24+",
    "inna szerokość fali niż Mali (16) — shadery z założeniem rozmiaru subgrupy nieprzenośne")
add("vulkan", "Xclipse 940: limity deskryptorów / zestawy", "4294967295 / 32", "", "SOURCED", "raport gpuinfo 52490",
    "maxPerStageDescriptorSamplers 4294967295; maxBoundDescriptorSets 32", "GI52490", "Limits", "S24+")
add("vulkan", "Xclipse 940: funkcje", "multiDrawIndirect true; ASTC LDR true; ASTC HDR false; ETC2 true; shaderFloat16 true; rayQuery true; fragment shading rate true",
    "", "SOURCED", "raport gpuinfo 52490",
    "multiDrawIndirect true; textureCompressionASTC_HDR false; rayQuery true VK_KHR_ray_query; pipelineFragmentShadingRate true VK_KHR_fragment_shading_rate",
    "GI52490", "Features/Extensions", "S24+", "VRS (fragment shading rate) dostępny na S24+, brak na G57 (datasheet: VRS od G715)")
add("vulkan", "Xclipse 940 / Mali-G57: maxImageDimension2D", "16384 / 16384", "px", "SOURCED", "raporty gpuinfo 52490 / 53265",
    "maxImageDimension2D 16384", "GI52490", "Limits", "S24+, A16")

# ===================== B. Techniki — mechanizm (Arm / Qualcomm / Unity / Khronos) =====================
add("technika", "Alpha-test (discard) na Mali", "wymusza późny test ZS", "", "SOURCED", "Arm BPG",
    "Do not use discard in the fragment shader, as it forces a late ZS test.", "BPG", "s.22", "A16",
    "dotyczy kart liści, impostorów, ścian HLOD (Kamion/Vegetation, Forest Canopy)",
    ryzyko="usunięcie discard = zmiana sylwetek (geometria zamiast alfy)",
    weryf="Streamline: liczniki 'late ZS tested/killed' (BPG s.23)")
add("technika", "Alpha-to-coverage na Mali", "wymusza późny test ZS", "", "SOURCED", "Arm BPG",
    "Do not use alpha-to-coverage, as it forces a late ZS test.", "BPG", "s.22", "A16",
    "Low: leafAlphaToCoverage: 1 (QualityProfile). ADR 0113: koszt lasu = pokrycie/raster dużych powierzchni A2C")
add("technika", "Discard/A2C: co robić, gdy konieczne", "rysować alpha-testowane od przodu do tyłu z testem głębi", "",
    "SOURCED", "Arm BPG",
    "Render alpha-tested geometry front-to-back with depth-testing enabled. Doing so causes as many fragments as possible to fail during early ZS testing.",
    "BPG", "s.104", "A16",
    "repo ADR 0113: kolejność komórek lasu bliżej→dalej dała +0,1..+0,6 ms (gorzej) i została odrzucona — sortowanie per komórka ≠ per fragment")
add("technika", "Forward Pixel Kill (FPK) — kiedy zawodzi", "blending, programowy dostęp do framebuffera, późny ZS, małe trójkąty",
    "", "SOURCED", "Arm BPG",
    "Situations where FPK commonly fails include draw calls using: Alpha blended transparency … Late ZS testing. Small triangles.",
    "BPG", "s.21", "A16")
add("technika", "Mieszanie (alpha blend) na Mali", "wyłącza early ZS i FPK dla mieszanych rysowań", "", "SOURCED", "Arm BPG",
    "blending disables many of the important optimizations that remove fragment overdraw, for example, early ZS testing and FPK.",
    "BPG", "s.67", "A16", "szyba kabiny (pełny ekran w widoku z kabiny) — repo ADR 0106: szyba 3,6–4,3 ms przed szybką ścieżką")
add("technika", "Mieszanie — formaty", "mieszać na unorm, nie na float; brak blendingu dla obiektów nieprzezroczystych", "",
    "SOURCED", "Arm BPG",
    "Use blending on unorm formats, rather than floating-point values. • Always disable blending and alpha-to-coverage if an object is opaque.",
    "BPG", "s.67", "A16", "Low: HDR off → bufor koloru 8-bit unorm (zgodne)")
add("technika", "Depth prepass na Mali", "nie stosować", "", "SOURCED", "Arm BPG",
    "Do not use depth prepass algorithms to remove any fragment overdraw.", "BPG", "s.23", "A16",
    "Unity: Depth Priming 'Disabled for mobile platforms'; repo Mobile_Renderer m_DepthPrimingMode: 0 (zgodne)")
add("technika", "URP: Depth Priming na mobile", "Disabled", "", "SOURCED", "Unity URP docs",
    "set Depth Priming Mode to Auto or Forced for PC and console platforms, or Disabled for mobile platforms.", "URPPERF",
    "Reduce processing time on the GPU", "A16, S24+")
add("technika", "MSAA 4× na Mali (Vulkan)", "tanie przy rozwiązaniu w tile (resolve on write-back)", "", "SOURCED", "Arm BPG",
    "Use 4x MSAA as it is not expensive and provides good image quality improvements.", "BPG", "s.61", "A16",
    "warunek: storeOp DONT_CARE dla obrazu MSAA, pResolveAttachments, LAZILY_ALLOCATED (s.61)")
add("technika", "MSAA — koszt złego resolve (Arm)", "3,9 GB/s vs 0,5 GB/s (4× MSAA, 1080p, 60 FPS)", "GB/s", "SOURCED", "Arm BPG",
    "manually writing and resolving a 4x MSAA 1080p surface at 60 FPS requires 3.9GB/s of memory bandwidth. This is compared to 500MB/s when using an inline resolve.",
    "BPG", "s.61", "A16")
add("technika", "MSAA — pomiar Khronos/Arm (Mali-G76)", "+3 % pasma przy resolve w tile; osobny przebieg resolve +5 GB/s", "",
    "SOURCED", "Vulkan-Samples, sample msaa (pomiar Streamline na Mali-G76)",
    "If this attachment remains in tile memory, the impact on performance remains minimal (3% bandwidth increase shown in the screenshots above) … a separate resolve pass is resulting in 5 GB/s increase in bandwidth.",
    "VKMSAA", "README.adoc", "Mali-G76 (inny GPU)", "liczby z G76, nie z G57 — tylko kierunek")
add("technika", "MSAA — najgorszy przypadek (głębia i kolor MSAA zapisane)", "+6,3 GB/s (302 %)", "GB/s", "SOURCED",
    "Vulkan-Samples, sample msaa (Mali-G76)",
    "In total the read/write bandwidth increase is 6.3GB/s, a 302% increase with respect to the write-back resolve best practice",
    "VKMSAA", "README.adoc (postprocessing)", "Mali-G76 (inny GPU)",
    "dotyczy URP, gdy Depth Texture/Opaque Texture wymusza zapis MSAA — Low ma oba wyłączone")
add("technika", "MSAA 2× na Adreno", "praktycznie darmowe", "", "SOURCED", "Qualcomm Adreno best practices",
    "MSAAx2 is likely to be practically free", "QCOM", "Upscaling/performance list", "Adreno (Fold, wariant S24+ Snapdragon)")
add("technika", "URP: MSAA vs Opaque Texture na mobile", "MSAA ignorowane, gdy brak StoreAndResolve i włączona Opaque Texture", "",
    "SOURCED", "Unity URP docs",
    "On mobile platforms that don't support the StoreAndResolve store action, if Opaque Texture is selected in the URP Asset , Unity ignores the MSAA property at runtime",
    "URPAA", "MSAA", "A16, S24+", "Low: Opaque Texture off (repo) — nie dotyczy")
add("technika", "URP: zalecenie AA na mobile", "Unity zaleca FXAA; MSAA tańsze na tiled GPU bez post-AA", "", "SOURCED",
    "Unity URP docs",
    "For anti-aliasing on mobile platforms, Unity recommends that you use FXAA. … when run on a tiled GPU with no post-processing anti-aliasing or custom render features in use, MSAA is a cheaper option",
    "URPAA", "FXAA / MSAA", "A16", "Arm: '4x MSAA … not expensive'; repo: MSAA 2×→1× Δ 0 ms na G3-B (ADR 0106) — zostawić MSAA, nie dodawać FXAA (pełny ekran)")
add("technika", "Render pass: LOAD zamiast CLEAR — pomiar", "600,2", "MiB/s dodatkowego odczytu", "SOURCED",
    "Vulkan-Samples, sample render_passes (Streamline)",
    "we observe a difference of `1533.9 - 933.7 = 600.2 MiB/s` if we select `LOAD_OP_CLEAR`", "VKRP", "README.adoc",
    "Mali (sample Arm)", "wzór kosztu: width * height * bpp/8 * FPS [MiB/s]")
add("technika", "Render pass: clear/invalidate i Store Actions w URP", "Store Actions Auto lub Discard na słabszym mobile", "",
    "SOURCED", "Unity URP docs",
    "On lower-end mobile platforms, set Store Actions to Auto or Discard, so that URP doesn't use memory bandwidth to copy the render targets",
    "URPPERF", "Reduce how much memory URP uses", "A16", "repo URP_Low m_StoreActionsOptimization: 0 (= Auto wg kolejności opcji Auto/Discard/Store; UNVERIFIED numeracja)")
add("technika", "URP: Native RenderPass na Vulkan", "włączyć", "", "SOURCED", "Unity URP docs",
    "Enable Native RenderPass if you use Vulkan, Metal or DirectX 12 graphics APIs, so that URP automatically reduces how often it copies render textures into and out of memory.",
    "URPPERF", "Universal Renderer asset", "A16, S24+", "repo Mobile_Renderer m_UseNativeRenderPass: 1 (zgodne)")
add("technika", "URP: Depth Texture / Opaque Texture", "wyłączyć, jeśli niepotrzebne", "", "SOURCED", "Unity URP docs",
    "Disable Depth Texture unless you need it … Disable Opaque Texture", "URPPERF", "Reduce how much memory URP uses",
    "A16", "repo URP_Low: m_RequireDepthTexture 0, m_RequireOpaqueTexture 0 (zgodne)")
add("technika", "URP: HDR", "wyłączyć; jeśli potrzebne — 32 Bit (R11G11B10)", "", "SOURCED", "Unity URP docs",
    "Disable High Dynamic Range (HDR) if you don't need it … If you need HDR, set HDR Precision to 32 Bit .", "URPPERF",
    "Reduce how much memory URP uses", "A16", "repo Low: hdr 0 (zgodne); Medium/High: hdr 1 — trzymać 32 bit")
add("technika", "URP: miękkie cienie na tiled GPU", "wysoki koszt", "", "SOURCED", "Unity URP asset docs",
    "Performance impact : High impact on platforms that use tile-based rendering, such as mobile platforms", "URPASSET",
    "Shadows > Soft Shadows", "A16", "repo Low softShadows 0 (zgodne)")
add("technika", "URP: dystans i kaskady cieni", "zmniejszać Max Distance i Cascade Count", "", "SOURCED", "Unity URP docs",
    "reduce Max Distance so that URP processes fewer objects in the shadow pass … reduce Cascade Count to reduce the number of render passes.",
    "URPPERF", "Reduce processing time on the CPU", "A16",
    "repo Low: 35 m, 1 kaskada, 1024 px; ADR 0136 r2c: 25 m / 512 px = szum (±0,3 ms) — wyczerpane")
add("technika", "Próbkowanie shadow map na Valhall", "2× koszt (porównanie głębi)", "", "SOURCED", "Arm BPG",
    "if there is a reference or comparison depth, then it is a 2x cost, for example Shadow Maps.", "BPG", "s.76", "A16")
add("technika", "Tekstury: trilinear, FP32, 3D", "2× koszt; mipmapy zawsze w 3D", "", "SOURCED", "Arm BPG",
    "Trilinear, LINEAR_MIPMAP_LINEAR, filtering has a 2x cost. • 3D formats have a 2x cost. • FP32 formats have a 2x cost. … always use mipmaps for textures that are in 3D scenes.",
    "BPG", "s.76", "A16", "repo ADR 0113: aniso roślinności 2→1 ~0 ms — las nie jest ograniczony teksturami")
add("technika", "Samplery mediump vs highp", "highp może być 2× wolniejszy", "", "SOURCED", "Arm BPG",
    "Use mediump samplers. highp samplers can be half the speed due to their wider data path requirements.", "BPG", "s.76", "A16")
add("technika", "ASTC i tryb dekodowania", "ASTC zalecane; VK_EXT_astc_decode_mode obniża precyzję filtrowania", "", "SOURCED",
    "Arm BPG",
    "ideally Adaptive Scaleable Texture Compression (ASTC) … Use the VK_EXT_astc_decode_modeextension for Vulkan.", "BPG",
    "s.76", "A16", "repo: tekstury Android ASTC 5×5/6×6/8×8 (PERFORMANCE_BUDGETS) — zgodne")
add("technika", "Precyzja half/mediump w shaderach", "16-bit zwykle wystarcza do koloru; lowp = mediump na Arm", "", "SOURCED",
    "Arm BPG",
    "Using 16-bit precision is normally sufficient for computer graphics, especially for fragment shading when computing an output color. … There is no benefit to using lowp for Arm GPUs as it is functionally identical to mediump.",
    "BPG", "s.94", "A16", "zysk tylko gdy shader ograniczony ALU (G57: FP16 128 vs FP32 64 ops/cykl)")
add("technika", "Precyzja: czego nie robić w FP16", "globalna pozycja świata, UV interfejsu", "", "SOURCED", "Arm BPG",
    "Use cases unlikely to work: • Global world position. • UI texture coordinates.", "BPG", "s.95", "A16",
    "świat 1:1 Białystok — pozycje świata w half dadzą artefakty; liczyć delta od kamery (s.95)")
add("technika", "Precyzja atrybutów wierzchołków", "konwersja do FP16/FP32 przy ładowaniu jest darmowa", "", "SOURCED", "Arm BPG",
    "Arm GPU hardware can convert attributes to FP16 and FP32 for free on data load.", "BPG", "s.48", "A16",
    "repo: siatki świata już w kompaktowych formatach (ADR 0012)")
add("technika", "Overdraw — podstawy", "test głębi, culling tylnych ścian, sortowanie, minimum przezroczystości", "", "SOURCED",
    "Arm BPG",
    "Enable depth testing. • Enable back face culling. • Sort objects by distance to camera. … Optimize use of transparency.",
    "BPG", "s.56", "A16")
add("technika", "Pamięć tile przy G-buforze / wielu RT", "16×16 px; od G72 do 256 bit/px; większe = mniejsze kafle", "", "SOURCED",
    "Arm BPG",
    "Most Arm GPUs are designed for rendering 16x16 pixel tiles … From Mali-G72, this count increased to up to 256 bits per pixel",
    "BPG", "s.62", "A16", "argument przeciw Deferred na A16 (Low = Forward, m_RenderingMode 0)")
add("technika", "Subpasy zamiast osobnych passów (Mali-G76)", "≈55 % mniej kafli i pasma", "%", "SOURCED",
    "Vulkan-Samples, sample subpasses (pomiar na Mali-G76)",
    "there is approximately a `55%` reduction in the number of tiles used (`262.2k/s` vs `614.7k/s`), and therefore a `55%` reduction in bandwidth.",
    "VKSUB", "README.adoc", "Mali-G76 (inny GPU)", "dotyczy deferred; w Forward URP Native RenderPass robi scalanie automatycznie")
add("technika", "URP: Render Scale a UI", "skaluje tylko renderowanie gry; UI w natywnej rozdzielczości", "", "SOURCED",
    "Unity URP asset docs", "Note : This only scales the game rendering. UI rendering is left at the native resolution for the device.",
    "URPASSET", "Quality > Render Scale", "A16", "upscale = dodatkowy przebieg pełnoekranowy (Upscaling Filter)")
add("technika", "Unity Android: Blit Type", "Always = render offscreen + blit; Never/Auto = bezpośrednio do framebuffera", "",
    "SOURCED", "Unity Android Player settings",
    "Always : Unity renders to an offscreen buffer and then uses a blit to copy the contents of the buffer to the device's framebuffer. This is compatible with most devices but is usually slower than not using blit.",
    "UANDR", "Other Settings > Blit Type", "A16, S24+")
add("technika", "Unity Android: enum AndroidBlitType", "Always = 0, Never = 1, Auto = 2", "", "SOURCED",
    "UnityCsReference (kod referencyjny edytora)", "Always = 0, … Never = 1,", "UCSREF", "enum AndroidBlitType", "",
    "Auto = 2 wynika z kolejności (linia po Never); potrzebne do odczytu ProjectSettings")
add("technika", "Unity Android: Resolution Scaling Fixed DPI", "skala = min(Target DPI × Factor / Screen DPI, 1)", "", "SOURCED",
    "Unity Android Player settings",
    "Unity calculates the scale using: min(Target DPI * Factor / Screen DPI, 1)", "UANDR", "Resolution Scaling", "A16",
    "alternatywa dla renderScale: mniejszy bufor okna, skalowanie robi kompozytor (zob. Qualcomm/SurfaceFlinger)")
add("technika", "Android: skalowanie końcowe przez SurfaceFlinger", "wydajne skalowanie dwuliniowe przy innym rozmiarze RT", "",
    "SOURCED", "Qualcomm Adreno best practices",
    "On Android, at the end of the frame, if the final render target is a different resolution than the device’s native resolution then SurfaceFlinger will bilinearly rescale the final image to native resolution with efficiency.",
    "QCOM", "Upscaling", "A16, S24+", "źródło Qualcomm (Adreno), ale SurfaceFlinger jest wspólny dla Androida; koszt na A16 UNVERIFIED")
add("technika", "Adreno: co wyłącza LRZ / Early-Z", "blending, stencil, zapis głębi w shaderze, A2C, discard, zmiana funkcji głębi, odczyt FB, maskowane zapisy",
    "", "SOURCED", "Qualcomm Adreno best practices",
    "blending, stencil use, manually writing to the depth buffer or UAVs, alpha-to-coverage use, the “discard” shader keyword, changing the depth comparison operator, reading from the framebuffer, or masked writes … all might disable LRZ",
    "QCOM", "LRZ, Early-Z and Fast-Z", "Adreno (Fold)", "zalecenie: takie rysowania jak najpóźniej w klatce")
add("technika", "Adreno: discard", "unikać; jeśli musi — po wszystkich nieprzezroczystych", "", "SOURCED",
    "Qualcomm Adreno best practices",
    "If a shader cannot avoid discard operations, the cost can be mitigated by executing the shader after (ideally all) opaque draw calls",
    "QCOM", "Avoid discarding pixels in the fragment shader", "Adreno (Fold)")
add("technika", "Adreno: MSAA attachment w pamięci leniwej", "VK_MEMORY_PROPERTY_LAZILY_ALLOCATED_BIT dla MSAA i głębi", "",
    "SOURCED", "Qualcomm Adreno best practices",
    "use VK\\_MEMORY\\_PROPERTY\\_LAZILY\\_ALLOCATED\\_BIT for buffers that are not read from outside of the renderpass (especially MSAA attachments",
    "QCOM", "Memory", "Adreno; Arm BPG s.61 mówi to samo dla Mali")
add("technika", "URP: LOD Cross Fade na słabym mobile", "wyłączyć (alpha test)", "", "SOURCED", "Unity URP docs",
    "On lower-end mobile platforms, disable LOD Cross Fade , so that URP doesn't use alpha testing to fade level of detail (LOD) meshes in and out.",
    "URPPERF", "Reduce processing time on the GPU", "A16",
    "repo: URP_Low m_EnableLODCrossFade: 1, ale wszystkie LODGroup mają fadeMode None (WorldSceneBuilder/TruckAssetBuilder) → koszt GPU ≈ 0; wyłączenie tylko zmniejsza warianty")
add("technika", "URP: sondy odbić na słabym mobile", "wyłączyć Probe Blending i Box Projection", "", "SOURCED", "Unity URP docs",
    "On lower-end mobile platforms, if you use Reflection Probes , disable Probe Blending and Box Projection .", "URPPERF",
    "Reduce processing time on the CPU", "A16", "repo URP_Low: m_ReflectionProbeBlending 1, m_ReflectionProbeBoxProjection 1 — kandydat (głównie CPU)")
add("technika", "URP: światła dodatkowe", "Disabled lub Per Vertex", "", "SOURCED", "Unity URP docs",
    "Set Additional Lights to Disabled , or Per Vertex if you use the Forward rendering path.", "URPPERF",
    "Reduce processing time on the GPU", "A16",
    "repo URP_Low m_AdditionalLightsRenderingMode: 1, limit 2; Low ma streetLights 0 i analityczne plamy latarni — zysk zależy od tego, czy w scenie są światła (UNVERIFIED)")

# ===================== C. Narzędzia pomiaru =====================
add("narzędzie", "Arm Performance Studio (Streamline, Performance Advisor, Frame Advisor, Mali Offline Compiler, RenderDoc for Arm GPUs)",
    "bezpłatne", "", "SOURCED", "Arm Learning Paths — instalacja",
    "All features of Arm Performance Studio are available free of charge without any additional license.", "AMSI", "", "A16")
add("narzędzie", "Streamline na Androidzie: wymagania aplikacji Unity", "Development Build (debuggable)", "", "SOURCED",
    "Arm Learning Paths — przygotowanie aplikacji",
    "To set Unity applications to be debuggable, enable Development Build in Build settings .", "AMSS", "Build your application",
    "A16", "repo: build-android.ps1 ma -Development; release APK nie jest debuggable → liczniki tylko w buildzie dev (inny profil CPU)")
add("narzędzie", "Android GPU Inspector (AGI) — lista wspieranych urządzeń", "Mali: tylko G76/G77/G78/G710 na liście; A16/G57 nie wymieniony",
    "", "SOURCED", "dokumentacja AGI",
    "The devices listed below and new devices with Android 12 (except some Android-Go devices) are expected to pass this validation check.",
    "AGI", "AGI supported devices", "A16", "A16 (Android 16) 'expected to pass' — UNVERIFIED, uruchomić walidację AGI")
add("narzędzie", "libGPUCounters (dawniej HWCPipe)", "liczniki Mali od G71 w aplikacji; MIT; tylko sterownik komercyjny Arm", "",
    "SOURCED", "README repozytorium Arm",
    "The project aims to support all Arm GPU products from the Mali-G71 series or later … This library only supports devices using the Arm commercial driver.",
    "HWC", "Supported devices", "A16", "opcja: GPU active cycles w DiagnosticsSampler (niezależne od DVFS) — wymaga wtyczki natywnej; dostęp bez roota UNVERIFIED")
add("narzędzie", "Unity: narzędzia do mierzenia ustawień URP", "Unity Profiler / RenderDoc / Xcode", "", "SOURCED", "Unity URP docs",
    "You can use the Unity Profiler or a GPU profiler such as RenderDoc or Xcode to measure the effect of each setting", "URPPERF",
    "wstęp", "A16, S24+")
add("narzędzie", "Mali Offline Compiler — ograniczenie", "liczy 1 cykl/teksel; trzeba ręcznie 'de-rate' dla trilinear/formatów", "",
    "SOURCED", "Arm BPG",
    "the texture cycle counts from the tool assumes one cycle per texel performance. … You must manually de-rate the texture performance",
    "BPG", "s.77", "A16")

# ===================== D. Znane problemy Unity / sterownik =====================
add("problem", "UUM-147578: korupcja renderu na Mali (Vulkan), shader z FrameBuffer + DepthTexture",
    "naprawione w 6000.3.28f1; Mali-G57 MC2 (Redmi Note 11S) NIE reprodukuje", "", "SOURCED", "Unity Issue Tracker (API JSON)",
    "Rendering corrupted with white square artifacts … Not reproducible with these devices: … Xiaomi Redmi Note 11S (2201117SY), CPU: MediaTek Helio G96 (MT6781), GPU: Mali-G57 MC2",
    "UUM147578", "description + issuePorts (6000.3.X fixedInVersion 6000.3.28f1)", "Mali (G715/G925)",
    "projekt: m_EditorVersion 6000.3.28f1 = wersja z poprawką")
add("problem", "UUM-137912: crash przy Depth of Field Bokeh na Vulkan (Mali)", "Galaxy A15 5G (Mali-G57 MC2) NIE reprodukuje; 6000.3 otwarte; poprawka 6000.6.3f1",
    "", "SOURCED", "Unity Issue Tracker (API JSON)",
    "App crashes on launch … VLNQA00655, Samsung Galaxy A15 5G (SM-A156E), CPU: -, GPU: Mali-G57 MC2, OS: 15 … Note: Not reproducible with OpenGLES3 Graphics API",
    "UUM137912", "description + issuePorts", "Mali (A54/A25)",
    "repo: DefaultVolumeProfile DepthOfField mode 0 (Off), Low bez post — ryzyko pomijalne; nie włączać Bokeh")
add("problem", "UUM-28518: crash libGLES_mali.so w FrameTimingManagerGLES::GetGPUFrameEvents",
    "dotyczy ścieżki GLES; wśród GPU klientów Mali-G57 MC2", "", "SOURCED", "Unity Issue Tracker (API JSON)",
    "libunity.so!FrameTimingManagerGLES::GetGPUFrameEvents … found three devices that coincided with some of the following Mali GPUs: G78, G68 MC4, G57 MC3, G57 MC2, G77 MC9, and G57",
    "UUM28518", "description", "Mali (GLES)",
    "projekt mierzy GPU przez FrameTimingManager; na A16 działa Vulkan (fallback GLES3 w ProjectSettings) — przy fallbacku GLES ryzyko crasha w telemetrii")
add("problem", "UUM-107530: spadek wydajności Vulkan po upgradzie projektu (2022.3/6000.0)", "reprodukcja na Adreno 618 itd.; Mali G76/G77/G78/G710 nie",
    "", "SOURCED", "Unity Issue Tracker (API JSON)",
    "There are two regressions, one in 2022.3 and the other in 6000.0 … Not reproducible with: … GPU: Mali-G77 … GPU: Mali-G76 … GPU: Mali-G78 … GPU: Mali-G710",
    "UUM107530", "description", "Adreno (Fold)", "G57 nie testowany w zgłoszeniu; dla A16 bez dowodu")
add("problem", "Projekt: wersja Unity", "6000.3.28f1", "", "SOURCED", "repo ProjectVersion.txt",
    "m_EditorVersion: 6000.3.28f1", "PV", "", "")
add("problem", "Projekt: API grafiki Android", "Vulkan, potem OpenGLES3 (ręcznie, nie Automatic)", "", "ESTIMATED",
    "dekodowanie m_APIs '150000000b000000' jako int32 LE: 0x15=21 (Vulkan), 0x0b=11 (OpenGLES3) — numeracja GraphicsDeviceType z pamięci, UNVERIFIED",
    "m_APIs: 150000000b000000 m_Automatic: 0", "PS", "m_BuildTargetGraphicsAPIs AndroidPlayer", "A16",
    "DEVICE_MATRIX potwierdza Vulkan na A16 w działaniu")

# ===================== E. Stan w repo (już zmierzone) =====================
add("stan", "Bramka 3 A16 Low (APK 77cfd94bf8): GPU p95", "G3-A 34,51; G3-B 34,28 (budżet 33,3)", "ms", "SOURCED",
    "repo, gate3-result.json streszczony w recenzji",
    "G3-A p95 33,46 / p99 33,57 ms, > 50 ms: 2, GPU p95 34,51, PSS 917,5 MB; G3-B p95 33,45 / p99 33,62 ms, > 50 ms: 6, GPU p95 34,28",
    "G3R", "Wydajność", "A16", "luka ≈ 1,0–1,2 ms GPU p95")
add("stan", "ADR 0136 r2c: Low po wszystkich cięciach profilu", "GPU p95 34,0; brakuje 0,7 ms", "ms", "SOURCED", "repo ADR",
    "Low r2 w tej sesji: GPU p95 34,0 ms (cel 33,3, brakuje 0,7 ms)", "A0136", "Runda 2c", "A16",
    "wniosek ADR: 'Kolejne ~0,7 ms wymaga zmiany treści, nie cięcia profilu'")
add("stan", "Governor (DVFS) Mali przy limicie 30 FPS", "+1,5–2", "ms GPU", "SOURCED", "repo ADR 0136 (pomiar z/bez limitu)",
    "Przy limicie 30 FPS governor Mali dodaje ~1,5–2 ms", "A0136", "Diagnoza", "A16",
    "czas GPU w ms przy limicie mierzy też obniżony zegar — metryka 'GPU p95 ≤ 33,3' miesza pracę i DVFS")
add("stan", "Rozkład GPU A16 Low (G3-B, bez limitu): ciężarówka w kamerze", "4,7–5,4 (szyba 3,6–4,3)", "ms", "SOURCED",
    "repo ADR 0106 (A/B przeplatane)", "Own truck in the main camera | 4.7-5.4 (cab glass 3.6-4.3, of which raster+blend ~1.2",
    "PB", "Measured: A16 Low GPU frame breakdown", "A16", "po szybkiej szybie −0,9 ms; ADR 0136: ciężarówka +4,03")
add("stan", "Rozkład GPU A16 Low: drzewa + HLOD", "2,4–3,0", "ms", "SOURCED", "repo ADR 0106",
    "Instanced trees + forest HLOD | 2.4-3.0 (HLOD edge walls 1.8, HLOD canopy 0.9, impostors 1.6", "PB",
    "Measured: A16 Low GPU frame breakdown", "A16")
add("stan", "Rozkład GPU A16 Low: skala renderu 0,75 → 0,70/0,65/0,60", "2,0 / 3,3 / 4,8", "ms", "SOURCED", "repo ADR 0106",
    "Render scale 0.75 -> 0.70 / 0.65 / 0.60 | 2.0 / 3.3 / 4.8 (~13 ms pixel-proportional at 0.75)", "PB",
    "Measured: A16 Low GPU frame breakdown", "A16", "D50: bez obniżania do 0,70 (decyzja właściciela)")
add("stan", "Rozkład GPU A16 Low: far clip / LOD bias", "900→720 m: 0,7; →450 m: 1,4; LOD bias ×0,6: 1,4", "ms", "SOURCED",
    "repo ADR 0106", "Far clip 900 -> 720 / 450 m; LOD bias x0.6 | 0.7 / 1.4; 1.4", "PB", "Measured: A16 Low GPU frame breakdown", "A16")
add("stan", "Rozkład GPU A16 Low: lusterka / cienie / MSAA", "lusterka 0,75–1,25; cienie off 0,9; MSAA 2×→1× 0", "ms", "SOURCED",
    "repo ADR 0106", "Mirrors (1 render/frame); mirror LOD 0.5 | 0.75-1.25; 0.1 … Shadows off; props + parked cars; HUD | 0.9; 0.3; 0.3 … MSAA 2x -> 1x; sky clouds/haze; A8 vehicle look | 0; 0; 0",
    "PB", "Measured: A16 Low GPU frame breakdown", "A16")
add("stan", "ADR 0013: MSAA i A2C w lesie DK8 (Medium)", "MSAA 4× 61,3 → 2×/1× 50,4; A2C off 58,7", "ms GPU p50", "SOURCED",
    "repo ADR 0013 (ablacja na A16)", "baseline (URP Lit leaves, MSAA 4×, HDR + post) | 61.3 ms … MSAA 2× / 1× | 50.4 / 50.4 ms … alpha-to-coverage off | 58.7 ms",
    "A0013", "Context", "A16", "4× droższe od 2× mimo 'promocji 2×→4×' w datasheet — hipoteza: Unity/sterownik nie używa 2× na G57 albo A2C liczy pokrycie inaczej (UNVERIFIED)")
add("stan", "ADR 0113: natura kosztu lasu", "pokrycie/raster dużych powierzchni A2C, nie ALU ani filtrowanie", "", "SOURCED",
    "repo ADR 0113", "The forest cost on the G57 is coverage/raster of large alpha-to-coverage surfaces, not fragment ALU or texture filtering.",
    "PB", "ADR 0113 (r2)", "A16")
add("stan", "ADR 0136: ciasne impostory", "impostory 1,37 → 0,51 ms średnio (las: 6,6/4,8 → 1,9/2,3)", "ms", "SOURCED", "repo ADR 0136",
    "impostory **1,37 → 0,51 ms** średnio, w oknach lasu **6,6 / 4,8 → 1,9 / 2,3 ms**", "A0136", "Wynik", "A16",
    "dowód, że przycinanie pustej alfy działa na G57")
add("stan", "Otwarte: karty liści LOD0/LOD1", "pokrycie alfy 23–48 % quada", "%", "SOURCED", "repo ADR 0136 Otwarte",
    "Karty liści LOD0/LOD1 (`leaves_*.png` pokrycie 23–48 %) — ta sama technika na kartach w `trees.glb`", "A0136", "Otwarte", "A16")
add("stan", "Otwarte: ściany HLOD", "górne ~12 % atlasu puste", "%", "SOURCED", "repo ADR 0136 Otwarte",
    "Ściany HLOD: górne ~12 % atlasu puste — przycięcie w `forest_hlod.py` (mały zysk).", "A0136", "Otwarte", "A16")
add("stan", "URP_Low: ustawienia", "renderScale 0,75; MSAA 2; HDR off; depth/opaque tex off; cienie 1024/1 kaskada/35 m twarde; SRP Batcher on",
    "", "SOURCED", "repo URP_Low.asset",
    "m_RenderScale: 0.75 m_MSAA: 2 m_SupportsHDR: 0 m_RequireDepthTexture: 0 m_MainLightShadowmapResolution: 1024 m_ShadowCascadeCount: 1 m_ShadowDistance: 35 m_SoftShadowsSupported: 0 m_UseSRPBatcher: 1",
    "URPLOW", "", "A16")
add("stan", "Mobile_Renderer: ścieżka i opcje", "Forward; Native RenderPass on; Depth Priming off; Intermediate Texture Auto", "",
    "SOURCED", "repo Mobile_Renderer.asset",
    "m_UseNativeRenderPass: 1 m_RenderingMode: 0 m_DepthPrimingMode: 0 m_IntermediateTextureMode: 0", "MR", "", "A16")
add("stan", "ProjectSettings Android: Blit Type", "0 = Always (offscreen + blit co klatkę)", "", "SOURCED",
    "repo ProjectSettings.asset + enum z UnityCsReference", "androidBlitType: 0", "PS", "PlayerSettings", "A16, S24+",
    "NOWE: nie występuje w żadnym ADR/raporcie repo (grep 'blit type' 2026-11-14)")
add("stan", "ProjectSettings Android: pre-transform / Swappy", "vulkanEnablePreTransform 1; androidUseSwappy 1", "", "SOURCED",
    "repo ProjectSettings.asset", "vulkanEnablePreTransform: 1 … androidUseSwappy: 1", "PS", "PlayerSettings", "A16")

# ===================== F. Plan oszczędności A16 Low (ranking) =====================
P = "pwsh scripts/device-metrics.ps1 -Launch -DurationSeconds 90 (G3-A i G3-B, przeplatane A/B w jednym APK lub para APK o tym samym versionCode; GPU p50/p95, klatki >40 ms)"
add("plan", "P1: Blit Type Always → Auto (lub Never)", "usuwa 1 kopię pełnoekranową 2340×1080", "", "UNVERIFIED",
    "mechanizm: Unity doc (Always = offscreen + blit, 'usually slower'); zysk = szacunek: ≥ 1 warstwa 2,53 Mpx (≈0,63 ms przy f=1 GHz, 4 px/cykl) + ~20 MB/klatkę pasma (odczyt 2,53 Mpx×4 B + zapis)",
    "Always : Unity renders to an offscreen buffer and then uses a blit", "UANDR", "", "A16, S24+",
    "ustawienie gracza (nie launch-arg) → para APK; Never może nie działać na niektórych urządzeniach (doc) — Auto bezpieczniejsze",
    "0,3", "1,5", "brak (ten sam obraz); ryzyko zgodności urządzeń (czarny ekran) przy Never",
    P + "; dodatkowo RenderDoc/Frame Advisor: liczba przebiegów po kamerze")
add("plan", "P2: skala 0,75 przez rozdzielczość okna (Fixed DPI / Screen.SetResolution) zamiast URP renderScale",
    "usuwa upscale URP + bufor pośredni; skaluje kompozytor", "", "UNVERIFIED",
    "mechanizm: Unity Fixed DPI + Qualcomm (SurfaceFlinger skaluje wydajnie); zysk = szacunek 1 przebieg pełnoekranowy + zapis RT pośredniego",
    "SurfaceFlinger will bilinearly rescale the final image to native resolution with efficiency.", "QCOM", "", "A16",
    "zgodne z D50 (skala zostaje 0,75); UI też w 0,75 (miększy HUD/tekst) — decyzja właściciela; łączy się z P1",
    "0,3", "1,5", "HUD i tekst renderowane w 1755×810 (miękkie); skalowanie dwuliniowe zamiast filtra URP",
    P + "; visual-qa HUD na zrzucie z telefonu")
add("plan", "P3: przycięcie kart liści LOD0/LOD1 (jak ImpostorTrim)", "mniej rasteryzacji pustej alfy A2C", "", "UNVERIFIED",
    "analogia do zmierzonego ImpostorTrim (−0,86 ms średnio, −4,7/−2,5 ms w lesie) przy pokryciu kart 23–48 % (vs 6–13 % impostorów) — mniejszy względny zysk",
    "Karty liści LOD0/LOD1 (`leaves_*.png` pokrycie 23–48 %)", "A0136", "", "A16",
    "dotyczy głównie G3-B/las; G3-A ≈ 0 (brak lasu wg ADR 0136)", "0,2", "1,0",
    "brak przy dylatacji jak w ImpostorTrim (PSNR ≥ 58 dB w 0136)", P + "; PSNR kamer kontrolnych Low")
add("plan", "P4: LOD1/LOD2 aut z 1–2 submeshami (ADR 0153) i powrót/utrzymanie cull 150 m", "mniej zgłoszeń; GPU-czas Mali rośnie z CPU zgłaszania",
    "", "UNVERIFIED", "repo ADR 0136 r2: auta osobowe +1,29 ms GPU / +4,44 ms CPU na G3-A (portret, bez limitu); ADR 0153 zaimplementowany, niezmierzony na A16",
    "auta osobowe + vany + contact (`diagA2`) | +1,29 | +4,44", "A0136", "Runda 2", "A16",
    "zysk przy limicie 30 FPS mniejszy (governor zjada część — cull 100 m dał tylko −0,17 ms)", "0,1", "0,6", "brak (atlas detali w dalekich LOD)", P)
add("plan", "P5: Mali Offline Compiler na shaderach świata/roślinności (statyczny profil G57) + half tam, gdzie ALU-bound",
    "lista shaderów ograniczonych ALU / rejestrami (>32 rejestry = połowa wątków)", "", "UNVERIFIED",
    "BPG: FP16 2× przepustowość; datasheet: 33–64 rejestry → 512 wątków; zysk tylko w shaderach ALU-bound (las nie jest — ADR 0113)",
    "Thread count with 33-64 work registers … 512", "DS", "s.2", "A16",
    "bez telefonu: można zrobić w chmurze/CI (malioc z Performance Studio)", "0", "1,0",
    "pasmowanie/artefakty przy half dla pozycji świata (BPG s.95) — tylko kolor/oświetlenie",
    "malioc -c Mali-G57 na wariantach Vulkan; potem " + P)
add("plan", "P6: szyba kabiny — mniejsza powierzchnia mieszania", "mniej pełnoekranowego blendu (wyłącza FPK/early ZS)", "", "UNVERIFIED",
    "repo: szyba 3,6–4,3 ms (ADR 0106, przed szybką ścieżką −0,9); BPG: blending wyłącza FPK; propozycja: maska — mieszać tylko obszar z refleksem/brudem, resztę pominąć",
    "blending disables many of the important optimizations that remove fragment overdraw", "BPG", "s.67", "A16",
    "wymaga zmiany materiału szyby; widok z kabiny = główny widok jazdy", "0,3", "1,5",
    "utrata subtelnego przyciemnienia/refleksu na części szyby — visual-qa cab-dash/cab-gate", P + "; widok kabiny")
add("plan", "P7: ściany HLOD — przycięcie pustych ~12 % atlasu", "mniej pustej alfy", "", "UNVERIFIED",
    "repo ADR 0136 Otwarte ('mały zysk'); ściany HLOD kosztują ~1,8 ms (0106/0136) → 12 % powierzchni ≈ do ~0,2 ms przy proporcjonalności do pokrycia",
    "Ściany HLOD: górne ~12 % atlasu puste — przycięcie w `forest_hlod.py` (mały zysk).", "A0136", "Otwarte", "A16", "",
    "0", "0,2", "brak przy zachowaniu konturu", P)
add("plan", "P8: liczenie pracy GPU w cyklach, nie w ms (licznik 'GPU active cycles' lub ms × f GPU)", "metryka niezależna od DVFS",
    "", "UNVERIFIED", "repo: governor dodaje 1,5–2 ms przy limicie; propozycja metodyczna, nie oszczędność",
    "Przy limicie 30 FPS governor Mali dodaje ~1,5–2 ms", "A0136", "Diagnoza", "A16",
    "może się okazać, że część 'nadwyżki' 34,5 ms to niski zegar przy niedociążeniu — wymaga odczytu zegara GPU", "0", "0", "brak",
    "device-metrics: dopisać próbkę częstotliwości GPU (sysfs, UNVERIFIED ścieżka) albo libGPUCounters w buildzie dev")
add("plan", "P9: sondy odbić Low — Probe Blending i Box Projection off", "mniej pracy CPU/sterownika; GPU marginalnie", "", "UNVERIFIED",
    "Unity: zalecenie dla słabego mobile (CPU); na Low przechwyt env 64 px co 10 klatek (PERFORMANCE_BUDGETS) — zysk GPU nieznany",
    "On lower-end mobile platforms, if you use Reflection Probes , disable Probe Blending and Box Projection .", "URPPERF",
    "", "A16", "przełącznik w URP_Low (generator ProjectSetup)", "0", "0,3", "odbicia mniej dopasowane do wnętrz/placów", P)
add("plan", "P10: światła dodatkowe Low → Disabled (jeśli w scenie brak świateł punktowych na Low)", "mniej wariantów i pętli świateł",
    "", "UNVERIFIED", "Unity: zalecenie; Low ma streetLights 0 i analityczne plamy — jeśli brak świateł, zysk GPU ≈ 0",
    "Set Additional Lights to Disabled , or Per Vertex", "URPPERF", "", "A16",
    "najpierw sprawdzić Frame Debuggerem, czy jakieś światło dodatkowe jest aktywne w G3", "0", "0,3",
    "utrata świateł dodatkowych (jeśli są, np. reflektory?)", P)
add("plan", "P11: far clip 900 → 720 m na Low", "zmierzone 0,7 ms (ADR 0106)", "ms", "SOURCED",
    "repo ADR 0106 (A/B na A16)", "Far clip 900 -> 720 / 450 m; LOD bias x0.6 | 0.7 / 1.4; 1.4", "PB", "", "A16",
    "zmiana obrazu (horyzont); sprzeczne z D51 rozpoznawalność? — decyzja właściciela; pomiar sprzed s11–s12 (powtórzyć)",
    "0,5", "0,7", "bliższy horyzont/mgła na prostych", P)
add("plan", "P12: LOD bias Low 0,5 → 0,3 (×0,6)", "zmierzone 1,4 ms (ADR 0106)", "ms", "SOURCED", "repo ADR 0106",
    "Far clip 900 -> 720 / 450 m; LOD bias x0.6 | 0.7 / 1.4; 1.4", "PB", "", "A16",
    "największa zmierzona dźwignia profilu poza skalą; widoczne przełączanie LOD bliżej", "1,0", "1,4",
    "wcześniejsze przełączanie LOD budynków/drzew (popping)", P + "; visual-qa Low")
add("plan", "NIE ROBIĆ: depth prepass / Depth Priming na A16", "Arm: koszt > zysk; Unity: Disabled dla mobile", "", "SOURCED",
    "Arm BPG + Unity", "Do not use depth prepass algorithms to remove any fragment overdraw.", "BPG", "s.23", "A16", "", "", "", "", "")
add("plan", "NIE ROBIĆ: MSAA 2× → 1× dla wydajności", "zmierzone 0 ms (ADR 0106)", "ms", "SOURCED", "repo ADR 0106 + Arm BPG",
    "MSAA 2x -> 1x; sky clouds/haze; A8 vehicle look | 0; 0; 0", "PB", "", "A16", "MSAA w tile jest tanie (BPG s.61)", "0", "0",
    "więcej aliasingu", "")
add("plan", "NIE ROBIĆ: cienie 25 m / 512 px, cull aut 100 m", "zmierzone: szum / −0,17 ms", "ms", "SOURCED", "repo ADR 0136 r2c",
    "Cienie 25 m / 512 px = szum (±0,3 ms). Cull 100 m daje powtarzalne, ale tylko −0,17 ms", "A0136", "Runda 2c", "A16",
    "", "0", "0,17", "auta znikają 100–150 m", "")
add("plan", "NIE ROBIĆ: FXAA zamiast MSAA na A16", "dodatkowy przebieg pełnoekranowy", "", "UNVERIFIED",
    "Unity zaleca FXAA na mobile, ale Arm: MSAA w tile tanie; FXAA = 1 przebieg pełnoekranowy (≥0,36 ms teoretycznie przy f=1 GHz)",
    "MSAA is a cheaper option than other anti-aliasing types", "URPAA", "MSAA", "A16", "", "", "", "", "")

for i, r in enumerate(rows, 1):
    r["id"] = f"R8-{i:03d}"

# duplikaty sha256 (ten sam plik źródłowy w wielu wierszach to nie duplikat danych — kolumna dotyczy duplikatów plików
# o różnych URL; tu każdy URL ma unikalny plik, więc pole puste)
seen = {}
for r in rows:
    key = (r["sha256"], r["url_pliku"] or r["url_źródła"])
    first = seen.setdefault(r["sha256"], key)
    if r["sha256"] and first != key:
        r["duplikat_sha256"] = "inny URL, ten sam plik"

with open(os.path.join(HERE, "manifest.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)
print(len(rows), "wierszy")
from collections import Counter
print(Counter(r["status"] for r in rows))
print(Counter(r["kategoria"] for r in rows))
