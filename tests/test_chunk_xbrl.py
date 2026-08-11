from __future__ import annotations

from duediligence.ingest.chunk_xbrl import extract_structured_facts

# Shape verified against a real downloaded companyfacts.json, not guessed.
SYNTHETIC_COMPANYFACTS = {
    "facts": {
        "us-gaap": {
            "NetIncomeLoss": {
                "label": "Net Income (Loss) Attributable to Parent",
                "units": {
                    "USD": [
                        {
                            "start": "2023-01-01", "end": "2023-12-31", "val": 349000000,
                            "accn": "0000887343-24-000089", "fy": 2023, "fp": "FY",
                            "form": "10-K", "filed": "2024-02-27", "frame": "CY2023",
                        },
                        {
                            "end": "2023-12-31", "val": 999999,  # instant-style, no "start"
                            "accn": "0000887343-24-000089", "fy": 2023, "fp": "FY",
                            "form": "10-K", "filed": "2024-02-27",
                            # no "frame" — exercises the fy/fp fallback
                        },
                    ]
                },
            },
            "Assets": {
                "label": "Assets",
                "units": {
                    "USD": [
                        {
                            "end": "2023-12-31", "val": 52000000000,
                            "accn": "0000887343-24-000089", "fy": 2023, "fp": "FY",
                            "form": "10-K", "filed": "2024-02-27", "frame": "CY2023Q4I",
                        },
                    ]
                },
            },
            # A real extension-taxonomy-style concept not in BANK_CONCEPTS —
            # must not show up in the results.
            "ColbSomeCustomExtensionConcept": {
                "label": "Custom", "units": {"USD": [{"end": "2023-12-31", "val": 1, "accn": "x"}]},
            },
        }
    }
}


def test_extracts_only_curated_concepts():
    results = extract_structured_facts(SYNTHETIC_COMPANYFACTS, company="COLB", cik="887343")
    concepts = {f.concept for f in results}
    assert concepts == {"NetIncomeLoss", "Assets"}
    assert "ColbSomeCustomExtensionConcept" not in concepts


def test_duration_vs_instant_period_type_is_correct():
    results = extract_structured_facts(SYNTHETIC_COMPANYFACTS, company="COLB", cik="887343")
    net_income = [f for f in results if f.concept == "NetIncomeLoss"]
    duration_fact = next(f for f in net_income if f.value == 349000000.0)
    instant_fact = next(f for f in net_income if f.value == 999999.0)
    assert duration_fact.period_type == "duration"
    assert instant_fact.period_type == "instant"


def test_fiscal_period_uses_frame_when_present():
    results = extract_structured_facts(SYNTHETIC_COMPANYFACTS, company="COLB", cik="887343")
    assets_fact = next(f for f in results if f.concept == "Assets")
    assert assets_fact.fiscal_period == "CY2023Q4I"


def test_fiscal_period_falls_back_to_fy_fp_when_frame_missing():
    results = extract_structured_facts(SYNTHETIC_COMPANYFACTS, company="COLB", cik="887343")
    net_income = [f for f in results if f.concept == "NetIncomeLoss"]
    no_frame_fact = next(f for f in net_income if f.value == 999999.0)
    assert no_frame_fact.fiscal_period == "FY2023FY"


def test_source_url_is_a_real_resolvable_sec_pattern():
    results = extract_structured_facts(SYNTHETIC_COMPANYFACTS, company="COLB", cik="887343")
    fact = results[0]
    assert fact.source_url == (
        "https://www.sec.gov/Archives/edgar/data/887343/"
        "000088734324000089/0000887343-24-000089-index.htm"
    )


def test_missing_concept_is_skipped_not_an_error():
    payload = {"facts": {"us-gaap": {}}}
    results = extract_structured_facts(payload, company="COLB", cik="887343")
    assert results == []


def test_fact_id_distinguishes_same_period_reported_in_different_filings():
    # The same (concept, period) legitimately appears in multiple filings —
    # each must remain a distinct fact keyed by its own accession number.
    payload = {
        "facts": {
            "us-gaap": {
                "NetIncomeLoss": {
                    "units": {
                        "USD": [
                            {"start": "2023-01-01", "end": "2023-12-31", "val": 349000000,
                             "accn": "0000887343-24-000089", "frame": "CY2023"},
                            {"start": "2023-01-01", "end": "2023-12-31", "val": 349000000,
                             "accn": "0000887343-25-000050", "frame": "CY2023"},
                        ]
                    }
                }
            }
        }
    }
    results = extract_structured_facts(payload, company="COLB", cik="887343")
    assert len(results) == 2
    assert results[0].fact_id != results[1].fact_id
