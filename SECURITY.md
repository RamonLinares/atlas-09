# Reporting security issues

For sensitive reports, use [GitHub private vulnerability reporting](https://github.com/RamonLinares/atlas-09/security/advisories/new). Do not include credentials, private camera footage, or exploitable details in a public issue.

Please describe the affected revision, browser/environment, impact, and a minimal reproduction. The current `main` branch is the maintained version; there is no guaranteed response schedule.

## Webcam privacy

Camera capture starts only after the user clicks Webcam Control and grants browser permission. Processing happens on-device. The app does not request microphone access, record camera frames, or upload them. Stop Webcam, closing the preview, changing characters or animations, and hiding or leaving the page release capture resources.

The live viewer is publicly hosted on GitHub Pages. Character downloads, client code, and the tracking runtime are public. Never put secrets in `public/`, frontend code, or `VITE_*` environment variables.
