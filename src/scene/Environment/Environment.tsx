import { Grid } from '@react-three/drei';
export function Environment({ width, depth }: { width: number; depth: number }) {
  return <>
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -.04, 0]} receiveShadow>
      <planeGeometry args={[width, depth]} /><meshStandardMaterial color="#111c2d" roughness={.88} />
    </mesh>
    <Grid args={[width, depth]} cellSize={1} cellThickness={.5} sectionSize={3} sectionThickness={1} fadeDistance={22} fadeStrength={1} infiniteGrid={false} position={[0, .005, 0]} />
    <axesHelper args={[1.5]} />
  </>;
}
