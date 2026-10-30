import { Html } from '@react-three/drei';
import type { EvidenceItem, SceneObject, Vec3 } from '../../types/scene';
export function EvidenceMarker({ evidence, object, selected, onSelect, onMeasurePoint }: { evidence: EvidenceItem; object: SceneObject; selected: boolean; onSelect: (id: string) => void; onMeasurePoint?: (point: Vec3) => void }) {
  return <group position={object.position}>
    <mesh position={[0,.42,0]} onClick={(e) => { e.stopPropagation(); onMeasurePoint?.([e.point.x,e.point.y,e.point.z]); onSelect(object.id); }}>
      <sphereGeometry args={[.16, 16, 16]} /><meshBasicMaterial color={evidence.confidence < .75 ? '#fb7185' : '#fbbf24'} />
    </mesh>
    <Html position={[0,.68,0]} center distanceFactor={13} style={{ pointerEvents: 'none' }}>
      <div className={`evidence-tag ${selected ? 'active' : ''}`}>{evidence.id}</div>
    </Html>
  </group>;
}
