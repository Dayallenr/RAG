"""Format an /ask response for a terminal demo.

Split out of ``scripts/demo.sh`` rather than inlined as ``python -c``: the
formatting is quoted shell inside quoted Python inside a shell script, and
the version that lived inline was unreadable enough to be a liability in a
repository whose selling point is that a reader can check the work.

Reads one JSON response on stdin. Invents nothing — every value printed is
read from the response body.
"""

from __future__ import annotations

import json
import sys
import textwrap
from typing import Any

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"

WRAP_WIDTH = 68


def _structured(response: dict[str, Any]) -> None:
    fact = response["structured_fact"]
    print(f"  route      {GREEN}{response['route']}{RESET}")
    for reason in response["routing_reasons"]:
        print(f"  {DIM}·{RESET} {reason}")
    print()
    print(f"  {BOLD}{response['answer']}{RESET}")
    print()
    print(f"  concept    {fact['concept']}  =  {fact['value']:,.0f} {fact['unit']}")
    print(f"  period     {fact['period_start']} .. {fact['period_end']}")
    print(f"  accession  {YELLOW}{fact['accession_number']}{RESET}")
    print(f"  source     {DIM}{fact['source_url']}{RESET}")
    print()
    print(
        f"  {GREEN}{response['latency_ms']} ms{RESET}  "
        f"{DIM}— retrieved 0 passages, called 0 models{RESET}"
    )


def _semantic(response: dict[str, Any]) -> None:
    print(f"  route      {GREEN}{response['route']}{RESET}")
    print(
        f"  {DIM}· no complete (concept, company, period) key "
        f"— falls back to search{RESET}"
    )
    print()
    for line in (response["answer"] or "").splitlines():
        for wrapped in textwrap.wrap(line, WRAP_WIDTH) or [""]:
            print("  " + wrapped)
    print()
    print(
        f"  {BOLD}citations{RESET}  "
        f"{DIM}(every [n] above resolves to a real filing){RESET}"
    )
    # Every citation, not the first few: the line above promises that each
    # [n] in the answer resolves to a real filing, and truncating the list
    # broke that promise on screen — the recorded answer cited [6] while the
    # block below stopped at [5]. Sorted because the pipeline returns them
    # in retrieval order, which reads as shuffled next to the numbered
    # markers in the prose.
    for citation in sorted(response["citations"], key=lambda c: c["number"]):
        print(
            f"   {YELLOW}[{citation['number']}]{RESET} "
            f"{citation['company']} {citation['filing_type']} "
            f"{citation['filing_date']}  "
            f"{DIM}{citation['section'][:38]}{RESET}"
        )
        print(f"       {DIM}{citation['source_url']}{RESET}")
    print()
    print(
        f"  {GREEN}{response['latency_ms']} ms{RESET}  "
        f"{DIM}— {len(response['passages'])} reranked passages, "
        f"1 model call{RESET}"
    )


def main() -> None:
    body = sys.stdin.read()
    try:
        response = json.loads(body)
    except json.JSONDecodeError:
        _unexpected(body)
        return
    # An /ask error (the hosted model 503s under load often enough to have
    # broken a recording) comes back as FastAPI's {"detail": ...}, with no
    # route. Print it rather than raising a KeyError over the top of it —
    # a demo that dies on a traceback is worse than one that says what
    # went wrong.
    if "route" not in response:
        _unexpected(body)
        return
    if response["route"] == "structured":
        _structured(response)
    else:
        _semantic(response)


def _unexpected(body: str) -> None:
    print(f"  {YELLOW}the API did not return an answer{RESET}")
    print(f"  {DIM}{body[:400]}{RESET}")
    sys.exit(1)


if __name__ == "__main__":
    main()
