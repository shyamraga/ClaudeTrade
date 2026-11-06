"""
Async wrapper that runs a trading skill (Python subprocess) and streams
its stdout line-by-line.  All skills share this interface:

    result = await run_skill(skill_path, args, cwd=trader_dir)
    # result.stdout  — full captured output
    # result.returncode  — 0 = found something / passed, 1 = nothing / blocked

Broadcasting live output over WebSocket is handled by the caller.
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SkillResult:
    returncode: int
    stdout: str
    stderr: str
    args: list[str] = field(default_factory=list)


async def run_skill(
    skill_path: Path,
    args: list[str],
    cwd: Path | None = None,
    env_extra: dict[str, str] | None = None,
    timeout: float = 300.0,
    line_callback=None,          # async callable(line: str) for live streaming
) -> SkillResult:
    """Run a skill subprocess and return its result.

    Args:
        skill_path: Absolute path to the skill .py file.
        args: CLI arguments (e.g. ["daily", "--symbols", "TSLA,NVDA"]).
        cwd: Working directory — should be the trader/ folder so relative
             file paths inside the skill resolve correctly.
        env_extra: Extra environment variables to inject (e.g. SEC_USER_AGENT).
        timeout: Hard timeout in seconds before the process is killed.
        line_callback: If provided, called with each stdout line as it arrives.
    """
    import os

    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)

    cmd = [sys.executable, "-I", str(skill_path), *args]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(cwd) if cwd else None,
        env=env,
    )

    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    async def read_stream(stream, lines, callback=None):
        while True:
            line_bytes = await stream.readline()
            if not line_bytes:
                break
            line = line_bytes.decode(errors="replace").rstrip("\n")
            lines.append(line)
            if callback:
                await callback(line)

    try:
        await asyncio.wait_for(
            asyncio.gather(
                read_stream(proc.stdout, stdout_lines, line_callback),
                read_stream(proc.stderr, stderr_lines),
            ),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        stderr_lines.append(f"[skill_runner] Killed after {timeout}s timeout")

    returncode = await proc.wait()

    return SkillResult(
        returncode=returncode,
        stdout="\n".join(stdout_lines),
        stderr="\n".join(stderr_lines),
        args=args,
    )
