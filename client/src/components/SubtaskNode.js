import React, { useState } from 'react';
import { Handle, Position } from '@xyflow/react';

const SubtaskNode = ({ data, isSelected }) => {
  const [isHovered, setIsHovered] = useState(false);
  
  const getBorderColor = () => {
    if (isSelected) return 'border-blue-700';
    if (isHovered) {
      return data.completed ? 'border-green-500' : 'border-blue-500';
    }
    return 'border-gray-200';
  };
  
  return (
    <div 
      className={`relative bg-white rounded-lg shadow-md p-4 border-2 w-[400px] h-[250px] flex flex-col transition-all duration-200 ${getBorderColor()} hover:shadow-lg ${isHovered ? 'scale-[1.02]' : ''}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Task name at the top */}
      <div className='text-3xl font-bold mb-2 text-center'>{data.task_name}</div>
      
      {/* Divider line */}
      <div className='border-b-2 border-gray-200 mb-3'></div>
      
      {/* Task description in the middle */}
      <div className='flex-1 text-lg text-gray-600 overflow-auto p-2'>
        {data.task_description}
      </div>

      {/* Top handle */}
      <Handle
        type="target"
        position={Position.Top}
        id="top"
        className="w-3 h-3 bg-blue-500 rounded-full border-2 border-white"
        style={{ top: -6, left: '50%' }}
        isConnectable={true}
      />

      {/* Left handle */}
      <Handle
        type="target"
        position={Position.Left}
        id="left"
        className="w-3 h-3 bg-blue-500 rounded-full border-2 border-white"
        style={{ left: -6, top: '50%' }}
        isConnectable={true}
      />

      {/* Right handle */}
      <Handle
        type="source"
        position={Position.Right}
        id="right"
        className="w-3 h-3 bg-blue-500 rounded-full border-2 border-white"
        style={{ right: -6, top: '50%' }}
        isConnectable={true}
      />

      {/* Bottom handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom"
        className="w-3 h-3 bg-blue-500 rounded-full border-2 border-white"
        style={{ bottom: -6, left: '50%' }}
        isConnectable={true}
      />
    </div>
  );
};

export default SubtaskNode;
