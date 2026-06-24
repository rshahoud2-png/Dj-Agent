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
  assert.equal(config.bundle.windows.webviewInstallMode.type, "offlineInstaller");
  assert.equal(config.productName, "DJ Agent Desktop");
  assert.equal(config.bundle.createUpdaterArtifacts, true);
  assert.match(config.plugins.updater.endpoints[0], /github\.com\/rshahoud2-png\/Dj-Agent\/releases/);
});

test("Python service declares all required local endpoints", async () => {
  const source = await readFile(new URL("../python-engine/app/main.py", import.meta.url), "utf8");
  for (const endpoint of ["/health", "/diagnostics", "/analyze-track", "/generate-cues", "/analyze-transition", "/generate-set-analysis", "/integrations", "/export-dj"]) {
    assert.match(source, new RegExp(endpoint.replace("/", "\\/")));
  }
});

test("Windows build validates prerequisites and generates icons", async () => {
  const build = await readFile(new URL("../scripts/build-windows.ps1", import.meta.url), "utf8");
  const sidecarBuild = await readFile(new URL("../scripts/build-sidecar.ps1", import.meta.url), "utf8");
  const sidecarEntry = await readFile(new URL("../python-engine/run.py", import.meta.url), "utf8");
  assert.match(build, /check-prerequisites\.ps1/);
  assert.match(build, /tauri icon/);
  assert.match(build, /DJAgentSetup\.exe/);
  assert.match(sidecarBuild, /test-sidecar\.ps1/);
  assert.match(sidecarBuild, /validate-sidecar-bundle\.ps1/);
  assert.match(sidecarBuild, /collect-all imageio_ffmpeg/);
  assert.match(sidecarEntry, /from app\.main import app/);
  assert.doesNotMatch(sidecarEntry, /"app\.main:app"/);
});

test("startup diagnostics cover clean Windows runtime dependencies", async () => {
  const component = await readFile(new URL("../src/components/StartupDiagnostics.tsx", import.meta.url), "utf8");
  const runtime = await readFile(new URL("../python-engine/app/runtime.py", import.meta.url), "utf8");
  const requirements = await readFile(new URL("../python-engine/requirements.txt", import.meta.url), "utf8");
  for (const phrase of ["Python analysis sidecar included", "Python analysis sidecar launches", "Local engine health responds"]) {
    assert.match(component, new RegExp(phrase));
  }
  for (const dependency of ["imageio-ffmpeg", "scipy", "scikit-learn", "numba"]) {
    assert.match(requirements, new RegExp(dependency));
  }
  for (const check of ["Bundled FFmpeg", "App data folder writable", "SQLite database writable", "SoundFile/libsndfile runtime"]) {
    assert.match(runtime, new RegExp(check.replace("/", "\\/")));
  }
});

test("GitHub Actions produces the named Windows installer artifact", async () => {
  const workflow = await readFile(new URL("../.github/workflows/windows-installer.yml", import.meta.url), "utf8");
  assert.match(workflow, /windows-latest/);
  assert.match(workflow, /build-windows\.ps1 -Unsigned/);
  assert.match(workflow, /test-installer\.ps1/);
  assert.match(workflow, /release\/DJAgentSetup\.exe/);
});

test("signed GitHub Releases power the in-app updater", async () => {
  const workflow = await readFile(new URL("../.github/workflows/release.yml", import.meta.url), "utf8");
  const settings = await readFile(new URL("../src/components/UpdatesPanel.tsx", import.meta.url), "utf8");
  const capabilities = JSON.parse(await readFile(new URL("../src-tauri/capabilities/default.json", import.meta.url), "utf8"));
  assert.match(workflow, /tauri-apps\/tauri-action@v1/);
  assert.match(workflow, /TAURI_SIGNING_PRIVATE_KEY/);
  assert.match(workflow, /uploadUpdaterJson: true/);
  assert.match(settings, /Check for Updates/);
  assert.match(settings, /downloadAndInstall/);
  assert.match(settings, /relaunch/);
  assert.ok(capabilities.permissions.includes("updater:default"));
  assert.ok(capabilities.permissions.includes("process:default"));
});
