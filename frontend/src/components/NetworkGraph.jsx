import React from 'react';

/**
 * NetworkGraph Component
 *
 * Props:
 * - graphData (object|null): Ego network graph { center_id, hops, truncated, nodes, edges }
 * - centerId (string|null): ID of the center account
 * - onNodeClick (function): Callback when a graph node is clicked
 */
export default function NetworkGraph({ graphData = null, centerId = null, onNodeClick = () => {} }) {
  return (
    <div className="network-graph-placeholder" data-testid="network-graph">
      <h3>Network Graph {centerId ? `for ${centerId}` : ''}</h3>
    </div>
  );
}
