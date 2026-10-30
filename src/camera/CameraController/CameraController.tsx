import { OrbitControls } from '@react-three/drei';
export function CameraController() {
  return <OrbitControls makeDefault enableDamping dampingFactor={.08} minDistance={3} maxDistance={24} maxPolarAngle={Math.PI / 2 - .03} />;
}
