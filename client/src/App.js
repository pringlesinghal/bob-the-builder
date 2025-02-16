import React, { useState, useCallback, useMemo, useRef } from 'react';
import {
  ReactFlow,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  Handle,
  Position,
  Connection,
} from '@xyflow/react';
import { AiFillPlusCircle } from 'react-icons/ai';
import { IoSend } from "react-icons/io5";
import '@xyflow/react/dist/style.css';
import './App.css';
import Header from './components/Header';
import CustomEdge from './components/CustomEdge';
import BranchedEdge from './components/BranchedEdge';
import SubtaskNode from './components/SubtaskNode';
import RightSidebar from './components/RightSidebar';
import dummyTasks from './dummydata.json';

console.log('Loaded dummy tasks:', dummyTasks);

let id = 0;
const getId = () => `node_${id++}`;

// Custom Node Component with multiple handles
const CustomNode = ({ data, isSelected }) => {
  const [isHovered, setIsHovered] = useState(false);

  // Determine border color based on hover and selection state
  const getBorderColor = () => {
    if (isSelected) return 'border-blue-700';
    if (isHovered) {
      return data.completed ? 'border-green-500' : 'border-blue-500';
    }
    return 'border-gray-200'; // Neutral border when not hovered
  };

  return (
    <div
      className={`relative bg-white rounded-lg shadow-md p-4 border-2 w-[400px] h-[250px] flex flex-col transition-all duration-200 ${getBorderColor()} hover:shadow-lg ${isHovered ? 'scale-[1.02]' : ''}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}>
      {/* Task name at the top */}
      <div className='text-3xl font-bold mb-2 text-center'>{data.task_name}</div>

      {/* Divider line */}
      <div className='border-b-2 border-gray-200 mb-3'></div>

      {/* Task description in the middle */}
      <div className='flex-1 text-lg text-gray-600 overflow-auto p-2'>
        {data.task_description}
      </div>

      {/* Top handle - for child nodes */}
      {data.isChild && (
        <Handle
          type="target"
          position={Position.Top}
          id="top"
          className="w-3 h-3 bg-blue-500 rounded-full border-2 border-white"
          style={{ top: -6, left: '50%' }}
          isConnectable={true}
        />
      )}

      {/* Left handle - only for parent-to-parent */}
      {!data.isChild && (
        <Handle
          type="target"
          position={Position.Left}
          id="left"
          className="w-3 h-3 bg-blue-500 rounded-full border-2 border-white"
          style={{ left: -6, top: '50%' }}
          isConnectable={true}
        />
      )}

      {/* Right handle - only for parent-to-parent */}
      {!data.isChild && (
        <Handle
          type="source"
          position={Position.Right}
          id="right"
          className="w-3 h-3 bg-blue-500 rounded-full border-2 border-white"
          style={{ right: -6, top: '50%' }}
          isConnectable={true}
        />
      )}

      {/* Bottom handle - for all nodes */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom"
        className="w-3 h-3 bg-blue-500 rounded-full border-2 border-white"
        style={{ bottom: -6, left: '50%' }}
        isConnectable={true}
      />

      {/* Left handle - for child nodes */}
      {data.isChild && (
        <Handle
          type="source"
          position={Position.Left}
          id="left"
          className="w-3 h-3 bg-blue-500 rounded-full border-2 border-white"
          style={{ left: -6, top: '50%' }}
          isConnectable={true}
        />
      )}

      {/* Right handle - for child nodes */}
      {data.isChild && (
        <Handle
          type="source"
          position={Position.Right}
          id="right"
          className="w-3 h-3 bg-blue-500 rounded-full border-2 border-white"
          style={{ right: -6, top: '50%' }}
          isConnectable={true}
        />
      )}
    </div>
  );
};

const nodeTypes = {
  customNode: CustomNode,
};

const edgeTypes = {
  custom: CustomEdge,      // Curved edges for parent-to-parent and subtask-to-subtask
  branched: BranchedEdge,  // Straight dotted edges for parent-to-child
};

console.log('Available edge types:', edgeTypes);

console.log('Available edge types:', Object.keys(edgeTypes));

function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [prompt, setPrompt] = useState('');
  const [selectedNode, setSelectedNode] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const reactFlowInstance = useRef(null);

  // Function to create nodes and edges based on task data
  const createNodesAndEdges = (taskData) => {
    console.log('Creating nodes and edges from data:', taskData);
    const newNodes = [];
    const newEdges = [];

    // --------------------------------------------------------------------------------
    // Directly add the edge between Subtask B (1_2) and Subtask C (2_1)
    const hardcodedEdge = {
      id: 'edge-1_2-2_1',
      source: 'node_1_2',  // Subtask B
      target: 'node_2_1',  // Subtask C
      type: 'custom',
      sourceHandle: 'right',
      targetHandle: 'left',
      animated: false,
      style: {
        stroke: '#2563eb',
        strokeWidth: 2,
        zIndex: 1
      },
      markerEnd: {
        type: 'arrowclosed',
        width: 20,
        height: 20,
        color: '#2563eb',
      },
    };
    newEdges.push(hardcodedEdge);
    // --------------------------------------------------------------------------------

    // Function to create an edge between nodes
    const createDependencyEdge = (sourceId, targetId, nodes) => {
      // Find source and target nodes to determine their types
      const sourceNode = nodes.find(n => n.id === `node_${sourceId}`);
      const targetNode = nodes.find(n => n.id === `node_${targetId}`);
      const isSourceChild = sourceNode?.data?.isChild;
      const targetChild = targetNode?.data?.isChild;

      // Parent-to-child connection should be dotted
      const isParentToChild = !isSourceChild && targetChild;

      console.log('Creating edge:', sourceId, '->', targetId, 'isParentToChild:', isParentToChild);

      return {
        id: `edge-${sourceId}-${targetId}`,
        source: `node_${sourceId}`,
        target: `node_${targetId}`,
        type: 'custom',
        sourceHandle: 'right',
        targetHandle: 'left',
        animated: false,
        style: {
          stroke: '#2563eb',
          strokeWidth: 2,
          strokeDasharray: isParentToChild ? '4' : undefined,
          zIndex: 1
        },
        markerEnd: {
          type: 'arrowclosed',
          width: 20,
          height: 20,
          color: '#2563eb',
        },
      };
    };

    // Add edges for all dependencies (both tasks and subtasks)
    taskData.forEach(task => {
      // Handle task dependencies
      if (task.dependencies) {
        task.dependencies.forEach(depId => {
          newEdges.push(createDependencyEdge(depId, task.task_id, newNodes));
        });
      }

      // Handle subtask dependencies
      if (task.subtasks) {
        task.subtasks.forEach(subtask => {
          if (subtask.dependencies) {
            subtask.dependencies.forEach(depId => {
              newEdges.push(createDependencyEdge(depId, subtask.task_id, newNodes));
            });
          }
        });
      }
    });

    // Calculate node levels based on dependencies
    const nodeLevels = {};

    // Initialize nodes with no dependencies at level 0
    taskData.forEach(task => {
      if (!task.dependencies || task.dependencies.length === 0) {
        nodeLevels[task.task_id] = 0;
      }
    });

    // Calculate levels for nodes with dependencies
    let changed = true;
    while (changed) {
      changed = false;
      taskData.forEach(task => {
        if (task.dependencies && task.dependencies.length > 0) {
          const maxDependencyLevel = Math.max(...task.dependencies.map(depId => nodeLevels[depId] || 0));
          const newLevel = maxDependencyLevel + 1;
          if (nodeLevels[task.task_id] !== newLevel) {
            nodeLevels[task.task_id] = newLevel;
            changed = true;
          }
        }
      });
    }

    // Create nodes with positions based on horizontal layout
    const nodeWidth = 400; // Width of each node
    const minSpacing = 100; // Minimum space between nodes
    const horizontalSpacing = 1000; // Much wider spacing for parent nodes
    const startX = 100; // Left padding
    const fixedY = 350; // Parent node Y position


    // First pass: create all nodes
    taskData.forEach((task, index) => {
      // Add main task node
      newNodes.push({
        id: `node_${task.task_id}`,
        type: 'customNode',
        position: {
          x: startX + (index * horizontalSpacing),
          y: fixedY
        },
        data: {
          id: task.task_id,
          task_name: task.task_name,
          task_description: task.task_description,
          completed: task.completed,
          hasChildren: task.subtasks && task.subtasks.length > 0 // Flag to show bottom handle
        }
      });

      // Add child nodes for each task
      if (task.subtasks && task.subtasks.length > 0) {
        const parentX = startX + (index * horizontalSpacing); // Get parent's X position
        const childSpacing = nodeWidth + minSpacing; // Space between child nodes (node width + minimum gap)
        const totalChildWidth = childSpacing * (task.subtasks.length - 1); // Total width of all children
        const childStartX = parentX - (totalChildWidth / 2); // Starting X position for first child

        task.subtasks.forEach((subtask, childIndex) => {
          // Create child node with exact task_id for dependencies
          const childNode = {
            id: `node_${subtask.task_id}`,
            type: 'customNode',
            position: {
              x: childStartX + (childIndex * childSpacing), // Position each child with proper spacing
              y: fixedY + 400 // Below parent task
            },
            draggable: true,
            data: {
              id: subtask.task_id,
              task_name: subtask.task_name,
              task_description: subtask.task_description,
              completed: subtask.completed || false,
              isChild: true, // Flag to show all 4 handles
              dependencies: subtask.dependencies || [] // Pass dependencies to node
            }
          };
          console.log('Created child node:', childNode.id, 'with dependencies:', subtask.dependencies);
          newNodes.push(childNode);

          // Add edge from parent task to subtask (branched dotted line)
          newEdges.push({
            id: `edge-${task.task_id}-${subtask.task_id}`,
            source: `node_${task.task_id}`,
            target: `node_${subtask.task_id}`,
            type: 'branched',  // Use branched edge type for parent-to-child
            sourceHandle: 'bottom', // Always use bottom handle for parent
            targetHandle: 'top',    // Always use top handle for child
            style: {
              strokeDasharray: '4',  // Dotted line for parent-to-child
              stroke: '#2563eb',
              strokeWidth: 2,
            }
          });

          // Add edges for subtask dependencies
          if (subtask.dependencies && subtask.dependencies.length > 0) {
            subtask.dependencies.forEach(depId => {
              console.log('Creating dependency edge:', depId, '->', subtask.task_id);
              newEdges.push({
                id: `edge-${depId}-${subtask.task_id}`,
                source: `node_${depId}`,
                target: `node_${subtask.task_id}`,
                type: 'custom',
                sourceHandle: 'right',
                targetHandle: 'left',
                animated: false,
                style: {
                  stroke: '#2563eb',
                  strokeWidth: 2,
                  zIndex: 1
                },
                markerEnd: {
                  type: 'arrowclosed',
                  width: 20,
                  height: 20,
                  color: '#2563eb',
                },
              });
            });
          }
        });
      }
    });


    // Create all nodes first
    taskData.forEach((task, index) => {
      // Add main task node
      newNodes.push({
        id: `node_${task.task_id}`,
        type: 'customNode',
        position: {
          x: startX + (index * horizontalSpacing),
          y: fixedY
        },
        data: {
          id: task.task_id,
          task_name: task.task_name,
          task_description: task.task_description,
          completed: task.completed,
          hasChildren: task.subtasks && task.subtasks.length > 0
        }
      });

      // Add subtask nodes
      if (task.subtasks && task.subtasks.length > 0) {
        const parentX = startX + (index * horizontalSpacing);
        const childSpacing = nodeWidth + minSpacing;
        const totalChildWidth = childSpacing * (task.subtasks.length - 1);
        const childStartX = parentX - (totalChildWidth / 2);

        task.subtasks.forEach((subtask, childIndex) => {
          newNodes.push({
            id: `node_${subtask.task_id}`,
            type: 'customNode',
            position: {
              x: childStartX + (childIndex * childSpacing),
              y: fixedY + 400
            },
            data: {
              id: subtask.task_id,
              task_name: subtask.task_name,
              task_description: subtask.task_description,
              completed: subtask.completed || false,
              isChild: true,
              dependencies: subtask.dependencies || []
            }
          });

          // Add parent-child connection
          newEdges.push({
            id: `edge-${task.task_id}-${subtask.task_id}`,
            source: `node_${task.task_id}`,
            target: `node_${subtask.task_id}`,
            type: 'branched',
            sourceHandle: 'bottom',
            targetHandle: 'top',
            style: {
              strokeDasharray: '4',
              stroke: '#2563eb',
              strokeWidth: 2,
            }
          });
        });
      }
    });

    // Create dependency edges after all nodes are created
    taskData.forEach(task => {
      // Handle main task dependencies
      if (task.dependencies) {
        task.dependencies.forEach(depId => {
          console.log('Creating task dependency:', depId, '->', task.task_id);
          newEdges.push(createDependencyEdge(depId, task.task_id, newNodes));
        });
      }

      // Handle subtask dependencies
      if (task.subtasks) {
        task.subtasks.forEach(subtask => {
          if (subtask.dependencies) {
            subtask.dependencies.forEach(depId => {
              console.log('Creating subtask dependency:', depId, '->', subtask.task_id);
              const edge = createDependencyEdge(depId, subtask.task_id, newNodes);
              console.log('Created edge:', edge);
              newEdges.push(edge);
            });
          }
        });
      }
    });

    console.log('Final nodes:', newNodes);
    console.log('Final edges:', newEdges);

    setNodes(newNodes);
    setEdges(newEdges);
  };

  // Function to handle send button click
  const handleSendClick = () => {
    if (prompt.trim()) {
      console.log('Handling send click with dummy tasks:', dummyTasks);
      createNodesAndEdges(dummyTasks);
      setPrompt('');
    }
  };

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
    setIsSidebarOpen(true);
  }, []);

  const handleSidebarClose = useCallback(() => {
    setIsSidebarOpen(false);
  }, []);

  const handleSaveChanges = useCallback(() => {
    // TODO: Implement save logic
    console.log('Saving changes for node:', selectedNode?.id);
    setIsSidebarOpen(false);
  }, [selectedNode]);

  // Enhanced connection handling with validation
  const onConnect = useCallback((params) => {
    // Validate connection - prevent self loops and duplicate connections
    if (params.source !== params.target) {
      setEdges((eds) => {
        // Check if connection already exists
        const connectionExists = eds.some(
          (edge) =>
            edge.source === params.source && edge.target === params.target
        );
        if (!connectionExists) {
          return addEdge(params, eds);
        }
        return eds;
      });
    }
  }, [setEdges]);

  const handleAddNode = useCallback(() => {
    const newNode = {
      id: getId(),
      type: 'customNode',
      data: { label: prompt },
      position: {
        x: Math.random() * 500,
        y: Math.random() * 300,
      },
      // Add input and output handles
      sourcePosition: 'right',
      targetPosition: 'left',
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

  const handleAddNodeWithPrompt = useCallback(() => {
    if (prompt.trim() === '') {
      alert('Please enter a prompt before adding a node.');
      return;
    }
    createNodesAndEdges(dummyTasks);
    setPrompt('');
  }, [setNodes, prompt, selectedNode, setEdges]);


  const handleAddNodeNoPrompt = useCallback(() => {
    const newNode = {
      id: getId(),
      type: 'customNode', // Specify the custom node type
      data: { label: "New Node" },
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
  }, [setNodes]);


  // Node types are already registered globally

  return (
    <div>
      <Header />

      <div className='flex flex-col items-center mt-10'>
        <div className='flex transition-transform hover:scale-105 justify-center'>
          <input
            className='px-4 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-400 w-[1200px]' // Increased width
            type='text'
            placeholder='Enter prompt...'
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
          <button
            className='bg-blue-500 text-white px-4 py-2 rounded-r-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400'
            onClick={handleSendClick}
          >
            <IoSend />
          </button>
        </div>

        <div className='self-start pl-4'>
          <button className='focus:outline-none mt-2 transition-transform hover:scale-110' onClick={handleAddNodeNoPrompt}>
            <AiFillPlusCircle size={40} className='text-green-500 hover:text-green-700' />
          </button>
        </div>
      </div>

      <div className='flow-container'>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onInit={(instance) => {
            reactFlowInstance.current = instance;
            instance.fitView({ padding: 0.2, includeHiddenNodes: true });
          }}
          fitView
          fitViewOptions={{ padding: 0.2, includeHiddenNodes: true }}
          minZoom={0.1}
          maxZoom={1.5}
          defaultViewport={{ x: 0, y: 0, zoom: 0.5 }}
          className='bg-gray-100'
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          onNodeClick={onNodeClick}
          defaultEdgeOptions={{
            animated: false,
            style: {
              stroke: '#2563eb',
              strokeWidth: 2,
              zIndex: 1
            },
            markerEnd: {
              type: 'arrowclosed',
              color: '#2563eb',
              width: 12,
              height: 12
            }
          }}
          proOptions={{ hideAttribution: true }}
        >
          <Background color='#aaa' variant='dots' />
          <Controls

            style={{ position: 'absolute', bottom: 20, right: 20, zIndex: 4 }}
            showZoom={true}
            showFitView={true}
            showInteractive={false}
          />
        </ReactFlow>
        <RightSidebar
          isOpen={isSidebarOpen}
          onClose={handleSidebarClose}
          selectedNode={selectedNode}
          onSave={handleSaveChanges}
        />
      </div>
    </div>
  );
}

export default App;
