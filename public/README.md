# Files served by the viewer

- `models/`: the five animated mecha GLBs and their [CC0 license](models/LICENSE.txt).
- `textures/`: exported character texture maps.
- `concept*.png`: character concept images.
- `tracking/`: the pose worker, third-party pose model, and generated MediaPipe runtime. See [tracking provenance](tracking/README.md).

Mecha models, their textures and character concept images are [CC0](../ASSET-LICENSE.md). Tracking components retain their separate upstream terms.

Vite copies this directory into the published site. Everything here is publicly downloadable; never add credentials or private files. The tracking runtime is generated during `npm run dev` or `npm run build` and excluded from Git.
