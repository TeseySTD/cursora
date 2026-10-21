// pnpm lint:ci — lint GitHub Actions workflows with the actionlint Docker image (no local install).
import { repoRoot, run } from "./lib.mjs";

const image = "rhysd/actionlint:1.7.12";
run("docker", ["run", "--rm", "-v", `${repoRoot}:/repo`, "--workdir", "/repo", image, "-color"]);
