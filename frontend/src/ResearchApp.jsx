import React, { useEffect, useRef, useState } from "react";
import WorldStudio from "./WorldStudio.jsx";
import ExplorationLab from "./ExplorationLab.jsx";
import LLMSociety from "./LLMSociety.jsx";
import ResearchStudies, { EffectDistribution } from "./ResearchStudies.jsx";
import {
  Activity,
  Play,
  Pause,
  SkipBack,
  Search,
  Download,
  Save,
  Trash2,
  RotateCw,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";

import { API } from './api';
const baseMetrics = {
  cooperation: "Cooperation Rate",
  inequality: "Resource Gini",
  disagreement: "Opinion Disagreement",
  largest_component: "Largest Component Ratio",
};
const number = (v) => (v == null ? "n/a" : Number(v).toFixed(4));
async function request(path, options = {}) {
  const response = await fetch(API + path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail),
    );
  return data;
}
const post = (body) => ({ method: "POST", body: JSON.stringify(body) });

export default function ResearchApp({ Network }) {
  const [world, setWorld] = useState(null),
    [record, setRecord] = useState(null),
    [history, setHistory] = useState([]);
  const [name, setName] = useState("50 Agent resource experiment"),
    [kind, setKind] = useState("resource"),
    [magnitude, setMagnitude] = useState(-10);
  const [agent, setAgent] = useState(0),
    [count, setCount] = useState(5),
    [start, setStart] = useState(42),
    [budget, setBudget] = useState(8);
  const [metric, setMetric] = useState("cooperation"),
    [direction, setDirection] = useState("decrease");
  const [seedIndex, setSeedIndex] = useState(0),
    [round, setRound] = useState(0),
    [playing, setPlaying] = useState(false);
  const [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false);
  const [ready, setReady] = useState(false);
  const active = useRef(null);
  const [chunks,setChunks]=useState(null),[archiveState,setArchiveState]=useState("");
  const metrics = {
    ...baseMetrics,
    ...(record?.world_config?.engine || world?.config?.engine
      ? {
          coverage: "Information Coverage",
          mean_trust: "Mean Trust",
          resource_mean: "Mean Resources",
        }
      : {}),
  };
  const refresh = async () =>
    setHistory((await request("/experiments")).experiments);
  const adopt = (data) => {
    active.current = data.experiment_id;
    localStorage.setItem("butterflylab.experiment", data.experiment_id);
    setRecord(data);
    setName(data.experiment_name);
    setSeedIndex(0);
    setRound(0);
    setPlaying(false);
    setNotice("");
    const c = data.configuration;
    const initial =
      data.result?.validation?.baseline?.[0]?.initial ||
      data.result?.baseline?.[0]?.initial;
    setWorld((w) => initial || (w ? { ...w, config: c.world } : w));
    if (!c.world.engine && !Object.hasOwn(baseMetrics, metric))
      setMetric("cooperation");
    setCount(c.seeds.length);
    setStart(c.seeds[0]);
    if (c.intervention) {
      setKind(c.intervention.kind);
      setMagnitude(c.intervention.magnitude);
      setAgent(c.intervention.agent);
    }
    if (data.kind === "search") {
      setMetric(c.metric);
      setDirection(c.direction);
      setBudget(c.max_experiments);
    }
  };
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const w = await request("/world");
        if (alive) setWorld(w);
        await refresh();
        const id = localStorage.getItem("butterflylab.experiment");
        if (id) {
          try {
            const r = await request("/experiments/" + id + "/summary");
            if (alive) adopt(r);
          } catch {
            localStorage.removeItem("butterflylab.experiment");
          }
        }
      } catch (e) {
        if (alive) setError(e.message);
      } finally {
        if (alive) setReady(true);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);
  useEffect(() => {
    if (record?.experiment_status !== "running") return;
    let cancelled = false;
    const timer = setInterval(async () => {
      try {
        const data = await request("/experiments/" + record.experiment_id + "/summary");
        if (!cancelled && active.current === data.experiment_id) {
          setRecord(data);
          if (data.experiment_status !== "running") {
            await refresh();
            if (data.error) setError(data.error);
          }
        }
      } catch (e) {
        if (!cancelled) setError(e.message);
      }
    }, 700);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [record?.experiment_id, record?.experiment_status]);
  const search = record?.kind === "search" ? record.result : null;
  const result = search?.validation || record?.result;
  const rawA = result?.baseline?.[seedIndex],rawB=result?.variant?.[seedIndex];
  const blockStart=Math.floor(round/10)*10;
  const chunkKey=record?.experiment_id+":"+rawA?.seed+":"+blockStart;
  const a=rawA ? {...rawA,...(chunks?.key===chunkKey?chunks.a:{})}:null;
  const b=rawB ? {...rawB,...(chunks?.key===chunkKey?chunks.b:{})}:null;
  const rounds = (rawA?.series?.length || 1) - 1;
  useEffect(()=>{
    if(!rawA?.trajectory_available)return;
    const controller=new AbortController();setChunks(null);
    Promise.all(['baseline','variant'].map(branch=>request(`/experiments/${record.experiment_id}/trajectory?seed=${rawA.seed}&branch=${branch}&start=${blockStart}&end=${Math.min(rounds,blockStart+9)}&view=network`,{signal:controller.signal})))
      .then(([a,b])=>setChunks({key:chunkKey,a,b})).catch(e=>{if(e.name!=='AbortError')setError(e.message)});
    return ()=>controller.abort();
  },[chunkKey,rawA?.trajectory_available]);
  useEffect(() => {
    if (!playing) return;
    const timer = setInterval(
      () =>
        setRound((r) => {
          if (r >= rounds) {
            setPlaying(false);
            return rounds;
          }
          return r + 1;
        }),
      150,
    );
    return () => clearInterval(timer);
  }, [playing, rounds]);
  const locked = busy || !ready || record?.experiment_status === "running";
  const perform = async (task) => {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await task();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };
  const run = (mode) =>
    perform(async () => {
      const seeds = Array.from(
        { length: Number(count) },
        (_, i) => Number(start) + i,
      );
      const body = {
        experiment_name: name,
        world: world.config,
        seeds,
        intervention:
          mode === "baseline"
            ? null
            : { kind, agent: Number(agent), magnitude: Number(magnitude) },
      };
      if (mode === "search")
        Object.assign(body, {
          intervention: null,
          metric,
          direction,
          max_experiments: Number(budget),
          evaluation_seeds: seeds.map((s) => s + 10000),
        });
      adopt(
        await request(
          mode === "search" ? "/search/jobs?light=true" : "/experiments?light=true",
          post(body),
        ),
      );
      await refresh();
    });
  const open = (id) =>
    perform(async () => adopt(await request("/experiments/" + id + "/summary")));
  const save = () =>
    perform(async () => {
      setRecord(
        await request("/experiments/" + record.experiment_id + "?light=true", {
          method: "PATCH",
          body: JSON.stringify({ experiment_name: name }),
        }),
      );
      await refresh();
      setNotice("Saved to SQLite");
    });
  const remove = (id) =>
    perform(async () => {
      await request("/experiments/" + id, { method: "DELETE" });
      if (active.current === id) {
        active.current = null;
        setRecord(null);
        localStorage.removeItem("butterflylab.experiment");
      }
      await refresh();
    });
  const reproduce = () =>
    perform(async () => {
      const r = await request(
        "/experiments/" + record.experiment_id + "/reproduce",
        post({}),
      );
      setNotice(
        r.identical
          ? "Exact reproduction verified: all trajectories, logs and metrics match."
          : "Reproduction mismatch",
      );
    });
  const intervention = result?.configuration?.intervention;
  const archive=()=>perform(async()=>{
    setArchiveState("Preparing archive");
    const job=await request(`/experiments/${record.experiment_id}/archive`,post({}));
    for(;;){
      const state=await request('/jobs/'+job.job_id);setArchiveState(state.state);
      if(state.state==='COMPLETED'){window.location.assign(API.replace('/api','')+job.download_url);break;}
      if(['FAILED','CANCELLED'].includes(state.state))throw new Error(state.error||state.state);
      await new Promise(resolve=>setTimeout(resolve,500));
    }
  });
  const frame = (run) =>
    run?.snapshots?.find(s=>s.round===round)
      ? {
          ...run.snapshots.find(s=>s.round===round),
          config: run.initial?.config || world?.config,
        }
      : (run?.trajectory_available ? null : world);
  const series = (a?.series || []).map((row, i) => ({
    ...row,
    ...Object.fromEntries(
      Object.keys(metrics).map((m) => [m + "_b", b.series[i][m]]),
    ),
  }));
  return (
    <div className="app research">
      <aside>
        <div className="brand">
          <Activity size={28} />
          <div>
            <b>ButterflyLab</b>
            <small>RESEARCH CONSOLE / 2D</small>
          </div>
        </div>
        <nav>
          {[
            ["studio", "World Studio"],
            ["worlds", "Parallel worlds"],
            ["observatory", "Observatory"],
            ["search", "Intervention search"],
            ["studies", "Research studies"],
            ["sensitivity", "Sensitivity Lab"],
            ["criticality", "Criticality Explorer"],
            ["llm-society", "LLM Society"],
            ["experiments", "Experiments"],
          ].map(([id, label]) => (
            <a key={id} href={"#" + id}>
              {label}
            </a>
          ))}
        </nav>
        <div className="aside-bottom">
          {world?.config?.engine || "RULE ENGINE 0.2.0"}
          <small>seeded / local SQLite</small>
        </div>
      </aside>
      <main>
        <header>
          <div>
            <h1>ButterflyLab</h1>
          </div>
          <div className="actions">
            <button
              className="export"
              disabled={!result || locked}
              onClick={reproduce}
            >
              <RotateCw size={15} /> Reproduce
            </button>
            <a
              className={"export " + (!result ? "disabled" : "")}
              href={
                record
                  ? `${API}/experiments/${record.experiment_id}/light-export`
                  : undefined
              }
              download
            >
              <Download size={15} /> Summary JSON
            </a>
            <button className="export" disabled={!result||locked} onClick={archive}><Download size={15}/> Full archive</button>
            {archiveState&&<span role="status">{archiveState}</span>}
          </div>
        </header>
        {error && (
          <div className="error-banner" role="alert">
            {error}
          </div>
        )}
        {notice && (
          <p className="notice" role="status">
            {notice}
          </p>
        )}
        <WorldStudio
          Network={Network}
          request={request}
          post={post}
          locked={locked}
          activeConfig={world?.config}
          onDemo={(config) => perform(async () => {
            setWorld(await request('/world/preview', post(config)));
            setKind('information');
            setMagnitude(1);
            setMetric('coverage');
            adopt(await request('/experiments?light=true', post({
              experiment_name: '50 Agent Information Cascade / free demo',
              world: config, seeds: [42,43,44,45,46], intervention: null,
            })));
            await refresh();
          })}
          onCreate={(w) => {
            setWorld(w);
            setRecord(null);
            active.current = null;
            localStorage.removeItem("butterflylab.experiment");
            setStart(w.seed);
            setCount(30);
            setRound(0);
            setNotice(
              "World created: " +
                w.agents.length +
                " Agents / " +
                w.config.engine,
            );
          }}
        />
        <section
          className="toolbar"
          aria-label="Experiment controls"
          inert={!ready}
        >
          <div className="field name-field">
            <label htmlFor="name">EXPERIMENT NAME</label>
            <input
              id="name"
              value={name}
              maxLength={120}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="kind">INTERVENTION</label>
            <select
              id="kind"
              value={kind}
              onChange={(e) => {
                setKind(e.target.value);
                setMagnitude(e.target.value === "resource" ? -10 : -0.15);
              }}
            >
              <option value="resource">Resource</option>
              <option value="opinion">Opinion</option>
              {world?.config?.engine && (
                <>
                  <option value="information">Information state</option>
                </>
              )}
            </select>
          </div>
          <div className="field">
            <label htmlFor="agent">
              AGENT INDEX / 0-{(world?.config?.population || 50) - 1}
            </label>
            <input
              id="agent"
              type="number"
              min="0"
              max={(world?.config?.population || 50) - 1}
              value={agent}
              onChange={(e) => setAgent(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="magnitude">
              DELTA / {kind === "resource" ? "UNITS" : "[0,1] SCALE"}
            </label>
            <input
              id="magnitude"
              type="number"
              min={kind === "resource" ? -50 : -1}
              max={kind === "resource" ? 50 : 1}
              step={kind === "resource" ? 1 : 0.05}
              value={magnitude}
              onChange={(e) => setMagnitude(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="count">PAIRED SEEDS / 1-100</label>
            <input
              id="count"
              type="number"
              min="1"
              max="100"
              value={count}
              onChange={(e) => setCount(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="start">FIRST SEED</label>
            <input
              id="start"
              type="number"
              min="0"
              max="2147473640"
              value={start}
              onChange={(e) => setStart(e.target.value)}
            />
          </div>
          <button
            className="search-btn"
            disabled={locked || !world}
            onClick={() => run("baseline")}
          >
            <Play size={15} /> Run baseline
          </button>
          <button
            className="run"
            disabled={locked || !world}
            onClick={() => run("comparison")}
          >
            <Play size={15} /> Run A/B experiment
          </button>
        </section>
        <div className="run-status">
          <span>
            {record
              ? `${record.experiment_status} / ${record.experiment_id}`
              : "50 Agents / 50 rounds"}
          </span>
          {record && (
            <button className="export" disabled={locked} onClick={save}>
              <Save size={14} /> Save experiment
            </button>
          )}
        </div>
        {record?.experiment_status === "running" && (
          <div role="status" className="progress">
            <progress
              value={record.progress_completed}
              max={record.progress_total || 1}
            />
            <span>
              {record.progress_completed} / {record.progress_total || "?"}{" "}
              {record.kind === "search" ? "simulations" : "paired seeds"}
            </span>
            <button className="export" onClick={()=>perform(()=>request(`/experiments/${record.experiment_id}/cancel`,post({})))}>Cancel task</button>
          </div>
        )}
        <section id="worlds" className="world-grid">
          {[
            [a, "A / BASELINE", "Natural evolution"],
            [
              b,
              "B / INTERVENTION",
              intervention
                ? `${intervention.kind} ${intervention.magnitude} / A${String(intervention.agent + 1).padStart(2, "0")}`
                : "No intervention",
            ],
          ].map(([run, label, title], i) => (
            <div className="panel world-panel" key={label}>
              <div className="panel-head">
                <div>
                  <span className={"tag " + (i ? "variant" : "baseline")}>
                    {label}
                  </span>
                  <h2>{title}</h2>
                </div>
                <span className="seed">seed {run?.seed ?? 42}</span>
              </div>
              <Network
                world={frame(run)}
                detailKey={`${record?.experiment_id}:${run?.seed}:${round}`}
                loadAgent={run?.trajectory_available ? async id=>(await request(`/experiments/${record.experiment_id}/trajectory?seed=${run.seed}&branch=${i?'variant':'baseline'}&start=${round}&end=${round}&agent=${encodeURIComponent(id)}`)).snapshots[0]?.agents[0] : undefined}
                transmissions={(run?.transmission_paths || []).filter(
                  (p) => p.round === round,
                )}
                highlight={!!i && !!intervention}
                interventionAgent={intervention?.agent ?? 0}
              />
              <div className="network-foot">
                <span>
                  <i className="legend-dot mint" />
                  cooperate
                </span>
                <span>
                  <i className="legend-dot coral" />
                  compete
                </span>
                {world?.config?.engine && (
                  <span>Blue: informed node / transmission this round</span>
                )}
                <span className="count">
                  {frame(run)?.agents?.length || 0} agents /{" "}
                  {frame(run)?.edges?.length || 0} ties
                </span>
              </div>
            </div>
          ))}
        </section>
        <section className="timeline">
          <div className="timeline-top">
            <h2>Evolution timeline</h2>
            <div className="controls">
              <select
                aria-label="Displayed seed"
                value={seedIndex}
                onChange={(e) => {
                  setSeedIndex(Number(e.target.value));
                  setRound(0);
                  setPlaying(false);
                }}
              >
                {(result?.seeds || [42]).map((s, i) => (
                  <option key={s} value={i}>
                    Seed {s}
                  </option>
                ))}
              </select>
              <button
                disabled={!a}
                onClick={() => {
                  setRound(0);
                  setPlaying(false);
                }}
                title="Rewind"
                aria-label="Rewind"
              >
                <SkipBack size={15} />
              </button>
              <button
                disabled={!a}
                onClick={() => setPlaying(!playing)}
                title="Play or pause"
                aria-label="Play or pause"
              >
                {playing ? <Pause size={15} /> : <Play size={15} />}
              </button>
              <span>
                round {round} / {rounds}
              </span>
            </div>
          </div>
          <input
            aria-label="Timeline round"
            type="range"
            min="0"
            max={rounds}
            value={round}
            onChange={(e) => {
              setRound(Number(e.target.value));
              setPlaying(false);
            }}
          />
        </section>
        <section id="observatory">
          <div className="section-heading">
            <h2>Emergence Observatory</h2>
            <span className="seed">
              A baseline / B intervention / ratios and resource units
            </span>
          </div>
          <div className="metric-grid">
            {Object.entries(metrics).map(([m, title]) => (
              <article className="metric-chart" key={m}>
                <div className="panel-head">
                  <h2>{title}</h2>
                  <span className="seed">
                    final B {number(b?.final[m])} / delta{" "}
                    {number(result?.paired[seedIndex].delta[m])}
                  </span>
                </div>
                {a ? (
                  <>
                    <div className="plot">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart
                          data={series}
                          margin={{ top: 8, right: 18, left: 0, bottom: 15 }}
                        >
                          <CartesianGrid
                            stroke="#304043"
                            strokeDasharray="3 3"
                          />
                          <XAxis
                            dataKey="round"
                            stroke="#a8b4ae"
                            tick={{ fontSize: 11, fill: "#c0cac4" }}
                            ticks={Array.from({ length: 6 }, (_, i) =>
                              Math.round((i * rounds) / 5),
                            )}
                            interval="preserveStartEnd"
                            label={{
                              value: "Round",
                              position: "insideBottom",
                              offset: -10,
                              fill: "#c0cac4",
                            }}
                          />
                          <YAxis
                            domain={
                              m === "resource_mean"
                                ? [
                                    0,
                                    Math.max(
                                      1,
                                      ...series.flatMap((v) => [
                                        v.resource_mean,
                                        v.resource_mean_b,
                                      ]),
                                    ),
                                  ]
                                : [0, 1]
                            }
                            ticks={
                              m === "resource_mean"
                                ? undefined
                                : [0, 0.25, 0.5, 0.75, 1]
                            }
                            width={40}
                            tickFormatter={(v) => Number(v.toPrecision(3)).toString()}
                            stroke="#a8b4ae"
                            tick={{ fontSize: 11, fill: "#c0cac4" }}
                          />
                          <Tooltip
                            contentStyle={{
                              background: "#151d1f",
                              border: "1px solid #566466",
                            }}
                            formatter={(v) => number(v)}
                          />
                          <Legend verticalAlign="top" />
                          <ReferenceLine x={round} stroke="#82949c" />
                          <Line
                            dataKey={m}
                            name="A baseline"
                            stroke="#a9ddc6"
                            dot={false}
                            strokeWidth={3}
                            strokeDasharray="6 4"
                            isAnimationActive={false}
                          />
                          <Line
                            dataKey={m + "_b"}
                            name="B intervention"
                            stroke="#d8a866"
                            dot={false}
                            strokeWidth={1.5}
                            isAnimationActive={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                    <p className="stats">
                      {m === "resource_mean" ? "Resource units / agent · " : ""}
                      R{round}: A {number(a.series[round][m])} / B{" "}
                      {number(b.series[round][m])}
                      <br />
                      Final A {number(a.final[m])} / B {number(b.final[m])}
                      <br />
                      Mean paired delta {number(result.summary[m]?.mean)} /
                      sample SD {number(result.summary[m]?.std)}
                      <br />
                      Bootstrap 95% interval{" "}
                      {result.summary[m]?.ci95?.map(number).join(" to ") ||
                        "unavailable (one seed)"}
                    </p>
                  </>
                ) : (
                  <div className="chart-empty">No completed experiment</div>
                )}
                <details>
                  <summary>Definition & boundaries</summary>
                  <p>{result?.metric_definitions[m]?.formula}</p>
                  <p>{world?.config?.engine && m === "largest_component"
                    ? "Undirected actual relationships with positive trust, including isolates. Ties can be pruned below the configured threshold; connectivity can change."
                    : result?.metric_definitions[m]?.note}</p>
                  <p>Range {world?.config?.engine && m === "resource_mean"
                    ? "Nonnegative resource units per agent; bounded by available system resources including explicit interventions."
                    : result?.metric_definitions[m]?.range}</p>
                </details>
              </article>
            ))}
          </div>
          {result && (
            <>
              <div className="section-heading">
                <h2>Paired seed effects</h2>
                <select
                  aria-label="Paired metric"
                  value={metric}
                  onChange={(e) => setMetric(e.target.value)}
                >
                  {Object.entries(metrics).map(([m, t]) => (
                    <option value={m} key={m}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Seed</th>
                      <th>A final</th>
                      <th>B final</th>
                      <th>B - A</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.paired.map((p) => (
                      <tr key={p.seed}>
                        <td>{p.seed}</td>
                        <td>{number(p.baseline[metric])}</td>
                        <td>{number(p.intervention[metric])}</td>
                        <td>{number(p.delta[metric])}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="limitations">
                {result.seeds.length} paired seeds. Intervals summarize this
                seed sample; small samples do not establish statistical
                significance. Synthetic rule simulation, not a real-world causal
                estimate.
              </p>
              <EffectDistribution result={result} metric={metric} />
            </>
          )}
        </section>
        <section id="search">
          <div className="section-heading">
            <h2>Intervention explorer</h2>
            <span className="seed">
              resource candidates / held-out validation
            </span>
          </div>
          <div className="toolbar">
            <div className="field">
              <label htmlFor="target">TARGET METRIC</label>
              <select
                id="target"
                value={metric}
                onChange={(e) => setMetric(e.target.value)}
              >
                {Object.entries(metrics).map(([m, t]) => (
                  <option value={m} key={m}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="direction">DIRECTION</label>
              <select
                id="direction"
                value={direction}
                onChange={(e) => setDirection(e.target.value)}
              >
                <option value="decrease">Decrease</option>
                <option value="increase">Increase</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="budget">CANDIDATE BUDGET / 1-24</label>
              <input
                id="budget"
                type="number"
                min="1"
                max="24"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
              />
            </div>
            <button
              className="run"
              disabled={locked || !world || Number(count) < 2}
              onClick={() => run("search")}
            >
              <Search size={15} /> Search interventions
            </button>
          </div>
          <p className="limitations">
            Budget: {(Number(budget) + 1) * Number(count) + 2 * Number(count)}{" "}
            simulations. Discovery seeds start at {start}; validation seeds
            start at {Number(start) + 10000}. At least two seeds required for
            search.
          </p>
          {search && (
            <>
              <p className="notice">
                Held-out mean delta ({metrics[search.metric]}):{" "}
                {number(search.validation.summary[search.metric].mean)} / SD{" "}
                {number(search.validation.summary[search.metric].std)}
              </p>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Rank</th>
                      <th>Agent / resource delta</th>
                      <th>Cost</th>
                      <th>Discovery mean delta</th>
                      <th>Sample SD</th>
                      <th>Bootstrap 95% interval</th>
                    </tr>
                  </thead>
                  <tbody>
                    {search.results.map((c, i) => (
                      <tr key={i}>
                        <td>{i + 1}</td>
                        <td>
                          {c.agent} / {c.resource_delta}
                        </td>
                        <td>{c.cost}</td>
                        <td>{number(c.mean_delta)}</td>
                        <td>{number(c.uncertainty.std)}</td>
                        <td>{c.uncertainty.ci95.map(number).join(" to ")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="limitations">
                {search.selection_note} Observatory displays held-out
                validation, not discovery trajectories.
              </p>
            </>
          )}
        </section>
        <ResearchStudies
          request={request}
          post={post}
          world={world?.config}
          seeds={Array.from(
            { length: Number(count) },
            (_, i) => Number(start) + i,
          )}
          metric={metric}
          locked={locked}
        />
        <ExplorationLab request={request} post={post} world={world?.config} openExperiment={open}/>
        {a && (
          <section className="events">
            <div className="section-heading">
              <h2>Observed events / through round {round}</h2>
              <span className="seed">seed {a.seed}</span>
            </div>
            {(b.events || [])
              .filter((e) => e.round <= round)
              .slice(-5)
              .reverse()
              .map((e, i) => (
                <div className="event" key={i}>
                  <b>R{e.round}</b>
                  <span>{e.type}</span>
                  <p>{e.detail}</p>
                </div>
              ))}
          </section>
        )}
        <LLMSociety request={request} post={post} Network={Network} onOpen={open} onSaved={refresh}/>
        <section id="experiments">
          <div className="section-heading">
            <h2>Saved experiments</h2>
            <button
              className="export"
              onClick={() => perform(refresh)}
              title="Refresh list"
            >
              <RotateCw size={15} />
            </button>
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Name / ID</th>
                  <th>Created</th>
                  <th>Seeds</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {history.map((r) => (
                  <tr key={r.experiment_id}>
                    <td>
                      <button
                        className="text-button"
                        onClick={() => open(r.experiment_id)}
                      >
                        {r.experiment_name}
                      </button>
                      <small>{r.experiment_id}</small>
                    </td>
                    <td>{new Date(r.created_at).toLocaleString()}</td>
                    <td>{r.random_seeds.join(", ")}</td>
                    <td>
                      {r.experiment_status} / {r.kind}
                    </td>
                    <td>
                      <button
                        className="icon-button"
                        disabled={!ready || r.experiment_status === "running" || busy}
                        title="Delete experiment"
                        aria-label={"Delete " + r.experiment_name}
                        onClick={() => remove(r.experiment_id)}
                      >
                        <Trash2 size={15} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!history.length && (
              <p className="chart-empty">No saved experiments</p>
            )}
          </div>
        </section>
        <p className="limitations">
          Engine {result?.engine_version || "0.2.0"} / local SQLite /
          addressable random streams / all generated experiments persist
          automatically.
        </p>
      </main>
    </div>
  );
}
