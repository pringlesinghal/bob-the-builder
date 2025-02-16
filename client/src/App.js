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

  // Generate handles based on ingests and produces
  const renderIngestHandles = () => {
    const ingests = data.ingests || [];
    return ingests.map((ingest, index) => {
      const offset = ((index + 1) * 150) + 200; // Start from 200px down and space by 150px
      return (
        <Handle
          key={`ingest-${index}`}
          type="target"
          position={Position.Left}
          id={`ingest-${index}`}
          className="w-6 h-6 bg-blue-500 rounded-full border-3 border-white"
          style={{ left: -10, top: `${offset}px` }}
          isConnectable={true}
        />
      );
    });
  };

  const renderProducesHandles = () => {
    const produces = data.produces || [];
    return produces.map((output, index) => {
      const offset = ((index + 1) * 150) + 200; // Start from 200px down and space by 150px
      return (
        <Handle
          key={`output-${index}`}
          type="source"
          position={Position.Right}
          id={`output-${index}`}
          className="w-6 h-6 bg-blue-500 rounded-full border-3 border-white"
          style={{ right: -10, top: `${offset}px` }}
          isConnectable={true}
        />
      );
    });
  };

  return (
    <div
      className={`relative bg-white rounded-lg shadow-md p-4 border-2 w-[800px] h-[800px] flex flex-col transition-all duration-200 ${getBorderColor()} hover:shadow-lg ${isHovered ? 'scale-[1.02]' : ''}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}>
      {/* Task name at the top */}
      <div className='text-6xl font-bold mb-4 text-center leading-tight'>{data.task_name}</div>

      {/* Divider line */}
      <div className='border-b-2 border-gray-200 mb-3'></div>

      {/* Task description in the middle */}
      <div className='flex-1 text-5xl text-gray-600 overflow-auto p-8 leading-relaxed'>
        {data.task_description}
      </div>

      {/* Dynamic handles based on ingests and produces */}
      {renderIngestHandles()}
      {renderProducesHandles()}

      {/* Top handle for hierarchy */}
      {data.isChild && (
        <Handle
          type="target"
          position={Position.Top}
          id="top"
          className="w-6 h-6 bg-blue-500 rounded-full border-3 border-white"
          style={{ top: -10, left: '50%' }}
          isConnectable={true}
        />
      )}

      {/* Bottom handle for hierarchy */}
      {data.hasChildren && (
        <Handle
          type="source"
          position={Position.Bottom}
          id="bottom"
          className="w-6 h-6 bg-blue-500 rounded-full border-3 border-white"
          style={{ bottom: -10, left: '50%' }}
          isConnectable={true}
        />
      )}

      {/* Bottom handle - for all nodes */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom"
        className="w-6 h-6 bg-blue-500 rounded-full border-3 border-white"
        style={{ bottom: -10, left: '50%' }}
        isConnectable={true}
      />

      {/* Left handle - for child nodes */}
      {data.isChild && (
        <Handle
          type="source"
          position={Position.Left}
          id="left"
          className="w-6 h-6 bg-blue-500 rounded-full border-3 border-white"
          style={{ left: -10, top: '50%' }}
          isConnectable={true}
        />
      )}

      {/* Right handle - for child nodes */}
      {data.isChild && (
        <Handle
          type="source"
          position={Position.Right}
          id="right"
          className="w-6 h-6 bg-blue-500 rounded-full border-3 border-white"
          style={{ right: -10, top: '50%' }}
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
  // Add CSS to ensure the app takes full viewport height
  React.useEffect(() => {
    document.body.style.margin = '0';
    document.body.style.height = '100vh';
    document.documentElement.style.height = '100vh';
  }, []);
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

    // Layout configuration
    const horizontalGap = 300;     // Space between nodes at same level
    const verticalSpacing = 1500;  // Extra large space between depth levels
    const gridStartX = 100;       // Starting X position
    const gridStartY = 150;       // Starting Y position
    const nodeWidth = 800;        // Width of each node


    // First collect all tasks by depth level
    const tasksByDepth = new Map();
    
    const collectTasksByDepth = (task, depth = 0) => {
      if (!tasksByDepth.has(depth)) {
        tasksByDepth.set(depth, []);
      }
      tasksByDepth.get(depth).push(task);
      
      if (task.subtasks && task.subtasks.length > 0) {
        task.subtasks.forEach(subtask => collectTasksByDepth(subtask, depth + 1));
      }
    };
    
    // Collect all tasks
    taskData.forEach(task => collectTasksByDepth(task));
    
    // Calculate positions and create nodes
    const depthLevels = Array.from(tasksByDepth.keys());
    const maxDepth = Math.max(...depthLevels);
    
    // Process nodes by depth
    
    // Create nodes level by level
    depthLevels.forEach(depth => {
      const tasks = tasksByDepth.get(depth);
      const tasksCount = tasks.length;
      
      // Calculate total width needed for this level
      const totalWidth = (tasksCount - 1) * (nodeWidth + horizontalGap);
      
      // Calculate viewport width (use a minimum width to prevent overcrowding)
      const viewportWidth = Math.max(window.innerWidth, totalWidth + nodeWidth + (2 * gridStartX));
      
      // Center the nodes horizontally in the viewport
      const levelStartX = (viewportWidth - totalWidth - nodeWidth) / 2;
      
      // Create nodes for this depth level
      tasks.forEach((task, index) => {
        // Position node with exact spacing to ensure alignment
        const x = levelStartX + (index * (nodeWidth + horizontalGap));
        const y = gridStartY + (depth * verticalSpacing);
        
        // Create node with precise positioning
        const taskNode = {
          id: `node_${task.task_id}`,
          type: 'customNode',
          position: { x, y },
          draggable: true,
          data: {
            id: task.task_id,
            task_name: task.task_name,
            task_description: task.task_description,
            completed: task.completed || false,
            isChild: depth > 0,
            hasChildren: task.subtasks && task.subtasks.length > 0,
            dependencies: task.dependencies || []
          }
        };
        newNodes.push(taskNode);
        
        // Create edges to children
        if (task.subtasks) {
          task.subtasks.forEach(subtask => {
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
        
        // Create dependency edges (only for same level or adjacent levels)
        if (task.dependencies) {
          task.dependencies.forEach(depId => {
            newEdges.push({
              id: `edge-${depId}-${task.task_id}`,
              source: `node_${depId}`,
              target: `node_${task.task_id}`,
              type: 'custom',
              sourceHandle: 'right',
              targetHandle: 'left',
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
              }
            });
          });
        }
      });
    });


    // Create nodes for each depth level
    taskData.forEach((task, index) => {
      // Add main task node
      newNodes.push({
        id: `node_${task.task_id}`,
        type: 'customNode',
        position: {
          x: gridStartX + (index * (nodeWidth + horizontalGap)),
          y: gridStartY
        },
        data: {
          id: task.task_id,
          task_name: task.task_name,
          task_description: task.task_description,
          completed: task.completed,
          hasChildren: task.subtasks && task.subtasks.length > 0,
          ingests: task.ingests || [],
          produces: task.produces || []
        }
      });

      // Add subtask nodes
      if (task.subtasks && task.subtasks.length > 0) {
        const parentX = gridStartX + (index * (nodeWidth + horizontalGap));
        const totalWidth = (task.subtasks.length - 1) * (nodeWidth + horizontalGap);
        const childStartX = parentX - (totalWidth / 2);

        task.subtasks.forEach((subtask, childIndex) => {
          newNodes.push({
            id: `node_${subtask.task_id}`,
            type: 'customNode',
            position: {
              x: childStartX + (childIndex * (nodeWidth + horizontalGap)),
              y: gridStartY + verticalSpacing
            },
            data: {
              id: subtask.task_id,
              task_name: subtask.task_name,
              task_description: subtask.task_description,
              completed: subtask.completed || false,
              isChild: true,
              dependencies: subtask.dependencies || [],
              ingests: subtask.ingests || [],
              produces: subtask.produces || []
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

    // Create edges for all ingests/produces relationships
    taskData.forEach((sourceTask, sourceIndex) => {
      // Skip if task has no produces
      if (!sourceTask.produces || sourceTask.produces.length === 0) return;
      
      // For each link this task produces
      sourceTask.produces.forEach((producedLink, produceIndex) => {
        // Find all tasks that ingest this link
        taskData.forEach((targetTask, targetIndex) => {
          if (sourceIndex === targetIndex) return; // Skip self
          
          // Find if target task ingests this link
          const ingestIndex = targetTask.ingests?.findIndex(ingest => 
            ingest.link_id === producedLink.link_id
          );
          
          if (ingestIndex !== -1) {
            // Create edge from producer to ingester
            newEdges.push({
              id: `link-${producedLink.link_id}-${sourceTask.task_id}-${targetTask.task_id}`,
              source: `node_${sourceTask.task_id}`,
              target: `node_${targetTask.task_id}`,
              type: 'custom',
              sourceHandle: `output-${produceIndex}`,
              targetHandle: `ingest-${ingestIndex}`,
              style: { stroke: '#ff0000', strokeWidth: 2 },  // Red color like in diagram
              animated: true,
              data: { text: producedLink.link_name }  // Show link name on edge
            });
          }
        });
      });
    });

    // Handle dependencies
    // allTasks.forEach(task => {
    //   if (task.dependencies) {
    //     task.dependencies.forEach(depId => {
    //       newEdges.push(createDependencyEdge(depId, task.task_id, newNodes));
    //     });
    //   }
    // });

    console.log('Final nodes:', newNodes);
    console.log('Final edges:', newEdges);

    setNodes(newNodes);
    setEdges(newEdges);

    // Set specific zoom and view after creating nodes
    // Wait for nodes to be rendered
    setTimeout(() => {
      if (reactFlowInstance.current) {
        reactFlowInstance.current.fitView({ 
          padding: 0.1,
          duration: 600 // Smooth, comfortable transition
        });
      }
    }, 100);
  };

  // Function to handle send button click
  const handleSendClick = () => {
    if (prompt.trim()) {
      console.log('Handling send click with dummy tasks:', dummyTasks.subtasks);
      createNodesAndEdges(dummyTasks.subtasks);
      // Keeping prompt in the text bar
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

  // const handleAddNodeWithPrompt = useCallback(() => {
  //   if (prompt.trim() === '') {
  //     alert('Please enter a prompt before adding a node.');
  //     return;
  //   }
  //   createNodesAndEdges(dummyTasks);
  //   setPrompt('');
  // }, [setNodes, prompt, selectedNode, setEdges]);


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
    <div className='flex flex-col h-screen'>
      <div className='flex-shrink-0'>
        <Header />
      </div>

      <div className='flex flex-col items-center py-4 flex-shrink-0 bg-white border-b border-gray-200'>
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
          <button className='focus:outline-none transition-transform hover:scale-110' onClick={handleAddNodeNoPrompt}>
            <AiFillPlusCircle size={40} className='text-green-500 hover:text-green-700' />
          </button>
        </div>
      </div>

      <div className='flow-container flex-grow' style={{ minHeight: 0 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onInit={(instance) => {
            reactFlowInstance.current = instance;
            // Start with a view that shows the top area
            // Initial view
            instance.fitView({ duration: 600 });
          }}
          fitView
          fitViewOptions={{ padding: 0.1, includeHiddenNodes: true, duration: 600 }}
          minZoom={0.05}
          maxZoom={1.5}
          defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
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
              width: 20,
              height: 20
            }
          }}
          proOptions={{ hideAttribution: true }}
        >
          <Background color='#aaa' variant='dots' />
          <Controls
            position="bottom-left"
            style={{
              marginLeft: '16px',
              marginBottom: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              background: 'white',
              padding: '8px',
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              transform: 'scale(1.1)',
              zIndex: 5,
              '& button': {
                width: '24px',
                height: '24px',
                borderRadius: '6px',
                border: '1px solid #e2e8f0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }
            }}
            showZoom={true}
            showFitView={true}
            showInteractive={true}
            fitViewOptions={{ padding: 1 }}
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