// store.js
import create from 'zustand';

const useStore = create((set) => ({
    nodes: [],
    edges: [],
    setNodes: (nodes) => set({ nodes }),
    setEdges: (edges) => set({ edges }),
}));

export default useStore;
