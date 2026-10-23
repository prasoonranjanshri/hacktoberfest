import React, { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";

export default function NetworkGraph({
  graphData = null,
  centerId = null,
  onNodeClick,
  loading = false,
  error = null,
}) {
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 600, height: 420 });

  useEffect(() => {
    if (!containerRef.current) return;
    const updateSize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth || 600,
          height: Math.max(380, containerRef.current.clientHeight || 420),
        });
      }
    };

    updateSize();
    const observer = new ResizeObserver(updateSize);
    observer.observe(containerRef.current);
    window.addEventListener("resize", updateSize);

    return () => {
      observer.disconnect();
      window.removeEventListener("resize", updateSize);
    };
  }, []);

  // Format data for react-force-graph
  const formattedData = useMemo(() => {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
      return { nodes: [], links: [] };
    }

    const nodeIds = new Set(graphData.nodes.map((n) => n.id));
    const nodes = graphData.nodes.map((n) => ({
      id: n.id,
      risk_score: n.risk_score,
      ground_truth_fraud: n.ground_truth_fraud,
      is_center: n.is_center || n.id === centerId,
    }));

    // Links must connect valid nodes
    const links = (graphData.edges || [])
      .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
      .map((e) => ({
        source: e.source,
        target: e.target,
        txn_count: e.txn_count,
        total_amount_inr: e.total_amount_inr,
        first_ts: e.first_ts,
        last_ts: e.last_ts,
      }));

    return { nodes, links };
  }, [graphData, centerId]);

  const getNodeColor = (node) => {
    if (node.is_center) return "#06b6d4"; // Cyan for center
    const s = node.risk_score || 0;
    if (s >= 0.8) return "#ef4444";
    if (s >= 0.4) return "#f59e0b";
    return "#10b981";
  };

  return (
    <div className="card graph-card">
      <div className="card-title">
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span>Ego-Network Graph</span>
          {centerId && (
            <span className="badge badge-fixture">Center: {centerId}</span>
          )}
          <span className="badge badge-status">Hops: 1</span>
        </div>
        <div style={{ display: "flex", gap: "10px", alignItems: "center", fontSize: "11px", color: "var(--text-muted)" }}>
          <span>Click counterparty node to pivot</span>
          <span className="ground-truth-tag">Red halo: ground-truth fraud</span>
        </div>
      </div>

      <div className="graph-canvas-container" ref={containerRef}>
        {graphData?.truncated && (
          <div className="graph-notice">
            Notice: Counterparties truncated to top connections by volume
          </div>
        )}

        {loading ? (
          <div className="skeleton" style={{ width: "100%", height: "100%" }} />
        ) : error ? (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#f87171" }}>
            Failed to load ego-network graph: {error}
          </div>
        ) : formattedData.nodes.length === 0 ? (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--text-muted)" }}>
            No transaction connections found for this account.
          </div>
        ) : (
          <ForceGraph2D
            width={dimensions.width}
            height={dimensions.height}
            graphData={formattedData}
            nodeLabel={(node) =>
              `Account: ${node.id}\nRisk: ${(node.risk_score ?? 0).toFixed(4)}\nEvaluation: ${
                node.ground_truth_fraud ? "FRAUD" : "Legitimate"
              }`
            }
            nodeColor={getNodeColor}
            nodeVal={(node) => (node.is_center ? 14 : 7)}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const label = node.id;
              const fontSize = node.is_center ? 13 / globalScale : 10 / globalScale;
              const radius = node.is_center ? 10 : 6;

              // Center halo
              if (node.is_center) {
                ctx.beginPath();
                ctx.arc(node.x, node.y, radius + 5, 0, 2 * Math.PI, false);
                ctx.fillStyle = "rgba(6, 182, 212, 0.25)";
                ctx.fill();
              }

              // Red outline for ground truth fraud
              if (node.ground_truth_fraud) {
                ctx.beginPath();
                ctx.arc(node.x, node.y, radius + 2, 0, 2 * Math.PI, false);
                ctx.strokeStyle = "#f43f5e";
                ctx.lineWidth = 2 / globalScale;
                ctx.stroke();
              }

              // Node circle
              ctx.beginPath();
              ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
              ctx.fillStyle = getNodeColor(node);
              ctx.fill();

              // Text label
              ctx.font = `${fontSize}px Sans-Serif`;
              ctx.textAlign = "center";
              ctx.textBaseline = "middle";
              ctx.fillStyle = node.is_center ? "#38bdf8" : "#cbd5e1";
              ctx.fillText(label, node.x, node.y + radius + 7);
            }}
            linkWidth={(link) => {
              const amt = link.total_amount_inr || 1000;
              return Math.min(6, Math.max(1, Math.log10(amt) - 2));
            }}
            linkColor={() => "rgba(100, 116, 139, 0.4)"}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={1}
            linkLabel={(link) =>
              `${link.source.id || link.source} -> ${link.target.id || link.target}\nAmount: INR ${Number(
                link.total_amount_inr
              ).toLocaleString()}\nTransactions: ${link.txn_count}`
            }
            onNodeClick={(node) => {
              if (onNodeClick && node && node.id) {
                onNodeClick(node.id);
              }
            }}
            cooldownTicks={80}
          />
        )}
      </div>
    </div>
  );
}
