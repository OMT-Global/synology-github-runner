import fs from "node:fs";
import path from "node:path";
import dotenv from "dotenv";
import { normalizeRunnerVersion } from "./runner-version.js";

export interface DeploymentEnv {
  githubPat?: string;
  githubApiUrl: string;
  synologyRunnerBaseDir: string;
  composeProjectName: string;
  runnerVersion: string;
  raw: Record<string, string>;
}

export interface LoadDeploymentEnvOptions {
  envPath?: string;
  requirePat?: boolean;
}

export function loadDeploymentEnv(
  options: LoadDeploymentEnvOptions = {}
): DeploymentEnv {
  const envPath = options.envPath ?? path.resolve(process.cwd(), ".env");
  const requirePat = options.requirePat ?? true;

  const fileEnv = fs.existsSync(envPath)
    ? dotenv.parse(fs.readFileSync(envPath, "utf8"))
    : {};

  const merged = {
    ...fileEnv,
    ...Object.fromEntries(
      Object.entries(process.env).filter(
        (entry): entry is [string, string] => typeof entry[1] === "string"
      )
    )
  };

  const githubPat = merged.GITHUB_PAT?.trim() || undefined;
  if (requirePat && !githubPat) {
    throw new Error(
      `GITHUB_PAT is required; set it in ${envPath} or the current environment`
    );
  }

  const githubApiUrl = normalizeUrl(
    merged.GITHUB_API_URL || "https://api.github.com"
  );
  const synologyRunnerBaseDir =
    merged.SYNOLOGY_RUNNER_BASE_DIR ||
    "/volume1/docker/synology-github-runner";
  const composeProjectName =
    merged.COMPOSE_PROJECT_NAME || "synology-github-runner";
  const runnerVersion = normalizeRunnerVersion(merged.RUNNER_VERSION || "2.333.0");

  return {
    githubPat,
    githubApiUrl,
    synologyRunnerBaseDir,
    composeProjectName,
    runnerVersion,
    raw: {
      ...merged,
      GITHUB_API_URL: githubApiUrl,
      SYNOLOGY_RUNNER_BASE_DIR: synologyRunnerBaseDir,
      COMPOSE_PROJECT_NAME: composeProjectName,
      RUNNER_VERSION: runnerVersion
    }
  };
}

function normalizeUrl(value: string): string {
  return value.replace(/\/+$/, "");
}
