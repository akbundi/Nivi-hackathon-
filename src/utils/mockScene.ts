import type { SceneData } from '../types/scene';
export const mockScene: SceneData = {
  id: 'demo-scene-001', title: 'Apartment — Scene Reconstruction', units: 'meters',
  room: { width: 12, depth: 9, height: 3.4 },
  objects: [
    { id: 'wall-back', name: 'Back wall', kind: 'structure', position: [0,1.7,-4.5], scale: [12,3.4,.12], color: '#25334a', confidence: .99 },
    { id: 'wall-left', name: 'Left wall', kind: 'structure', position: [-6,1.7,0], scale: [.12,3.4,9], color: '#25334a', confidence: .99 },
    { id: 'wall-right', name: 'Right wall', kind: 'structure', position: [6,1.7,0], scale: [.12,3.4,9], color: '#25334a', confidence: .99 },
    { id: 'sofa', name: 'Sofa', kind: 'furniture', position: [-2, .48, -2], scale: [2.6,.9,1], color: '#526a82', confidence: .94, description: 'Three-seat sofa near the north wall.' },
    { id: 'table', name: 'Coffee table', kind: 'furniture', position: [-1.5,.28,-.4], scale: [1.6,.12,.9], color: '#a77a55', confidence: .91, description: 'Low rectangular coffee table.' },
    { id: 'cabinet', name: 'Cabinet', kind: 'furniture', position: [3,.75,-3.4], scale: [1.2,1.5,.55], color: '#64748b', confidence: .83, description: 'Cabinet; placement is estimated.' },
    { id: 'chair', name: 'Chair', kind: 'furniture', position: [2,.45,1.2], scale: [.8,.9,.8], color: '#8b735e', confidence: .62, description: 'Chair with uncertain orientation.' },
    { id: 'door', name: 'Door opening', kind: 'structure', position: [0,1.1,4.45], scale: [1.5,2.2,.08], color: '#334155', confidence: .88 },
    { id: 'ev-01', name: 'Evidence A', kind: 'evidence', position: [-.8,.08,-.1], scale: [.22,.16,.22], color: '#f59e0b', confidence: .97, evidenceId: 'EV-001', description: 'Small item recorded near the coffee table.' },
    { id: 'ev-02', name: 'Evidence B', kind: 'evidence', position: [2.4,.08,1.8], scale: [.22,.16,.22], color: '#fb7185', confidence: .58, evidenceId: 'EV-002', description: 'Position inferred from a low-resolution image.' }
  ],
  evidence: [
    { id: 'EV-001', label: 'Evidence A', objectId: 'ev-01', description: 'Small item recorded near the coffee table. Source: demo evidence record.', confidence: .97, timestamp: '10:14:22' },
    { id: 'EV-002', label: 'Evidence B', objectId: 'ev-02', description: 'Position inferred from a low-resolution image; verify against source media.', confidence: .58, timestamp: '10:18:07' }
  ],
  timeline: [
    { id: 'T-01', time: '10:12', title: 'Room entered', description: 'Initial room state recorded.', objectIds: ['sofa','table'] },
    { id: 'T-02', time: '10:14', title: 'Evidence A logged', description: 'Evidence marker EV-001 added near the table.', objectIds: ['ev-01'] },
    { id: 'T-03', time: '10:18', title: 'Evidence B logged', description: 'Lower-confidence evidence position added.', objectIds: ['ev-02','chair'] }
  ]
};
