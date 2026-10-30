import type { EvidenceItem } from '../../types/scene';
export function EvidenceInteraction({ item }: { item?: EvidenceItem }) {
  if (!item) return <div className="empty-detail">Select an object or evidence marker to inspect details.</div>;
  return <div className="detail-content"><div className="eyebrow">SELECTED EVIDENCE</div><h3>{item.label}</h3><p>{item.description}</p><div className="detail-row"><span>Evidence ID</span><strong>{item.id}</strong></div><div className="detail-row"><span>Recorded at</span><strong>{item.timestamp}</strong></div><div className="detail-row"><span>Confidence</span><strong>{Math.round(item.confidence * 100)}%</strong></div><div className="confidence-track"><span style={{width:`${item.confidence * 100}%`}} /></div></div>;
}
