import { readFile, writeFile } from "node:fs/promises";

const version = process.argv[2];
if (!version || !/^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/.test(version)) {
  console.error("Usage: npm run version:set -- 0.2.1");
  process.exit(1);
}

async function updateJson(path, update) {
  const value = JSON.parse(await readFile(path, "utf8"));
  update(value);
  await writeFile(path, `${JSON.stringify(value, null, 2)}\n`);
}

await updateJson("package.json", (pkg) => {
  pkg.version = version;
});
await updateJson("package-lock.json", (lock) => {
  lock.version = version;
  if (lock.packages?.[""]) lock.packages[""].version = version;
});
await updateJson("src-tauri/tauri.conf.json", (config) => {
  config.version = version;
});

const cargoPath = "src-tauri/Cargo.toml";
const cargo = await readFile(cargoPath, "utf8");
await writeFile(cargoPath, cargo.replace(/^version = "[^"]+"/m, `version = "${version}"`));

console.log(`DJ Agent Desktop version set to ${version}.`);
