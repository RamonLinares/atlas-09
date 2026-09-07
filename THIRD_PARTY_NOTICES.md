# Third-party components

The seven mecha characters are dedicated under [CC0](ASSET-LICENSE.md). This does not replace the following upstream notices.

| Component | Use | License / source |
| --- | --- | --- |
| Three.js | Viewer and 3D loaders | MIT; `node_modules/three/LICENSE` |
| Vite | Development and production build | MIT; `node_modules/vite/LICENSE.md` |
| glTF Validator | Asset verification | Apache-2.0; `node_modules/gltf-validator/LICENSE` |
| MediaPipe Tasks Vision | On-device pose tracking | Apache-2.0; [upstream project](https://github.com/google-ai-edge/mediapipe) |
| Pose Landmarker Lite | Third-party pose-detection model | [Model source and documentation](public/tracking/README.md); upstream model terms apply |
| Quaternius Universal Animation Libraries | Selected source motions | CC0-1.0; [preserved licenses and provenance](assets/animations/quaternius/README.md) |
| Barlow Condensed, DM Sans, IBM Plex Mono | Google Fonts typography | SIL Open Font License 1.1; [Google Fonts repository](https://github.com/google/fonts) |
| MediaPipe pose sample photo | Test input pictured in webcam screenshots | [Official sample](https://storage.googleapis.com/mediapipe-assets/pose.jpg); excluded from the mecha asset dedication |

Dependency versions are pinned by `package-lock.json`. Installing dependencies retains their distributed notices. The MediaPipe runtime is copied from the installed package at build time; generated runtime files are not maintained as project source.

The character concepts and source surfaces were generated with OpenAI image generation and Tripo. Generation settings, receipts, and local preparation are recorded in [ASSET-PROVENANCE.md](ASSET-PROVENANCE.md) and each character's documentation. The owner's CC0 dedication is in [ASSET-LICENSE.md](ASSET-LICENSE.md).
