import os
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
agent_dir = repo_root / 'app' / 'agents'
files = [
    'compliance.py', 'educator.py', 'market.py', 'orchestrator.py',
    'portfolio_coach.py', 'risk_profiler.py', 'strategy.py'
]

for fname in files:
    path = agent_dir / fname
    if not path.exists():
        print(f"MISSING: {fname}")
        continue
    lines = path.read_text(encoding='utf-8').splitlines()
    print(f"\n=== {fname} (total {len(lines)} lines) ===")
    for i, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith('def ') or stripped.startswith('class '):
            print(f"{i:4d}: {stripped}")
    # Also print top 400 lines with numbers for spot checking
    print('\n-- Snippet (first 200 lines) --')
    for i, line in enumerate(lines[:200], start=1):
        print(f"{i:4d}: {line}")
