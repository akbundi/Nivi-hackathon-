import { Canvas, useThree } from '@react-three/fiber';
import { CameraControls, Html, Line } from '@react-three/drei';
import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import type { SceneData, SceneObject, Vec3 } from '../../types/scene';
import { Environment } from '../Environment/Environment';
import { Lighting } from '../Lighting/Lighting';
import { ObjectRenderer } from '../../objects/ObjectRenderer/ObjectRenderer';
import { EvidenceMarker } from '../../objects/EvidenceMarker/EvidenceMarker';
import { UncertaintyOverlay } from '../../objects/UncertaintyOverlay/UncertaintyOverlay';
import type { ViewName } from '../../interactions/SceneNavigation/SceneNavigation';
import { viewpoints } from '../../camera/Viewpoints/Viewpoints';

function CameraMotion({ view, selected }: { view: ViewName; selected: SceneObject | undefined }) {
  const controls = useRef<any>(null);
  useEffect(() => {
    const c = controls.current; if (!c) return;
    if (selected) {
      const p = new THREE.Vector3(...selected.position);
      const direction = new THREE.Vector3(1, .72, 1).normalize().multiplyScalar(5.5);
      const camera = p.clone().add(direction);
      void c.setLookAt(camera.x,camera.y,camera.z,p.x,p.y,p.z,true);
    } else {
      const p = viewpoints[view]; void c.setLookAt(p[0],p[1],p[2],0,0,0,true);
    }
  }, [view, selected?.id]);
  return <CameraControls ref={controls} makeDefault minDistance={2} maxDistance={28} smoothTime={.8} />;
}
function MeasurementLine({ points, units }: { points: Vec3[]; units: string }) {
  if (points.length < 2) return null;
  const a = new THREE.Vector3(...points[0]), b = new THREE.Vector3(...points[1]);
  const distance = a.distanceTo(b);
  const midpoint = a.clone().add(b).multiplyScalar(.5);
  return <>
    <Line points={[a,b]} color="#fbbf24" dashed dashSize={.16} gapSize={.1} lineWidth={1.5}/>
    <mesh position={midpoint}><sphereGeometry args={[.045,12,12]}/><meshBasicMaterial color="#fbbf24"/></mesh>
    <Html position={[midpoint.x,midpoint.y+.22,midpoint.z]} center><span className="measurement-label">{distance.toFixed(2)} {units}</span></Html>
  </>;
}
export function SceneRenderer({ scene, selectedId, onSelect, showUncertainty, view, onTransform, transformMode, measureMode, measurePoints, onMeasurePoint }: {
  scene: SceneData; selectedId: string | null; onSelect: (id: string) => void; showUncertainty: boolean; view: ViewName;
  onTransform: (id: string, patch: { position: Vec3; rotation: Vec3; scale: Vec3 }) => void;
  transformMode: 'translate' | 'rotate' | 'scale'; measureMode: boolean; measurePoints: Vec3[]; onMeasurePoint: (point: Vec3) => void;
}) {
  const selected = scene.objects.find(item => item.id === selectedId);
  return <Canvas shadows camera={{ position: viewpoints.perspective, fov: 48, near: .1, far: 100 }} dpr={[1,1.5]} gl={{ antialias: true, preserveDrawingBuffer: true, powerPreference: 'high-performance' }} onPointerMissed={(event) => { if (measureMode) { /* Ground clicks are handled by the floor surface. */ } else onSelect(''); }}>
    <color attach="background" args={['#0b1020']} /><fog attach="fog" args={['#0b1020',17,36]}/>
    <Lighting/><Environment width={scene.room.width} depth={scene.room.depth} onGroundClick={point => { if (measureMode) onMeasurePoint(point); }}/><CameraMotion view={view} selected={selected}/>
    {scene.objects.map(item => <ObjectRenderer key={item.id} item={item} selected={selectedId===item.id} onSelect={onSelect} showUncertainty={showUncertainty} transformMode={transformMode} onTransform={onTransform} onMeasurePoint={onMeasurePoint}/>)}
    {scene.evidence.map(ev => { const object=scene.objects.find(o=>o.id===ev.objectId); return object ? <EvidenceMarker key={ev.id} evidence={ev} object={object} selected={selectedId===object.id} onSelect={onSelect} onMeasurePoint={point => { if (measureMode) onMeasurePoint(point); }}/> : null; })}
    <UncertaintyOverlay objects={scene.objects} enabled={showUncertainty}/><MeasurementLine points={measurePoints} units={scene.units}/>
  </Canvas>;
}
