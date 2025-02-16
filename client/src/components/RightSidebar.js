import React from 'react';

const RightSidebar = ({ isOpen, onClose, selectedNode, onSave }) => {
  return (
    <div 
      className={`fixed top-[150px] right-0 h-[calc(100vh-150px)] w-96 bg-gray-50/20 backdrop-blur-sm transform transition-transform duration-300 ease-in-out ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}
    >
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      {/* Content container */}
      <div className="p-6 h-full flex flex-col space-y-2 overflow-y-auto">
        {/* Current Description */}
        <div className="flex-1">
          <h3 className="text-2xl font-semibold mb-1 text-gray-700">Current Description</h3>
          <textarea
            className="w-full h-48 p-4 bg-white/10 backdrop-blur-sm border border-gray-300/30 rounded-lg focus:ring-blue-500 focus:border-blue-500 transition-all text-lg"
            defaultValue={selectedNode?.data?.task_description || ''}
            placeholder="No description available"
          />
        </div>

        {/* New Prompt */}
        <div className="flex-1">
          <h3 className="text-2xl font-semibold mb-1 text-gray-700">New Prompt</h3>
          <textarea
            className="w-full h-48 p-4 bg-white/10 backdrop-blur-sm border border-gray-300/30 rounded-lg focus:ring-blue-500 focus:border-blue-500 transition-all text-lg"
            placeholder="Enter new prompt..."
          />
        </div>

        {/* Save Button */}
        <button
          onClick={onSave}
          className="w-full bg-blue-600/80 backdrop-blur-sm text-white py-3 rounded-lg hover:bg-blue-700/90 transition-all duration-200 mb-6"
        >
          Save Changes
        </button>
      </div>
    </div>
  );
};

export default RightSidebar;
