import type { TimelineEvent } from '../../types/scene';
export function TimelineSceneSync({ events, active, onChange }: { events: TimelineEvent[]; active: number; onChange: (index: number) => void }) {
  return <div className="timeline-list">{events.map((event,index) => <button key={event.id} className={`timeline-event ${index===active?'selected':''}`} onClick={() => onChange(index)}><span className="timeline-dot" /><span className="timeline-time">{event.time}</span><span className="timeline-copy"><strong>{event.title}</strong><small>{event.description}</small></span></button>)}</div>;
}
