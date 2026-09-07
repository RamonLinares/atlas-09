# Build and validation scripts

Run commands from the repository root. Use Node.js 22 for JavaScript tools and Blender 5.1 for scripts importing `bpy`. Standalone Python helper requirements vary; the character guides identify each supported rebuild sequence.

- `prepare-pose-runtime.mjs`: copies the installed MediaPipe runtime to `public/tracking/runtime/`; automatically runs before development and production builds.
- `build_mecha.py`, `build_aether.py`, `build_seraph.py`, `build_ronin.py`, `build_scorpio.py`: base asset preparation. Follow the character guides for subsequent motion upgrades.
- `add_combat_motions.py`: appends selected combat animations to prepared character files.
- `upgrade_seraph_wings.py`: adds independent feather hinges and the revised deployment.
- `validate_glb.mjs`: validates an exported GLB. Example: `node scripts/validate_glb.mjs public/models/seraph-03.glb /tmp/seraph-validation.json`.
- `validate_*.py`: Blender checks for geometry, bindings, motion, and character-specific behavior.
- `validate-pose-browser.js`: an async function to evaluate in a running viewer's browser context. Checks real rigs with synthetic full-body and cropped upper-body poses; no webcam access required.
- Browser inspection routines such as `browser_checks.js` run in their documented Playwright/browser context, not as standalone Node scripts.

Asset preparation uses preserved local inputs. It does not regenerate characters through paid APIs. Reports go to `output/`. Do not run every historical preparation script indiscriminately: some are specific upgrade steps and may overwrite current assets.
