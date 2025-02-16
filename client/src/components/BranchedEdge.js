import React from 'react';
import { BaseEdge } from '@xyflow/react';

function BranchedEdge({ sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition }) {
  // Calculate branching point (40% down from source)
  const branchY = sourceY + (targetY - sourceY) * 0.4;
  
  // Calculate control points for smooth curve
  const controlY = branchY + (targetY - branchY) * 0.5;
  
  // Create a path with smooth curves
  const path = `
    M ${sourceX},${sourceY} 
    L ${sourceX},${branchY} 
    C ${sourceX},${controlY} ${targetX},${controlY} ${targetX},${targetY}
  `;

  return (
    <BaseEdge
      path={path}
      style={{
        strokeWidth: 2,
        stroke: '#2563eb',
        strokeDasharray: '4',
      }}
    />
  );
}

export default BranchedEdge;
