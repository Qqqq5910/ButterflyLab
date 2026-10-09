import React, { useEffect, useState } from "react";
import { Save, RotateCcw, GitBranch, Play, Eye } from "lucide-react";

const defaults = {
  schema_version: 3,
  engine: "social-1.0.0",
  population: 50,
  rounds: 50,
  network: "small_world",
  initial_seed: 42,
  neighbor_count: 4,
  rewiring: 0.15,
  edge_probability: 0.1,
  attachment: 2,
  resource_distribution: "uniform",
  resource_scale: 60,
  opinion_distribution: "uniform",
  cooperation_distribution: "uniform",
  cooperation_mean: 0.55,
  heterogeneity: 0.6,
  initial_trust: 0.6,
  transmission: 0.18,
  cooperation_threshold: 0.5,
  trust_enabled: true,
  cooperation_enabled: true,
  diffusion_enabled: true,
  relationships_enabled: true,
  trust_speed: 0.03,
  incentive: 0.3,
  exchange: 1,
  treasury: 500,
  opinion_speed: 0.1,
  break_threshold: 0.1,
  information_origin: 0,
  decision_mode: "rule",
};
export default function WorldStudio({
  Network,
  request,
  post,
  onCreate,
  onDemo,
  locked,
  activeConfig,
}) {
  const [config, setConfig] = useState(defaults),
    [preview, setPreview] = useState(null),
    [catalog, setCatalog] = useState([]),
    [saved, setSaved] = useState(""),
    [name, setName] = useState("Small-world society"),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const [provider, setProvider] = useState({
      base_url: "http://127.0.0.1:8080/v1",
      model: "mock-v1",
      temperature: 0,
      token_budget: 20000,
      max_calls: 100,
      timeout: 10,
      retries: 0,
    }),
    [demo, setDemo] = useState(null);
  const refresh = async () =>
    setCatalog(
      (await request("/worlds")).worlds.filter((w) => w.configuration.engine),
    );
  useEffect(() => {
    refresh().catch((e) => setError(e.message));
  }, []);
  const perform = async (task) => {
    setBusy(true);
    setError("");
    try {
      await task();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };
  const change = (key, value) => {
    setConfig((c) => ({ ...c, [key]: value }));
    setPreview(null);
  };
  const numeric = (key, label, min, max, step = 1) => (
    <div className="field" key={key}>
      <label htmlFor={"studio-" + key}>{label}</label>
      <input
        id={"studio-" + key}
        type="number"
        min={min}
        max={max}
        step={step}
        value={config[key]}
        onChange={(e) => change(key, Number(e.target.value))}
      />
    </div>
  );
  const select = (key, label, values) => (
    <div className="field" key={key}>
      <label htmlFor={"studio-" + key}>{label}</label>
      <select
        id={"studio-" + key}
        value={config[key]}
        onChange={(e) => change(key, e.target.value)}
      >
        {values.map((v) => (
          <option key={v} value={v}>
            {v.replaceAll("_", " ")}
          </option>
        ))}
      </select>
    </div>
  );
  const create = () =>
    perform(async () => {
      const w = await request("/world/preview", post(config));
      setPreview(w);
      onCreate(w);
    });
  return (
    <section id="studio">
      <div className="section-heading">
        <h2>World Studio</h2>
        <span className="seed">social-1.0.0 / versioned configuration</span>
      </div>
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      <div className="studio-grid">
        <div className="studio-settings">
          <div className="field">
            <label htmlFor="world-name">World name</label>
            <input
              id="world-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={120}
            />
          </div>
          <div className="field">
            <label htmlFor="scenario">Scenario</label>
            <select
              id="scenario"
              defaultValue="custom"
              onChange={(e) =>
                perform(async () => {
                  if (e.target.value === "custom") return;
                  const p = await request("/scenarios");
                  setConfig(p[e.target.value]);
                  setPreview(null);
                })
              }
            >
              <option value="custom">Custom</option>
              <option value="fragile">The Fragile Society</option>
              <option value="cascade">Information Cascade</option>
            </select>
          </div>
          <h3>Initial society</h3>
          <div className="studio-fields">
            {numeric("population", "Agent count", 10, 100)}
            {numeric("initial_seed", "Initial seed", 0, 2147483647)}
            {numeric("rounds", "Simulation rounds", 5, 100)}
            {select("network", "Network", [
              "small_world",
              "random",
              "scale_free",
            ])}
            {config.network === "small_world" && (
              <>
                {numeric(
                  "neighbor_count",
                  "Neighbor count (even)",
                  2,
                  config.population - 1,
                  2,
                )}
                {numeric("rewiring", "Rewiring probability", 0, 1, 0.01)}
              </>
            )}
            {config.network === "random" &&
              numeric("edge_probability", "Edge probability", 0, 1, 0.01)}
            {config.network === "scale_free" &&
              numeric(
                "attachment",
                "Attachments per new agent",
                1,
                config.population - 1,
              )}
            {select("resource_distribution", "Resource distribution", [
              "equal",
              "uniform",
              "unequal",
            ])}
            {numeric("resource_scale", "Resource scale / units", 0, 200)}
            {select("opinion_distribution", "Opinion distribution", [
              "uniform",
              "polarized",
              "consensus",
            ])}
            {select("cooperation_distribution", "Cooperation distribution", [
              "equal",
              "uniform",
              "bimodal",
            ])}
            {numeric(
              "cooperation_mean",
              "Cooperation propensity mean",
              0,
              1,
              0.01,
            )}
            {numeric("heterogeneity", "Individual heterogeneity", 0, 1, 0.01)}
            {numeric("initial_trust", "Initial trust", 0, 1, 0.01)}
            {numeric(
              "information_origin",
              "Information origin / index",
              0,
              config.population - 1,
            )}
          </div>
          <h3>Social rules</h3>
          <div className="mechanisms">
            {[
              ["trust_enabled", "Dynamic trust"],
              ["cooperation_enabled", "Cooperation & transfers"],
              ["diffusion_enabled", "Information & opinion diffusion"],
              ["relationships_enabled", "Remove weak relationships"],
            ].map(([key, label]) => (
              <label key={key}>
                <input
                  type="checkbox"
                  checked={config[key]}
                  onChange={(e) => change(key, e.target.checked)}
                />
                {label}
              </label>
            ))}
          </div>
          <div className="studio-fields">
            {numeric("trust_speed", "Trust update speed", 0, 0.5, 0.01)}
            {numeric(
              "cooperation_threshold",
              "Cooperation decision threshold",
              0,
              1,
              0.01,
            )}
            {numeric("incentive", "Cooperation incentive", 0, 1, 0.01)}
            {numeric("exchange", "Donation per neighbor / units", 0, 10, 0.1)}
            {numeric(
              "treasury",
              "Finite incentive treasury / units",
              0,
              100000,
            )}
            {numeric(
              "transmission",
              "Information transmission probability",
              0,
              1,
              0.01,
            )}
            {numeric("opinion_speed", "Opinion update speed", 0, 1, 0.01)}
            {numeric("break_threshold", "Remove ties below trust", 0, 1, 0.01)}
            {select("decision_mode", "Decision mode", ["rule", "mock"])}
          </div>
        </div>
        <div className="studio-preview">
          <div className="section-heading">
            <h3>Initial network</h3>
            <button
              className="export"
              disabled={busy}
              onClick={() =>
                perform(async () =>
                  setPreview(await request("/world/preview", post(config))),
                )
              }
            >
              <Eye size={14} />
              Preview network
            </button>
          </div>
          <Network world={preview} />
          {preview && (
            <p className="stats">
              {preview.agents.length} Agents / {preview.edges.length} ties /
              seed {preview.seed}
              <br />
              Opening resources{" "}
              {preview.agents
                .reduce((s, a) => s + a.resource, 0)
                .toFixed(2)}{" "}
              units / treasury {preview.treasury} units
            </p>
          )}
          <div className="studio-summary">
            <h3>World configuration</h3>
            <p className="stats">
              {config.network.replaceAll("_", " ")} / {config.population} Agents
              / {config.rounds} rounds
              <br />
              {config.resource_distribution} resources /{" "}
              {config.opinion_distribution} opinions
              <br />
              Decisions: {config.decision_mode}
            </p>
            <div className="actions">
              <button className="run" disabled={locked || busy} onClick={() => perform(async () => {
                const scenarios = await request("/scenarios");
                setConfig(scenarios.cascade);
                await onDemo(scenarios.cascade);
              })}>
                <Play size={14} />Run Demo
              </button>
              <button
                className="run"
                disabled={locked || busy}
                onClick={create}
              >
                <Play size={14} />
                Create world
              </button>
              <button
                className="export"
                disabled={busy}
                onClick={() =>
                  perform(async () => {
                    const w = await request(
                      "/worlds",
                      post({
                        name,
                        configuration: config,
                        parent_id: saved || null,
                      }),
                    );
                    setSaved(w.world_id);
                    await refresh();
                  })
                }
              >
                <Save size={14} />
                Save configuration
              </button>
              <button
                className="export"
                onClick={() => {
                  setConfig(defaults);
                  setSaved("");
                  setPreview(null);
                }}
              >
                <RotateCcw size={14} />
                Restore defaults
              </button>
              <button
                className="export"
                disabled={!activeConfig?.engine}
                onClick={() => {
                  setConfig(activeConfig);
                  setSaved("");
                  setPreview(null);
                }}
              >
                <GitBranch size={14} />
                Branch current world
              </button>
            </div>
            <div className="field">
              <label htmlFor="load-world">Saved world</label>
              <select
                id="load-world"
                value={saved}
                onChange={(e) =>
                  perform(async () => {
                    setSaved(e.target.value);
                    if (!e.target.value) return;
                    const w = await request("/worlds/" + e.target.value);
                    setName(w.name);
                    setConfig(w.configuration);
                    setPreview(
                      await request("/world/preview", post(w.configuration)),
                    );
                  })
                }
              >
                <option value="">Select world</option>
                {catalog.map((w) => (
                  <option key={w.world_id} value={w.world_id}>
                    {w.name}
                    {w.parent_id ? " / branch" : ""}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <details>
            <summary>Agent Decision provider</summary>
            <div className="studio-fields">
              {Object.entries(provider).map(([key, value]) => (
                <div className="field" key={key}>
                  <label htmlFor={"provider-" + key}>
                    {key.replaceAll("_", " ")}
                  </label>
                  <input
                    id={"provider-" + key}
                    type={typeof value === "number" ? "number" : "text"}
                    value={value}
                    onChange={(e) =>
                      setProvider((p) => ({
                        ...p,
                        [key]:
                          typeof value === "number"
                            ? Number(e.target.value)
                            : e.target.value,
                      }))
                    }
                  />
                </div>
              ))}
            </div>
            <div className="actions">
              <button
                className="export"
                disabled={busy}
                onClick={() =>
                  perform(async () =>
                    setDemo(
                      await request(
                        "/decisions/demo",
                        post({
                          world: { ...config, decision_mode: "mock" },
                          seed: config.initial_seed,
                          provider,
                        }),
                      ),
                    ),
                  )
                }
              >
                <Play size={14} />
                Run Mock decisions
              </button>
              <button
                className="export"
                disabled={busy}
                onClick={() =>
                  perform(async () =>
                    setDemo(
                      await request(
                        "/decisions/demo",
                        post({
                          world: { ...config, decision_mode: "external" },
                          seed: config.initial_seed,
                          provider,
                        }),
                      ),
                    ),
                  )
                }
              >
                <Play size={14} />
                Run configured provider
              </button>
            </div>
            <p className="limitations">
              External credentials: server environment BUTTERFLYLAB_LLM_KEY. No
              credentials are stored in the world or export.
            </p>
            {demo && (
              <>
                <p role="status" className="notice">
                  Recorded decision replay:{" "}
                  {demo.replay_identical ? "identical" : "mismatch"} /{" "}
                  {demo.run.provider_usage?.calls} calls
                </p>
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Round</th>
                        <th>Agent</th>
                        <th>Action</th>
                        <th>Target</th>
                        <th>Reason / status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {demo.run.decisions.slice(0, 12).map((d) => (
                        <tr key={d.round + "-" + d.agent}>
                          <td>{d.round}</td>
                          <td>{d.agent}</td>
                          <td>
                            {d.decision.cooperate ? "cooperate" : "compete"}
                          </td>
                          <td>{d.decision.target ?? "none"}</td>
                          <td>
                            {d.decision.reason}
                            <small>{d.status}</small>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <button
                  className="export"
                  onClick={() => {
                    const u = URL.createObjectURL(
                      new Blob([JSON.stringify(demo, null, 2)], {
                        type: "application/json",
                      }),
                    );
                    const a = document.createElement("a");
                    a.href = u;
                    a.download = "decision-replay.json";
                    a.click();
                    URL.revokeObjectURL(u);
                  }}
                >
                  <Save size={14} />
                  Export decision tape
                </button>
              </>
            )}
          </details>
        </div>
      </div>
    </section>
  );
}
