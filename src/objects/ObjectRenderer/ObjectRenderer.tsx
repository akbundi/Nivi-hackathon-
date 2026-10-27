import { useMemo } from 'react';
import * as THREE from 'three';
import type { SceneObject } from '../../types/scene';
export function ObjectRenderer({ item, selected, onSelect, showUncertainty }: { item: SceneObject; selected: boolean; onSelect: (id: string) => void; showUncertainty: boolean }) {
  const geometry = useMemo(() => {
    if (item.kind === 'evidence') return new THREE.SphereGeometry(.5, 24, 16);
    return new THREE.BoxGeometry(1, 1, 1);
  }, [item.kind]);
  const lowConfidence = (item.confidence ?? 1) < .75;
  return <mesh
    geometry={geometry}
    position={item.position}
    rotation={item.rotation as [number, number, number] | undefined}
    scale={item.scale ?? [1,1,1]}
    castShadow receiveShadow
    onClick={(event) => { event.stopPropagation(); onSelect(item.id); }}
  >
    <meshStandardMaterial color={selected ? '#38bdf8' : item.color ?? '#718096'} roughness={.62} metalness={.08} transparent={showUncertainty && lowConfidence} opacity={showUncertainty && lowConfidence ? .58 : 1} wireframe={showUncertainty && lowConfidence} />
    {selected && <lineSegments>
      <edgesGeometry args={[geometry]} /><lineBasicMaterial color="#e0f2fe" />
    </lineSegments>}
  </mesh>;
}
