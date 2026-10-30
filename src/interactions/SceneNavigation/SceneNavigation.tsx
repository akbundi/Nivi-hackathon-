import { viewpoints } from '../../camera/Viewpoints/Viewpoints';
export type ViewName = keyof typeof viewpoints;
export function SceneNavigation({ onView }: { onView: (view: ViewName) => void }) {
  return <div className="view-buttons">{(['perspective','top','front'] as ViewName[]).map(view => <button key={view} onClick={() => onView(view)}>{view === 'perspective' ? '3D View' : view === 'top' ? 'Top View' : 'Front View'}</button>)}</div>;
}
