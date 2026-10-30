# Nivi Hackathon — Feature Branch

Interactive 3D forensic-scene reconstruction workspace built with React, TypeScript, Vite, Three.js and React Three Fiber.

## Run locally

```bash
npm install
npm run dev
```

## Added investigation tools

- **GLTF / GLB objects:** Add a `modelUrl` property to any object in the scene JSON to load a GLTF/GLB asset. Objects without `modelUrl` continue to render as procedural geometry. Example: `"modelUrl": "/models/chair.glb"` (place the file under `public/models/`).
- **Smooth camera focus:** Selecting an object or timeline event smoothly moves the camera toward it. Viewpoint buttons remain available.
- **3D transform gizmo:** Select an object, then choose Translate, Rotate or Scale in the Gizmo toolbar and manipulate it directly in the canvas. Numeric inspector fields remain available.
- **Forensic ruler:** Enable Measure, then click two object surfaces or two points on the floor. The scene draws a dashed connector and displays the distance in scene units.
- **Timeline playback:** Use Play/Pause, the scrubber and playback-speed selector to step through timeline events.
- **Scene exports:** Snapshot saves a PNG of the 3D canvas; JSON exports the current scene, metadata and any completed measurement; PDF Report opens a print-ready report that can be saved as PDF from the browser print dialog.

## Notes

- `modelUrl` should be a URL/path accessible by the browser. For local assets, put models in `public/` and reference them with an absolute path such as `/models/evidence.glb`.
- The PDF export uses the browser's print-to-PDF flow, so choose **Save as PDF** in the print dialog.
- Confidence values are illustrative demo metadata and should not be treated as verified forensic conclusions.
