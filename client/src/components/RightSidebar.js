import React from 'react';

const RightSidebar = ({ isOpen, onClose, selectedNode }) => {
  // Extract input and output parameters from the selected node
  const inputLinks = selectedNode?.data?.ingests?.map(ingest => ingest.link_name) || [];
  const outputLinks = selectedNode?.data?.produces?.map(produce => produce.link_name) || [];

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
      <div className="p-6 h-full flex flex-col space-y-4 overflow-y-auto">
        {/* Task Name */}
        <div>
          <h3 className="text-xl font-semibold text-gray-700">Task Name</h3>
          <p className="mt-2 p-3 bg-white/10 backdrop-blur-sm border border-gray-300/30 rounded-lg text-gray-800">
            {selectedNode?.data?.task_name || 'No task name available'}
          </p>
        </div>

        {/* Task Description */}
        <div>
          <h3 className="text-xl font-semibold text-gray-700">Task Description</h3>
          <p className="mt-2 p-3 bg-white/10 backdrop-blur-sm border border-gray-300/30 rounded-lg text-gray-800 whitespace-pre-wrap">
            {selectedNode?.data?.task_description || 'No description available'}
          </p>
        </div>

        {/* Input Parameters */}
        <div>
          <h3 className="text-xl font-semibold text-gray-700">Input Parameters</h3>
          <div className="mt-2 p-3 bg-white/10 backdrop-blur-sm border border-gray-300/30 rounded-lg">
            {inputLinks.length > 0 ? (
              <ul className="list-disc list-inside space-y-1">
                {inputLinks.map((link, index) => (
                  <li key={index} className="text-gray-800">{link}</li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-600">No input parameters</p>
            )}
          </div>
        </div>

        {/* Output Parameters */}
        <div>
          <h3 className="text-xl font-semibold text-gray-700">Output Parameters</h3>
          <div className="mt-2 p-3 bg-white/10 backdrop-blur-sm border border-gray-300/30 rounded-lg">
            {outputLinks.length > 0 ? (
              <ul className="list-disc list-inside space-y-1">
                {outputLinks.map((link, index) => (
                  <li key={index} className="text-gray-800">{link}</li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-600">No output parameters</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RightSidebar;
