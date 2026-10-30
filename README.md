# 🔍 3D Forensic Scene Visualization

An interactive 3D forensic scene visualization platform designed to digitally reconstruct, explore, and analyze crime scenes using 3D objects, evidence markers, floor plans, and timeline-based scene navigation.

## 📌 Overview

3D Forensic Scene Visualization aims to make crime scene investigation more interactive and understandable through a 3D environment.

The platform allows investigators to visualize scene objects, navigate between different viewpoints, interact with evidence markers, and explore scene-related information in a structured way.

It provides a foundation for digital crime scene reconstruction and spatial investigation.

## ✨ Key Features

- **3D Scene Visualization:** Explore forensic scenes in an interactive 3D environment.
- **Object Rendering:** Visualize objects placed within the reconstructed scene.
- **Evidence Markers:** Identify and interact with evidence points in the scene.
- **Floor Plan Visualization:** View the scene layout through a floor plan.
- **Scene Navigation:** Navigate through different viewpoints of the 3D environment.
- **Camera Controls:** Explore the scene from different camera perspectives.
- **Timeline Synchronization:** Connect timeline events with the corresponding scene state.
- **Uncertainty Visualization:** Represent uncertain or estimated areas within the reconstruction.
- **Scene Loading:** Load and render scene data.
- **Scene API Integration:** Manage scene-related data through API services.

## 🛠️ Tech Stack

- **Frontend:** React.js, TypeScript
- **3D Visualization:** Three.js / React Three Fiber
- **Build Tool:** Vite
- **Styling:** CSS
- **Version Control:** Git & GitHub

## 📂 Project Structure

```text
Nivi-Hackathon/
│
├── public/
├── src/
│   ├── camera/
│   │   ├── CameraController/
│   │   └── Viewpoints/
│   │
│   ├── floor_plan/
│   │   └── FloorPlanRenderer/
│   │
│   ├── interactions/
│   │   ├── EvidenceInteraction/
│   │   ├── ObjectSelection/
│   │   └── SceneNavigation/
│   │
│   ├── objects/
│   │   ├── EvidenceMarker/
│   │   ├── ObjectRenderer/
│   │   └── UncertaintyOverlay/
│   │
│   ├── scene/
│   │   ├── Environment/
│   │   ├── Lighting/
│   │   ├── SceneLoader/
│   │   └── SceneRenderer/
│   │
│   ├── services/
│   │   └── sceneApi.ts
│   │
│   ├── timeline/
│   │   └── TimelineSceneSync/
│   │
│   ├── types/
│   ├── utils/
│   ├── App.tsx
│   ├── main.tsx
│   └── styles.css
│
├── tests/
├── package.json
├── package-lock.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/RIYAYADAV08/3d-Visualization.git
```

### 2. Navigate to the Project Directory

```bash
cd 3d-Visualization
```

### 3. Install Dependencies

```bash
npm install
```

### 4. Start the Development Server

```bash
npm run dev
```

### 5. Open in Browser

Open the local URL displayed in your terminal, usually:

```text
http://localhost:5173
```

## 🎯 Project Objectives

- Create an interactive digital representation of forensic scenes.
- Improve spatial understanding through 3D visualization.
- Enable structured exploration of evidence and scene objects.
- Connect investigation timelines with scene visualization.
- Provide a foundation for advanced forensic reconstruction tools.

## 🚀 Future Enhancements

- Realistic GLTF/GLB 3D model integration.
- Smooth animated camera transitions.
- Interactive 3D transformation gizmos.
- 3D distance measurement and forensic ruler.
- Automated timeline playback controls.
- High-resolution scene snapshots.
- JSON and PDF forensic report generation.

## 👩‍💻 Contributors

Developed as part of a hackathon project focused on 3D visualization and forensic scene reconstruction.

## 📄 License

This project is developed for educational, research, and hackathon purposes.

---

**3D Forensic Scene Visualization — Bringing Digital Crime Scene Reconstruction to Life.**
