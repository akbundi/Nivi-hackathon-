import type { SceneObject } from '../../types/scene';
export function UncertaintyOverlay({ objects, enabled }: { objects: SceneObject[]; enabled: boolean }) {
  if (!enabled) return null;
  return <group>{objects.filter(o => (o.confidence ?? 1) < .75).map(o =>
    <mesh key={o.id} position={o.position} scale={(o.scale ?? [1,1,1]).map(n => n * 1.18) as [number,number,number]}>
      <boxGeometry /><meshBasicMaterial color="#fb7185" wireframe transparent opacity={.45} />
    </mesh>
  )}</group>;
}
