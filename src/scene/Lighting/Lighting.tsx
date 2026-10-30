export function Lighting() {
  return <>
    <ambientLight intensity={1.15} />
    <hemisphereLight args={['#c8ddff', '#182235', .8]} />
    <directionalLight position={[5, 10, 5]} intensity={2.2} castShadow shadow-mapSize-width={1024} shadow-mapSize-height={1024} />
    <pointLight position={[-4, 3, -2]} intensity={18} distance={14} color="#4f8cff" />
  </>;
}
