import type { SceneData } from '../types/scene';
import { mockScene } from '../utils/mockScene';

/** Loads a scene JSON URL; falls back to demo data when no API URL is configured. */
export async function loadScene(url = import.meta.env.VITE_SCENE_API_URL): Promise<SceneData> {
  if (!url) return mockScene;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Scene request failed (${response.status})`);
  const data: unknown = await response.json();
  if (!isSceneData(data)) throw new Error('The scene API returned an unsupported scene schema.');
  return data;
}
export function isSceneData(value: unknown): value is SceneData {
  if (!value || typeof value !== 'object') return false;
  const scene = value as Partial<SceneData>;
  const isNumber = (n: unknown): n is number => typeof n === 'number' && Number.isFinite(n);
  const isVec3 = (v: unknown): v is [number, number, number] => Array.isArray(v) && v.length === 3 && v.every(isNumber);
  if (typeof scene.id !== 'string' || typeof scene.title !== 'string' || typeof scene.units !== 'string') return false;
  if (!scene.room || !isNumber(scene.room.width) || !isNumber(scene.room.depth) || !isNumber(scene.room.height)) return false;
  if (scene.room.width <= 0 || scene.room.depth <= 0 || scene.room.height <= 0) return false;
  if (!Array.isArray(scene.objects) || !Array.isArray(scene.evidence) || !Array.isArray(scene.timeline)) return false;
  const objectIds = new Set<string>();
  for (const object of scene.objects) {
    if (!object || typeof object.id !== 'string' || typeof object.name !== 'string') return false;
    if (!['furniture', 'structure', 'evidence', 'unknown'].includes(object.kind)) return false;
    if (!isVec3(object.position) || (object.rotation !== undefined && !isVec3(object.rotation)) || (object.scale !== undefined && !isVec3(object.scale))) return false;
    if (object.modelUrl !== undefined && (typeof object.modelUrl !== 'string' || object.modelUrl.trim() === '')) return false;
    if (object.confidence !== undefined && (!isNumber(object.confidence) || object.confidence < 0 || object.confidence > 1)) return false;
    if (objectIds.has(object.id)) return false;
    objectIds.add(object.id);
  }
  for (const evidence of scene.evidence) {
    if (!evidence || typeof evidence.id !== 'string' || typeof evidence.label !== 'string' || typeof evidence.description !== 'string' || typeof evidence.timestamp !== 'string' || typeof evidence.objectId !== 'string') return false;
    if (!isNumber(evidence.confidence) || evidence.confidence < 0 || evidence.confidence > 1 || !objectIds.has(evidence.objectId)) return false;
  }
  for (const event of scene.timeline) {
    if (!event || typeof event.id !== 'string' || typeof event.time !== 'string' || typeof event.title !== 'string' || typeof event.description !== 'string' || !Array.isArray(event.objectIds)) return false;
    if (!event.objectIds.every(id => typeof id === 'string' && objectIds.has(id))) return false;
  }
  return true;
}
