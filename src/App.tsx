import { useEffect, useMemo, useState } from 'react';
import { Activity, Box, Camera, ChevronDown, CircleHelp, Crosshair, Layers3, Maximize2, RotateCcw, ShieldAlert } from 'lucide-react';
import { useSceneLoader } from './scene/SceneLoader/SceneLoader';
import { SceneRenderer } from './scene/SceneRenderer/SceneRenderer';
import { SceneNavigation, type ViewName } from './interactions/SceneNavigation/SceneNavigation';
import { EvidenceInteraction } from './interactions/EvidenceInteraction/EvidenceInteraction';
import { FloorPlanRenderer } from './floor_plan/FloorPlanRenderer/FloorPlanRenderer';
import { TimelineSceneSync } from './timeline/TimelineSceneSync/TimelineSceneSync';
import { toggleSelection } from './interactions/ObjectSelection/ObjectSelection';
import type { SceneData, SceneObject, Vec3 } from './types/scene';

export default function App() {
  const { scene: loadedScene, error } = useSceneLoader();
  const [scene, setScene] = useState<SceneData | null>(null);
  useEffect(() => { if (loadedScene) setScene(loadedScene); }, [loadedScene]);
  const [selectedId,setSelectedId] = useState<string|null>(null);
  const [showUncertainty,setShowUncertainty] = useState(true);
  const [view,setView] = useState<ViewName>('perspective');
  const [activeEvent,setActiveEvent] = useState(0);
  const [rightTab,setRightTab] = useState<'details'|'floor'>('details');
  const selectedEvidence = useMemo(() => scene?.evidence.find(e => e.objectId===selectedId),[scene,selectedId]);
  if (error) return <main className="status-screen"><h2>Unable to load scene</h2><p>{error}</p><p>Check VITE_SCENE_API_URL and the scene JSON schema.</p></main>;
  if (!scene) return <main className="status-screen"><div className="loader" /><p>Preparing reconstruction workspace…</p></main>;
  const event = scene.timeline[activeEvent];
  const selectObject = (id:string) => setSelectedId(current => id ? toggleSelection(current,id) : null);
  const updateObject = (id: string, patch: Partial<Pick<SceneObject, 'position' | 'rotation' | 'scale'>>) => setScene(current => current ? ({ ...current, objects: current.objects.map(object => object.id === id ? { ...object, ...patch } : object) }) : current);
  const updateVector = (id: string, key: 'position' | 'rotation' | 'scale', axis: 0 | 1 | 2, value: number) => { const object = scene.objects.find(item => item.id === id); if (!object || !Number.isFinite(value)) return; const vector = [...(object[key] ?? (key === 'scale' ? [1,1,1] : [0,0,0]))] as Vec3; vector[axis] = value; updateObject(id, { [key]: vector }); };
  return <div className="app-shell">
    <header className="topbar"><div className="brand-mark"><Box size={20}/></div><div className="brand-copy"><strong>REALITY<span>OS</span></strong><small>RECONSTRUCTION WORKSPACE</small></div><div className="project-name"><span className="live-dot"/><span>{scene.title}</span><ChevronDown size={14}/></div><div className="top-actions"><span className="status-pill"><span/> DEMO DATA</span><button className="icon-button" title="Help"><CircleHelp size={18}/></button><div className="avatar">R</div></div></header>
    <main className="workspace">
      <aside className="left-rail"><button className="rail-button active" title="3D Scene"><Box/></button><button className="rail-button" title="Evidence"><Crosshair/></button><button className="rail-button" title="Timeline"><Activity/></button><div className="rail-spacer"/><button className="rail-button" title="Layers"><Layers3/></button></aside>
      <section className="main-column">
        <div className="scene-toolbar"><div><div className="eyebrow">SCENE VIEWER <span>/</span> {scene.id.toUpperCase()}</div><h1>Reconstructed environment</h1></div><div className="toolbar-actions"><button onClick={() => {setSelectedId(null);setView('perspective');setShowUncertainty(true);}}><RotateCcw size={15}/> Reset</button><button onClick={() => setShowUncertainty(v=>!v)} className={showUncertainty?'toggled':''}><ShieldAlert size={15}/> Uncertainty</button><button title="Viewport"><Maximize2 size={15}/></button></div></div>
        <div className="viewer-card"><div className="viewer-topline"><span><span className="live-dot"/> INTERACTIVE 3D</span><span>UNITS: {scene.units.toUpperCase()}</span></div><div className="canvas-wrap"><SceneRenderer scene={scene} selectedId={selectedId} onSelect={selectObject} showUncertainty={showUncertainty} view={view}/><div className="viewer-hint"><MouseIcon/> Drag to orbit <span>·</span> Scroll to zoom <span>·</span> Click an object</div><SceneNavigation onView={setView}/><div className="axis-label">Y ↑<br/>X →</div></div><div className="viewer-footer"><span><span className="legend-dot evidence-dot"/> Evidence marker</span><span><span className="legend-dot uncertain-dot"/> Low confidence</span><span><span className="legend-dot selected-dot"/> Selected object</span><span className="object-count">{scene.objects.length} OBJECTS · {scene.evidence.length} EVIDENCE ITEMS</span></div></div>
        <section className="timeline-panel"><div className="panel-heading"><div><div className="eyebrow">CHRONOLOGY</div><h2>Investigation timeline</h2></div><span className="count-chip">{scene.timeline.length} EVENTS</span></div><TimelineSceneSync events={scene.timeline} active={activeEvent} onChange={i=>{setActiveEvent(i); const first=scene.timeline[i]?.objectIds[0]; if(first) setSelectedId(first);}}/><div className="active-event-note"><span className="timeline-time">{event?.time}</span><span>{event?.description}</span></div></section>
      </section>
      <aside className="right-panel"><div className="right-tabs"><button className={rightTab==='details'?'active':''} onClick={()=>setRightTab('details')}>Object details</button><button className={rightTab==='floor'?'active':''} onClick={()=>setRightTab('floor')}>Floor plan</button></div>{rightTab==='details'?<><div className="detail-header"><span className="eyebrow">INSPECTOR</span><span className="count-chip">LIVE</span></div>{selectedEvidence?<EvidenceInteraction item={selectedEvidence}/>:selectedId?<div className="detail-content"><div className="eyebrow">SELECTED OBJECT</div><h3>{scene.objects.find(o=>o.id===selectedId)?.name}</h3><p>{scene.objects.find(o=>o.id===selectedId)?.description ?? 'No additional description is available for this object.'}</p><div className="detail-row"><span>Object ID</span><strong>{selectedId}</strong></div><div className="detail-row"><span>Confidence</span><strong>{Math.round((scene.objects.find(o=>o.id===selectedId)?.confidence ?? 1)*100)}%</strong></div><ObjectTransformEditor object={scene.objects.find(o=>o.id===selectedId)!} onChange={(key,axis,value)=>updateVector(selectedId,key,axis,value)}/></div>:<EvidenceInteraction/>}<div className="right-divider"/><div className="panel-heading compact"><h2>Evidence register</h2><span className="count-chip">{scene.evidence.length}</span></div><div className="evidence-list">{scene.evidence.map(ev=><button key={ev.id} className={`evidence-row ${selectedId===ev.objectId?'selected':''}`} onClick={()=>setSelectedId(ev.objectId)}><span className={`evidence-symbol ${ev.confidence<.75?'low':''}`}><Crosshair size={16}/></span><span className="evidence-copy"><strong>{ev.label}</strong><small>{ev.id} · {ev.timestamp}</small></span><span className="evidence-confidence">{Math.round(ev.confidence*100)}%</span></button>)}</div></>:<div className="floor-panel"><p className="muted-copy">Top-down room map. Select a marker to focus its object in the 3D scene.</p><FloorPlanRenderer scene={scene} selectedId={selectedId} onSelect={selectObject}/><div className="floor-legend"><span><i className="legend-dot evidence-dot"/> Evidence</span><span><i className="legend-dot selected-dot"/> Selected</span></div></div>}
        <div className="integrity-card"><ShieldAlert size={17}/><div><strong>Interpret with care</strong><p>Confidence values are illustrative demo metadata, not verified forensic conclusions.</p></div></div>
      </aside>
    </main>
    <footer className="app-footer"><span><span className="live-dot"/> VIEWER READY</span><span><Camera size={13}/> THREE.JS · REACT THREE FIBER</span><span>AI REALITY RECONSTRUCTOR <b>·</b> MEMBER 7</span></footer>
  </div>;
}
function MouseIcon(){return <span className="mouse-icon">▯</span>}

function ObjectTransformEditor({ object, onChange }: { object: SceneObject; onChange: (key: 'position' | 'rotation' | 'scale', axis: 0 | 1 | 2, value: number) => void }) {
  const vectors: Array<{ key: 'position' | 'rotation' | 'scale'; label: string; values: Vec3 }> = [
    { key: 'position', label: 'Position (m)', values: object.position },
    { key: 'rotation', label: 'Rotation (rad)', values: object.rotation ?? [0,0,0] },
    { key: 'scale', label: 'Scale', values: object.scale ?? [1,1,1] },
  ];
  return <div className="transform-editor"><div className="eyebrow">TRANSFORM CONTROLS</div>{vectors.map(vector => <div className="transform-row" key={vector.key}><label>{vector.label}</label><div>{vector.values.map((value, axis) => <input aria-label={`${vector.label} ${['X','Y','Z'][axis]}`} key={axis} type="number" step={vector.key === 'rotation' ? 0.1 : 0.1} value={Number(value.toFixed(2))} onChange={event => onChange(vector.key, axis as 0|1|2, Number(event.target.value))}/>)}</div></div>)}</div>;
}
