"""Prove the registration contract detects the old destination, without HTTP."""

import json
import subprocess

from prepare_copy import TARGET, evidence_name, evidence_path, write_json
from quality import source_hashes


def main():
    before = source_hashes()
    directory = TARGET / ".quality/mutations"
    directory.mkdir(parents=True, exist_ok=True)
    hook = directory / "old-registration.cjs"
    hook.write_text(
        """const fs = require('node:fs');
const read = fs.readFileSync;
fs.readFileSync = function(file, ...args) {
  const result = read.call(this, file, ...args);
  if (String(file).replaceAll('\\\\','/').endsWith('src/features/auth/api/authApi.ts') && typeof result === 'string') {
    return result.replace("fetch('/graphql'", "fetch('https://ag.full-style.com'");
  }
  return result;
};
""",
        encoding="utf-8",
    )
    # The suite injects fetch at the network boundary; neither execution contacts HTTP.
    command = ["node", "--test", "tests/provider-contracts.cjs"]
    baseline = subprocess.run(
        command, cwd=TARGET / "FullStyle-Frontend", capture_output=True, text=True, encoding="utf-8"
    )
    mutated = subprocess.run(
        ["node", "--require", str(hook), *command[1:]],
        cwd=TARGET / "FullStyle-Frontend",
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    output = mutated.stdout + mutated.stderr
    passed = (
        baseline.returncode == 0
        and mutated.returncode != 0
        and "ag.full-style.com" in output
        and before == source_hashes()
    )
    evidence_path("phase-3-mutation.log").write_text(output, encoding="utf-8")
    write_json(
        "phase-3-mutation.json",
        {
            "passed": passed,
            "baseline_exit_code": baseline.returncode,
            "mutated_exit_code": mutated.returncode,
            "mutation": "In-memory restoration of the legacy registration destination",
            "sources_changed": before != source_hashes(),
            "providers_contacted": False,
            "report": evidence_name("phase-3-mutation.log"),
        },
    )
    print(
        json.dumps({"regression_detected": passed, "sources_unchanged": before == source_hashes()})
    )
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
