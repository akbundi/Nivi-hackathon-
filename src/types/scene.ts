export type Vec3 = [number, number, number];
export type SceneObject = {
  id: string; name: string; kind: 'furniture' | 'structure' | 'evidence' | 'unknown';
  position: Vec3; rotation?: Vec3; scale?: Vec3; color?: string;
  confidence?: number; description?: string; evidenceId?: string; eventIds?: string[];
};
export type EvidenceItem = { id: string; label: string; objectId: string; description: string; confidence: number; timestamp: string };
export type TimelineEvent = { id: string; time: string; title: string; description: string; objectIds: string[] };
export type SceneData = { id: string; title: string; units: string; room: { width: number; depth: number; height: number }; objects: SceneObject[]; evidence: EvidenceItem[]; timeline: TimelineEvent[] };
