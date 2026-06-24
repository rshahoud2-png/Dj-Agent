# Publishing desktop updates

DJ Agent Desktop uses the Tauri v2 updater and GitHub Releases. Update packages are signed; an installed app rejects files that do not match the public key embedded in `src-tauri/tauri.conf.json`.

## One-time repository setup

1. Open the GitHub repository's **Settings > Secrets and variables > Actions**.
2. Create `TAURI_SIGNING_PRIVATE_KEY` and paste the complete private updater key.
3. If the key has a password, create `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`.
4. Keep an offline backup of the private key. Do not commit it, rotate it casually, or lose it. Existing installations trust this key.

The key generated for this repository is stored locally in the ignored `work-keys/dj-agent-updater.key` file until it is moved to a secure password manager and GitHub Actions.

## Bump the version

Run:

```powershell
npm run version:set -- 0.2.1
npm test
```

The version script updates `package.json`, `package-lock.json`, `src-tauri/Cargo.toml`, and `src-tauri/tauri.conf.json`.

## Publish a release

Commit the version bump, then create a matching tag:

```powershell
git add .
git commit -m "Release DJ Agent Desktop 0.2.1"
git push origin main
git tag v0.2.1
git push origin v0.2.1
```

The tag starts `.github/workflows/release.yml`. The Windows runner builds the Python sidecar and NSIS installer, signs the updater artifact, creates the GitHub Release, and uploads `DJAgentSetup.exe`, its signature, and `latest.json`.

The tag and app version must match. Release jobs require `TAURI_SIGNING_PRIVATE_KEY`.

## Installed user experience

The Settings page displays the installed version. **Check for Updates** requests:

```text
https://github.com/rshahoud2-png/Dj-Agent/releases/latest/download/latest.json
```

If a newer version exists, the app shows its release notes. The user can download and install it in place; DJ Agent Desktop verifies the signature, runs the NSIS installer in passive mode, and restarts itself. No manual reinstall is needed after the first updater-enabled installation.

Live updating begins with version 0.2.0. Any older build that did not contain the updater must install 0.2.0 once.
