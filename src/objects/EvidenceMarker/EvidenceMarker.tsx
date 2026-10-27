import { Html } from '@react-three/drei';
import type { EvidenceItem, SceneObject } from '../../types/scene';
export function EvidenceMarker({ evidence, object, selected, onSelect }: { evidence: EvidenceItem; object: SceneObject; selected: boolean; onSelect: (id: string) => void }) {
  return <group position={object.position}>
    <mesh position={[0,.42,0]} onClick={(e) => { e.stopPropagation(); onSelect(object.id); }}>
      <sphereGeometry args={[.16, 16, 16]} /><meshBasicMaterial color={evidence.confidence < .75 ? '#fb7185' : '#fbbf24'} />
    </mesh>
    <Html position={[0,.68,0]} center distanceFactor={13} style={{ pointerEvents: 'none' }}>
      <div className={`evidence-tag ${selected ? 'active' : ''}`}>{evidence.id}</div>
    </Html>
  </group>;
}
