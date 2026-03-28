# Execution Checks

Use this guide when the orchestrator is expected to launch workers for real instead of stopping at planning or packet generation.

## What To Understand First

Before any worker launch, the main thread should know:
- which files or directories must already exist
- whether the task starts from a failing scaffold, a passing baseline, or an empty stub
- which exact working directory each backend should use
- how packet paths map into that working directory
- which backend command proves non-interactive readiness
- which signal proves the worker actually finished
- which timeout or stall pattern should trigger a kill
- which artifacts must be captured for later debugging

## Preflight Checklist

Run these in order when live execution matters:
1. validate the manifest shape and overlap policy
2. confirm the shared scaffold or worker-owned files exist
3. confirm the untouched baseline behaves as expected
4. confirm each backend CLI is installed and callable
5. confirm auth, provider, model, and permission assumptions for each backend
6. confirm the worker's working directory and path mapping
7. run a tiny smoke command when a backend has been flaky or untested

## Worker-Level Checks

Recommended manifest fields for live runs:
- `working_directory`: where that backend should start
- `launch_checks`: commands or facts to verify before launching the worker
- `success_signals`: output, files, or tests that indicate success
- `failure_signals`: timeout, no-output stall, auth failure, scope violation, or failing command patterns
- `artifacts`: paths to capture such as last-message files, logs, json output, or diffs
- `timeout_seconds`: hard stop for that worker

## Runtime Monitoring

During execution:
- record started time and finished time for every worker
- capture stdout, stderr, exit code, and changed files
- detect no-output stalls separately from clean failures
- kill workers that exceed `timeout_seconds`
- preserve successful workers when one backend fails
- write a machine-readable run report even on partial failure

## Partial Failure Policy

If one backend fails and others succeed:
- do not throw away successful edits
- isolate the failed worker and inspect its logs and artifacts
- check whether the failure is backend-specific, prompt-specific, or scope-specific
- retry only the failed worker if the ownership model is still valid
- switch backend or collapse the remaining work only after the failure is understood

## Good Evidence To Capture

Useful artifacts include:
- rendered worker packet
- last assistant message
- raw json event stream if the backend supports it
- focused test output
- final diff limited to the worker scope
- timeout or kill reason
- run report summarizing timing and changed files
