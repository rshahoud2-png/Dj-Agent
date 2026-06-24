import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("desktop package exposes required commands", async () => {
  const pkg = JSON.parse(await readFile(new URL("../package.json", import.meta.url), "utf8"));
  assert.ok(pkg.scripts.dev);
  assert.ok(pkg.scripts["tauri:dev"]);
  assert.ok(pkg.scripts["tauri:build"]);
});

test("Tauri packages an NSIS installer and local sidecar", async () => {
  const config = JSON.parse(await readFile(new URL("../src-tauri/tauri.conf.json", import.meta.url), "utf8"));
  assert.deepEqual(config.bundle.targets, ["nsis"]);
  assert.deepEqual(config.bundle.externalBin, ["binaries/dj-agent-engine"]);
  assert.equal(config.productName, "DJ Agent Desktop");
});

test("Python service declares all required local endpoints", async () => {
  const source = await readFile(new URL("../python-engine/app/main.py", import.meta.url), "utf8");
  for (const endpoint of ["/health", "/analyze-track", "/generate-cues", "/analyze-transition", "/generate-set-analysis", "/integrations", "/export-dj"]) {
    assert.match(source, new RegExp(endpoint.replace("/", "\\/")));
  }
});

test("Windows build validates prerequisites and generates icons", async () => {
  const build = await readFile(new URL("../scripts/build-windows.ps1", import.meta.url), "utf8");
  assert.match(build, /check-prerequisites\.ps1/);
  assert.match(build, /tauri icon/);
  assert.match(build, /DJAgentSetup\.exe/);
});

test("GitHub Actions produces the named Windows installer artifact", async () => {
  const workflow = await readFile(new URL("../.github/workflows/windows-installer.yml", import.meta.url), "utf8");
  assert.match(workflow, /windows-latest/);
  assert.match(workflow, /npm run tauri:build/);
  assert.match(workflow, /release\/DJAgentSetup\.exe/);
});
