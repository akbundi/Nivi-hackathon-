import { Grid } from '@react-three/drei';
import type { Vec3 } from '../../types/scene';
export function Environment({ width, depth, onGroundClick }: { width: number; depth: number; onGroundClick?: (point: Vec3) => void }) {
  return <>
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -.04, 0]} receiveShadow onClick={event => { if (onGroundClick) { event.stopPropagation(); onGroundClick([event.point.x,event.point.y,event.point.z]); } }}>
      <planeGeometry args={[width, depth]} /><meshStandardMaterial color="#111c2d" roughness={.88} />
    </mesh>
    <Grid args={[width, depth]} cellSize={1} cellThickness={.5} sectionSize={3} sectionThickness={1} fadeDistance={22} fadeStrength={1} infiniteGrid={false} position={[0, .005, 0]} />
    <axesHelper args={[1.5]} />
  </>;
}
