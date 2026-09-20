# Final commit manifest

Every modified/untracked file is classified below. Staging uses explicit paths; no git add . is used. Final evidence files created after this inventory are added explicitly and scanned before commit.

## COMMIT

- `.gitignore`
- `FINAL_RELEASE_REPORT.md`
- `README.md`
- `docs/AGENT_GUARD.md`
- `docs/AI_CODING_LOG_PROVENANCE.md`
- `docs/AI_CODING_SESSION_NOTES.md`
- `docs/AI_LOG_EXPORT_MANUAL.md`
- `docs/FINAL_ACCEPTANCE.md`
- `docs/FINAL_INTEGRATION.md`
- `docs/FINAL_INTEGRATION_GIT_STATUS.txt`
- `docs/FINAL_VIDEO_PREP.md`
- `docs/FINAL_VIDEO_SCRIPT.md`
- `docs/RELEASE_CANDIDATE.md`
- `docs/STAGE_ACCEPTANCE_REPORT.md`
- `docs/VIDEO_RECORDING_CHECKLIST.md`
- `docs/VIDEO_SCRIPT.md`
- `docs/WEB_DEMO.md`
- `docs/codex_rollout_sha256.txt`
- `docs/evidence/final-agent-guard-runtime.txt`
- `docs/evidence/final-agent-tool-trace.txt`
- `docs/evidence/final-ai-agent-required.patch`
- `docs/evidence/final-browser-acceptance.md`
- `docs/evidence/final-build-source.json`
- `docs/evidence/final-clean-build.txt`
- `docs/evidence/final-index-refresh.json`
- `docs/evidence/final-release-regression.json`
- `docs/evidence/final-release-synthetic.json`
- `docs/evidence/final-repo-dirty-check.txt`
- `docs/evidence/final-secret-scan.json`
- `docs/evidence/final-source-hydration.json`
- `docs/evidence/final-synthetic-validation.json`
- `docs/evidence/rc-synthetic-validation.json`
- `docs/evidence/real-openvela-integration.json`
- `docs/templates/technical-report.docx`
- `logs/README.md`
- `logs/sdh12312/2026-09-18/codex__01a0b2ea-67a2-7ea0-b00c-afa2e32aec6a.jsonl`
- `logs/sdh12312/2026-09-19/codex__01a0b9b4-c572-7b70-b99b-35cd4196ac14.jsonl`
- `logs/sdh12312/manifest.json`
- `tests/test_finalize_last_codex_session.py`
- `tests/test_web_bridge.py`
- `tools/audit_workspace.py`
- `tools/build_final_openvela.sh`
- `tools/build_technical_report.py`
- `tools/codex_rollout_converter.py`
- `tools/configure_agent_guard.sh`
- `tools/deploy_guard_skill.py`
- `tools/finalize_last_codex_session.py`
- `tools/interactive_bridge.py`
- `tools/normalize_tracked_scripts.py`
- `tools/package_submission.py`
- `tools/real_openvela_integration.py`
- `tools/run_web_emulator.sh`
- `tools/scan_release_secrets.py`
- `tools/start_final_demo.ps1`
- `tools/start_final_demo.py`
- `tools/test_agent_guard.py`
- `tools/web_bridge.py`
- `web/app.js`
- `web/index.html`
- `web/telemetry.js`
- `web/tests/telemetry.test.mjs`

## DO NOT COMMIT

- `FlyReflex_项目介绍.docx`
- `mintty.2026-09-19_17-12-54.png`

## SUBMISSION ONLY

- `submission/FlyReflex_技术报告.docx`
- `submission/FlyReflex_技术报告.pdf`
- `submission/final/FlyReflex_技术报告.docx`
- `submission/final/FlyReflex_技术报告.pdf`
- `submission/FlyReflex_浏览器实录素材.mp4`

## LOCAL ONLY

- `.qa/`
- `C:/Users/29329/.codex/private-backups/flyreflex-sealed-20260919/`
- `D:/openvela_official/cmake_out/`
- `Original Codex rollouts and external API key files`
- `build/`
- `web/node_modules/`

Existing tracked submission/FlyReflex_项目介绍.docx is retained as historical material. The final technical report and video are submission deliverables, not source/log ZIP contents. Old browser footage is not the final contest video.

Release qualification note: the formal clean-first build is recorded as `PARTIAL` in `FINAL_RELEASE_REPORT.md` and `docs/evidence/final-clean-build.txt`. No historical candidate firmware or runtime evidence is represented as the incomplete build's result, and no new-firmware smoke artifact is claimed.

Sealed log exception: user authorized an external backup and converter-based re-redaction of session 1; session 2 is unchanged. See AI_LOG_EXPORT_MANUAL.md.
