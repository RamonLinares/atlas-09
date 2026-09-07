# Verification and render outputs

This directory preserves useful build reports, geometry and motion checks, and visual review captures. Reports document the revision at which they were generated; they are not a substitute for rerunning checks after changes.

Character-specific reports live in their named folders. Shared motion reports are under `motion/`; browser captures are under `playwright/`. `webcam-rig-validation.json` covers all five skeletons, including upper-body fallback. `webcam-upper-body-validation.json` records detection from a test image cropped above the hips.

Camera tests use synthetic input or the official MediaPipe sample, not personal webcam footage. That third-party sample photograph appears in some test screenshots and is excluded from the mecha CC0 dedication. Original character renders are covered by [CC0](../ASSET-LICENSE.md).
