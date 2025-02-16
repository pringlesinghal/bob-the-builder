import React from 'react';
import { BaseEdge } from '@xyflow/react';

const getCustomPath = ({ sourceX, sourceY, targetX, targetY, data }) => {
  const distance = Math.abs(targetX - sourceX);
  const sourceId = data?.sourceId || '';
  const targetId = data?.targetId || '';
  
  // Calculate node indices from IDs (assuming format 'node_1', 'node_2', etc.)
  const sourceIndex = parseInt(sourceId.split('_')[1]);
  const targetIndex = parseInt(targetId.split('_')[1]);
  const nodeDistance = Math.abs(targetIndex - sourceIndex);
  
  // Increase curve height for nodes that are further apart
  const baseHeight = distance * 1.8; // Doubled base height
  const heightMultiplier = nodeDistance > 1 ? 4.5 : 1.2; // Much higher for longer edges, shorter for adjacent
  const curveHeight = -Math.min(baseHeight * heightMultiplier, 800); // Increased max height for longer curves
  
  // Adjust control points based on node distance
  const spreadMultiplier = nodeDistance > 1 ? 0.6 : 0.4; // Increased spread significantly
  const controlPoint1X = sourceX + distance * spreadMultiplier;
  const controlPoint2X = targetX - distance * spreadMultiplier;
  const controlPointY = sourceY + curveHeight;
  
  // Create a cubic bezier curve with dynamic curvature
  return `M ${sourceX} ${sourceY} C ${controlPoint1X} ${controlPointY}, ${controlPoint2X} ${controlPointY}, ${targetX} ${targetY}`;
};

export default function CustomEdge({
  sourceX,
  sourceY,
  targetX,
  targetY,
  markerEnd,
  style = {},
  data
}) {
  const path = getCustomPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    data
  });

  return (
    <BaseEdge 
      path={path} 
      markerEnd={markerEnd}
      className="react-flow__edge-path"
      style={{
        ...style,
        strokeWidth: 3,
        stroke: '#2563eb',
        fill: 'none',
        strokeDasharray: 'none',
        filter: 'drop-shadow(0 1px 2px rgb(0 0 0 / 0.1))', // Add subtle shadow for depth
      }}
    />
  );
}
