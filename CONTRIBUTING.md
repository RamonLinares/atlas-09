# Contributing to FORGE

Bug reports, improvements, and new character work are welcome. Open an issue to discuss substantial changes before implementing them.

## Local setup

Use Node.js 22 (see `.nvmrc`) and npm. Blender 5.1 is only needed to rebuild character assets.

```sh
npm ci
npm run dev
npm run build -- --base=/atlas-09/
```

No generation API keys are needed to run the viewer. The pose runtime is prepared automatically. Follow the character documents when rebuilding Blender or GLB files; preserve their textures, motion clips, and physical scale.

## Pull requests

Describe the problem, the resulting behavior, and the checks you ran. Include screenshots for visual changes. Verify desktop and mobile controls when changing the UI. For animation or rigging changes, check joint connections, rigid armor, floor contact, and relevant motion transitions with the existing validation scripts.

Keep generated dependencies, local credentials, editor files, and caches out of commits. Retain intentional asset sources and useful validation reports. Do not include webcam recordings or personal images in tests; use synthetic inputs or appropriately licensed fixtures.

Code and documentation contributions are under the project's MIT license. Contributions to the seven mecha asset collections are under CC0 as described in [ASSET-LICENSE.md](ASSET-LICENSE.md). Only submit material you have permission to contribute, and preserve all third-party notices.
