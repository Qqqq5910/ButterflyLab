async (page) => {
  const assert = (value, message) => {
    if (!value) throw new Error(message);
  };
  const root = "D:/Projects/ButterflyLab/output/playwright/";
  const done = () =>
    page.waitForFunction(
      () =>
        document
          .querySelector(".run-status")
          ?.textContent.includes("completed"),
      {},
      { timeout: 120000 },
    );
  const get = async (path) =>
    (
      await page.request.get("http://127.0.0.1:8001/api" + path, {
        timeout: 180000,
      })
    ).json();
  const current = async () =>
    get(
      "/experiments/" +
        (await page.evaluate(() =>
          localStorage.getItem("butterflylab.experiment"),
        )),
    );
  const run = async (name) => {
    const old = await page.evaluate(() =>
      localStorage.getItem("butterflylab.experiment"),
    );
    await page.getByRole("button", { name, exact: true }).click();
    await page.waitForFunction(
      (id) => localStorage.getItem("butterflylab.experiment") !== id,
      old,
    );
    await done();
    return current();
  };
  await page.goto("http://127.0.0.1:5173");
  await page
    .getByRole("button", { name: "Create world", exact: true })
    .waitFor();
  await page
    .getByRole("button", { name: "Restore defaults", exact: true })
    .click();
  await page
    .getByLabel("World name", { exact: true })
    .fill("Phase 2B verified small world");
  await page.getByLabel("Agent count", { exact: true }).fill("50");
  await page.getByLabel("Network", { exact: true }).selectOption("small_world");
  for (const label of [
    "Dynamic trust",
    "Cooperation & transfers",
    "Information & opinion diffusion",
    "Remove weak relationships",
  ])
    await page.getByLabel(label, { exact: true }).check();
  await page
    .getByRole("button", { name: "Preview network", exact: true })
    .click();
  await page.waitForFunction(
    () => document.querySelectorAll("#studio .node").length === 50,
  );
  await page
    .getByRole("button", { name: "Save configuration", exact: true })
    .click();
  await page.waitForFunction(
    () => document.querySelector("#load-world").value !== "",
  );
  const worldId = await page
    .getByLabel("Saved world", { exact: true })
    .inputValue();
  await page.getByRole("button", { name: "Create world", exact: true }).click();
  await page.getByRole("status").filter({ hasText: "World created" }).waitFor();
  await page.getByLabel("PAIRED SEEDS / 1-100").fill("30");
  await page.getByLabel("FIRST SEED").fill("42");
  await page.getByLabel("EXPERIMENT NAME").fill("Phase 2B baseline / 30 seeds");
  const baseline = await run("Run baseline");
  await page
    .getByLabel("EXPERIMENT NAME")
    .fill("Phase 2B resource -1 / 30 seeds");
  await page
    .getByLabel("INTERVENTION", { exact: true })
    .selectOption("resource");
  await page.getByLabel("DELTA / UNITS").fill("-1");
  const record = await run("Run A/B experiment");
  assert(record.engine_version === "social-1.0.0", "Wrong engine");
  assert(record.result.paired.length === 30, "Missing paired seeds");
  assert(
    JSON.stringify(record.result.baseline) ===
      JSON.stringify(baseline.result.baseline),
    "Baseline changed",
  );
  assert(
    record.result.baseline.every(
      (a, i) =>
        JSON.stringify(a.initial) ===
        JSON.stringify(record.result.variant[i].initial),
    ),
    "Unpaired initial state",
  );
  await page.waitForFunction(
    () =>
      document.querySelectorAll(".metric-chart .recharts-line-curve").length ===
      14,
  );
  assert(
    (await page.locator("#observatory tbody tr").count()) === 30,
    "Missing seed table",
  );
  await page
    .getByLabel("Paired metric", { exact: true })
    .selectOption("mean_trust");
  await page.getByLabel("Timeline round").fill("50");
  await page.locator(".world-grid .node").first().click();
  assert(
    (await page.locator(".agent-pop").innerText()).includes("mean trust"),
    "Agent trust missing",
  );
  await page
    .getByLabel("Mechanism", { exact: true })
    .selectOption("trust_enabled");
  await page.getByLabel("Study type", { exact: true }).selectOption("ablation");
  const previousStudy = await page.evaluate(() => localStorage.getItem("butterflylab.study"));
  await page
    .getByRole("button", { name: "Run research study", exact: true })
    .click();
  await page.waitForFunction(
    (previous) =>
      localStorage.getItem("butterflylab.study") !== previous &&
      !document.querySelector("#studies button.run").disabled,
    previousStudy,
    { timeout: 120000 },
  );
  const studyId = await page.evaluate(() =>
    localStorage.getItem("butterflylab.study"),
  );
  const ablation = await get("/worlds/" + studyId);
  assert(
    ablation.configuration.result.cells[0].paired.length === 30,
    "Ablation seed count",
  );
  assert(ablation.configuration.result.kind === "ablation", "Wrong study");
  const studyDownload = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export study JSON", exact: true })
    .click();
  await (await studyDownload).saveAs(root + "phase2b-ablation.json");
  await page
    .getByRole("button", { name: "Save experiment", exact: true })
    .click();
  await page
    .getByRole("status")
    .filter({ hasText: "Saved to SQLite" })
    .waitFor();
  await page.reload();
  await done();
  assert(
    (await current()).experiment_id === record.experiment_id,
    "Experiment reload failed",
  );
  await page
    .getByRole("button", {
      name: "Phase 2B resource -1 / 30 seeds",
      exact: true,
    })
    .first()
    .click();
  await done();
  await page.getByLabel("Saved world", { exact: true }).selectOption(worldId);
  await page.waitForFunction(
    () => document.querySelectorAll("#studio .node").length === 50,
  );
  assert(
    (await page.getByLabel("Network", { exact: true }).inputValue()) ===
      "small_world",
    "World load failed",
  );
  await page.getByLabel("Saved study", { exact: true }).selectOption(studyId);
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: "Export JSON", exact: true }).click();
  await (await downloadPromise).saveAs(root + "phase2b-experiment.json");
  await page.getByRole("button", { name: "Reproduce", exact: true }).click();
  await page
    .getByRole("status")
    .filter({ hasText: "Exact reproduction verified" })
    .waitFor({ timeout: 120000 });
  await page
    .locator("summary")
    .filter({ hasText: "Decision provider" })
    .click();
  await page
    .getByRole("button", { name: "Run Mock decisions", exact: true })
    .click();
  await page
    .getByRole("status")
    .filter({ hasText: "Recorded decision replay: identical" })
    .waitFor({ timeout: 60000 });
  const mockDownload = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export decision tape", exact: true })
    .click();
  await (await mockDownload).saveAs(root + "phase2b-decisions.json");
  await page
    .getByLabel("Paired metric", { exact: true })
    .selectOption("mean_trust");
  await page.getByLabel("Timeline round").fill("25");
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForFunction(() =>
    [...document.querySelectorAll(".recharts-wrapper")].every(
      (e) => e.getBoundingClientRect().right <= innerWidth,
    ),
  );
  await page.screenshot({ path: root + "phase2b-desktop.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForFunction(() =>
    [...document.querySelectorAll(".recharts-wrapper")].every(
      (e) => e.getBoundingClientRect().right <= innerWidth,
    ),
  );
  assert(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
    "Mobile overflow",
  );
  await page.screenshot({ path: root + "phase2b-mobile.png", fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  return {
    id: record.experiment_id,
    baselineId: baseline.experiment_id,
    worldId,
    studyId,
    steps: "12 Phase 2B acceptance steps passed",
    summary: record.result.summary,
    ablation: ablation.configuration.result.cells[0].summary,
  };
};
