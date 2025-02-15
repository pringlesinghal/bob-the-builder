import React, { useState, useCallback } from 'react';
import {
  ReactFlow,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './App.css';
import Header from './components/Header';

let id = 0;
const getId = () => `node_${id++}`;

// Custom Node Component
const CustomNode = ({ data }) => {
  return (
    <div className='bg-white rounded-lg shadow-md p-4 border border-gray-200'>
      <div>{data.label}</div>
    </div>
  );
};

function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [prompt, setPrompt] = useState('');

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const handleAddNode = useCallback(() => {
    if (prompt.trim() === '') {
      alert('Please enter a prompt before adding a node.');
      return;
    }

    const newNode = {
      id: getId(),
      type: 'customNode', // Specify the custom node type
      data: { label: prompt },
      position: {
        x: Math.random() * 500,
        y: Math.random() * 300,
      },
      style: {
        background: 'transparent', // Remove default background
        border: 'none', // Remove default border
        padding: 0, // Remove default padding
        width: 'auto', // Adjust width based on content
      },
    };

    setNodes((nds) => nds.concat(newNode));
    setPrompt('');
  }, [setNodes, prompt]);

  const nodeTypes = React.useMemo(() => ({ customNode: CustomNode }), []); //Register Custom Node

  return (
    <div>
      <Header />

      <div className='flex justify-center items-center mt-10 transition-transform hover:scale-105'>
        <input
          className='px-4 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-400 w-[800px]' // Increased width
          type='text'
          placeholder='Enter prompt...'
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
        <button
          className='bg-blue-500 text-white px-4 py-2 rounded-r-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400'
          onClick={handleAddNode}
        >
          Add Node
        </button>
      </div>

      <div className='h-[500px] mt-4'>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
          className='bg-gray-100'
          nodeTypes={nodeTypes} // Pass custom node types
        >
          <Controls />
          <Background color='#aaa' variant='dots' />
        </ReactFlow>
      </div>
    </div>
  );
}

export default App;
