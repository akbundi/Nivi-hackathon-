import { useEffect, useState } from 'react';
import type { SceneData } from '../../types/scene';
import { loadScene } from '../../services/sceneApi';
export function useSceneLoader() {
  const [scene,setScene] = useState<SceneData | null>(null);
  const [error,setError] = useState<string | null>(null);
  useEffect(() => { let alive = true; loadScene().then(data => { if (alive) setScene(data); }).catch(e => { if (alive) setError(e instanceof Error ? e.message : 'Could not load scene'); }); return () => { alive=false; }; }, []);
  return { scene, error };
}
