from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

from duediligence.config import CompanyConfig, EdgarConfig
from duediligence.ingest.edgar_client import EdgarClient, _RateLimiter

CONFIG = EdgarConfig(
    user_agent="Test test@example.com",
    data_base_url="https://data.sec.gov",
    archives_base_url="https://www.sec.gov/Archives/edgar/data",
    ticker_lookup_url="https://www.sec.gov/files/company_tickers.json",
    rate_limit_per_second=1000,  # fast for tests
)


def _mock_response(payload):
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_rate_limiter_enforces_minimum_interval():
    limiter = _RateLimiter(per_second=100)  # 10ms interval
    start = time.monotonic()
    limiter.wait()
    limiter.wait()
    limiter.wait()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.02  # at least 2 intervals waited


def test_cik_for_uses_explicit_override_without_hitting_ticker_lookup():
    client = EdgarClient(CONFIG)
    company = CompanyConfig(ticker="UMPQ", name="Umpqua Holdings", cik="1077771")

    with patch.object(client, "_get") as mock_get:
        cik = client.cik_for(company)
        assert cik == "0001077771"
        mock_get.assert_not_called()  # never fetched the ticker lookup file


def test_cik_for_falls_back_to_ticker_resolution_when_no_override():
    client = EdgarClient(CONFIG)
    company = CompanyConfig(ticker="COLB", name="Columbia Banking System")

    lookup_payload = {"0": {"cik_str": 887343, "ticker": "COLB", "title": "Columbia Banking System"}}
    with patch.object(client, "_get", return_value=_mock_response(lookup_payload)) as mock_get:
        cik = client.cik_for(company)
        assert cik == "0000887343"
        mock_get.assert_called_once()


def test_resolve_cik_raises_for_unknown_ticker():
    client = EdgarClient(CONFIG)
    lookup_payload = {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple"}}
    with patch.object(client, "_get", return_value=_mock_response(lookup_payload)):
        try:
            client.resolve_cik("NOTREAL")
            raise AssertionError("expected KeyError")
        except KeyError:
            pass


def test_list_filings_filters_by_type_and_date_and_builds_correct_url():
    client = EdgarClient(CONFIG)
    company = CompanyConfig(ticker="COLB", name="Columbia Banking System", cik="887343")

    submissions_payload = {
        "filings": {
            "recent": {
                "form": ["10-K", "8-K", "10-Q", "10-K"],
                "filingDate": ["2024-02-27", "2024-03-05", "2019-08-06", "2018-02-27"],
                "accessionNumber": [
                    "0000887343-24-000089", "0000887343-24-000112",
                    "0000887343-19-000155", "0000887343-18-000070",
                ],
                "primaryDocument": ["colb-10k.htm", "colb-8k.htm", "colb-10q.htm", "colb-10k-old.htm"],
            }
        }
    }
    with patch.object(client, "_get", return_value=_mock_response(submissions_payload)):
        filings = client.list_filings(
            company, filing_types=["10-K"], start_date="2020-01-01", end_date="2024-12-31"
        )

    # Only the 2024 10-K survives: the 8-K is the wrong type, the 2019 10-Q
    # is both the wrong type and outside the date range, and the 2018 10-K
    # is the right type but outside the date range.
    assert len(filings) == 1
    filing = filings[0]
    assert filing.accession_number == "0000887343-24-000089"
    assert filing.document_url == (
        "https://www.sec.gov/Archives/edgar/data/887343/000088734324000089/colb-10k.htm"
    )


def test_download_filing_is_idempotent(tmp_path):
    from duediligence.ingest.edgar_client import FilingMetadata

    client = EdgarClient(CONFIG)
    filing = FilingMetadata(
        company="COLB", cik="0000887343", accession_number="0000887343-24-000089",
        filing_type="10-K", filing_date="2024-02-27", primary_document="colb-10k.htm",
        document_url="https://www.sec.gov/Archives/edgar/data/887343/000088734324000089/colb-10k.htm",
    )

    call_count = 0

    def fake_get(url):
        nonlocal call_count
        call_count += 1
        response = MagicMock()
        response.content = b"<html>fake filing</html>"
        response.raise_for_status.return_value = None
        return response

    with patch.object(client, "_get", side_effect=fake_get):
        path1 = client.download_filing(filing, tmp_path)
        path2 = client.download_filing(filing, tmp_path)  # should not re-fetch

    assert path1 == path2
    assert call_count == 1
    assert path1.read_bytes() == b"<html>fake filing</html>"


def test_download_bytes_returns_raw_content_through_the_rate_limited_session():
    client = EdgarClient(CONFIG)
    response = _mock_response({})
    response.content = b"\xff\xd8\xff\xe0fakejpegbytes"
    with patch.object(client, "_get", return_value=response) as mock_get:
        content = client.download_bytes("https://www.sec.gov/Archives/edgar/data/887343/chart01.jpg")
        assert content == b"\xff\xd8\xff\xe0fakejpegbytes"
        mock_get.assert_called_once_with("https://www.sec.gov/Archives/edgar/data/887343/chart01.jpg")
