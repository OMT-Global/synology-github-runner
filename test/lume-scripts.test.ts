import fs from "node:fs";
import path from "node:path";
import { describe, expect, test } from "vitest";

describe("Lume pool scripts", () => {
  test("creates and recycles cloned macOS VM slots", () => {
    const createSlot = read("scripts/lume/create-slot.sh");
    const destroySlot = read("scripts/lume/destroy-slot.sh");
    const runSlot = read("scripts/lume/run-slot.sh");
    const reconcile = read("scripts/lume/reconcile-pool.sh");

    expect(createSlot).toContain('lume clone "${LUME_VM_BASE_NAME}" "${LUME_VM_NAME}"');
    expect(createSlot).toContain('lume set "${LUME_VM_NAME}" --cpu "${LUME_VM_CPU}"');
    expect(createSlot).toContain('nohup lume run "${LUME_VM_NAME}" --no-display');
    expect(destroySlot).toContain('lume stop "${LUME_VM_NAME}"');
    expect(destroySlot).toContain('lume delete "${LUME_VM_NAME}" --force');
    expect(runSlot).toContain("uploading guest bootstrap assets");
    expect(runSlot).toContain('lume ssh "${LUME_VM_NAME}"');
    expect(reconcile).toContain('nohup "${SCRIPT_DIR}/run-slot.sh" --slot "${slot}"');
  });

  test("bootstraps ephemeral macOS runners inside guest VMs", () => {
    const bootstrap = read("scripts/guest/macos-runner-bootstrap.sh");
    const helper = read("scripts/lib/github-runner-common.sh");

    expect(bootstrap).toContain("actions-runner-osx-arm64-${RUNNER_VERSION}.tar.gz");
    expect(bootstrap).toContain("--ephemeral");
    expect(bootstrap).toContain("--disableupdate");
    expect(bootstrap).toContain('cleanup_runner_registration');
    expect(helper).toContain("github_runner_endpoint_base");
    expect(helper).toContain("request_runner_token");
  });
});

function read(relativePath: string): string {
  return fs.readFileSync(path.resolve(relativePath), "utf8");
}
