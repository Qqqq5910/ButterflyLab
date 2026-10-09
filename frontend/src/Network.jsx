import React, { useState, useEffect } from "react";
export default function Network({
  world,
  highlight = false,
  interventionAgent = 0,
  transmissions = [],
  loadAgent,
  detailKey,
  differences = [],
}) {
  const [selected, setSelected] = useState(null);
  const [detail,setDetail]=useState(null),[detailError,setDetailError]=useState('');
  useEffect(()=>{
    let alive=true;setDetail(null);setDetailError('');
    if(selected!=null&&loadAgent)loadAgent(selected).then(a=>{if(alive)setDetail(a)}).catch(e=>{if(alive)setDetailError(e.message)});
    return()=>{alive=false};
  },[selected,detailKey]);
  if (!world) return <div className="network-empty">Loading world...</div>;
  const nodes = world.agents || [],
    edges = world.edges || [];
  const indexOf = (id) =>
    typeof id === "string" && id.startsWith("A")
      ? Number(id.slice(1)) - 1
      : Number(id);
  const position = (id) => {
    const node = nodes.find((a) => a.id === id);
    if (
      node &&
      world.config?.engine &&
      Number.isFinite(node.x) &&
      Number.isFinite(node.y)
    )
      return { x: 50 + node.x * 40, y: 50 + node.y * 36 };
    const i = indexOf(id),
      angle = i * 2.399963,
      radius = 4 + 42 * Math.sqrt((i + 0.5) / Math.max(nodes.length, 1));
    return {
      x: 50 + Math.cos(angle) * radius,
      y: 50 + Math.sin(angle) * radius * 0.8,
    };
  };
  const selectedAgent = detail||nodes.find((a) => a.id === selected);
  return (
    <div
      className="network"
      aria-label={`${nodes.length} agent social network`}
    >
      <svg className="edge-layer" aria-hidden="true">
        {edges.map((edge, i) => {
          if (
            !nodes.some((a) => a.id === edge.source) ||
            !nodes.some((a) => a.id === edge.target)
          )
            return null;
          const a = position(edge.source),
            b = position(edge.target);
          return (
            <line
              key={i}
              x1={`${a.x}%`}
              y1={`${a.y}%`}
              x2={`${b.x}%`}
              y2={`${b.y}%`}
              stroke={
                transmissions.some(
                  (p) =>
                    (p.source === edge.source && p.target === edge.target) ||
                    (p.target === edge.source && p.source === edge.target),
                )
                  ? "#72b5d0"
                  : highlight
                    ? "#c8a86b"
                    : "#33424d"
              }
              strokeOpacity={Math.min(0.35 + edge.weight * 0.4, 0.75)}
              strokeWidth={Math.max(0.5, edge.weight * 1.1)}
            />
          );
        })}
      </svg>
      {nodes.map((agent, i) => {
        const point = position(agent.id),
          label = agent.label || `A${String(i + 1).padStart(2, "0")}`,
          size = 8 + (agent.resource || 0) / 18;
        return (
          <button
            key={agent.id}
            className={`node ${differences.includes(agent.id) ? "different" : ""} ${agent.action === "compete" ? "competing" : ""} ${selected === agent.id ? "selected" : ""} ${highlight && indexOf(agent.id) === interventionAgent ? "intervened" : ""}`}
            style={{
              left: `${point.x}%`,
              top: `${point.y}%`,
              width: size,
              height: size,
              border: agent.informed ? "2px solid #72b5d0" : undefined,
            }}
            onClick={() => setSelected(agent.id)}
            aria-label={`${label}, ${agent.role}, ${agent.action}, resource ${Number(agent.resource || 0).toFixed(1)}`}
            title={`${label} / ${agent.role} / ${agent.action}`}
          >
            <span>{label.replace("A", "")}</span>
          </button>
        );
      })}
      {selectedAgent && (
        <div className="agent-pop" role="status">
          <strong>{selectedAgent.label || selected}</strong>
          {detailError&&<span>{detailError}</span>}
          <span>
            {selectedAgent.role} / {selectedAgent.action}
          </span>
          <span>
            resource {Number(selectedAgent.resource || 0).toFixed(1)} / opinion{" "}
            {Number(selectedAgent.opinion || 0).toFixed(2)}
          </span>
          <span>
            information {selectedAgent.informed ? "informed" : "unaware"} /
            history {Number(selectedAgent.history ?? 0).toFixed(2)}
          </span>
          <span>
            ties{" "}
            {
              edges.filter(
                (e) => e.source === selected || e.target === selected,
              ).length
            }{" "}
            / mean trust{" "}
            {(
              edges
                .filter((e) => e.source === selected || e.target === selected)
                .reduce((s, e) => s + e.weight, 0) /
              Math.max(
                1,
                edges.filter(
                  (e) => e.source === selected || e.target === selected,
                ).length,
              )
            ).toFixed(2)}
          </span>
          {selectedAgent.memory?.slice(-2).map((m) => (
            <span key={m.round}>
              R{m.round}: {m.action} / resource Δ {m.resource_change.toFixed(2)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
