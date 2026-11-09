# Tooling research — 2026-11-09

Research by a Sonnet agent (web, official repos/docs). Items marked *unverified* were not confirmed at source. Owner decides what to install.

## Recommended (high value)
| Tool | Value | Licence / cost | Setup | Risk |
|---|---|---|---|---|
| **Unity CLI + Pipeline package** (official, `unity` 1.0.0-beta.17) | Tests, Android build, console/scene access, optional `unity mcp configure claude-code`; replaces Unity's deprecated in-Editor MCP | Unity ToS, free | install CLI, `unity pipeline install` in project | beta; remove old AI Assistant package |
| **Unity agent plugin** (`Unity-Technologies/unity-agent-plugin`, also in the Anthropic plugin directory) | ~30 skills; useful: URP/Render Graph, post-processing, Shader Graph, UI Toolkit, audio optimisation. Skip 2D/IAP/ads | Unity Companion License, free | install from plugin directory | low |
| **Blender MCP** (`ahujasid/blender-mcp`, MIT, ~13.7k★) | Live viewport screenshots (`look`), interactive iteration on truck/cab; Poly Haven import | free | `claude mcp add blender uvx mcp-for-blender` + add-on | telemetry on by default (set `DISABLE_TELEMETRY=true`); keep Sketchfab/Hyper3D off (licences) |
| **Context7** (MIT) | Current library docs (URP, Input System, glTFast — coverage to be checked) | free API key | `npx ctx7 setup --claude` | hosted service; queries leave the PC |
| **Poly Haven / ambientCG** | CC0 scanned PBR textures, HDRIs | CC0 | none (already allowed) | verify licence page per download |
| **RealityScan** (Epic) | Photogrammetry from owner's phone photos | free < $1M revenue/yr | installer | licence terms change above $1M |

## Maybe
- **unity-perf** plugin (community, directory): zero-GC / performance skills — overlaps our rules; read before installing.
- **CoplayDev/unity-mcp** (MIT, v10.3.0) — only if Unity CLI's editor control is not enough.
- **IvanMurzak/Unity-MCP** — needs Docker on Windows, unclear pricing → probably skip.
- Material Maker (MIT), ArmorPaint (zlib), Meshroom (MPL-2.0) — *unverified*.
- Fab/Quixel Megascans — conflicting info on use outside Unreal; treat as **not usable** until the current Fab EULA is read.

## Skip
- Unity's deprecated in-Editor MCP (`com.unity.ai.assistant`).
- Sketchfab / Hyper3D inside Blender MCP (licence ambiguity).
- Unvetted community skills (prompt-injection / malicious payload reports) — read SKILL.md + scripts before any install.
- Paid MCPs (zero budget).

## Token-saving practices (Anthropic costs doc)
- Route models: Haiku for simple, Sonnet for routine, Opus for heavy + all visual/art work (owner rule).
- Keep CLAUDE.md < ~200 lines; move procedures into skills (load on demand).
- Scripts print compact JSON summaries; hooks filter test/log output to errors.
- Prefer CLIs over MCP servers when both exist; disable idle MCP servers.
- Downscale QA screenshots (~768 px) and crop to the area under test before viewing.
- `/compact` with focus before long idle; `/clear` between unrelated tasks.

## CI
- Public repo → free GitHub Actions minutes. Current CI: physics runner + GIS tests (`.github/workflows/ci.yml`).
- Unity Android build in CI via **GameCI** is possible with a Personal licence but needs secrets `UNITY_LICENSE`, `UNITY_EMAIL`, `UNITY_PASSWORD` (use a dedicated Unity account) — owner must add them; runner disk (~14 GB) needs cleanup + Library cache.

Sources: docs.unity.com (Unity CLI release notes, Unity plugin for Claude Code), code.claude.com/docs/en/costs, game.ci docs, github.com/CoplayDev/unity-mcp, github.com/ahujasid/blender-mcp, github.com/upstash/context7, realityscan.com/license.
