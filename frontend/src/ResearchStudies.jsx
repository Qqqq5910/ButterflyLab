import React, { useState, useEffect } from "react";
import { Play, Download, Square } from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from "recharts";

export function EffectDistribution({ result, metric }) {
  const values =
    result?.paired?.map((p) => ({ seed: p.seed, delta: p.delta[metric] })) ||
    [];
  const bound = Math.max(0.01, ...values.map((p) => Math.abs(p.delta)));
  return (
    <div className="effect-plot">
      <h3>Paired effect distribution / B − A</h3>
      <div className="plot">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={values}
            margin={{ top: 10, right: 15, bottom: 20, left: 10 }}
          >
            <CartesianGrid stroke="#304043" strokeDasharray="3 3" />
            <XAxis
              dataKey="seed"
              stroke="#c0cac4"
              label={{
                value: "Seed",
                position: "insideBottom",
                offset: -12,
                fill: "#c0cac4",
              }}
            />
            <YAxis
              domain={[-bound, bound]}
              stroke="#c0cac4"
              tickFormatter={(v) => v.toPrecision(2)}
            />
            <Tooltip
              contentStyle={{
                background: "#151d1f",
                border: "1px solid #566466",
              }}
            />
            <ReferenceLine y={0} stroke="#c0cac4" />
            <Bar dataKey="delta" fill="#a9ddc6" isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="limitations">
        Symmetric axis around zero. One bar per paired seed; axis extent
        includes every observed effect.
      </p>
    </div>
  );
}

export default function ResearchStudies({
  request,
  post,
  world,
  seeds,
  metric,
  locked,
}) {
  const [kind, setKind] = useState("ablation"),
    [mechanism, setMechanism] = useState("trust_enabled"),
    [parameter, setParameter] = useState("trust_speed"),
    [second, setSecond] = useState("incentive"),
    [values, setValues] = useState("0,0.03,0.1"),
    [secondValues, setSecondValues] = useState("0,0.3,0.6"),
    [record, setRecord] = useState(null),
    [history, setHistory] = useState([]),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [cellIndex, setCellIndex] = useState(0);
  const refresh = async () =>
    setHistory(
      (await request("/worlds")).worlds.filter(
        (w) => w.configuration.study_request,
      ),
    );
  useEffect(() => {
    refresh().catch((e) => setError(e.message));
    const id = localStorage.getItem("butterflylab.study");
    if (id)
      request("/worlds/" + id)
        .then(setRecord)
        .catch((e) => setError(e.message));
  }, []);
  const result = record?.configuration.result;
  const active=record?.task&&['QUEUED','RUNNING','CANCEL_REQUESTED'].includes(record.task.state);
  useEffect(()=>{if(!active)return;const timer=setInterval(()=>request('/worlds/'+record.world_id).then(r=>{setRecord(r);if(!['QUEUED','RUNNING','CANCEL_REQUESTED'].includes(r.task?.state))refresh();}).catch(e=>setError(e.message)),1000);return()=>clearInterval(timer)},[record?.world_id,active]);
  useEffect(() => setCellIndex(0), [record?.world_id]);
  const run = async () => {
    setBusy(true);
    setError("");
    try {
      const r = await request(
        "/studies/jobs",
        post({
          experiment_name: "Social " + kind,
          world,
          seeds,
          kind,
          mechanism,
          parameter,
          second_parameter: second,
          values: values.split(",").map(Number),
          second_values: secondValues.split(",").map(Number),
        }),
      );
      setRecord(r);
      localStorage.setItem("butterflylab.study", r.world_id);
      await refresh();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };
  const extent = Math.max(
    0.000001,
    ...(result?.cells || []).map((c) => Math.abs(c.summary[metric]?.mean || 0)),
  );
  const exportRecord = () => {
    const u = URL.createObjectURL(
      new Blob([JSON.stringify(record, null, 2)], { type: "application/json" }),
    );
    const a = document.createElement("a");
    a.href = u;
    a.download = "butterflylab-study.json";
    a.click();
    URL.revokeObjectURL(u);
  };
  return (
    <section id="studies">
      <div className="section-heading">
        <h2>Research studies</h2>
        <span className="seed">Paired ablation / full parameter grid</span>
      </div>
      {error && (
        <p className="error-banner" role="alert">
          {error}
        </p>
      )}
      <div className="toolbar">
        <div className="field">
          <label htmlFor="study-kind">Study type</label>
          <select
            id="study-kind"
            value={kind}
            onChange={(e) => setKind(e.target.value)}
          >
            <option value="ablation">Mechanism ablation</option>
            <option value="sensitivity">Sensitivity grid</option>
          </select>
        </div>
        {kind === "ablation" ? (
          <div className="field">
            <label htmlFor="mechanism">Mechanism</label>
            <select
              id="mechanism"
              value={mechanism}
              onChange={(e) => setMechanism(e.target.value)}
            >
              {[
                "trust_enabled",
                "cooperation_enabled",
                "diffusion_enabled",
                "relationships_enabled",
              ].map((v) => (
                <option key={v} value={v}>
                  {v.replaceAll("_", " ")}
                </option>
              ))}
            </select>
          </div>
        ) : (
          <>
            {[
              [parameter, setParameter, values, setValues, "X"],
              [second, setSecond, secondValues, setSecondValues, "Y"],
            ].map(([p, sp, v, sv, label]) => (
              <React.Fragment key={label}>
                <div className="field">
                  <label htmlFor={"parameter-" + label}>
                    {label} parameter
                  </label>
                  <select
                    id={"parameter-" + label}
                    value={p}
                    onChange={(e) => sp(e.target.value)}
                  >
                    {[
                      "trust_speed",
                      "incentive",
                      "transmission",
                      "exchange",
                      "opinion_speed",
                      "resource_scale",
                    ].map((k) => (
                      <option key={k} value={k}>
                        {k}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label htmlFor={"values-" + label}>
                    {label} values / comma separated
                  </label>
                  <input
                    id={"values-" + label}
                    value={v}
                    onChange={(e) => sv(e.target.value)}
                  />
                </div>
              </React.Fragment>
            ))}
          </>
        )}
        <button
          className="run"
          disabled={locked || busy || active || !world?.engine}
          onClick={run}
        >
          <Play size={14} />
          {busy ? "Running study…" : "Run research study"}
        </button>
      </div>
      {record?.task&&<div className="run-status"><span>{record.task.state} / {record.task.completed} of {record.task.total} pairs</span>{active&&<button className="export" onClick={()=>request('/experiments/'+record.world_id+'/cancel',post({})).catch(e=>setError(e.message))}><Square size={14}/>Cancel study</button>}</div>}
      <p className="limitations">
        Next run: {seeds.length} paired seeds. Formal evaluations should generally begin
        with at least 30 seeds and plan precision from observed variance. Every
        requested cell is saved.
      </p>
      <div className="field">
        <label htmlFor="saved-study">Saved study</label>
        <select
          id="saved-study"
          value={record?.world_id || ""}
          onChange={(e) => {
            const r = history.find((r) => r.world_id === e.target.value);
            setRecord(r || null);
            if (r) localStorage.setItem("butterflylab.study", r.world_id);
          }}
        >
          <option value="">Select study</option>
          {history.map((r) => (
            <option key={r.world_id} value={r.world_id}>
              {r.name} / {r.world_id.slice(0, 8)}
            </option>
          ))}
        </select>
      </div>
      {result && (
        <>
          <div className="section-heading">
            <h3>
              {result.kind === "ablation"
                ? "Mechanism on → off"
                : "Parameter sensitivity / mean paired effect"}
            </h3>
            <button className="export" onClick={exportRecord}>
              <Download size={14} />
              Export study JSON
            </button>
          </div>
          <p className="limitations">
            Saved result: {result.seeds.length} paired seeds / {result.seeds.join(", ")}. Metric: {metric}.
          </p>
          {result.kind === "sensitivity" && (
            <div className="table-scroll">
              <table className="heatmap">
                <thead>
                  <tr>
                    <th>
                      {result.configuration.second_parameter} ↓ /{" "}
                      {result.configuration.parameter} →
                    </th>
                    {result.configuration.values.map((x) => (
                      <th key={x}>{x}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.configuration.second_values.map((y) => (
                    <tr key={y}>
                      <th>{y}</th>
                      {result.configuration.values.map((x) => {
                        const cell = result.cells.find(
                          (c) => c.x === x && c.y === y,
                        );
                        const v = cell.summary[metric].mean;
                        return (
                          <td
                            key={x}
                            style={{
                              background: `rgba(${v >= 0 ? "169,221,198" : "222,136,119"},${0.1 + (0.55 * Math.abs(v)) / extent})`,
                            }}
                            title={"SD " + cell.summary[metric].std}
                          >
                            {v.toPrecision(4)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>X / Y</th>
                  <th>Metric</th>
                  <th>Mean B−A</th>
                  <th>Sample SD</th>
                  <th>95% bootstrap interval</th>
                </tr>
              </thead>
              <tbody>
                {result.cells.map((c, i) => (
                  <tr key={i}>
                    <td>
                      {String(c.x)} / {String(c.y)}
                    </td>
                    <td>{metric}</td>
                    <td>{c.summary[metric].mean.toPrecision(5)}</td>
                    <td>{c.summary[metric].std?.toPrecision(5) || "n/a"}</td>
                    <td>
                      {c.summary[metric].ci95
                        ?.map((v) => v.toPrecision(5))
                        .join(" to ") || "n/a"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="field">
            <label htmlFor="effect-cell">Effect distribution cell</label>
            <select id="effect-cell" value={cellIndex} onChange={(e) => setCellIndex(Number(e.target.value))}>
              {result.cells.map((c, i) => (
                <option key={i} value={i}>
                  {result.kind === "ablation"
                    ? `${result.configuration.mechanism}: on to off`
                    : `${result.configuration.parameter}=${c.x} / ${result.configuration.second_parameter}=${c.y}`}
                </option>
              ))}
            </select>
          </div>
          <p className="limitations" data-testid="selected-study-cell">
            {result.kind === "ablation"
              ? `${result.configuration.mechanism}: on to off`
              : `${result.configuration.parameter} = ${(result.cells[cellIndex] || result.cells[0]).x}; ${result.configuration.second_parameter} = ${(result.cells[cellIndex] || result.cells[0]).y}`}
            {" · "}{metric}
          </p>
          <EffectDistribution result={result.cells[cellIndex] || result.cells[0]} metric={metric} />
          <p className="limitations">
            {result.note} Heatmap color uses a symmetric zero-centered scale ±
            {extent.toPrecision(4)}. Displayed metric follows the observatory
            metric selector.
          </p>
        </>
      )}
    </section>
  );
}
