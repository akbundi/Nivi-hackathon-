import { describe, expect, it } from 'vitest';
import { isSceneData } from '../src/services/sceneApi';
import { mockScene } from '../src/utils/mockScene';

describe('scene schema guard', () => {
  it('accepts the demo scene', () => expect(isSceneData(mockScene)).toBe(true));
  it('rejects an unrelated object', () => expect(isSceneData({ hello: 'world' })).toBe(false));
  it('rejects invalid room dimensions', () => expect(isSceneData({ ...mockScene, room: { ...mockScene.room, width: -1 } })).toBe(false));
  it('rejects evidence pointing to a missing object', () => expect(isSceneData({ ...mockScene, evidence: [{ ...mockScene.evidence[0], objectId: 'missing-object' }] })).toBe(false));
  it('rejects duplicate object IDs', () => expect(isSceneData({ ...mockScene, objects: [...mockScene.objects, mockScene.objects[0]] })).toBe(false));
});
