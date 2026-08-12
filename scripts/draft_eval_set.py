"""
Emit data/eval_set.jsonl — the retrieval eval's (question, relevant_chunk_ids)
ground truth.

Every question below was written by reading the actual text of a sampled
corpus chunk (see ``scripts/sample_eval_candidates.py``, which produced the
stratified candidate pool) and asking something that chunk specifically
answers. Questions are keyed to candidates by pool index, and the chunk_ids
and filing metadata are looked up from the candidate file rather than
transcribed by hand — a mistyped character in a 16-hex id would silently
turn one eval entry into an unanswerable query and quietly depress every
metric.

**Known limitation, stated rather than hidden.** Ground truth is drawn from
a 163-chunk sampled pool, not from exhaustively judging all 38,839 chunks
against all 100 questions. Another chunk elsewhere in the corpus may also
answer a given question and would be scored as a miss. Every metric this
produces is therefore a **lower bound** on true retrieval quality. That is
acceptable for the purpose — Phase 5 measures hybrid search and reranking
against the same fixed eval set, so the *delta* is sound even where the
absolute level is pessimistic — but it must not be reported as an unqualified
absolute.

``verified: false`` on every entry until a human confirms it. The eval
report counts and prints how many entries are human-verified, so a
self-graded eval set can't quietly be presented as a curated one.

Usage:
    python scripts/draft_eval_set.py --candidates <path> --out data/eval_set.jsonl
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# (candidate_index_or_tuple, question, question_type)
#
# A tuple of indices means several sampled chunks genuinely answer the same
# question — nearly always because a filing's section chunk and one of its
# child paragraph chunks carry the same passage. Labeling only one of them
# would penalize a retriever for returning the other, which is not an error.
QUESTIONS: list[tuple[int | tuple[int, ...], str, str]] = [
    # ---- Columbia Banking System (COLB) ----
    (0, "In Columbia Banking System's total return performance chart through 2019, which index overtook Columbia by the end of the period?", "chart"),
    (3, "By how much did Columbia's total liabilities increase during 2019, and what drove the increase?", "numeric"),
    (4, "What were Columbia's nonaccrual loans at December 31, 2019 and 2018?", "numeric"),
    (7, "What is the date of the merger agreement between Columbia Banking System and Umpqua Holdings?", "table"),
    (8, "What net income did Columbia report for 2019 in its consolidated statement of changes in shareholders' equity?", "table"),
    (9, "How did PPP loans affect Columbia's deposit balances in 2020?", "narrative"),
    (10, "What drove the increase in Columbia's noninterest income for the first six months of 2020?", "numeric"),
    (13, "What was Columbia's net income for the three months ended September 30, 2021?", "table"),
    (14, "What valuation technique and unobservable inputs does Columbia use to value residential mortgage servicing rights?", "table"),
    (15, "By how much was the number of authorized Columbia common shares increased in connection with the Umpqua merger?", "narrative"),
    (16, "What compensation arrangement did Columbia enter into with Aaron Deer when the Umpqua merger closed?", "narrative"),
    (17, "Who became Executive Chair of Columbia's board after the Umpqua merger, and what was his prior role?", "narrative"),
    (18, "What quarterly cash dividend did Columbia declare in February 2024, and when was it payable?", "numeric"),
    (19, "What quarterly cash dividend did Columbia announce in November 2023?", "numeric"),
    (20, "How many votes for did Cort O'Haver receive at Columbia's 2024 annual meeting?", "table"),
    (21, "How did Columbia's and Umpqua's tangible common equity to tangible assets ratios compare in the merger's selected-companies analysis?", "table"),
    (22, "What does Columbia's pay-versus-performance chart show about compensation actually paid versus total shareholder return for 2020 through 2022?", "chart"),
    (23, "How did Columbia's stock perform against the KBW Nasdaq Regional Banking Index between 2017 and 2022?", "chart"),
    (25, "What restricted stock awards did Mr. McDonald hold, and on what schedule did they vest?", "narrative"),
    (26, "How does Columbia calculate ROTCE Performance for PSU vesting, and what example does the proxy give?", "narrative"),
    (28, "What was the racial and gender composition of Columbia's workforce reported in the 2021 proxy statement?", "table"),
    (29, "What percentage of Columbia's workforce identified as White in the 2022 proxy statement?", "table"),
    (30, "What discount rates and terminal multiples did Raymond James use in its discounted cash flow analysis of Bank of Commerce Holdings?", "narrative"),
    (31, "What were Bank of Commerce Holdings' total assets, net loans, and total deposits at March 31, 2021?", "numeric"),
    (33, "Under which state's business corporation act are Columbia's directors and officers indemnified?", "narrative"),
    (34, "What was the pro forma combined net loss of Umpqua and Columbia for the year ended December 31, 2020?", "table"),
    (35, "What were the implied transaction metrics in the summary transaction multiples analysis of Columbia's S-4?", "table"),
    # ---- Glacier Bancorp (GBCI) ----
    (38, "What was the liability related to Glacier's non-funded deferred compensation plans at December 31, 2023 and 2022?", "numeric"),
    (39, "What were Glacier's interest rate lock commitments at December 31, 2020 and 2019?", "numeric"),
    (40, "How many shareholders of record did Glacier Bancorp have as of December 31, 2020?", "numeric"),
    (42, "What subordinated debentures did Glacier owe to trust subsidiaries, and at what rates?", "table"),
    (43, "What was Glacier's interest income in 2019 and its five-year compounded annual growth rate?", "table"),
    (44, "What did the Paycheck Protection Program and Health Care Enhancement Act provide in additional PPP funding?", "narrative"),
    (50, "Who did Glacier appoint as Chief Compliance Officer in 2024, and what role was he expected to take on?", "narrative"),
    (51, "What was the aggregate value of the merger consideration in Glacier's May 2021 merger agreement?", "numeric"),
    (52, "What amendment to Glacier's articles of incorporation was voted on at the 2022 annual meeting?", "narrative"),
    (54, "How many votes for did Randall Chesler receive at Glacier's 2022 annual meeting?", "table"),
    (55, "How many votes were withheld for James M. English at Glacier's 2020 annual meeting?", "table"),
    (56, "At what percentage of target were Glacier's overall 2023 short-term incentive plan performance goals achieved?", "numeric"),
    (57, "What return on tangible equity did Glacier use for its 2021 401(k) discretionary contribution, and what was the contribution rate?", "numeric"),
    (58, "What annual incentive did Glacier's President and CEO actually earn in the year covered by the 2020 proxy?", "table"),
    (59, "How many restricted stock units were granted to Randall Chesler according to Glacier's 2024 proxy?", "table"),
    (63, "Under which state's business corporation act are Glacier's directors and officers indemnified?", "narrative"),
    (64, "What were Altabancorp's total assets at acquisition, and when did Glacier's acquisition of it close?", "table"),
    (65, "What per-share values did Glacier's discounted cash flow sensitivity analysis produce at a 10% discount rate?", "table"),
    # ---- SouthState (SSB) ----
    (68, "What were SouthState's total deposits at December 31, 2021, and how much did they grow during the year?", "numeric"),
    (69, "How much did SouthState's deposits increase during 2020, and what drove the increase?", "numeric"),
    (70, "How many securities remained available for future issuance under SouthState's equity compensation plans at December 31, 2021?", "numeric"),
    (72, "What were SouthState's total loans by amortized cost basis at December 31, 2020?", "table"),
    ((74, 77), "How many shares had SouthState repurchased under its 2021 Stock Repurchase Plan through June 30, 2022, and at what average price?", "numeric"),
    (75, "How many shares had SouthState repurchased under the 2021 Stock Repurchase Plan through March 31, 2022?", "numeric"),
    (76, "How many shares remained available under SouthState's New Repurchase Program as of September 30, 2020?", "narrative"),
    (81, "What role did Ms. Cooper hold before joining the Atlanta Committee for Progress?", "narrative"),
    (82, "What adjustment to the tangible book value growth metric did SouthState's Compensation Committee approve in December 2022?", "narrative"),
    (83, "When did South State and CenterState enter into their merger agreement?", "narrative"),
    (84, "What dividend and share repurchase authorization did SouthState announce in January 2021?", "numeric"),
    (86, "When did SouthState enter into a merger agreement with Independent Bank Group (IBTX)?", "table"),
    (87, "Who was appointed SouthState's President in connection with the CenterState merger, and what was his prior role?", "narrative"),
    (88, "What restricted stock unit awards did SouthState's non-employee directors receive in 2023, and at what value did they vest?", "narrative"),
    (89, "What was SouthState's combined-business-basis total adjusted revenue for full-year 2020?", "table"),
    (90, "What were John Corbett's annual incentive and long-term incentive opportunity levels as a percentage of base salary?", "table"),
    (93, "Under which state's law and which bylaw provision are SouthState's directors and officers indemnified?", "narrative"),
    (95, "How did South State's and CenterState's stock price to tangible book value per share compare in the merger analysis?", "table"),
    (96, "What per-share values did South State's sensitivity analysis produce at a 13.0x multiple and no estimate variance?", "table"),
    # ---- Umpqua Holdings (UMPQ) ----
    (99, "What economic forecast and macroeconomic variables did Umpqua use to estimate its allowance for credit losses at December 31, 2021?", "narrative"),
    (100, "What did Umpqua's net cash provided by financing activities consist of during 2019?", "numeric"),
    (101, "How many shareholders of record did Umpqua have at December 31, 2020, and on what exchange did its stock trade?", "numeric"),
    (103, "What was Cort O'Haver's total compensation in 2021?", "table"),
    (104, "How did Umpqua's cumulative total return compare with the NASDAQ U.S. index from 2014 through 2019?", "table"),
    (107, "What were Umpqua's net cash flows from financing activities for the nine months ended September 30, 2022?", "numeric"),
    (108, "What was Umpqua's provision for credit losses for the three months ended June 30, 2022?", "numeric"),
    (111, "What unobservable inputs did Umpqua use to value residential mortgage servicing rights and interest rate lock commitments?", "table"),
    (112, "What was Umpqua's allowance for credit losses on loans and leases at March 31, 2020?", "table"),
    (114, "Why did Umpqua receive a deficiency notice from Nasdaq in January 2023?", "narrative"),
    (115, "What share repurchase program did Umpqua announce in July 2021?", "numeric"),
    (117, "Which peer company had the highest 2022 estimated price-to-earnings multiple in Umpqua's comparable company analysis?", "table"),
    (118, "How many votes for did Maria Pope receive at Umpqua's 2020 annual meeting?", "table"),
    (119, "How did Umpqua's total return compare with the KBW Regional Bank Index between 2014 and 2019?", "chart"),
    (120, "Over which time horizons did the KRX index outperform Umpqua in the proxy's total return bar chart?", "chart"),
    (127, "What payment related to position elimination appears in Umpqua's executive perquisites table?", "table"),
    (128, "What percentage of Cort O'Haver's total annual compensation was at risk rather than fixed?", "table"),
    # ---- WesBanco (WSBC) ----
    (131, "What were Wesbanco's total assets and total portfolio loans at December 31, 2022?", "numeric"),
    (132, "How much did Wesbanco's interest expense increase in 2022, and why?", "numeric"),
    (134, "How many banking offices did Wesbanco operate at December 31, 2023, and how many were owned versus leased?", "numeric"),
    (135, "What was the weighted average exercise price of Wesbanco's outstanding stock options?", "table"),
    (136, "What was the percentage change in Wesbanco's economic value of equity for a +400 basis point rate shock at December 31, 2019?", "table"),
    ((137, 138), "What are Wesbanco's policy limits on the reduction in net interest income from interest rate changes?", "narrative"),
    (139, "How many shares remained for repurchase under Wesbanco's stock repurchase plan as of March 31, 2023?", "numeric"),
    (140, "How many shares remained for repurchase under Wesbanco's stock repurchase plan as of June 30, 2024?", "numeric"),
    (141, "What was the percentage change in Wesbanco's net interest income for a +300 basis point shock at September 30, 2022?", "table"),
    (142, "What common dividends per share did Wesbanco declare for the nine months ended September 30, 2022?", "table"),
    (145, "How did Wesbanco change the target annual cash incentive award opportunities for 2021?", "narrative"),
    (147, "What line of credit did Wesbanco renew with PNC Bank in August 2022, and for how much?", "narrative"),
    (148, "When did Wesbanco hold its conference call to discuss second quarter 2024 results?", "narrative"),
    (151, "Why were Wesbanco's 2021 TSRP grants made contingent on stockholder approval?", "narrative"),
    (153, "Which firm did Wesbanco's Audit Committee select as its independent registered public accounting firm for fiscal 2020?", "narrative"),
    (155, "What was Wesbanco's core earnings per share in 2023?", "table"),
    (156, "What was the compensation actually paid to Wesbanco's PEO Jackson in 2023?", "table"),
    (160, "Under which state's business corporation act are Wesbanco's directors and officers indemnified?", "narrative"),
    (161, "What net income was projected for 2025 in Wesbanco's S-4 financial projections?", "table"),
    (162, "What per-share value did Wesbanco's sensitivity analysis produce at an 11.0x multiple with no estimate variance?", "table"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True, help="candidates JSONL from sample_eval_candidates.py")
    parser.add_argument("--out", default="data/eval_set.jsonl")
    args = parser.parse_args()

    pool = [json.loads(line) for line in Path(args.candidates).read_text().splitlines() if line.strip()]

    entries = []
    for position, (indices, question, question_type) in enumerate(QUESTIONS, start=1):
        indices = (indices,) if isinstance(indices, int) else indices
        chunks = [pool[i] for i in indices]
        primary = chunks[0]
        entries.append(
            {
                "eval_id": f"r{position:03d}",
                "question": question,
                "relevant_chunk_ids": [c["chunk_id"] for c in chunks],
                "question_type": question_type,
                "company": primary["company"],
                "filing_type": primary["filing_type"],
                "filing_date": primary["filing_date"],
                "chunk_type": primary["chunk_type"],
                "source_url": primary["source_url"],
                "drafted_by": "claude",
                "verified": False,
                "verification_note": "",
            }
        )

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(json.dumps(e) for e in entries) + "\n")

    by_company: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for entry in entries:
        by_company[entry["company"]] = by_company.get(entry["company"], 0) + 1
        by_type[entry["question_type"]] = by_type.get(entry["question_type"], 0) + 1

    print(f"wrote {len(entries)} eval entries to {output}")
    print(f"  by company: {by_company}")
    print(f"  by type:    {by_type}")
    print(f"  multi-chunk ground truth: {sum(1 for e in entries if len(e['relevant_chunk_ids']) > 1)}")


if __name__ == "__main__":
    main()
