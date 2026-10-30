import type { SceneData } from '../../types/scene';
export function FloorPlanRenderer({ scene, selectedId, onSelect }: { scene: SceneData; selectedId: string | null; onSelect: (id: string) => void }) {
  const scale = Math.min(220 / scene.room.width, 160 / scene.room.depth);
  return <svg className="floor-plan" viewBox={`0 0 ${scene.room.width*scale+24} ${scene.room.depth*scale+24}`} role="img" aria-label="Top-down floor plan">
    <rect x="12" y="12" width={scene.room.width*scale} height={scene.room.depth*scale} rx="3" fill="#111c2d" stroke="#64748b" strokeWidth="3" />
    {scene.objects.filter(o => o.kind !== 'structure').map(o => {
      const w = Math.max(6, (o.scale?.[0] ?? .5)*scale); const h = Math.max(6, (o.scale?.[2] ?? .5)*scale);
      const x = 12 + (o.position[0] + scene.room.width/2)*scale - w/2;
      const y = 12 + (o.position[2] + scene.room.depth/2)*scale - h/2;
      return <rect key={o.id} x={x} y={y} width={w} height={h} rx="2" fill={o.id===selectedId ? '#38bdf8' : o.kind==='evidence' ? '#fbbf24' : o.color ?? '#64748b'} opacity=".95" onClick={() => onSelect(o.id)} style={{cursor:'pointer'}} />;
    })}
  </svg>;
}
