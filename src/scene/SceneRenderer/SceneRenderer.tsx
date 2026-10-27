import { Canvas } from '@react-three/fiber';
import type { SceneData } from '../../types/scene';
import { Environment } from '../Environment/Environment';
import { Lighting } from '../Lighting/Lighting';
import { ObjectRenderer } from '../../objects/ObjectRenderer/ObjectRenderer';
import { EvidenceMarker } from '../../objects/EvidenceMarker/EvidenceMarker';
import { UncertaintyOverlay } from '../../objects/UncertaintyOverlay/UncertaintyOverlay';
import { CameraController } from '../../camera/CameraController/CameraController';
import { useEffect } from 'react';
import type { ViewName } from '../../interactions/SceneNavigation/SceneNavigation';
import { viewpoints } from '../../camera/Viewpoints/Viewpoints';
import { useThree } from '@react-three/fiber';
function ViewSync({ view }: { view: ViewName }) { const { camera } = useThree(); useEffect(() => { camera.position.set(...viewpoints[view]); camera.lookAt(0,0,0); }, [camera,view]); return null; }
export function SceneRenderer({ scene, selectedId, onSelect, showUncertainty, view }: { scene: SceneData; selectedId: string | null; onSelect: (id: string) => void; showUncertainty: boolean; view: ViewName }) {
  return <Canvas shadows camera={{ position: viewpoints.perspective, fov: 48, near: .1, far: 100 }} dpr={[1,1.5]} gl={{ antialias: true, powerPreference: 'high-performance' }} onPointerMissed={() => onSelect('')}>
    <color attach="background" args={['#0b1020']} /><fog attach="fog" args={['#0b1020', 17, 36]} />
    <Lighting /><Environment width={scene.room.width} depth={scene.room.depth} /><ViewSync view={view} />
    {scene.objects.map(item => <ObjectRenderer key={item.id} item={item} selected={selectedId===item.id} onSelect={onSelect} showUncertainty={showUncertainty} />)}
    {scene.evidence.map(ev => { const object = scene.objects.find(o => o.id===ev.objectId); return object ? <EvidenceMarker key={ev.id} evidence={ev} object={object} selected={selectedId===object.id} onSelect={onSelect} /> : null; })}
    <UncertaintyOverlay objects={scene.objects} enabled={showUncertainty} /><CameraController />
  </Canvas>;
}
