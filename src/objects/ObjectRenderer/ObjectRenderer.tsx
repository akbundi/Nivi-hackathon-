import { Suspense, useMemo, useRef } from 'react';
import { Html, TransformControls, useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import type { SceneObject, Vec3 } from '../../types/scene';

function Model({ url }: { url: string }) {
  const gltf = useGLTF(url);
  return <primitive object={gltf.scene.clone(true)} />;
}

export function ObjectRenderer({ item, selected, onSelect, showUncertainty, transformMode, onTransform, onMeasurePoint }: {
  item: SceneObject; selected: boolean; onSelect: (id: string) => void; showUncertainty: boolean;
  transformMode: 'translate' | 'rotate' | 'scale'; onTransform: (id: string, patch: { position: Vec3; rotation: Vec3; scale: Vec3 }) => void;
  onMeasurePoint: (point: Vec3) => void;
}) {
  const group = useRef<THREE.Group>(null);
  const geometry = useMemo(() => item.kind === 'evidence' ? new THREE.SphereGeometry(.5, 24, 16) : new THREE.BoxGeometry(1, 1, 1), [item.kind]);
  const lowConfidence = (item.confidence ?? 1) < .75;
  const content = item.modelUrl ? <Suspense fallback={<mesh><boxGeometry args={[1,1,1]}/><meshStandardMaterial color="#64748b" wireframe/></mesh>}><Model url={item.modelUrl}/></Suspense> : <mesh geometry={geometry} castShadow receiveShadow>
    <meshStandardMaterial color={selected ? '#38bdf8' : item.color ?? '#718096'} roughness={.62} metalness={.08} transparent={showUncertainty && lowConfidence} opacity={showUncertainty && lowConfidence ? .58 : 1} wireframe={showUncertainty && lowConfidence} />
    {selected && <lineSegments><edgesGeometry args={[geometry]} /><lineBasicMaterial color="#e0f2fe" /></lineSegments>}
  </mesh>;
  const objectGroup = <group ref={group} position={item.position} rotation={item.rotation ?? [0,0,0]} scale={item.scale ?? [1,1,1]}
    onClick={(event) => { event.stopPropagation(); if (event.point) onMeasurePoint([event.point.x,event.point.y,event.point.z]); onSelect(item.id); }}>
    {content}
  </group>;
  return <>
    {selected ? <TransformControls mode={transformMode} onObjectChange={() => { const target = group.current; if (target) onTransform(item.id, { position: [target.position.x,target.position.y,target.position.z], rotation: [target.rotation.x,target.rotation.y,target.rotation.z], scale: [target.scale.x,target.scale.y,target.scale.z] }); }}>{objectGroup}</TransformControls> : objectGroup}
    {selected && <Html position={item.position} center distanceFactor={15} style={{ pointerEvents: 'none' }}><span className="selected-model-tag">{item.name}</span></Html>}
  </>;
}
