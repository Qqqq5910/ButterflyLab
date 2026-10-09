async (page) => {
  const assert = (condition, message) => {
    if (!condition) throw new Error(message);
  };
  const done = () =>
    page.waitForFunction(
      () =>
        document
          .querySelector(".run-status")
          ?.textContent.includes("completed"),
      {},
      { timeout: 60000 },
    );
  const run = async (name) => {
    const previous = await page.evaluate(() =>
      localStorage.getItem("butterflylab.experiment"),
    );
    await page.getByRole("button", { name, exact: true }).click();
    await page.waitForFunction(
      (id) => localStorage.getItem("butterflylab.experiment") !== id,
      previous,
    );
    await done();
  };
  await page.goto("http://127.0.0.1:5173");
  await page.evaluate(() => localStorage.setItem("butterflylab.experiment", "3f87a501-0313-4c1b-9d37-57a1f8b24357"));
  await page.reload();
  await page.waitForFunction(() => [...document.querySelectorAll("button")].some(b => b.textContent.trim() === "Run baseline" && !b.disabled) && document.querySelectorAll(".metric-chart").length === 4);
  await page
    .getByRole("button", { name: "Run baseline", exact: true })
    .waitFor();
  await page.waitForFunction(
    () => document.querySelectorAll(".world-grid .node").length === 100,
  );
  await page
    .getByLabel("EXPERIMENT NAME")
    .fill("Phase 2A baseline / 50 Agents");
  await page.getByLabel("PAIRED SEEDS / 1-100").fill("5");
  await page.getByLabel("FIRST SEED").fill("42");
  await run("Run baseline");
  const baselineId = await page.evaluate(() =>
    localStorage.getItem("butterflylab.experiment"),
  );
  const baseline = await (
    await page.request.get(
      "http://127.0.0.1:8001/api/experiments/" + baselineId,
    )
  ).json();
  assert(
    baseline.result.configuration.intervention === null,
    "Baseline has intervention",
  );
  await page
    .getByLabel("EXPERIMENT NAME")
    .fill("Phase 2A regression resource / 5 seeds");
  await page
    .getByLabel("INTERVENTION", { exact: true })
    .selectOption("resource");
  await page.getByLabel("DELTA / UNITS").fill("-10");
  await run("Run A/B experiment");
  const id = await page.evaluate(() =>
    localStorage.getItem("butterflylab.experiment"),
  );
  const record = await (
    await page.request.get("http://127.0.0.1:8001/api/experiments/" + id)
  ).json();
  assert(record.result.seeds.length === 5, "Five paired seeds missing");
  assert(
    JSON.stringify(record.result.baseline) ===
      JSON.stringify(baseline.result.baseline),
    "Baseline changed across branch",
  );
  await page.waitForFunction(
    () =>
      document.querySelectorAll(".metric-chart .recharts-wrapper").length === 4,
  );
  assert(
    (await page.locator(".metric-chart .recharts-line-curve").count()) === 8,
    "Eight A/B metric curves missing",
  );
  assert(
    (await page.locator("#observatory tbody tr").count()) === 5,
    "Per-seed rows missing",
  );
  await page.getByLabel("Displayed seed").selectOption("4");
  await page.getByLabel("Timeline round").fill("50");
  assert(
    (await page.locator(".world-grid").innerText()).includes("seed 46"),
    "Selected seed not reflected",
  );
  await page.getByLabel("Displayed seed").selectOption("0");
  await page.getByRole("button", { name: "Play or pause" }).click();
  await page.waitForFunction(
    () => Number(document.querySelector("input[type=range]").value) > 0,
  );
  await page.getByRole("button", { name: "Play or pause" }).click();
  await page.getByLabel("Timeline round").fill("50");
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
    (await page.evaluate(() =>
      localStorage.getItem("butterflylab.experiment"),
    )) === id,
    "Reload lost current ID",
  );
  await page
    .getByRole("button", {
      name: "Phase 2A regression resource / 5 seeds",
      exact: true,
    })
    .first()
    .click();
  await done();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: "Export JSON", exact: true }).click();
  const download = await downloadPromise;
  await download.saveAs(
    "D:/Projects/ButterflyLab/output/playwright/phase2a-regression-experiment.json",
  );
  await page.getByRole("button", { name: "Reproduce", exact: true }).click();
  await page
    .getByRole("status")
    .filter({ hasText: "Exact reproduction verified" })
    .waitFor({ timeout: 60000 });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByLabel("Timeline round").fill("50");
  await page.screenshot({
    path: "D:/Projects/ButterflyLab/output/playwright/phase2a-regression-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForFunction(() =>
    [...document.querySelectorAll('.recharts-wrapper')].every(
      element => element.getBoundingClientRect().right <= innerWidth,
    ),
  );
  await page.screenshot({
    path: "D:/Projects/ButterflyLab/output/playwright/phase2a-regression-mobile.png",
    fullPage: true,
  });
  assert(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
    "Mobile page overflow",
  );
  await page.setViewportSize({ width: 1440, height: 1000 });
  return {
    id,
    baselineId,
    steps: "all 12 acceptance steps passed",
    seedCount: 5,
    snapshots: record.result.baseline[0].snapshots.length,
    paired: record.result.paired.map((p) => ({ seed: p.seed, delta: p.delta })),
    summary: record.result.summary,
  };
}
