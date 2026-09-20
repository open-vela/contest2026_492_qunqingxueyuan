#!/usr/bin/env python3
"""
Transparent Codex rollout -> openvela contest log converter.

Purpose:
- Convert an original Codex rollout JSONL that uses response_item/event_msg
  into the openvela contest event schema.
- Preserve the original session_id/timestamps/tool call IDs.
- Never modify the source rollout.
- Record SHA256/size/mtime of the source in manifest.json.
- Apply the official-style base redaction patterns plus provider-aware MiMo
  Token Plan and GitHub fine-grained token redaction; report the rule count.

This is a post-hoc compatibility converter for Codex rollout files when the
official collector cannot parse the newer Codex response_item/event_msg schema.
Keep the original rollout unchanged for audit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
GENERATOR = "codex-rollout-converter@1.3-transparent-manual"

DEFAULT_REDACT_RULES = [
    (re.compile(r"(?:sk-|tp-)[A-Za-z0-9_-]{20,}"), "provider-***REDACTED***"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "github_pat_***REDACTED***"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "gh*_***REDACTED***"),
    (re.compile(r"Bearer\s+[A-Za-z0-9._\-+/=]{20,}", re.I), "Bearer ***REDACTED***"),
    (
        re.compile(
            r"(?i)(\b(?:password|passwd|pwd)\b"
            r"(?:\\?[\"'])?\s*[:=]\s*(?:\\?[\"'])?)"
            r"((?!\*{3}REDACTED\*{3})[^\\\"'\s,}\]]{6,})"
        ),
        r"\1***REDACTED***",
    ),
    (
        re.compile(
            r"(?i)(\b(?:api[_-]?key|access[_-]?token|secret[_-]?key|client[_-]?secret|"
            r"refresh[_-]?token|session[_-]?token)\b"
            r"(?:\\?[\"'])?\s*[:=]\s*(?:\\?[\"'])?)"
            r"((?!\*{3}REDACTED\*{3})[^\\\"'\s,}\]]{8,})"
        ),
        r"\1***REDACTED***",
    ),
]

SENSITIVE_KEY_RE = re.compile(
    r"(?i)^(password|passwd|pwd|api[_-]?key|access[_-]?token|secret[_-]?key|"
    r"client[_-]?secret|refresh[_-]?token|session[_-]?token|authorization|"
    r"private[_-]?key)$"
)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def redact_value(value: Any, counter: list[int]) -> Any:
    if isinstance(value, str):
        out = value
        for pattern, replacement in DEFAULT_REDACT_RULES:
            out, n = pattern.subn(replacement, out)
            counter[0] += n
        return out
    if isinstance(value, list):
        return [redact_value(v, counter) for v in value]
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if SENSITIVE_KEY_RE.match(str(k)):
                out[k] = "***REDACTED***"
                counter[0] += 1
            else:
                out[k] = redact_value(v, counter)
        return out
    return value


def maybe_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    s = value.strip()
    if not s:
        return value
    if s[0] not in "[{":
        return value
    try:
        return json.loads(s)
    except Exception:
        return value


def extract_reasoning_summary(summary: Any) -> str:
    parts: list[str] = []

    def walk(v: Any) -> None:
        if isinstance(v, str):
            if v.strip():
                parts.append(v)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, dict):
            for key in ("text", "summary_text"):
                x = v.get(key)
                if isinstance(x, str) and x.strip():
                    parts.append(x)
            # Do not recursively dump unknown encrypted/opaque fields.

    walk(summary)
    return "\n".join(parts).strip()


def map_role(role: str | None) -> tuple[str, dict]:
    role = (role or "system").lower()
    if role in ("user", "assistant", "system", "tool"):
        return role, {}
    if role == "developer":
        return "system", {"original_role": "developer"}
    return "system", {"original_role": role}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="Original Codex rollout JSONL")
    ap.add_argument("--repo", required=True, help="Contest repository root")
    ap.add_argument("--team-id", required=True)
    ap.add_argument("--github-login", required=True)
    args = ap.parse_args()

    source = Path(args.source).expanduser().resolve()
    repo = Path(args.repo).expanduser().resolve()

    if not source.is_file():
        raise SystemExit(f"Source not found: {source}")
    if not (repo / ".git").exists():
        raise SystemExit(f"Not a Git repo root: {repo}")

    raw_records: list[dict] = []
    with source.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception as e:
                raise SystemExit(f"Invalid JSON at source line {line_no}: {e}")
            if isinstance(obj, dict):
                raw_records.append(obj)

    meta = None
    for obj in raw_records:
        if obj.get("type") == "session_meta" and isinstance(obj.get("payload"), dict):
            meta = obj["payload"]
            break
    if not meta:
        raise SystemExit("No session_meta record found")

    session_id = meta.get("session_id") or meta.get("id")
    if not session_id:
        raise SystemExit("session_meta has no session_id/id")

    source_sha = sha256_file(source)
    stat = source.stat()

    model = None
    for obj in raw_records:
        if obj.get("type") == "turn_context":
            p = obj.get("payload")
            if isinstance(p, dict) and isinstance(p.get("model"), str):
                model = p["model"]
                break

    events: list[dict] = []
    call_names: dict[str, str] = {}
    redacted_total = 0
    skipped_images = 0
    skipped_encrypted_reasoning = 0
    max_reported_total_tokens = 0

    def emit(ts: str, role: str, **fields: Any) -> None:
        nonlocal redacted_total
        event = {
            "schema_version": SCHEMA_VERSION,
            "session_id": session_id,
            "team_id": args.team_id,
            "github_login": args.github_login,
            "tool": "codex",
            "ts": ts,
            "role": role,
            "seq": len(events),
        }
        if model and role == "assistant":
            event["model"] = model
        event.update(fields)

        counter = [0]
        event = redact_value(event, counter)
        if counter[0]:
            event["redacted_count"] = counter[0]
            redacted_total += counter[0]
        events.append(event)

    for obj in raw_records:
        ts = obj.get("timestamp") or meta.get("timestamp") or iso_now()
        payload = obj.get("payload")
        if not isinstance(payload, dict):
            continue
        ptype = payload.get("type")

        # Newer Codex rollout canonical conversational/tool records.
        if obj.get("type") == "response_item":
            if ptype == "message":
                role, role_meta = map_role(payload.get("role"))
                content = payload.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type")
                    if btype == "input_image":
                        skipped_images += 1
                        continue
                    text = block.get("text")
                    if isinstance(text, str) and text:
                        md = {
                            "source_record_type": "response_item",
                            "source_payload_type": "message",
                            "content_block_type": btype,
                            **role_meta,
                        }
                        emit(ts, role, text=text, metadata=md)

            elif ptype == "reasoning":
                summary_text = extract_reasoning_summary(payload.get("summary"))
                if summary_text:
                    emit(
                        ts,
                        "assistant",
                        thinking=summary_text,
                        metadata={
                            "source_record_type": "response_item",
                            "source_payload_type": "reasoning",
                            "reasoning_source": "plaintext_summary",
                        },
                    )
                elif payload.get("encrypted_content"):
                    skipped_encrypted_reasoning += 1

            elif ptype in ("custom_tool_call", "function_call"):
                call_id = payload.get("call_id") or payload.get("id")
                if not call_id:
                    continue
                if ptype == "function_call":
                    name = payload.get("name") or "unknown"
                    namespace = payload.get("namespace")
                    tool_name = f"{namespace}.{name}" if namespace else str(name)
                    tool_input = maybe_json(payload.get("arguments"))
                else:
                    tool_name = str(payload.get("name") or "unknown")
                    tool_input = maybe_json(payload.get("input"))

                call_names[str(call_id)] = tool_name
                emit(
                    ts,
                    "tool",
                    tool_name=tool_name,
                    tool_call_id=str(call_id),
                    input=tool_input,
                    output=None,
                    metadata={
                        "source_record_type": "response_item",
                        "source_payload_type": ptype,
                        "source_item_id": payload.get("id"),
                    },
                )

            elif ptype in ("custom_tool_call_output", "function_call_output"):
                call_id = payload.get("call_id") or payload.get("id")
                if not call_id:
                    continue
                tool_name = call_names.get(str(call_id), "<result>")
                emit(
                    ts,
                    "tool",
                    tool_name=tool_name,
                    tool_call_id=str(call_id),
                    input=None,
                    output=payload.get("output"),
                    metadata={
                        "source_record_type": "response_item",
                        "source_payload_type": ptype,
                        "source_item_id": payload.get("id"),
                    },
                )

        # Preserve token usage records without inventing chat text.
        if ptype == "token_count":
            info = payload.get("info")
            if not isinstance(info, dict):
                continue
            last = info.get("last_token_usage")
            total = info.get("total_token_usage")
            last = last if isinstance(last, dict) else {}
            total = total if isinstance(total, dict) else {}
            total_tokens = total.get("total_tokens")
            if isinstance(total_tokens, int):
                max_reported_total_tokens = max(max_reported_total_tokens, total_tokens)

            fields: dict[str, Any] = {
                "metadata": {
                    "source_record_type": obj.get("type"),
                    "source_payload_type": "token_count",
                    "total_token_usage": total,
                    "model_context_window": info.get("model_context_window"),
                }
            }
            if isinstance(last.get("input_tokens"), int):
                fields["tokens_in"] = last["input_tokens"]
            if isinstance(last.get("output_tokens"), int):
                fields["tokens_out"] = last["output_tokens"]
            emit(ts, "system", **fields)

    if not events:
        raise SystemExit("Conversion produced 0 events")

    started_at = events[0]["ts"]
    last_event_at = events[-1]["ts"]
    date_part = started_at[:10]

    member_dir = repo / "logs" / args.github_login
    out_dir = member_dir / date_part
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"codex__{session_id}.jsonl"

    with out_path.open("w", encoding="utf-8", newline="\n") as f:
        for ev in events:
            f.write(json.dumps(ev, ensure_ascii=False, separators=(",", ":")) + "\n")

    manifest_path = member_dir / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise SystemExit(f"Existing manifest is invalid JSON: {e}")
    else:
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "team_id": args.team_id,
            "github_login": args.github_login,
            "sessions": [],
        }

    manifest["schema_version"] = SCHEMA_VERSION
    manifest["team_id"] = args.team_id
    manifest["github_login"] = args.github_login
    manifest["generator"] = GENERATOR
    manifest["updated_at"] = iso_now()
    sessions = manifest.setdefault("sessions", [])

    entry = {
        "session_id": session_id,
        "tool": "codex",
        "started_at": started_at,
        "last_event_at": last_event_at,
        "event_count": len(events),
        "file_path": f"logs/{args.github_login}/{date_part}/codex__{session_id}.jsonl",
        # Schema has no dedicated manual-Codex-backfill enum; source was Codex CLI.
        # Keep collection_mode validator-compatible and state the post-hoc conversion explicitly.
        "collection_mode": "cli",
        "health": "degraded" if (skipped_images or skipped_encrypted_reasoning) else "ok",
        "model": model or "",
        "redacted_count_total": redacted_total,
        "source_integrity": {
            "main_sha256": source_sha,
            "main_size": stat.st_size,
            "main_mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            "captured_at": iso_now(),
        },
        "conversion_mode": "post-hoc-codex-rollout-response_item-v1",
        "source_cli_version": meta.get("cli_version"),
        "source_cwd": meta.get("cwd"),
        "original_record_count": len(raw_records),
        "skipped_input_image_blocks": skipped_images,
        "skipped_encrypted_reasoning_records": skipped_encrypted_reasoning,
        "max_reported_total_tokens": max_reported_total_tokens,
        "data_completeness_warning": (
            "Post-hoc transparent conversion from original Codex rollout because the "
            "contest collector did not parse response_item/event_msg. Encrypted reasoning "
            "was not decrypted or fabricated; image blocks were not embedded in the textual "
            "contest JSONL. Original rollout is retained unchanged and identified by SHA256."
        ),
    }

    existing = next((s for s in sessions if s.get("session_id") == session_id), None)
    if existing:
        existing.clear()
        existing.update(entry)
    else:
        sessions.append(entry)

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    provenance_dir = repo / "docs"
    provenance_dir.mkdir(parents=True, exist_ok=True)
    sha_path = provenance_dir / "codex_rollout_sha256.txt"
    line = f"{source_sha}  {source.name}\n"
    existing_lines = []
    if sha_path.exists():
        existing_lines = sha_path.read_text(encoding="utf-8").splitlines(True)
    if line not in existing_lines:
        with sha_path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(line)

    print("Conversion complete")
    print(f"source_session_id : {session_id}")
    print(f"source_sha256     : {source_sha}")
    print(f"source_records    : {len(raw_records)}")
    print(f"contest_events    : {len(events)}")
    print(f"redactions        : {redacted_total}")
    print(f"skipped_images    : {skipped_images}")
    print(f"skipped_encrypted_reasoning: {skipped_encrypted_reasoning}")
    print(f"max_reported_total_tokens  : {max_reported_total_tokens}")
    print(f"jsonl             : {out_path}")
    print(f"manifest          : {manifest_path}")
    print(f"sha256 list       : {sha_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
