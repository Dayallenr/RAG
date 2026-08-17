# Co-validity review

Each question below already has a **correct** label. The question here is
different: does any *other* chunk answer it as well? Every co-valid chunk left
unlabelled is scored as a retrieval miss, which is what currently depresses the
reported recall.

**How to use this:** tick `[x]` for every candidate that genuinely also answers
the question. Leave it unticked if it is off-topic, or if it merely mentions the
subject without answering. When done, run:

```
python scripts/apply_covalidity_review.py
```

Ticking nothing for a question is a valid outcome — it means the single existing
label really is the only chunk that answers it.

---

### `r001` — In Columbia Banking System's total return performance chart through 2019, which index overtook Columbia by the end of the period?

**Already labelled** `59a1307879d0d11a` — COLB · 10-K · 2020-02-27 · chart_description  
> This line chart titled "Total Return Performance" plots cumulative index values across annual periods ending from December 31, 2014, to December 31, 2019. It compares the total returns of Columbia Banking System, Inc. against the NASDAQ Composite and the KBW Regional Banking Index. All three series start at a baseline value of 100 and show an overall upward trend over the five-year span, with Columbia Banking System …

Also answers the question?

- [ ] `775105dbe0a986fc` — rank 1 · COLB · DEF 14A · 2023-04-06 · chart_description  
      > This is a line chart titled "Total Return Performance" comparing the stock performance of Columbia Banking System, Inc. against the KBW Nasdaq Regional Banking Index. The horizontal axis covers an annual timeframe from December 31, 2017, to December 31, 2022, with the vertical axis representing the Index Value starting from a base of 100. Both series track closely together from late 2017 through 2020; after 2020, the …
- [ ] `33b4b9d35495b919` — rank 2 · COLB · 10-K · 2021-02-26 · table  
      > Index | Period Ending Index | 12/31/2015 | 12/31/2016 | 12/31/2017 | 12/31/2018 | 12/31/2019 | 12/31/2020 Columbia Banking System, Inc. | 100.00 | 144.57 | 143.65 | 123.46 | 143.71 | 132.56 NASDAQ Composite | 100.00 | 108.87 | 141.13 | 137.12 | 187.44 | 271.64 KBW Regional Banking Index | 100.00 | 139.02 | 141.45 | 116.70 | 144.49 | 131.91
- [ ] `a111d4ceba34d555` — rank 3 · COLB · 10-K · 2020-02-27 · table  
      > Index | Period Ending Index | 12/31/2014 | 12/31/2015 | 12/31/2016 | 12/31/2017 | 12/31/2018 | 12/31/2019 Columbia Banking System, Inc. | 100.00 | 122.92 | 177.71 | 176.58 | 151.76 | 176.65 NASDAQ Composite | 100.00 | 106.96 | 116.45 | 150.96 | 146.67 | 200.49 KBW Regional Banking Index | 100.00 | 105.91 | 147.24 | 149.82 | 123.60 | 153.03
- [ ] `3868ec6292f49954` — rank 4 · COLB · 10-K · 2023-02-24 · table  
      > Index | Period Ending Index | 12/31/2017 | 12/31/2018 | 12/31/2019 | 12/31/2020 | 12/31/2021 | 12/31/2022 Columbia Banking System, Inc. | 100.00 | 85.96 | 100.06 | 92.43 | 86.66 | 82.97 NASDAQ Composite | 100.00 | 97.16 | 132.81 | 192.47 | 235.15 | 158.65 KBW Regional Banking Index | 100.00 | 82.50 | 102.15 | 93.25 | 127.42 | 118.59
- [ ] `cbcd8ffb872443a5` — rank 5 · COLB · 10-K · 2022-02-25 · table  
      > Index | Period Ending Index | 12/31/2016 | 12/31/2017 | 12/31/2018 | 12/31/2019 | 12/31/2020 | 12/31/2021 Columbia Banking System, Inc. | 100.00 | 99.35 | 85.41 | 99.41 | 91.83 | 86.10 NASDAQ Composite | 100.00 | 129.64 | 125.96 | 172.18 | 249.51 | 304.85 KBW Regional Banking Index | 100.00 | 101.75 | 83.95 | 103.94 | 94.89 | 129.65
- [ ] `6140e060ab3d9fee` — rank 6 · COLB · 10-K · 2022-02-25 · paragraph · Item 5. MARKET FOR REGISTRANT’S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES  
      > The following graph shows a five-year comparison of the total return to shareholders of Columbia’s common stock, the NASDAQ Composite Index (which is a broad nationally recognized index of stock performance by companies listed on the Nasdaq Stock Market) and the KBW Regional Banking Index (comprised of 50 banks and bank holding companies headquartered throughout the country, including Columbia).
- [ ] `6648380cf7721c35` — rank 7 · COLB · 10-K · 2021-02-26 · paragraph · Item 5. MARKET FOR REGISTRANT’S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES  
      > The following graph shows a five-year comparison of the total return to shareholders of Columbia’s common stock, the NASDAQ Composite Index (which is a broad nationally recognized index of stock performance by companies listed on the Nasdaq Stock Market) and the KBW Regional Banking Index (comprised of 50 banks and bank holding companies headquartered throughout the country, including Columbia).
- [ ] `cbe596d9c73b219d` — rank 8 · COLB · 10-K · 2020-02-27 · paragraph · Item 4. MINE SAFETY DISCLOSURES  
      > The following graph shows a five-year comparison of the total return to shareholders of Columbia’s common stock, the NASDAQ Composite Index (which is a broad nationally recognized index of stock performance by companies listed on the Nasdaq Stock Market) and the KBW Regional Banking Index (comprised of 50 banks and bank holding companies headquartered throughout the country, including Columbia).

---

### `r002` — By how much did Columbia's total liabilities increase during 2019, and what drove the increase?

**Already labelled** `ea09c398f64fcce7` — COLB · 10-K · 2020-02-27 · paragraph · Item 6. SELECTED FINANCIAL DATA  
> Liabilities increased $858.1 million, or 8% to $11.92 billion due to increases in FHLB advances, deposits, the adoption of ASU 2016-02, Leases and increases in interest rate swap derivatives during the year. FHLB advances increased $553.9 million to $953.5 million and deposit balances increased $226.6 million to $10.68 billion to supplement the growth in our loan and securities portfolios. Other liabilities increased …

Also answers the question?

- [ ] `3d9ffe26448bf9a9` — rank 1 · COLB · 10-Q · 2020-07-31 · paragraph · Item 1. FINANCIAL STATEMENTS  
      > Total assets were $15.92 billion at June 30, 2020, an increase of $1.84 billion from December 31, 2019. Cash and cash equivalents increased $850.0 million. Loans increased $1.03 billion during the first six months of 2020, which was primarily the result of new loan production, supplemented by PPP loans, partially offset by payments. Debt securities available for sale were $3.69 billion at June 30, 2020, a decrease of …
- [ ] `eee8c6d89c12e52f` — rank 2 · COLB · 10-Q · 2020-05-08 · paragraph · Item 1. FINANCIAL STATEMENTS  
      > Total assets were $14.04 billion at March 31, 2020, a decrease of $41.0 million from December 31, 2019. Cash and cash equivalents decreased $31.9 million. Loans increased $189.9 million during the first quarter of 2020, which was primarily the result of new loan production and increased seasonal line utilization, partially offset by payments. Debt securities available for sale were $3.55 billion at March 31, 2020, a …
- [ ] `a287ca0d3248e0ff` — rank 3 · COLB · 10-K · 2022-02-25 · paragraph · Item 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Liabilities increased $4.12 billion, or 29% to $18.36 billion due to increases in total deposits partially offset by decreases in subordinated debentures. Total deposits increased $4.14 billion. Total shareholders’ equity increased $241.1 million to $2.59 billion.
- [ ] `0083e835f61bb126` — rank 4 · COLB · 10-K · 2021-02-26 · paragraph · Item 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Our total assets increased 18% to $16.58 billion at December 31, 2020 from $14.08 billion at December 31, 2019. The increase in total assets was driven by increases in debt securities available for sale, loans and cash and cash equivalents. Our available for sale debt securities portfolio increased $1.46 billion as a result of purchases of securities throughout the year to utilize our excess liquidity. The loan portf …
- [ ] `9604f291a93faa25` — rank 5 · UMPQ · 10-K · 2020-02-28 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > The net interest margin (net interest income as a percentage of average interest-earning assets) on a fully tax equivalent basis was 3.71% for 2019, a decrease of 33 basis points compared to 2018. The decrease in the net interest margin primarily resulted from an increase in the cost of interest-bearing liabilities and lower average yields on the securities portfolio, which was partially offset by higher average bala …
- [ ] `505192cf1ca17c75` — rank 6 · SSB · 10-K · 2020-02-21 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > During 2019, our total investment securities increased $462.5 million, or 30.0%, from December 31, 2018, as a result of our purchases of $979.1 million in investment securities as well as improvements in the market value of the portfolio of $38.9 million, partially offset by maturities, calls and paydowns of investment securities totaling $308.1 million and sales totaling $240.1 million during 2019. Net amortization …
- [ ] `df323e9ad52c9f04` — rank 7 · COLB · 10-K · 2021-02-26 · paragraph · Item 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Liabilities increased $2.32 billion, or 19% to $14.24 billion due to increases in total deposits partially offset by decreases in FHLB advances. Total deposits increased $3.19 billion primarily as a result of COVID-19 related events such as the PPP loan recipients depositing their funds into their deposit accounts at the Bank, stimulus funds being distributed by the federal government and reduced expenditures by cons …
- [ ] `51c6b73004a142ac` — rank 8 · COLB · 10-K · 2021-02-26 · paragraph · Item 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Taxable-equivalent net interest income totaled $501.8 million in 2019, compared with $486.7 million for 2018. The increase in net interest income during 2019 resulted from the increase in the size of the loan and securities portfolios as well as the increase in yield on the loan portfolio. The increase in net interest income was partially offset by higher interest rates paid on interest-bearing deposits combined with …

---

### `r003` — What were Columbia's nonaccrual loans at December 31, 2019 and 2018?

**Already labelled** `be715618af2bf86d` — COLB · 10-K · 2020-02-27 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
> Nonaccrual loans totaled $33.1 million and $54.8 million at December 31, 2019 and 2018, respectively. The amount of interest income foregone as a result of these loans being placed on nonaccrual status totaled $2.0 million for 2019, $3.6 million for 2018 and $2.4 million for 2017. There were no loans 90 days past due and still accruing interest as of December 31, 2019 and 2018. At December 31, 2019 and 2018, there we …

Also answers the question?

- [ ] `f13d0ce23c6cded6` — rank 1 · WSBC · 10-K · 2020-02-28 · paragraph  
      > Non-accrual loans increased $14.2 million or 46.3% from December 31, 2018 to December 31, 2019 primarily from one loan in the manufacturing industry. Approximately $1.4 million or 3.2% of total non-accrual loans at December 31, 2019 also have restructured terms that would require them to be reported as a TDR if they were accruing interest, compared to $2.9 million or 9.3% of the total at December 31, 2018.
- [ ] `c7debfacf020225e` — rank 2 · SSB · 10-K · 2020-02-21 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > Total non-acquired nonperforming loans were $22.8 million, or 0.25% of total non-acquired loans, an increase of approximately $7.8 million, or 51.9%, from December 31, 2018. The increase in nonperforming loans was driven primarily by an increase in commercial nonaccrual loans of $5.9 million and an increase in restructured nonaccrual loans of $1.9 million. The increase in commercial nonaccrual loans was mainly driven …
- [ ] `e3894f7073c5c960` — rank 3 · SSB · 10-K · 2020-02-21 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > The ALLL declined slightly to 0.62% of total non-acquired loans at December 31, 2019 compared to 0.65% at December 31, 2018. The allowance provides 2.50 times coverage of non-acquired nonperforming loans at December 31, 2019, a decrease from 3.41 times coverage at December 31, 2018. Net charge-offs as a percentage of average non-acquired loans remained flat at 0.04% in 2019 compared to 2018 as net charge-offs from th …
- [ ] `1740a2e79522681b` — rank 4 · UMPQ · 10-K · 2020-02-28 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > At December 31, 2019, the recorded investment in loans classified as impaired totaled $16.4 million, with a corresponding valuation allowance (included in the ALLL) of $155,000. At December 31, 2018, the total recorded investment in impaired loans was $42.3 million, with a corresponding valuation allowance (included in the ALLL) of $180,000. The valuation allowance on impaired loans represents the impairment reserves …
- [ ] `ef8cb3e3507311d1` — rank 5 · COLB · 10-K · 2020-02-27 · table  
      > December 31, 2019 | 2018 Recorded Investment Nonaccrual Loans | Unpaid Principal Balance Nonaccrual Loans | Recorded Investment Nonaccrual Loans | Unpaid Principal Balance Nonaccrual Loans (in thousands) Commercial business: Secured | $ | 26615 | $ | 38278 | $ | 35504 | $ | 45072 Unsecured | 359 | 360 | 9 Real estate: One-to-four family residential | 591 | 632 | 1158 | 1178 Commercial and multifamily residential: Com …
- [ ] `42cb2104cc749979` — rank 6 · SSB · 10-K · 2021-02-26 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > Total non-acquired nonperforming loans were $29.2 million, or 0.24% of total non-acquired loans, an increase of approximately $6.4 million, or 27.9%, from December 31, 2019. The increase in nonperforming loans was driven primarily by an increase in accruing loans past due 90 days or more of $9.1 million, an increase in restructured nonaccrual loans of $1.0 million, offset by a decline in primarily commercial nonaccru …
- [ ] `c8c35ccd8578129b` — rank 7 · COLB · 10-K · 2020-02-27 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > The following is an analysis of nonaccrual loans as of December 31, 2019 and 2018:
- [ ] `126f0bc3bb5f1d1f` — rank 8 · SSB · 10-K · 2020-02-21 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > Non-acquired nonperforming loans increased by approximately $3.6 million during the fourth quarter of 2019 from the level at September 30, 2019. The increase was mainly due to an increase in commercial nonaccrual loans of $1.4 million and restructured nonaccrual loans of $2.0 million. The increase in commercial nonaccrual loans was mainly driven by a $1.5 million increase in commercial and industrial nonaccrual loans …

---

### `r004` — What is the date of the merger agreement between Columbia Banking System and Umpqua Holdings?

**Already labelled** `a305b271220dc13e` — COLB · 10-K · 2022-02-25 · table  
> INDEX TO EXHIBITS Exhibit No. | Exhibit 2.1 | Agreement and Plan of Merger, dated as of June 23, 2021, by and between Columbia Banking System, Inc. and Bank of Commerce Holdings (1) 2.2 | Agreement and Plan of Merger, dated as of October 11, 2021, by and among Umpqua Holdings Corporation, Columbia Banking System, Inc., and Cascade Merger Sub, Inc.*(2) 3.1 | Amended and Restated Articles of Incorporation (3) 3.2 | Art …

Also answers the question?

- [ ] `68d6d08f5e5d26a6` — rank 1 · UMPQ · 8-K · 2021-10-12 · paragraph · Item 8.01. Other Events.  
      > On October 12, 2021, Umpqua Holdings Corporation (“Umpqua”) and Columbia Banking System, Inc. (“Columbia”) issued a joint press release announcing the execution of the Agreement and Plan of Merger (the “Merger Agreement”), dated as of October 11, 2021, by and among Umpqua, Columbia, and Cascade Merger Sub, Inc., a Delaware corporation and a direct, wholly owned subsidiary of Columbia (“Merger Sub”), pursuant to which …
- [ ] `1b09aea098e1029f` — rank 2 · UMPQ · 8-K · 2022-01-28 · paragraph  
      > On January 26, 2022, Umpqua Holdings Corporation (“Umpqua”) held a special meeting of shareholders (the “Umpqua special meeting”) to consider certain proposals related to the Agreement and Plan of Merger (the “merger agreement”), dated as of October 11, 2021, by and among Umpqua, Columbia Banking System, Inc. (“Columbia”) and Cascade Merger Sub, Inc. (the “Merger Sub”), which provides, among other things and subject …
- [ ] `4ccee2cf4fb5505f` — rank 3 · COLB · 8-K · 2023-01-10 · table  
      > Exhibit No. | Description 2.1 | Amendment No. 1 to the Merger Agreement, dated as of January 9, 2023, by and among Columbia, Umpqua and Merger Sub. 99.1 | Joint Press Release of Columbia Banking System, Inc. and Umpqua Holdings Corporation, dated January 9, 2023. 104 | The cover page for this Current Report on Form 8-K, formatted in Inline XBRL.
- [ ] `20dafca7f8713c49` — rank 4 · COLB · 8-K · 2021-10-12 · paragraph  
      > On October 12, 2021, Columbia Banking System, Inc., a Washington corporation (“Columbia”) and Umpqua Holdings Corporation, an Oregon corporation (“Umpqua”) issued a joint press release announcing the execution of an Agreement and Plan of Merger, dated as of October 11, 2021 (the “Merger Agreement’), by and among Columbia, Cascade Merger Sub, Inc., a Delaware corporation and a direct wholly owned subsidiary of Columbi …
- [ ] `5caf551c23a51698` — rank 5 · COLB · 8-K · 2022-01-28 · paragraph · Item 5.07. Submission of Matters to a Vote of Security Holders.  
      > On January 26, 2022, Columbia Banking System, Inc. (“Columbia”) held a virtual special meeting of shareholders (the “Special Meeting”) in connection with the Agreement and Plan of Merger, dated as of October 11, 2021 (the “Merger Agreement”), among Columbia, Umpqua Holdings Corporation (“Umpqua”) and Cascade Merger Sub, Inc., a direct, wholly owned subsidiary of Columbia (“Merger Sub”). Pursuant to the Merger Agreeme …
- [ ] `a7107e52c1d994b4` — rank 6 · COLB · 8-K · 2023-01-10 · paragraph  
      > On January 9, 2023, Columbia Banking System, Inc., a Washington corporation (“Columbia”), Umpqua Holdings Corporation, an Oregon corporation (“Umpqua”), and Cascade Merger Sub, Inc., a Delaware corporation and a direct, wholly-owned subsidiary of Columbia (“Merger Sub”), entered into Amendment No. 1 (the “Amendment”) to the Agreement and Plan of Merger, dated as of October 11, 2021 (the “Merger Agreement”), by and am …
- [ ] `452422b6a7629f67` — rank 7 · UMPQ · 8-K · 2023-01-10 · table  
      > Exhibit No. | Description 2.1 | Amendment No. 1, dated as of January 9, 2023, to the Agreement and Plan of Merger dated as of October 11, 2021, by and among Umpqua Holdings Corporation, Columbia Banking System, Inc., and Cascade Merger Sub, Inc. 99.1 | Joint Press Release of Umpqua Holdings Corporation and Columbia Banking System, Inc., dated January 9, 2023 104 | Cover Page Interactive Data File (embedded within the …
- [ ] `51e73bb312e367a1` — rank 8 · UMPQ · 8-K · 2021-10-12 · section · Item 8.01. Other Events.  
      > Item 8.01. Other Events. On October 12, 2021, Umpqua Holdings Corporation (“Umpqua”) and Columbia Banking System, Inc. (“Columbia”) issued a joint press release announcing the execution of the Agreement and Plan of Merger (the “Merger Agreement”), dated as of October 11, 2021, by and among Umpqua, Columbia, and Cascade Merger Sub, Inc., a Delaware corporation and a direct, wholly owned subsidiary of Columbia (“Merger …

---

### `r005` — What net income did Columbia report for 2019 in its consolidated statement of changes in shareholders' equity?

**Already labelled** `679857067625598b` — COLB · 10-K · 2022-02-25 · table  
> CONSOLIDATED STATEMENTS OF CHANGES IN SHAREHOLDERS’ EQUITY Common Stock Number of Shares | Amount | Retained Earnings | Accumulated Other Comprehensive Income (Loss) | Treasury Stock | Total Shareholders’ Equity (in thousands, except per share amounts) Balance at January 1, 2019 | 73249 | $ | 1642246 | $ | 426708 | $ | (35,305) | $ | — | $ | 2033649 Adjustment to opening retained earnings pursuant to adoption of ASU …

Also answers the question?

- [ ] `d1cf09ad829822c3` — rank 1 · COLB · 10-Q · 2022-05-05 · table  
      > CONSOLIDATED STATEMENTS OF CHANGES IN SHAREHOLDERS’ EQUITY Columbia Banking System, Inc. (Unaudited) Common Stock | Retained Earnings | Accumulated Other Comprehensive Income (Loss) | Treasury Stock | Total Shareholders’ Equity Shares Outstanding | Amount | Retained Earnings | Accumulated Other Comprehensive Income (Loss) | Treasury Stock | Total Shareholders’ Equity For the Three Months Ended March 31, 2021 | (in th …
- [ ] `e4c7e5157ef791c0` — rank 2 · COLB · 10-Q · 2021-05-06 · table  
      > CONSOLIDATED STATEMENTS OF CHANGES IN SHAREHOLDERS’ EQUITY Columbia Banking System, Inc. (Unaudited) Common Stock | Retained Earnings | Accumulated Other Comprehensive Income (Loss) | Treasury Stock | Total Shareholders’ Equity Shares Outstanding | Amount | Retained Earnings | Accumulated Other Comprehensive Income (Loss) | Treasury Stock | Total Shareholders’ Equity For the Three Months Ended March 31, 2021 | (in th …
- [ ] `4212386ca0db3f74` — rank 3 · COLB · 10-Q · 2022-05-05 · table  
      > CONSOLIDATED STATEMENTS OF CHANGES IN SHAREHOLDERS’ EQUITY Columbia Banking System, Inc. (Unaudited) Common Stock | Retained Earnings | Accumulated Other Comprehensive Income (Loss) | Treasury Stock | Total Shareholders’ Equity Shares Outstanding | Amount | Retained Earnings | Accumulated Other Comprehensive Income (Loss) | Treasury Stock | Total Shareholders’ Equity For the Three Months Ended March 31, 2022 | (in th …
- [ ] `b4203d9725540414` — rank 4 · COLB · 10-K · 2020-02-27 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > We have audited the accompanying consolidated balance sheets of Columbia Banking System, Inc. and subsidiaries (the "Company") as of December 31, 2019 and 2018, the related consolidated statements of income, comprehensive income, shareholders' equity, and cash flows for each of the three years in the period ended December 31, 2019, and the related notes (collectively referred to as the "financial statements"). In our …
- [ ] `6bb6a4199498b2a4` — rank 5 · COLB · 10-K · 2021-02-26 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > We have audited the accompanying consolidated balance sheets of Columbia Banking System, Inc. and subsidiaries (the "Company") as of December 31, 2020 and 2019, the related consolidated statements of income, comprehensive income, shareholders' equity, and cash flows for each of the three years in the period ended December 31, 2020, and the related notes (collectively referred to as the "financial statements"). In our …
- [ ] `5055df903326aae8` — rank 6 · COLB · 10-K · 2020-02-27 · section · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA We have audited the accompanying consolidated balance sheets of Columbia Banking System, Inc. and subsidiaries (the "Company") as of December 31, 2019 and 2018, the related consolidated statements of income, comprehensive income, shareholders' equity, and cash flows for each of the three years in the period ended December 31, 2019, and the related notes (collectivel …
- [ ] `33310b3e1c151950` — rank 7 · COLB · 10-K · 2021-02-26 · section · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA We have audited the accompanying consolidated balance sheets of Columbia Banking System, Inc. and subsidiaries (the "Company") as of December 31, 2020 and 2019, the related consolidated statements of income, comprehensive income, shareholders' equity, and cash flows for each of the three years in the period ended December 31, 2020, and the related notes (collectivel …
- [ ] `796826db75a486d3` — rank 8 · SSB · 10-K · 2021-02-26 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > The merger with CSFL approximately doubled the size of the Company, resulting in significant increases to assets, liabilities and equity on the Consolidated Statements of Balance Sheet, as well as to many categories of revenue and expense on the Consolidated Statements of Income. We earned net income of $120.6 million, or $2.19 diluted earnings per share (“EPS”), during 2020 compared to net income of $186.5 million, …

---

### `r006` — How did PPP loans affect Columbia's deposit balances in 2020?

**Already labelled** `a6fb2164e49a434c` — COLB · 10-Q · 2020-07-31 · paragraph · Item 1. FINANCIAL STATEMENTS  
> Our deposit products include a wide variety of transaction accounts, savings accounts and time deposit accounts. We have established a branch system to serve our consumer and business depositors. Deposits increased $2.40 billion from December 31, 2019. The addition of PPP loans during the current quarter had a notable impact on our deposits, as our clients deposited these funds into their deposit accounts. In additio …

Also answers the question?

- [ ] `1e309ceea3124694` — rank 1 · WSBC · 10-K · 2022-02-28 · paragraph · Item 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > positively impacted the 2021 net interest margin by a net 10 basis points. Excluding PPP loans, portfolio loans decreased by 4.9% from December 31, 2020, due to lower new loan demand and high levels of commercial real estate loan payoffs. In addition, purchase accounting accretion decreased in 2021, as approximately 11 basis points of accretion from prior acquisitions was included in the 2021 net interest margin as c …
- [ ] `5e2dd5caa577855a` — rank 2 · WSBC · 10-K · 2021-02-26 · paragraph · Item 1A. RISK FACTORS  
      > For the twelve months ending December 31, 2020, net interest income increased $79.6 million, or 19.9%, due to an increase in earning assets from the OLBK acquisition. The net interest margin decreased 25 basis points to 3.37% due to the overall lower rate environment. Average loan balances increased 36.1% in 2020, mostly due to the OLBK acquisition and PPP loans as compared to 2019, as organic loan growth was mitigat …
- [ ] `583882a6cd48512b` — rank 3 · WSBC · 10-K · 2021-02-26 · paragraph · Item 1A. RISK FACTORS  
      > Total deposits increased by $1.4 billion or 13.0% in 2020 primarily due to CARES Act funds received, both consumer stimulus-related and from PPP loan proceeds deposited and increased personal savings. Non-interest bearing demand deposits and interest bearing demand deposits increased 28.1% and 22.6%, respectively, while savings deposits and money market deposits increased 14.5% and 11.0%, respectively, due to the afo …
- [ ] `9813bd706803498c` — rank 4 · UMPQ · 10-K · 2021-02-25 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > •The Company participates in the PPP, offering loans to both customers and non-customers throughout our footprint. As of December 31, 2020, the Company had approximately 14,800 PPP loans and $1.8 billion in PPP loans, with an average customer loan balance of $118,000. PPP loan balances will decline as customers complete the applicable loan forgiveness process through the Company and the SBA.
- [ ] `54758dc1f76e3b08` — rank 5 · WSBC · 10-K · 2021-02-26 · paragraph · Item 1A. RISK FACTORS  
      > Net interest income, which is Wesbanco’s largest source of revenue, is the difference between interest income on earning assets, primarily loans and securities, and interest expense on liabilities, primarily deposits and short and long-term borrowings. Net interest income is affected by the general level of, and changes in interest rates, the steepness and shape of the yield curve, changes in the amount and compositi …
- [ ] `46b8295ea603b78e` — rank 6 · WSBC · 10-K · 2022-02-28 · paragraph · Item 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Total deposits increased by $1.1 billion or 9.1% in 2021 primarily due to consumer stimulus-related funds, PPP loan proceeds deposited, and increased personal savings. Interest bearing demand deposits and non-interest bearing demand deposits increased 19.0% and 12.8%, respectively, while savings deposits and money market deposits increased 15.7% and 3.2%, respectively, due to the aforementioned CARES Act funds previo …
- [ ] `1113628c152d8e0a` — rank 7 · UMPQ · 10-K · 2022-02-25 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > In April 2020, the Bank began originating loans to qualified small businesses under the PPP administered by the SBA. The remaining unamortized balance of the PPP-related net loan processing fees will be recognized as a yield adjustment over the remaining term of these loans, although the forgiveness of these loans by the SBA accelerates the recognition of these fees.
- [ ] `4627ab8f3758d38c` — rank 8 · COLB · 10-K · 2022-02-25 · paragraph · Item 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Taxable-equivalent net interest income totaled $507.6 million in 2020, compared with $501.8 million for 2019. The increase in net interest income during 2020 resulted from the increase in the size of the loan and investment securities portfolios as well as an increase in the average balance of interest-earning deposits with banks. The loan portfolio benefited from the origination of PPP loans during the year as a res …

---

### `r007` — What drove the increase in Columbia's noninterest income for the first six months of 2020?

**Already labelled** `ad3270e258b8ce65` — COLB · 10-Q · 2020-07-31 · paragraph · Item 1. FINANCIAL STATEMENTS  
> For the six months ended June 30, 2020, noninterest income was $58.5 million compared to $47.3 million for the same period in 2019, an increase of $11.1 million. The increase was primarily due to the previously noted $16.4 million gain from the sale and write-up of Visa Class B restricted shares to fair value during the second quarter of 2020. Loan revenue increased during the first half of 2020 due to increases in i …

Also answers the question?

- [ ] `2571ec8c92db9c8c` — rank 1 · COLB · 10-Q · 2020-07-31 · paragraph · Item 1. FINANCIAL STATEMENTS  
      > Noninterest income for the six months ended June 30, 2020 was $58.5 million, an increase of $11.1 million from the prior year period. The increase was primarily due to the previously noted $16.4 million gain from the sale and upward adjustment to the carrying value of the Visa Class B restricted shares to the market price and loan revenue. These increases were partially offset by decreases in deposit account and trea …
- [ ] `3c3d5d552bbfaca7` — rank 2 · COLB · 10-Q · 2020-05-08 · paragraph · Item 1. FINANCIAL STATEMENTS  
      > Noninterest income was $21.2 million for the first quarter of 2020, compared to $21.7 million for the same period in 2019. The decrease was primarily due to lower deposit account and treasury management fees, principally lower treasury management fees, and lower net investment securities gains partially offset by higher loan revenue during the first quarter of 2020.
- [ ] `ccd357e2925bc370` — rank 3 · COLB · 10-K · 2021-02-26 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > (2) During the second quarter of 2020, Columbia sold a portion of its Visa Class B restricted stock and subsequently wrote up to fair value the remaining Visa Class B shares. The gain from the sale of shares and the increase in the fair value of the remaining Visa Class B restricted shares were included in noninterest income on the Consolidated Statements of Income. For additional information, see Note 3. “Securities …
- [ ] `ac996c8ec764a65c` — rank 4 · COLB · 10-Q · 2020-05-08 · paragraph · Item 1. FINANCIAL STATEMENTS  
      > Noninterest income for the current quarter was $21.2 million, a decrease of $489 thousand from the prior year period. The decrease was primarily due to lower treasury management fees and lower net securities gains partially offset by higher loan revenue during the first quarter of 2020.
- [ ] `2e2fca755f837940` — rank 5 · COLB · 10-Q · 2020-07-31 · paragraph · Item 1. FINANCIAL STATEMENTS  
      > The provision for credit losses for the six months ended June 30, 2020 was $75.0 million compared to a provision of $1.6 million for the first six months of 2019. The increase in the provision for the first six months of 2020 compared to the same period in 2019 was due to the ongoing COVID-19 pandemic which has negatively affected the economy and increased unemployment rates, similar to the quarterly results above.
- [ ] `b3284110b23aac3a` — rank 6 · SSB · 10-K · 2023-02-24 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > Our noninterest income increased 13.9% for the year ended December 31, 2021 compared to 2020. This change in total noninterest income resulted from the following:
- [ ] `a5cdaf8a42e803d2` — rank 7 · SSB · 10-K · 2022-02-25 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > Our noninterest income increased 13.8% for the year ended December 31, 2021 compared to 2020. This change in total noninterest income resulted from the following:
- [ ] `05d8aa4d40d7ce2e` — rank 8 · COLB · 10-Q · 2020-07-31 · paragraph · Item 1. FINANCIAL STATEMENTS  
      > The results for the first half of 2020 compared to the same period in 2019 were similar to the quarterly results. Net interest income for the six months ended June 30, 2020 was $244.3 million, relative to $246.1 million for the prior year period. The decrease in net interest income on loans was due to the lower rate environment partially offset by increases in interest income on loans and securities due to higher ave …

---

### `r008` — What was Columbia's net income for the three months ended September 30, 2021?

**Already labelled** `6a64cbef33fafeaf` — COLB · 10-Q · 2021-11-05 · table  
> CONSOLIDATED STATEMENTS OF COMPREHENSIVE INCOME Columbia Banking System, Inc. (Unaudited) Three Months Ended September 30, 2021 | 2020 (in thousands) Net income | $ | 53017 | $ | 44734 Other comprehensive loss, net of tax: Unrealized loss from securities: Net unrealized holding loss from available for sale debt securities arising during the period, net of tax of $6,671 and $436 | (22,022) | (1,442) Amortization of ne …

Also answers the question?

- [ ] `23478fac4ed371dd` — rank 1 · UMPQ · 10-Q · 2022-10-31 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended September 30, 2022 and June 30, 2022, where applicable, throughout this Management's Discussion and Analysis.  
      > Merger related expenses, related to the proposed merger with Columbia decreased $1.9 million during the three months ended September 30, 2022 as compared to the three months ended June 30, 2022, due to reduced consulting and legal costs incurred.
- [ ] `8bca219ec2525293` — rank 2 · UMPQ · 10-Q · 2022-10-31 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended September 30, 2022 and June 30, 2022, where applicable, throughout this Management's Discussion and Analysis.  
      > Net interest income for the nine months ended September 30, 2022 was $764.5 million, an increase of $78.3 million compared to the nine months ended September 30, 2021. The increase for the nine months ended September 30, 2022 was due primarily to higher loan interest income from increasing rates and higher average loan and lease balances.
- [ ] `2e16c5515829ea8a` — rank 3 · WSBC · 10-Q · 2022-11-03 · table  
      > For the Three Months Ended September 30, | For the Nine Months Ended September 30, (unaudited, dollars in thousands) | 2022 | 2021 | 2022 | 2021 Net interest income | $ | 124501 | $ | 115275 | $ | 344439 | $ | 347607 Taxable equivalent adjustment to net interest income | 1307 | 1080 | 3712 | 3170 Net interest income, fully taxable equivalent | $ | 125808 | $ | 116355 | $ | 348151 | $ | 350777 Net interest spread, non …
- [ ] `e172686fa4b6048c` — rank 4 · WSBC · 10-Q · 2021-11-08 · table  
      > For the Three Months Ended September 30, | For the Nine Months Ended September 30, (unaudited, dollars in thousands) | 2021 | 2020 | 2021 | 2020 Net interest income | $ | 115275 | $ | 120593 | $ | 347607 | $ | 359768 Taxable equivalent adjustment to net interest income | 1080 | 1112 | 3170 | 3440 Net interest income, fully taxable equivalent | $ | 116355 | $ | 121705 | $ | 350777 | $ | 363208 Net interest spread, non …
- [ ] `9da66282df85c481` — rank 5 · UMPQ · 10-Q · 2022-10-31 · table  
      > Three Months Ended | Nine Months Ended (in thousands, except per share data) | September 30, 2022 | September 30, 2021 | September 30, 2022 | September 30, 2021 Net income | $ | 84040 | $ | 108066 | $ | 253788 | $ | 331946 Weighted average number of common shares outstanding - basic | 217051 | 218416 | 216955 | 219791 Effect of potentially dilutive common shares (1) | 335 | 562 | 398 | 487 Weighted average number of …
- [ ] `053018167ede1e72` — rank 6 · UMPQ · 10-Q · 2022-10-31 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended September 30, 2022 and June 30, 2022, where applicable, throughout this Management's Discussion and Analysis.  
      > •Earnings per diluted common share was $0.39 for the three months ended September 30, 2022, as compared to $0.36 for the three months ended June 30, 2022. The increase for the three months ended September 30, 2022, as compared to the prior period, was primarily driven by an increase in net interest income due to the rising interest rate environment. The increase was partially offset by a decrease in non-interest inco …
- [ ] `567d388c7872959d` — rank 7 · SSB · 10-Q · 2022-11-04 · table  
      > ​ ​ | Three Months Ended | ​ | Nine Months Ended | ​ ​ | September 30, | ​ | September 30, | ​ ​ | 2022 | 2021 | 2022 | 2021 Net income | $ | 133043 | $ | 122788 | $ | 352547 | $ | 368697 | ​ Other comprehensive (loss) income: | ​ Unrealized holding losses on available for sale securities: | ​ Unrealized holding losses arising during period | ​ | (299,139) | ​ | (32,284) | ​ | (922,437) | ​ | (63,019) | ​ Tax effect …
- [ ] `41d4e7198787ab03` — rank 8 · GBCI · 10-Q · 2021-11-01 · table  
      > Three Months ended | Nine Months ended (Dollars in thousands) | September 30, 2021 | September 30, 2020 | September 30, 2021 | September 30, 2020 Net Income | $ | 75619 | 77757 | 234048 | 184540 Other Comprehensive Income (Loss), Net of Tax Available-For-Sale and Transferred Securities: Unrealized (losses) gains on available-for-sale securities | (15,259) | 1693 | (84,929) | 123262 Reclassification adjustment for gai …

---

### `r009` — What valuation technique and unobservable inputs does Columbia use to value residential mortgage servicing rights?

**Already labelled** `fc9665ce205873b1` — COLB · 10-Q · 2023-11-03 · table  
> Financial Instrument | Fair Value (in thousands) | Valuation Technique | Unobservable Input | Range of Inputs | Weighted Average Assets: Residential mortgage servicing rights | $ | 117640 | Discounted cash flow Constant prepayment rate | 6.07% - 26.05% | 6.49% Discount rate | 9.50% - 16.04% | 10.23% Liabilities: Interest rate lock commitments, net | $ | 427 | Internal pricing model Pull-through rate | 73.20% - 100.00 …

Also answers the question?

- [ ] `6cee4c0b00d48b48` — rank 1 · COLB · 10-Q · 2024-05-07 · table  
      > Financial Instrument | Fair Value (in thousands) | Valuation Technique | Unobservable Input | Range of Inputs | Weighted Average Assets: Residential mortgage servicing rights | $ | 110444 | Discounted cash flow | Constant prepayment rate | 6.07% - 27.52% | 6.74% Discount rate | 9.50% - 16.08% | 10.24% Interest rate lock commitments, net | $ | 16 | Internal pricing model | Pull-through rate | 64.27% - 100.00% | 85.71% …
- [ ] `67ba85d6afeb26d6` — rank 2 · UMPQ · 10-K · 2023-02-24 · table  
      > Financial Instrument | Fair Value (in thousands) | Valuation Technique | Unobservable Input | Range of Inputs | Weighted Average Assets: Residential mortgage servicing rights | $ | 185017 | Discounted cash flow Constant prepayment rate | 4.72% - 20.16% | 6.39% Discount rate | 9.50% - 15.96% | 10.06% Interest rate lock commitments, net | $ | 32 | Internal pricing model Pull-through rate | 12.55% - 100.00% | 89.53% Lia …
- [ ] `34c1253a6cebfc30` — rank 3 · COLB · 10-Q · 2024-11-05 · table  
      > Financial Instrument | Fair Value (in thousands) | Valuation Technique | Unobservable Input | Range of Inputs | Weighted Average September 30, 2024 Assets: Residential mortgage servicing rights | $ | 101919 | Discounted cash flow | Constant prepayment rate | 6.06% - 26.35% | 7.24% Discount rate | 9.62% - 16.13% | 10.24% Interest rate lock commitments, net | $ | 82 | Internal pricing model | Pull-through rate | 66.28% …
- [ ] `1ccc0e1fbd27c530` — rank 4 · COLB · 10-Q · 2023-05-09 · table  
      > Financial Instrument | Fair Value (in thousands) | Valuation Technique | Unobservable Input | Range of Inputs | Weighted Average Assets: Residential mortgage servicing rights | $ | 178800 | Discounted cash flow Constant prepayment rate | 5.92% - 44.13% | 6.53% Discount rate | 9.50% - 15.98% | 10.06% Interest rate lock commitments, net | $ | 137 | Internal pricing model Pull-through rate | 12.00% - 100.00% | 85.15% Li …
- [ ] `04cc02eb7913a4fb` — rank 5 · UMPQ · 10-Q · 2022-05-05 · table  
      > Financial Instrument | Fair Value (in thousands) | Valuation Technique | Unobservable Input | Range of Inputs | Weighted Average Assets: Residential mortgage servicing rights | $ | 165807 | Discounted cash flow Constant prepayment rate | 6.23% - 31.72% | 7.27% Discount rate | 9.00% - 14.90% | 9.51% Liabilities: Interest rate lock commitments | $ | 853 | Internal pricing model Pull-through rate | 67.72% - 100.00% | 91 …
- [ ] `93d7745bbac571c4` — rank 6 · COLB · 10-Q · 2023-08-03 · table  
      > Financial Instrument | Fair Value (in thousands) | Valuation Technique | Unobservable Input | Range of Inputs | Weighted Average Assets: Residential mortgage servicing rights | $ | 172929 | Discounted cash flow Constant prepayment rate | 6.07% - 24.79% | 6.42% Discount rate | 9.50% - 16.00% | 10.06% Liabilities: Interest rate lock commitments, net | $ | 51 | Internal pricing model Pull-through rate | 76.03% - 101.50% …
- [ ] `a6ab366cb48580bd` — rank 7 · COLB · 10-Q · 2024-08-06 · table  
      > Financial Instrument | Fair Value (in thousands) | Valuation Technique | Unobservable Input | Range of Inputs | Weighted Average Assets: Residential mortgage servicing rights | $ | 110039 | Discounted cash flow | Constant prepayment rate | 6.03% - 27.36% | 6.76% Discount rate | 9.50% - 16.10% | 10.23% Liabilities: Interest rate lock commitments, net | $ | 452 | Internal pricing model | Pull-through rate | 69.73% - 10 …
- [ ] `5b501545116c744c` — rank 8 · COLB · 10-K · 2024-02-27 · table  
      > Financial Instrument | Fair Value (in thousands) | Valuation Technique | Unobservable Input | Range of Inputs | Weighted Average Assets: Residential mortgage servicing rights | $ | 109243 | Discounted cash flow Constant prepayment rate | 6.07% - 28.17% | 6.78% Discount rate | 9.50% - 16.05% | 10.25% Liabilities: Interest rate lock commitments, net | $ | 137 | Internal pricing model Pull-through rate | 67.33% - 100.00 …

---

### `r010` — By how much was the number of authorized Columbia common shares increased in connection with the Umpqua merger?

**Already labelled** `31b9af98d512182c` — COLB · 8-K · 2022-01-28 · document  
> 8-K filed by COLB on 2022-01-28 Item 5.07. Submission of Matters to a Vote of Security Holders. Item 1. – Columbia Articles Amendment Proposal. A proposal to approve an amendment to the amended and restated articles of incorporation of Columbia to effect an increase in the number of authorized shares of Columbia common stock from 115,000,000 to 520,000,000 (the “Columbia articles amendment proposal”) was approved upo …

Also answers the question?

- [ ] `60c9f384d0ec15d7` — rank 1 · UMPQ · 8-K · 2023-03-01 · paragraph  
      > The total aggregate consideration delivered to holders of Umpqua Common Stock in the Merger was approximately 129,575,804 shares of Columbia Common Stock. The issuance of shares of Columbia Common Stock in connection with the Merger was registered under the Securities Act of 1933, as amended, pursuant to a registration statement on Form S-4 (File No. 333-261281) filed by Columbia with the Securities and Exchange Comm …
- [ ] `aaac535a39bec25c` — rank 2 · COLB · 8-K · 2023-03-01 · paragraph  
      > The total aggregate consideration delivered to holders of Umpqua Common Stock in the Merger was approximately 129,575,804 shares of Columbia Common Stock. The issuance of shares of Columbia Common Stock in connection with the Merger was registered under the Securities Act of 1933, as amended, pursuant to a registration statement on Form S-4 (File No. 333-261281) filed by Columbia with the Securities and Exchange Comm …
- [ ] `b9553cd0099a2d07` — rank 3 · COLB · 8-K · 2023-03-01 · paragraph  
      > In connection with the consummation of the Mergers, Columbia filed articles of amendment with the Washington Secretary of State for the purpose of amending its Amended and Restated Articles of Incorporation, as amended, to increase the total number of authorized shares of Columbia Common Stock from 115,000,000 to 520,000,000 (the “Articles of Amendment”). The Articles of Amendment became effective on February 28, 202 …
- [ ] `79ffff75e11d9e49` — rank 4 · COLB · 10-K · 2024-02-27 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > As the legal acquirer, Columbia issued approximately 129.4 million shares of Columbia common stock in connection with the Merger, which represented approximately 62.1% of the voting interests in Columbia upon completion of the Merger. The purchase price in a reverse acquisition is determined based on the number of equity interests the legal acquiree would have had to issue to give the owners of the legal acquirer the …
- [ ] `7401ca7ae1630ca4` — rank 5 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > Pursuant to the terms of the Merger Agreement, each share of Umpqua common stock outstanding was converted into the right to receive 0.5958 of a share (the “Exchange Ratio”) of Columbia common stock at Closing. Each outstanding Umpqua equity award granted under Umpqua’s equity compensation plans was generally converted into a corresponding award with respect to Columbia common stock, with the number of shares underly …
- [ ] `34f0731b46ff8cea` — rank 6 · SSB · 8-K · 2020-06-08 · paragraph · Item 5.03. Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year.  
      > In connection with the completion of the Merger and in accordance with the Merger Agreement, the Company’s articles of incorporation were amended to increase the number of authorized shares of South State Common Stock from 80,000,000 shares to 160,000,000 shares (the “Articles Amendment”), effective as of the Effective Time.
- [ ] `a861b618bc264824` — rank 7 · COLB · S-4 · 2021-08-06 · paragraph  
      > Columbia common shares that are issued to shareholders of BOCH in the parent merger will be freely tradable without restrictions or further registration under the Securities Act of 1933, as amended, which we refer to as the Securities Act. As of June 21, 2021, Columbia had approximately 71,743,885 common shares outstanding and 2,210,216 Columbia common shares were reserved for issuance under the Columbia stock plans. …
- [ ] `5caf551c23a51698` — rank 8 · COLB · 8-K · 2022-01-28 · paragraph · Item 5.07. Submission of Matters to a Vote of Security Holders.  
      > On January 26, 2022, Columbia Banking System, Inc. (“Columbia”) held a virtual special meeting of shareholders (the “Special Meeting”) in connection with the Agreement and Plan of Merger, dated as of October 11, 2021 (the “Merger Agreement”), among Columbia, Umpqua Holdings Corporation (“Umpqua”) and Cascade Merger Sub, Inc., a direct, wholly owned subsidiary of Columbia (“Merger Sub”). Pursuant to the Merger Agreeme …

---

### `r011` — What compensation arrangement did Columbia enter into with Aaron Deer when the Umpqua merger closed?

**Already labelled** `05be2f020253fbd0` — COLB · 8-K · 2023-03-01 · paragraph  
> Deer Letter Agreement. In connection with the Closing, Aaron Deer ceased serving as Executive Vice President and Chief Financial Officer of Columbia and going forward will serve as Chief Strategy and Innovation Officer of Columbia. Columbia entered into a letter agreement with Aaron Deer, dated March 1, 2023 (the “Deer Letter Agreement”), which provides that in lieu of any entitlements under Mr. Deer’s existing chang …

Also answers the question?

- [ ] `a7dcdc92ee2d6cc7` — rank 1 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > Deer Letter Agreement. In connection with the Closing, Mr. Deer ceased serving as Executive Vice President and Chief Financial Officer of Columbia and became Chief Strategy and Innovation Officer of the Company. Columbia entered into a letter agreement with Mr. Deer (the “Deer Letter Agreement”), which provides that in lieu of any entitlements under Mr. Deer’s existing change in control agreement with Columbia, which …
- [ ] `0566569b7c63185e` — rank 2 · COLB · 8-K · 2023-03-01 · paragraph  
      > No later than the second anniversary of the Closing (or on such earlier date on which Columbia implements new employment or severance agreements, plans or arrangements for similarly situated executives), Mr. Deer will be eligible to enter into a new employment or severance agreement that provides change in control severance benefits no less favorable than those under Mr. Deer’s prior change in control agreement with …
- [ ] `c1150761201b5ad8` — rank 3 · UMPQ · 10-K · 2023-02-24 · section · Item 11. EXECUTIVE COMPENSATION  
      > Item 11. EXECUTIVE COMPENSATION The CD&A describes our executive compensation program for the following "named executive officers": We maintain a strong pay for performance philosophy that links executive compensation to achieving the operating and financial goals set by the Board. Our independent Compensation Committee has built strong governance features into our executive compensation program. On October 11, 2021, …
- [ ] `eb8def7a84c75c3b` — rank 4 · UMPQ · 10-Q · 2022-10-31 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended September 30, 2022 and June 30, 2022, where applicable, throughout this Management's Discussion and Analysis.  
      > •In October 2021, Umpqua and Columbia announced their entering into the Merger Agreement under which the two companies will combine in an all-stock transaction. On September 17,2022, a Letter of Agreement was entered into with the Department of Justice, which stipulates that in order to obtain regulatory approvals necessary to complete the transaction, ten Columbia State Bank branches will need to be divested. On Oct …
- [ ] `aab192645f8f0047` — rank 5 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > On October 11, 2021, Columbia entered into the O’Haver Letter Agreement with Mr. O’Haver, which incorporated the terms of the succession plan and confirmed his compensation arrangements following the Merger. See “Compensation Decisions” above.
- [ ] `eb45922267d6f772` — rank 6 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > On October 11, 2021, Columbia entered into the O’Haver Letter Agreement, which incorporated the terms of the succession plan and confirmed his compensation arrangements following the Merger. The O’Haver Letter Agreement provides for the following:
- [ ] `a96002f04c1592f4` — rank 7 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > Following the second anniversary of the Closing (or on such earlier date on which Columbia implements new employment or severance agreements, plans or arrangements for similarly situated executives), if Mr. Deer remains employed by the Company, he will be eligible to enter into a new employment or severance agreement (or participate in a new severance program) that includes change in control severance benefits no les …
- [ ] `5d619d5b6e895f4c` — rank 8 · UMPQ · 10-Q · 2022-07-29 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended June 30, 2022 and March 31, 2022, where applicable, throughout this Management's Discussion and Analysis.  
      > •In October 2021, Umpqua and Columbia announced their entering into the Merger Agreement under which the two companies will combine in an all-stock transaction, which is expected to close in the third quarter of 2022, pending the receipt of regulatory approvals.

---

### `r012` — Who became Executive Chair of Columbia's board after the Umpqua merger, and what was his prior role?

**Already labelled** `da9a01e4dfe0d897` — COLB · 8-K · 2023-03-01 · paragraph  
> Effective as of the Effective Time, in accordance with the terms of the Merger Agreement, Cort L. O’Haver, the former President and Chief Executive Officer of Umpqua, was appointed Executive Chair of the board of directors of Columbia (the “Board”) and of Umpqua Bank. Mr. O’Haver, age 60, served from 2017 through the Closing Date as President and Chief Executive Officer of Umpqua after having served as Umpqua’s Execu …

Also answers the question?

- [ ] `499ef02b2ee53f63` — rank 1 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > Prior to the Merger, the Company’s practice was for an independent director to serve as Board Chair. From May 2018 through February 28, 2023, Craig D. Eerkes served as the Columbia Board Chair. On March 1, 2023, pursuant to a letter agreement executed in connection with the Merger, Mr. O’ Haver became the Executive Chair of the Board and will continue in that capacity for three years following the Merger. The Board b …
- [ ] `d3d4d5aa06a23156` — rank 2 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > practice of Columbia to separate the duties of Board Chair and Chief Executive Officer. With the Merger, Umpqua’s former President and Chief Executive Officer, Cort L. O’Haver, was appointed to the newly created position of Executive Chair, and Columbia’s Board Chair, Craig D. Eerkes, was appointed to the newly created position of Lead Independent Director. In keeping with good governance practices, the Board believe …
- [ ] `7f42a54b85db058c` — rank 3 · COLB · 8-K · 2023-03-01 · paragraph  
      > Other than the Merger Agreement, the Amended and Restated Bylaws and the O’Haver Letter Agreement, there are no arrangements or understandings between Mr. O’Haver and any person pursuant to which he was selected as the Executive Chair of Columbia and of Umpqua Bank.
- [ ] `d255321530057625` — rank 4 · COLB · DEF 14A · 2022-03-18 · paragraph  
      > As described in the joint proxy statement/prospectus filed with the SEC in connection with the special meeting of our shareholders held on January 26, 2022, our merger agreement with Umpqua provides that, upon consummation of the transaction, we will expand the size of our Board to 14 directors. Seven of the directors of the combined company will be former members of the Umpqua board of directors, including Cort L. O …
- [ ] `a9107cf3efa320df` — rank 5 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > The Merger brought together two talented groups of executives, and retaining talent and creating a cohesive and high-functioning team was a priority for the boards and Messrs. Stein and O’Haver. Messrs. Stein and O’Haver selected the post-Merger executive leadership team, with the approval of both boards, based on a variety of factors including experience, skills, and the needs of the company. Immediately after Closi …
- [ ] `d2945c8370838ae3` — rank 6 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > The Board has affirmatively determined that all directors other than Executive Chair O’ Haver and CEO Stein are independent. In determining the independence of directors, the Board considered responses to Director & Officer questionnaires that indicated no transactions between the Company or its affiliates and directors other than banking transactions with Umpqua Bank or, prior to the Merger, Columbia Bank. The Board …
- [ ] `39f4a716b4265769` — rank 7 · COLB · 8-K · 2021-10-15 · paragraph  
      > The Merger Agreement also provides, among other things, that (i) effective as of the Effective Time, Cort L. O’Haver, the current President and Chief Executive Officer of Umpqua, will serve as Executive Chairman of the board of directors of the surviving corporation and, as of the effective time of the Bank Merger, the surviving bank, (ii) effective as of the Effective Time, Clint E. Stein, the current President and …
- [ ] `6bec24a23a881d7a` — rank 8 · UMPQ · 8-K · 2021-10-15 · paragraph · Item 1.01. Entry into a Material Definitive Agreement.  
      > The Merger Agreement also provides, among other things, that (i) effective as of the Effective Time, Cort L. O’Haver, the current President and Chief Executive Officer of Umpqua, will serve as Executive Chairman of the board of directors of the surviving corporation and, as of the effective time of the Bank Merger, the surviving bank, (ii) effective as of the Effective Time, Clint E. Stein, the current President and …

---

### `r013` — What quarterly cash dividend did Columbia declare in February 2024, and when was it payable?

**Already labelled** `48e57e3168103922` — COLB · 8-K · 2024-02-09 · section · Item 8.01. Other Events.  
> Item 8.01. Other Events. On February 9, 2024, Columbia Banking System, Inc., parent company of Umpqua Bank, announced its Board of Directors has approved a quarterly cash dividend in the amount of $0.36 per common share. The dividend is payable March 11, 2024, to shareholders of record as of February 23, 2024. A copy of the press release is attached hereto as Exhibit 99.1 and is incorporated herein by reference in it …

Also answers the question?

- [ ] `283da21065642d71` — rank 1 · COLB · 8-K · 2024-02-09 · paragraph · Item 8.01. Other Events.  
      > On February 9, 2024, Columbia Banking System, Inc., parent company of Umpqua Bank, announced its Board of Directors has approved a quarterly cash dividend in the amount of $0.36 per common share. The dividend is payable March 11, 2024, to shareholders of record as of February 23, 2024. A copy of the press release is attached hereto as Exhibit 99.1 and is incorporated herein by reference in its entirety.
- [ ] `ba95237764844b29` — rank 2 · COLB · 10-K · 2024-02-27 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > Subsequent to year end, on February 9, 2024, the Company declared a regular quarterly cash dividend of $0.36 per common share payable on March 11, 2024, to shareholders of record at the close of business on February 23, 2024.
- [ ] `db33edc997d8b0dd` — rank 3 · COLB · 10-K · 2023-02-24 · paragraph · Item 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Subsequent to year end, on January 24, 2023, the Company declared a quarterly cash dividend of $0.30 per share payable on February 21, 2023, to shareholders of record at the close of business on February 6, 2023.
- [ ] `51e1a478c8fcc436` — rank 4 · SSB · 8-K · 2024-01-25 · paragraph  
      > The Board of Directors of the Company declared a quarterly cash dividend on its common stock of $0.52 per share, payable on February 16, 2024 to shareholders of record as of February 9, 2024.
- [ ] `2fe27074c6b9cc58` — rank 5 · COLB · 10-K · 2022-02-25 · paragraph · Item 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Subsequent to year end, on January 19, 2022, the Company declared a quarterly cash dividend of $0.30 per share payable on February 16, 2022, to shareholders of record at the close of business on February 2, 2022.
- [ ] `dc3f47077d45d2b8` — rank 6 · COLB · 8-K · 2024-11-15 · paragraph · Item 8.01. Other Events.  
      > On November 15, 2024, Columbia Banking System, Inc., parent company of Umpqua Bank, announced its Board of Directors has approved a quarterly cash dividend in the amount of $0.36 per common share. The dividend is payable December 16, 2024, to shareholders of record as of November 29, 2024. A copy of the press release is attached hereto as Exhibit 99.1 and is incorporated herein by reference in its entirety.
- [ ] `fa7e31e0b44c5db8` — rank 7 · COLB · 10-K · 2023-02-24 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > Subsequent to year end, on January 24, 2023, the Company declared a regular quarterly cash dividend of $0.30 per common share payable on February 21, 2023, to shareholders of record at the close of business on February 6, 2023.
- [ ] `4a6208158bcfc8ee` — rank 8 · SSB · 10-K · 2024-03-04 · paragraph · Item 15. Exhibits, Financial Statement Schedules.  
      > On January 25, 2024, the Company announced the declaration of a quarterly cash dividend on its common stock at $0.52 per share. The dividend was paid on February 16, 2024 to shareholders of record as of February 9, 2024.

---

### `r014` — What quarterly cash dividend did Columbia announce in November 2023?

**Already labelled** `6715f2203c1b83b4` — COLB · 8-K · 2023-11-13 · section · Item 8.01. Other Events.  
> Item 8.01. Other Events. On November 13, 2023, Columbia Banking System, Inc., parent company of Umpqua Bank, announced its Board of Directors has approved a quarterly cash dividend in the amount of $0.36 per common share. The dividend is payable December 11, 2023, to shareholders of record as of November 24, 2023. A copy of the press release is attached hereto as Exhibit 99.1 and is incorporated herein by reference i …

Also answers the question?

- [ ] `e29897554a993d1f` — rank 1 · COLB · 8-K · 2023-11-13 · paragraph · Item 8.01. Other Events.  
      > On November 13, 2023, Columbia Banking System, Inc., parent company of Umpqua Bank, announced its Board of Directors has approved a quarterly cash dividend in the amount of $0.36 per common share. The dividend is payable December 11, 2023, to shareholders of record as of November 24, 2023. A copy of the press release is attached hereto as Exhibit 99.1 and is incorporated herein by reference in its entirety.
- [ ] `dc3f47077d45d2b8` — rank 2 · COLB · 8-K · 2024-11-15 · paragraph · Item 8.01. Other Events.  
      > On November 15, 2024, Columbia Banking System, Inc., parent company of Umpqua Bank, announced its Board of Directors has approved a quarterly cash dividend in the amount of $0.36 per common share. The dividend is payable December 16, 2024, to shareholders of record as of November 29, 2024. A copy of the press release is attached hereto as Exhibit 99.1 and is incorporated herein by reference in its entirety.
- [ ] `854792081d18541f` — rank 3 · COLB · 8-K · 2024-11-15 · section · Item 8.01. Other Events.  
      > Item 8.01. Other Events. On November 15, 2024, Columbia Banking System, Inc., parent company of Umpqua Bank, announced its Board of Directors has approved a quarterly cash dividend in the amount of $0.36 per common share. The dividend is payable December 16, 2024, to shareholders of record as of November 29, 2024. A copy of the press release is attached hereto as Exhibit 99.1 and is incorporated herein by reference i …
- [ ] `4a46104bc116968e` — rank 4 · COLB · 8-K · 2023-08-14 · paragraph · Item 8.01. Other Events.  
      > On August 14, 2023, Columbia Banking System, Inc., parent company of Umpqua Bank, announced its Board of Directors has approved a quarterly cash dividend in the amount of $0.36 per common share. The dividend is payable September 11, 2023, to shareholders of record as of August 25, 2023. A copy of the press release is attached hereto as Exhibit 99.1 and is incorporated herein by reference in its entirety.
- [ ] `571e48cc86783cde` — rank 5 · COLB · 8-K · 2023-05-15 · paragraph · Item 8.01. Other Events.  
      > On May 15, 2023, Columbia Banking System, Inc., parent company of Umpqua Bank, announced its Board of Directors has approved a quarterly cash dividend in the amount of $0.36 per common share. The dividend is payable June 15, 2023, to shareholders of record as of May 31, 2023. A copy of the press release is attached hereto as Exhibit 99.1 and is incorporated herein by reference in its entirety.
- [ ] `283da21065642d71` — rank 6 · COLB · 8-K · 2024-02-09 · paragraph · Item 8.01. Other Events.  
      > On February 9, 2024, Columbia Banking System, Inc., parent company of Umpqua Bank, announced its Board of Directors has approved a quarterly cash dividend in the amount of $0.36 per common share. The dividend is payable March 11, 2024, to shareholders of record as of February 23, 2024. A copy of the press release is attached hereto as Exhibit 99.1 and is incorporated herein by reference in its entirety.
- [ ] `edf14daa775df0a1` — rank 7 · COLB · 8-K · 2023-08-14 · section · Item 8.01. Other Events.  
      > Item 8.01. Other Events. On August 14, 2023, Columbia Banking System, Inc., parent company of Umpqua Bank, announced its Board of Directors has approved a quarterly cash dividend in the amount of $0.36 per common share. The dividend is payable September 11, 2023, to shareholders of record as of August 25, 2023. A copy of the press release is attached hereto as Exhibit 99.1 and is incorporated herein by reference in i …
- [ ] `e11456c6599676bf` — rank 8 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > We paid regular quarterly cash dividends of $0.30 per share in February 2023 and $0.36 per share in May, August, and November 2023. The annualized dividend yield at year-end 2023 was 5.17%. Prior to the Merger, Columbia Banking System, Inc. ($0.30 cash dividend per share) and Umpqua Holdings Corporation ($0.21 cash dividend per share) paid first quarter 2023 dividends consistent with their respective past practices a …

---

### `r015` — How many votes for did Cort O'Haver receive at Columbia's 2024 annual meeting?

**Already labelled** `b9ffca301705a075` — COLB · 8-K · 2024-05-09 · table  
> Director's Name | Votes For | Votes Against | Abstentions | Broker Non-Votes Cort L. O'Haver | 167921051 | 4610270 | 188995 | 14472750 Craig D. Eerkes | 170333474 | 2216707 | 170135 | 14472750 Mark A. Finkelstein | 165471486 | 7082068 | 166762 | 14472750 Eric S. Forrest | 169862712 | 2689725 | 167879 | 14472750 Peggy Y. Fowler | 164630758 | 7917420 | 172138 | 14472750 Randal L. Lund | 170538451 | 2016004 | 165861 | 1 …

Also answers the question?

- [ ] `f21ee21fe980fd63` — rank 1 · COLB · 8-K · 2023-05-23 · paragraph  
      > On May 18, 2023, Columbia Banking System, Inc. (the “Company”) held its 2023 Annual Meeting of Shareholders (the “2023 Annual Meeting”). There were 208,436,922 shares outstanding and entitled to vote at the 2023 Annual Meeting; of those shares 186,613,645 were present in person or by proxy. The following matters were voted upon at the 2023 Annual Meeting:
- [ ] `8b4003d6e105a31d` — rank 2 · COLB · 8-K · 2022-04-29 · paragraph · Item 5.07. Submission of Matters to a Vote of Security Holders.  
      > On April 27, 2022, Columbia Banking System, Inc. (the “Company”) held its 2022 Annual Meeting of Shareholders (the “2022 Annual Meeting”). There were 78,706,184 shares outstanding and entitled to vote at the 2022 Annual Meeting; of those shares 70,983,256 were present in person or by proxy. The following matters were voted upon at the 2022 Annual Meeting:
- [ ] `20f0689664c654eb` — rank 3 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > The Board set March 11, 2024 as the record date for the meeting (the “Record Date”). Shareholders who owned Columbia common stock at the close of business on that date are entitled to vote at the Annual Meeting, with each share entitled to one vote for each matter to be voted on at the meeting. There were 209,311,089 shares of Columbia common stock outstanding on the Record Date.
- [ ] `38815466e417dff7` — rank 4 · COLB · DEF 14A · 2022-03-18 · paragraph  
      > The Board set March 2, 2022 as the record date for the meeting (the “Record Date”). Shareholders who owned Columbia common stock at the close of business on that date are entitled to vote at the Annual Meeting, with each share entitled to one vote for each matter to be voted on at the meeting. There were 78,706,184 shares of Columbia common stock outstanding on the Record Date.
- [ ] `ed51ecd274ec8ae8` — rank 5 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > Important Notice Regarding the Availability of Proxy Materials for the Annual Meeting: The Notice and Proxy Statement and AR/10K are available at www.proxyvote.com. V33070-P06276 COLUMBIA BANKING SYSTEM, INC. Annual Meeting of Shareholders May 8, 2024 10:00 AM Pacific Time This proxy is solicited by the Board of Directors The undersigned shareholder of COLUMBIA BANKING SYSTEM, INC. (“Columbia”) hereby nominates, cons …
- [ ] `3d15d4bec47d5f42` — rank 6 · UMPQ · 10-K · 2023-02-24 · paragraph · Item 11. EXECUTIVE COMPENSATION  
      > Our say-on-pay resolution at the 2021 annual meeting received a favorable vote from over 95% of the shares voted. Our Compensation Committee considers the results of say-on-pay votes in making compensation decisions. Due to the pending Columbia merger, we did not hold an annual shareholder meeting in 2022.
- [ ] `812ed8d5506b1030` — rank 7 · COLB · 8-K · 2024-05-09 · paragraph  
      > On May 8, 2024, the Company held the 2024 Annual Meeting. There were 209,311,089 shares outstanding and entitled to vote at the 2024 Annual Meeting; of those shares 187,193,066 were present in person or by proxy. The following matters were voted upon at the 2024 Annual Meeting:
- [ ] `d38f6539866fe931` — rank 8 · COLB · 8-K · 2021-05-28 · paragraph · Item 5.07. Submission of Matters to a Vote of Security Holders.  
      > On May 26, 2021, Columbia Banking System, Inc. (the “Company”) held its 2021 Annual Meeting of Shareholders (the “2021 Annual Meeting”). There were 71,739,143 shares outstanding and entitled to vote at the 2021 Annual Meeting; of those shares 66,765,038 were present in person or by proxy. The following matters were voted upon at the 2021 Annual Meeting:

---

### `r016` — How did Columbia's and Umpqua's tangible common equity to tangible assets ratios compare in the merger's selected-companies analysis?

**Already labelled** `bb1e9fa059314a47` — COLB · 8-K · 2022-01-20 · table  
> Selected Companies Columbia | Umpqua | 75th Percentile | Average | Median | 25th Percentile Tangible Common Equity / Tangible Assets | 8.86 | %(1) | 9.09 | % | 8.83 | % | 7.94 | % | 7.95 | % | 7.17 | % Total Risk-Based Capital Ratio | 14.51 | %(1) | 15.41 | % | 15.10 | % | 14.55 | % | 14.54 | % | 14.03 | % Loans HFI / Deposits | 63.3 | %(1) | 84.7 | % | 63.3 | % | 69.4 | % | 66.4 | % | 71.4 | % Loan Loss Reserves / L …

Also answers the question?

- [ ] `128451c10cbb2a7d` — rank 1 · COLB · 10-K · 2024-02-27 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Additionally, management believes tangible common equity and the tangible common equity ratio are meaningful measures of capital adequacy. Columbia believes the exclusion of certain intangible assets in the computation of tangible common equity and the tangible common equity ratio provides a meaningful base for period-to-period and company-to-company comparisons, which management believes will assist investors in ana …
- [ ] `03c4126e3263c236` — rank 2 · UMPQ · 10-Q · 2022-10-31 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended September 30, 2022 and June 30, 2022, where applicable, throughout this Management's Discussion and Analysis.  
      > Additionally, management believes tangible common equity and the tangible common equity ratio are meaningful measures of capital adequacy. Umpqua believes the exclusion of certain intangible assets in the computation of tangible common equity and tangible common equity ratio provides a meaningful base for period-to-period and company-to-company comparisons, which management believes will assist investors in analyzing …
- [ ] `8dcb9624dd8bfb04` — rank 3 · UMPQ · 10-Q · 2022-07-29 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended June 30, 2022 and March 31, 2022, where applicable, throughout this Management's Discussion and Analysis.  
      > Additionally, management believes tangible common equity and the tangible common equity ratio are meaningful measures of capital adequacy. Umpqua believes the exclusion of certain intangible assets in the computation of tangible common equity and tangible common equity ratio provides a meaningful base for period-to-period and company-to-company comparisons, which management believes will assist investors in analyzing …
- [ ] `5d2783803602eba8` — rank 4 · UMPQ · 8-K · 2022-01-20 · table  
      > Selected Companies Columbia | Umpqua | 75th Percentile | Average | Median | 25th Percentile Tangible Common Equity / Tangible Assets | 8.86 | %(1) | 9.09 | % | 8.83 | % | 7.94 | % | 7.95 | % | 7.17 | % Total Risk-Based Capital Ratio | 14.51 | %(1) | 15.41 | % | 15.10 | % | 14.55 | % | 14.54 | % | 14.03 | % Loans HFI / Deposits | 63.3 | %(1) | 84.7 | % | 63.3 | % | 69.4 | % | 66.4 | % | 71.4 | % Loan Loss Reserves / L …
- [ ] `8e791a10d4b5c106` — rank 5 · COLB · S-4 · 2021-11-22 · table  
      > Selected Companies Columbia | Umpqua | 75th Percentile | Average | Median | 25th Percentile Tangible Common Equity / Tangible Assets | 8.86 | %(1) | 9.09 | % | 8.83 | % | 7.94 | % | 7.95 | % | 7.17 | % Total Risk-Based Capital Ratio | 14.51 | %(1) | 15.41 | % | 15.10 | % | 14.55 | % | 14.54 | % | 14.03 | % Loans HFI / Deposits | 63.3 | %(1) | 84.7 | % | 63.3 | % | 69.4 | % | 66.4 | % | 71.4 | % Loan Loss Reserves / L …
- [ ] `5870e2936280906d` — rank 6 · UMPQ · 10-K · 2023-02-24 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Additionally, management believes tangible common equity and the tangible common equity ratio are meaningful measures of capital adequacy. Umpqua believes the exclusion of certain intangible assets in the computation of tangible common equity and the tangible common equity ratio provides a meaningful base for period-to-period and company-to-company comparisons, which management believes will assist investors in analy …
- [ ] `f0f43841dcd84b7b` — rank 7 · UMPQ · 10-Q · 2022-05-05 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended March 31, 2022 and December 31, 2021, where applicable, throughout this Management's Discussion and Analysis.  
      > Additionally, management believes tangible common equity and the tangible common equity ratio are meaningful measures of capital adequacy. Umpqua believes the exclusion of certain intangible assets in the computation of tangible common equity and tangible common equity ratio provides a meaningful base for period-to-period and company-to-company comparisons, which management believes will assist investors in analyzing …
- [ ] `07edfb3adf4c48e4` — rank 8 · UMPQ · 10-K · 2021-02-25 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Additionally, management believes tangible common equity and the tangible common equity ratio are meaningful measures of capital adequacy. Umpqua believes the exclusion of certain intangible assets in the computation of tangible common equity and tangible common equity ratio provides a meaningful base for period-to-period and company-to-company comparisons, which management believes will assist investors in analyzing …

---

### `r017` — What does Columbia's pay-versus-performance chart show about compensation actually paid versus total shareholder return for 2020 through 2022?

**Already labelled** `15ef55e673d4b42f` — COLB · DEF 14A · 2023-04-06 · chart_description  
> This dual-axis combination bar and line chart compares executive compensation against total shareholder return across fiscal years 2020, 2021, and 2022. The left vertical axis measures "Compensation Actually Paid ($M)" using bar graphs for "CEO CAP" and "Average Non-CEO NEO CAP," while the right vertical axis tracks "Total Shareholder Return" using line graphs for "COLB TSR" and a peer benchmark ("KRX TSR"). Overall, …

Also answers the question?

- [ ] `20b58178dd453944` — rank 1 · COLB · DEF 14A · 2020-04-17 · paragraph  
      > The compensation of our executives for 2019 is closely aligned with 2019 shareholder returns and Company financial performance, neither of which were affected by the COVID-19 pandemic. In 2019, Columbia had strong financial results including significant increases in net income and shareholder return. The compensation of our executives increased along with our strong performance and Columbia’s growth. We recognize tha …
- [ ] `a2fa04c876439286` — rank 2 · SSB · DEF 14A · 2023-03-10 · paragraph  
      > The table below reflects compensation of the Company’s Principal Executive Officer (“PEO”) and average compensation pf the Company’s non-PEO NEOs during 2020 through 2022, both as reported in the Summary Compensation Table and with certain adjustments to reflect the "compensation actually paid”, as defined under SEC rules. In addition, the table provides our cumulative Total Shareholder Return (“TSR”), the cumulative …
- [ ] `a46977ddc2f4de86` — rank 3 · SSB · DEF 14A · 2024-03-08 · paragraph  
      > The table below reflects compensation of the Company’s Principal Executive Officer (“PEO”) and average compensation of the Company’s non-PEO NEOs during 2020 through 2023, both as reported in the Summary Compensation Table and with certain adjustments to reflect the "compensation actually paid”, as defined under SEC rules. In addition, the table provides our cumulative Total Shareholder Return (“TSR”), the cumulative …
- [ ] `775105dbe0a986fc` — rank 4 · COLB · DEF 14A · 2023-04-06 · chart_description  
      > This is a line chart titled "Total Return Performance" comparing the stock performance of Columbia Banking System, Inc. against the KBW Nasdaq Regional Banking Index. The horizontal axis covers an annual timeframe from December 31, 2017, to December 31, 2022, with the vertical axis representing the Index Value starting from a base of 100. Both series track closely together from late 2017 through 2020; after 2020, the …
- [ ] `d9c0634673d1d547` — rank 5 · GBCI · DEF 14A · 2024-03-15 · paragraph  
      > The Compensation and Human Capital Committee determined the number of RSUs to be granted in 2023 based on the achievement of the performance goals in 2022, as described in the table below, excluding the impact of any acquisitions during the year. The 2022 LTIP goals were selected in light of Glacier’s long-term strategic plan, long-term initiatives and the need to balance risks in executive compensation arrangements. …
- [ ] `fd946344a46c9a85` — rank 6 · WSBC · 10-K · 2023-02-27 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > As of December 31, 2022, contingently issuable shares totaling 53,280 were estimated to be awarded under the 2022, 2021 and 2020 total shareholder return plans as stock performance targets were met to date and were included in the diluted calculation. No shares were contingently issuable as of December 31, 2021 and 2020 because the performance criteria was not met at that time and the effect would be antidilutive. In …
- [ ] `0ec7793931826c79` — rank 7 · GBCI · DEF 14A · 2023-03-15 · paragraph  
      > (5) We determined Return on Tangible Equity to be the most important financial performance measure used to link Company performance to Compensation Actually Paid to our PEO and Non-PEO NEOs in 2022. This performance measure may not have been the most important financial performance measure for years 2021 and 2020 and we may determine a different financial performance measure to be the most important financial perform …
- [ ] `6140e060ab3d9fee` — rank 8 · COLB · 10-K · 2022-02-25 · paragraph · Item 5. MARKET FOR REGISTRANT’S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES  
      > The following graph shows a five-year comparison of the total return to shareholders of Columbia’s common stock, the NASDAQ Composite Index (which is a broad nationally recognized index of stock performance by companies listed on the Nasdaq Stock Market) and the KBW Regional Banking Index (comprised of 50 banks and bank holding companies headquartered throughout the country, including Columbia).

---

### `r018` — How did Columbia's stock perform against the KBW Nasdaq Regional Banking Index between 2017 and 2022?

**Already labelled** `775105dbe0a986fc` — COLB · DEF 14A · 2023-04-06 · chart_description  
> This is a line chart titled "Total Return Performance" comparing the stock performance of Columbia Banking System, Inc. against the KBW Nasdaq Regional Banking Index. The horizontal axis covers an annual timeframe from December 31, 2017, to December 31, 2022, with the vertical axis representing the Index Value starting from a base of 100. Both series track closely together from late 2017 through 2020; after 2020, the …

Also answers the question?

- [ ] `59a1307879d0d11a` — rank 1 · COLB · 10-K · 2020-02-27 · chart_description  
      > This line chart titled "Total Return Performance" plots cumulative index values across annual periods ending from December 31, 2014, to December 31, 2019. It compares the total returns of Columbia Banking System, Inc. against the NASDAQ Composite and the KBW Regional Banking Index. All three series start at a baseline value of 100 and show an overall upward trend over the five-year span, with Columbia Banking System …
- [ ] `3868ec6292f49954` — rank 2 · COLB · 10-K · 2023-02-24 · table  
      > Index | Period Ending Index | 12/31/2017 | 12/31/2018 | 12/31/2019 | 12/31/2020 | 12/31/2021 | 12/31/2022 Columbia Banking System, Inc. | 100.00 | 85.96 | 100.06 | 92.43 | 86.66 | 82.97 NASDAQ Composite | 100.00 | 97.16 | 132.81 | 192.47 | 235.15 | 158.65 KBW Regional Banking Index | 100.00 | 82.50 | 102.15 | 93.25 | 127.42 | 118.59
- [ ] `030ed6e18ca5d1c7` — rank 3 · COLB · 10-K · 2023-02-24 · section · Item 5. MARKET FOR REGISTRANT’S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES  
      > Item 5. MARKET FOR REGISTRANT’S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES The Company’s common stock is traded on the Nasdaq Global Select Market of The Nasdaq Stock Market LLC under the symbol “COLB.” At January 31, 2023, the number of shareholders of record was 3,040. This figure does not represent the actual number of beneficial owners of common stock because shares are f …
- [ ] `ce8b6d8e43c18e5b` — rank 4 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > The Company’s total shareholder return (“TSR”) was -5.9% for 2023, compared to the KBW Regional Banking Index (“KRX”) performance of -0.4% and the new peer group performance of 5.3%. The lingering impact of the prolonged approval process for the Merger, the post-Merger operational integration, and growing into the new peer group are factors that management believes contributed to the Company’s underperformance compar …
- [ ] `6140e060ab3d9fee` — rank 5 · COLB · 10-K · 2022-02-25 · paragraph · Item 5. MARKET FOR REGISTRANT’S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES  
      > The following graph shows a five-year comparison of the total return to shareholders of Columbia’s common stock, the NASDAQ Composite Index (which is a broad nationally recognized index of stock performance by companies listed on the Nasdaq Stock Market) and the KBW Regional Banking Index (comprised of 50 banks and bank holding companies headquartered throughout the country, including Columbia).
- [ ] `6648380cf7721c35` — rank 6 · COLB · 10-K · 2021-02-26 · paragraph · Item 5. MARKET FOR REGISTRANT’S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES  
      > The following graph shows a five-year comparison of the total return to shareholders of Columbia’s common stock, the NASDAQ Composite Index (which is a broad nationally recognized index of stock performance by companies listed on the Nasdaq Stock Market) and the KBW Regional Banking Index (comprised of 50 banks and bank holding companies headquartered throughout the country, including Columbia).
- [ ] `cbe596d9c73b219d` — rank 7 · COLB · 10-K · 2020-02-27 · paragraph · Item 4. MINE SAFETY DISCLOSURES  
      > The following graph shows a five-year comparison of the total return to shareholders of Columbia’s common stock, the NASDAQ Composite Index (which is a broad nationally recognized index of stock performance by companies listed on the Nasdaq Stock Market) and the KBW Regional Banking Index (comprised of 50 banks and bank holding companies headquartered throughout the country, including Columbia).
- [ ] `f0dd8805a98797ef` — rank 8 · COLB · 10-K · 2023-02-24 · paragraph · Item 5. MARKET FOR REGISTRANT’S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES  
      > The following graph shows a five-year comparison of the total return to shareholders of Columbia’s common stock, the NASDAQ Composite Index (which is a broad nationally recognized index of stock performance by companies listed on the Nasdaq Stock Market) and the KBW Regional Banking Index (comprised of 50 banks and bank holding companies headquartered throughout the country, including Columbia).

---

### `r019` — What restricted stock awards did Mr. McDonald hold, and on what schedule did they vest?

**Already labelled** `541ebb8c9300e53a` — COLB · DEF 14A · 2020-04-17 · paragraph  
> For Mr. McDonald, represents 1,362 shares of Restricted Stock granted on February 24, 2016 that vest on February 24, 2020; 1,724 shares of Restricted Stock granted on February 22, 2017 that vest 37.5% on the third anniversary of the date of grant and 62.5% on the fourth anniversary of the grant date, respectively; 2,214 shares of restricted stock granted on February 28, 2018 that vest 20% on the second anniversary of …

Also answers the question?

- [ ] `9340cda47cd5719e` — rank 1 · COLB · DEF 14A · 2022-03-18 · paragraph  
      > For Mr. McDonald, represents 1,107 shares of Restricted Stock granted on February 28, 2018 that vest 100% on February 28, 2022; 2,385 shares of Restricted Stock granted on March 27, 2019 that vest 100% on January 1, 2022; 6,000 shares of Restricted Stock granted on January 22, 2020 that vest 100% on January 22, 2022; 2,114 Restricted Stock Units granted on February 27, 2020 that vest 50% each year on February 15, 202 …
- [ ] `2213cb42393c8059` — rank 2 · COLB · DEF 14A · 2021-04-12 · paragraph  
      > For Mr. McDonald, represents 1,078 shares of Restricted Stock granted on February 22, 2017 that vest on February 22, 2021; 1,771 shares of Restricted Stock granted on February 28, 2018 that vest 37.5% on the third anniversary and 62.5% on the fourth anniversary of the grant date, respectively; 2,982 shares of Restricted Stock granted on March 27, 2019 that vest 20% on the second anniversary of the grant date, 30% on …
- [ ] `80e9da96b9481988` — rank 3 · COLB · DEF 14A · 2022-03-18 · paragraph  
      > For 2020, amounts shown include (a) the grant date fair value of Restricted Stock Units granted on February 27, 2020 (or, in the case of Mr. Deer, on April 27, 2020) that vest one-third each year on February 15, 2021, 2022, and 2023, (b) in the case of Mr. McDonald, his Restricted Stock award granted on January 22, 2020 that vests 100% on January 22, 2022, and (c) the grant date fair value of Performance Stock Units …
- [ ] `a956c2315d0ea877` — rank 4 · COLB · DEF 14A · 2020-04-17 · paragraph  
      > For 2017, amounts shown include the grant date fair value of (a) Restricted Stock awards granted on February 22, 2017 that vest 20% on the second anniversary of grant date, 30% on the third anniversary of grant date and the remaining 50% vesting on February 22, 2021, (b) in the case of Messrs. Robbins and Stein, Restricted Stock awards granted on April 26, 2017 that vest on April 26, 2019, (c) in the case of Mr. Robb …
- [ ] `db64f1000c1d4f3b` — rank 5 · COLB · DEF 14A · 2022-03-18 · paragraph  
      > For 2019, amounts shown include (a) the grant date fair value of Restricted Stock awards granted on March 27, 2019 that vest 20% on the second anniversary of grant date, 30% on the third anniversary of grant date and the remaining 50% vesting on March 27, 2023, and (b) the grant date fair value of Performance Shares granted on March 27, 2019 for the period commencing January 1, 2019 and ending December 31, 2021 (the …
- [ ] `8419c649d4c00398` — rank 6 · COLB · DEF 14A · 2022-03-18 · paragraph  
      > For Mr. McDonald, represents the fair market value of 1,078 shares of Restricted Stock granted in 2017 that vested on February 22, 2021, 664 shares of Restricted Stock granted in 2018 that vested on February 28, 2021, 597 shares of Restricted Stock granted in 2019 that vested on March 27, 2021 and 1,090 Restricted Stock Units granted in 2021 that vested on February 15, 2021.
- [ ] `5692d6eba7616db6` — rank 7 · COLB · DEF 14A · 2020-04-17 · paragraph  
      > For Mr. McDonald, represents the fair market value of 1,058 shares of restricted stock granted in 2015 that vested on March 25, 2019, 817 shares of restricted stock granted in 2016 that vested on February 22, 2019, 432 shares of restricted stock granted in 2017 that vested on February 22, 2019 and 2,473 performance shares granted in 2017 that vested on December 31, 2019.
- [ ] `edb12ebe1836920a` — rank 8 · COLB · DEF 14A · 2021-04-12 · paragraph  
      > For Mr. McDonald, represents the fair market value of 1,362 shares of Restricted Stock granted in 2016 that vested on February 24, 2020, 646 shares of Restricted Stock granted in 2017 that vested on February 22, 2020 and 443 shares of Restricted Stock granted in 2018 that vested on February 28, 2020.

---

### `r020` — How does Columbia calculate ROTCE Performance for PSU vesting, and what example does the proxy give?

**Already labelled** `eb382b5245e950d6` — COLB · DEF 14A · 2024-03-27 · paragraph  
> For example, if the Company’s Average ROTCE is 15% and the Peer Group Average ROTCE is 16%, for the 2023-2025 period, ROTCE Performance is equal to 93.75% (15 divided by 16), resulting in 93.75% award vesting. If over the same performance period the Company TSR is 20% and the Peer Group TSR is 16%, TSR Performance is 125%, resulting in 125% award vesting. When ROTCE Performance or TSR Performance matches the peer gro …

Also answers the question?

- [ ] `7912c475741b6ad4` — rank 1 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > In February 2023, Columbia and Umpqua granted PSUs that are to be earned and vest at the end of the three fiscal year performance period ending December 31, 2026, based on achievement levels of our TSR and our ROTCE compared to the Peer Group. The NEOs also received RSUs that vest ratably over three years subject to continued service. The Committee set these long-term incentive targets based on peer and market data f …
- [ ] `a52bf60fcabb6558` — rank 2 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > The vesting of PSUs will be determined based on the Company’s achievement of Threshold, Target or Maximum levels of TSR Performance and ROTCE Performance as follows:
- [ ] `c2ac17fbd6ed0591` — rank 3 · UMPQ · 10-K · 2022-02-25 · paragraph · Item 11. EXECUTIVE COMPENSATION  
      > * When performance is between 50% and 100% relative to peers, such results will be interpolated on a straight-line basis to determine the applicable vesting percentage. For example, TSR or ROATCE performance of 80% or 111% will result in 80% or 111%, respectively, of the award vesting.
- [ ] `d4e0f8a304c363c1` — rank 4 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > ROTCE Performance is equal to the quotient resulting from dividing Company Average ROTCE by the Peer Group Average ROTCE. Company Average ROTCE is calculated by dividing the sum of the Company’s ROTCE for 2023, 2024 and 2025 by three. Peer Group Average ROTCE is the sum of each peer company’s Peer ROTCE divided by the number of peers. Peer ROTCE is calculated in the same manner as the Company’s ROTCE—the sum of a pee …
- [ ] `25e2bce344a6a7d0` — rank 5 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > The Committee selected two performance metrics for the PSUs with half of the awards to vest based on ROTCE and half based on TSR performance, both relative to the peer group approved by the Committee and discussed above in “Compensation Philosophy and Process – Considerations in Determining Compensation – Peer Group.” We believe TSR directly links executive compensation to the returns realized by our shareholders, an …
- [ ] `4945fe171f923ac1` — rank 6 · COLB · 10-K · 2024-02-27 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > In connection with the Merger, all outstanding restricted equity units granted under UHC’s equity plans were legally assumed by Columbia and adjusted so that its holder was entitled to receive shares of Columbia's common stock equal to the product of (a) the number of shares of UHC common stock subject to such award multiplied by (b) the Exchange Ratio and (c) rounded to the nearest whole share of Columbia common sto …
- [ ] `ba7663ad5dbe4ab2` — rank 7 · COLB · 10-K · 2024-02-27 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > In connection with the Merger, all outstanding and unvested performance-based restricted stock units and time-vesting restricted stock units and awards, granted under Columbia's equity plans, that were outstanding immediately before the Merger Date continued to be units or awards in respect of Columbia common stock following the Merger, subject to the same terms and conditions that were applicable to such awards befo …
- [ ] `8c1483a72378d120` — rank 8 · UMPQ · 8-K · 2023-03-01 · paragraph  
      > Pursuant to the Merger Agreement, at the Effective Time, each outstanding Umpqua equity award granted under Umpqua’s equity compensation plans was generally converted into a corresponding award with respect to Columbia Common Stock, with the number of shares underlying such award (and, in the case of stock options, the applicable exercise price) adjusted based on the Exchange Ratio. Each such converted Columbia equit …

---

### `r021` — What was the racial and gender composition of Columbia's workforce reported in the 2021 proxy statement?

**Already labelled** `774bc0ac5ad6820f` — COLB · DEF 14A · 2021-04-12 · table  
> % of Total RACE | Male | Female | Total American Indian or Alaska Native | 0.14% | 0.46% | 0.60% Asian | 1.60% | 3.39% | 4.99% Black or African American | 1.24% | 1.05% | 2.29% Hispanic or Latino | 1.65% | 4.71% | 6.36% Native Hawaiian or Other Pacific Islander | 0.50% | 0.73% | 1.23% Two or More Races | 0.64% | 1.37% | 2.01% White | 22.23% | 51.28% | 73.51% Not Specified | 3.47% | 5.54% | 9.01% Total | 31.47% | 68.5 …

Also answers the question?

- [ ] `a44bb5cf05b0ffb2` — rank 1 · COLB · 8-K · 2021-10-12 · paragraph  
      > 2021 Annual Meeting of Shareholders, which was filed with the SEC on March 5, 2021, and other documents filed by Umpqua with the SEC. Information regarding Columbia’s directors and executive officers is available in Columbia’s definitive proxy statement relating to its 2021 Annual Meeting of Shareholders, which was filed with the SEC on April 12, 2021, and other documents filed by Columbia with the SEC. Other informa …
- [ ] `3b9fe823789b555c` — rank 2 · COLB · 8-K · 2022-01-20 · paragraph · Item 8.01. Other Events.  
      > The six additional continuing Umpqua directors and the five additional continuing Columbia directors will be designated prior to closing by the Umpqua board and the Columbia board, respectively, with the goal of establishing a combined board with strong and relevant skills, deep industry knowledge and a diversity of experiences and backgrounds. The compensation received by Columbia’s directors for 2020 is described i …
- [ ] `c8c4e06ee2dfbaf8` — rank 3 · UMPQ · 8-K · 2022-01-20 · paragraph  
      > The six additional continuing Umpqua directors and the five additional continuing Columbia directors will be designated prior to closing by the Umpqua board and the Columbia board, respectively, with the goal of establishing a combined board with strong and relevant skills, deep industry knowledge and a diversity of experiences and backgrounds. The compensation received by Columbia’s directors for 2020 is described i …
- [ ] `0a2ff6e048d55560` — rank 4 · UMPQ · 8-K · 2022-01-20 · paragraph  
      > Umpqua, Columbia, and certain of their respective directors and executive officers may be deemed to be participants in the solicitation of proxies from the shareholders of Umpqua and Columbia in connection with the Proposed Transaction under the rules of the SEC. Information regarding Umpqua’s directors and executive officers is available in Umpqua’s definitive proxy statement relating to its 2021 Annual Meeting of S …
- [ ] `6da1376f42e85780` — rank 5 · COLB · 8-K · 2022-01-20 · paragraph · Item 8.01. Other Events.  
      > Umpqua, Columbia, and certain of their respective directors and executive officers may be deemed to be participants in the solicitation of proxies from the shareholders of Umpqua and Columbia in connection with the Proposed Transaction under the rules of the SEC. Information regarding Umpqua’s directors and executive officers is available in Umpqua’s definitive proxy statement relating to its 2021 Annual Meeting of S …
- [ ] `5091e8b7d27048f4` — rank 6 · COLB · 8-K · 2021-10-15 · paragraph  
      > Umpqua, Columbia, and certain of their respective directors and executive officers may be deemed to be participants in the solicitation of proxies from the shareholders of Umpqua and Columbia in connection with the Transaction under the rules of the SEC. Information regarding Umpqua’s directors and executive officers is available in Umpqua’s definitive proxy statement relating to its 2021 Annual Meeting of Shareholde …
- [ ] `646d84b8f2df0203` — rank 7 · UMPQ · 8-K · 2021-10-15 · paragraph · Item 9.01. Financial Statements and Exhibits.  
      > Umpqua, Columbia, and certain of their respective directors and executive officers may be deemed to be participants in the solicitation of proxies from the shareholders of Umpqua and Columbia in connection with the Transaction under the rules of the SEC. Information regarding Umpqua’s directors and executive officers is available in Umpqua’s definitive proxy statement relating to its 2021 Annual Meeting of Shareholde …
- [ ] `98b04031aa78e3b9` — rank 8 · UMPQ · 8-K · 2021-10-12 · paragraph · Item 9.01. Financial Statements and Exhibits.  
      > Umpqua, Columbia, and certain of their respective directors and executive officers may be deemed to be participants in the solicitation of proxies from the shareholders of Umpqua and Columbia in connection with the Transaction under the rules of the SEC. Information regarding Umpqua’s directors and executive officers is available in Umpqua’s definitive proxy statement relating to its 2021 Annual Meeting of Shareholde …

---

### `r022` — What percentage of Columbia's workforce identified as White in the 2022 proxy statement?

**Already labelled** `1a5161e301841e45` — COLB · DEF 14A · 2022-03-18 · table  
> ​ | % of Total | ​ ​ | RACE | ​ | Male | ​ | Female | ​ | Not Specified | ​ | Total | ​ ​ | American Indian or Alaska Native | ​ | 0.13% | ​ | 0.44% | ​ | — | ​ | 0.57% | ​ ​ | Asian | ​ | 1.64% | ​ | 3.67% | ​ | — | ​ | 5.31% | ​ ​ | Black or African American | ​ | 0.89% | ​ | 1.06% | ​ | — | ​ | 1.95% | ​ ​ | Hispanic or Latino | ​ | 1.50% | ​ | 4.03% | ​ | 0.04% | ​ | 5.57% | ​ ​ | Native Hawaiian or Other Pacific …

Also answers the question?

- [ ] `35279420ca188ec6` — rank 1 · COLB · DEF 14A · 2022-03-18 · paragraph  
      > As of March 2, 2022 (except as otherwise noted), the shareholders identified in the table below beneficially owned more than 5% of the outstanding Columbia shares. To the Company’s knowledge, based on the public filings which beneficial owners of more than 5% of the outstanding shares of Columbia common shares are required to make with the SEC, there are no other beneficial owners of more than 5% of the outstanding C …
- [ ] `f4bb6387cdd5019e` — rank 2 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > As of March 11, 2024 (except as otherwise noted), the shareholders identified in the table below beneficially owned more than 5% of the outstanding Columbia shares. To the Company’s knowledge, based on the public filings which beneficial owners of more than 5% of the outstanding shares of Columbia common shares are required to make with the SEC, there are no other beneficial owners of more than 5% of the outstanding …
- [ ] `d79dea3b59a12bd2` — rank 3 · COLB · 8-K · 2023-03-01 · paragraph  
      > In connection with her appointment as Corporate Controller, Principal Accounting Officer, Columbia entered into a letter agreement with Ms. White, dated March 1 (the “White Letter Agreement”), which provides for a cash retention award of $75,000 (the “White Integration Award”), with 34% of such award vesting on the Systems Conversion Date and 33% vesting on each of the first and second anniversaries of the Systems Co …
- [ ] `6ab128a9469d6370` — rank 4 · COLB · DEF 14A · 2021-04-12 · paragraph  
      > As of March 17, 2021 (except as otherwise noted), the shareholders identified in the table below beneficially owned more than 5% of the outstanding Columbia shares. To the Company’s knowledge, based on the public filings which beneficial owners of more than 5% of the outstanding shares of Columbia common shares are required to make with the SEC, there are no other beneficial owners of more than 5% of the outstanding …
- [ ] `a0439c029a645ece` — rank 5 · COLB · DEF 14A · 2022-03-18 · paragraph  
      > The Board recommends a vote (i) FOR the election of the director nominees listed in this proxy statement, (ii) FOR the approval, on an advisory basis (non-binding), of the compensation of Columbia’s named executive officers, and (iii) FOR the ratification of Deloitte as the independent registered public accounting firm for the fiscal year 2022.
- [ ] `91be0512a9c3c4bb` — rank 6 · COLB · DEF 14A · 2020-04-17 · paragraph  
      > As of March 13, 2020 (except as otherwise noted), the shareholders identified in the table below beneficially owned more than 5% of the outstanding Columbia shares. To the Company’s knowledge, based on the public filings which beneficial owners of more than 5% of the outstanding shares of Columbia common shares are required to make with the SEC, there are no other beneficial owners of more than 5% of the outstanding …
- [ ] `5caf551c23a51698` — rank 7 · COLB · 8-K · 2022-01-28 · paragraph · Item 5.07. Submission of Matters to a Vote of Security Holders.  
      > On January 26, 2022, Columbia Banking System, Inc. (“Columbia”) held a virtual special meeting of shareholders (the “Special Meeting”) in connection with the Agreement and Plan of Merger, dated as of October 11, 2021 (the “Merger Agreement”), among Columbia, Umpqua Holdings Corporation (“Umpqua”) and Cascade Merger Sub, Inc., a direct, wholly owned subsidiary of Columbia (“Merger Sub”). Pursuant to the Merger Agreeme …
- [ ] `998cbf2e7f21a026` — rank 8 · COLB · 8-K · 2022-01-28 · section · Item 5.07. Submission of Matters to a Vote of Security Holders.  
      > Item 5.07. Submission of Matters to a Vote of Security Holders. On January 26, 2022, Columbia Banking System, Inc. (“Columbia”) held a virtual special meeting of shareholders (the “Special Meeting”) in connection with the Agreement and Plan of Merger, dated as of October 11, 2021 (the “Merger Agreement”), among Columbia, Umpqua Holdings Corporation (“Umpqua”) and Cascade Merger Sub, Inc., a direct, wholly owned subsi …

---

### `r023` — What discount rates and terminal multiples did Raymond James use in its discounted cash flow analysis of Bank of Commerce Holdings?

**Already labelled** `438a8cc7fce5a114` — COLB · S-4 · 2021-08-06 · paragraph  
> The discounted cash flow analysis was based solely on the projections. Consistent with the periods included in the projections, Raymond James used calendar year 2025 as the final year for the analysis and applied multiples, ranging from 13.0x to 15.0x, to calendar year 2025 adjusted net income in order to derive a range of terminal values for BOCH in 2025. The projected free cash flows and terminal values were discou …

Also answers the question?

- [ ] `b711ac21e684bfcc` — rank 1 · COLB · S-4 · 2021-08-06 · paragraph  
      > Discounted Cash Flow Analysis. Raymond James analyzed the discounted present value of BOCH’s projected free cash flows for the nine months ending December 31, 2021 and the 12 months ending December 31, 2022 through December 31, 2025 on a standalone basis, which were provided to Raymond James and approved for its use by BOCH. Raymond James used tangible common equity in excess of a target ratio of 8.0% of tangible ass …
- [ ] `1608c7c8cbb94e7b` — rank 2 · COLB · S-4 · 2021-08-06 · paragraph  
      > The resulting range of present equity values was divided by the number of diluted shares outstanding. Raymond James reviewed the range of per share prices derived in the discounted cash flow analysis and compared them to $16.70, the value attributed to the per share merger consideration for purposes of the Raymond James opinion. The results of the discounted cash flow analysis indicated a range of values from $13.62 …
- [ ] `7428862ba83dd113` — rank 3 · COLB · S-4 · 2021-08-06 · paragraph  
      > In connection with its analysis, Raymond James considered and discussed with BOCH’s management how the discounted cash flow analysis would be affected by changes in the underlying assumptions. Raymond James noted that discounted cash flow analysis is a widely used valuation methodology, but the results of such methodology are highly dependent upon the numerous assumptions that must be made, and the results are not ne …
- [ ] `32690d9f88b23ee5` — rank 4 · COLB · S-4 · 2021-08-06 · paragraph  
      > Raymond James examined valuation multiples of transaction value compared to the target companies’ (i) most recent quarter tangible book value at announcement; (ii) last twelve months earnings at the time of announcement; and (iii) premium to core deposits (total deposits less time deposits greater than $100,000). Raymond James adjusted earnings of subchapter S corporations using an effective tax rate of 21%. Raymond …
- [ ] `1684587066017f34` — rank 5 · COLB · S-4 · 2021-08-06 · paragraph  
      > Furthermore, Raymond James applied the 75th percentile, median, mean and 25th percentile relative valuation multiples for the selected regional and national transactions to BOCH’s tangible book value, last twelve months earnings, and core deposits. Raymond James then compared those implied values to $16.70, the value attributed to the per share merger consideration for the purposes of the Raymond James opinion. The r …
- [ ] `af3c80af8e7f76e2` — rank 6 · COLB · S-4 · 2021-08-06 · paragraph  
      > Furthermore, Raymond James applied the 75th percentile, median, mean and 25th percentile relative valuation multiples for each of the metrics to BOCH’s actual financial results to derive an implied transaction value. Raymond James then compared those implied values to $16.70, the value attributed to the per share merger consideration for the purposes of the Raymond James opinion. The results of this analysis are summ …
- [ ] `477cd71262faa03b` — rank 7 · UMPQ · 10-K · 2021-02-25 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > The Company performed a quantitative analysis of the Wholesale Bank and Retail Bank reporting units, by comparing the fair value of these reporting units with their carrying amount. The Company estimated the fair value of its Wholesale Bank and Retail Bank reporting units using an income approach to estimate the fair value of both reporting units. The income approach estimates the fair value of the reporting units by …
- [ ] `63e5ec8cad130974` — rank 8 · UMPQ · 10-K · 2021-02-25 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > The Company performed a quantitative assessment of goodwill for the Wholesale Bank and Retail Bank reporting units as of March 31, 2020, by comparing the fair value of each of these reporting units with their carrying amount. The Company estimated the fair value of these reporting units using an income approach that estimated the fair values by discounting management's projections of the reporting units' cash flows, …

---

### `r024` — What were Bank of Commerce Holdings' total assets, net loans, and total deposits at March 31, 2021?

**Already labelled** `4fceae56931a7839` — COLB · S-4 · 2021-08-06 · paragraph  
> Headquartered in Sacramento, California, BOCH is the holding company of Merchants Bank of Commerce, which we refer to as Merchants Bank, a California state-chartered commercial bank, with deposits insured by the FDIC. At July 22, 2021, Merchants Bank had 10 full service facilities, one internet banking branch, one limited service facility, and one loan production office in northern California. BOCH provides a wide ra …

Also answers the question?

- [ ] `9e012190e094e5f2` — rank 1 · COLB · 10-K · 2022-02-25 · paragraph · Item 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > •Total assets at December 31, 2021 were $20.95 billion, up 26%, or $4.36 billion from $16.58 billion at the end of 2020 due to organic growth as well as our acquisition of Bank of Commerce.
- [ ] `eee8c6d89c12e52f` — rank 2 · COLB · 10-Q · 2020-05-08 · paragraph · Item 1. FINANCIAL STATEMENTS  
      > Total assets were $14.04 billion at March 31, 2020, a decrease of $41.0 million from December 31, 2019. Cash and cash equivalents decreased $31.9 million. Loans increased $189.9 million during the first quarter of 2020, which was primarily the result of new loan production and increased seasonal line utilization, partially offset by payments. Debt securities available for sale were $3.55 billion at March 31, 2020, a …
- [ ] `9bea9f670cbfca70` — rank 3 · COLB · 10-K · 2022-02-25 · paragraph · Item 9A. CONTROLS AND PROCEDURES  
      > As described in Management’s Annual Report on Internal Control Over Financial Reporting, management excluded from its assessment the internal control over financial reporting at Bank of Commerce Holdings, which was acquired on October 1, 2021 and whose financial data results constituted, of the consolidated financial statements amounts, approximately 10% of loans (net of allowance for credit losses), 10% of deposits, …
- [ ] `0c0649478ac4b9c2` — rank 4 · COLB · 10-K · 2022-02-25 · paragraph · Item 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Our total assets increased 26% to $20.95 billion at December 31, 2021 from $16.58 billion at December 31, 2020. The acquisition of the Bank of Commerce during 2021 was a driver for the increase to total assets along with increases to other line items on our balance sheet. See Note 2 to the Consolidated Financial Statements in “Item 8. Financial Statements and Supplementary Data” of this report for further information …
- [ ] `fe85e47d68dceefd` — rank 5 · UMPQ · 10-Q · 2022-05-05 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended March 31, 2022 and December 31, 2021, where applicable, throughout this Management's Discussion and Analysis.  
      > The Company's total core deposits, which are deposits less time deposits greater than $250,000 and all brokered deposits, were $26.1 billion at March 31, 2022, compared to $26.0 billion at December 31, 2021. The Company's brokered deposits totaled $140.3 million at March 31, 2022, compared to $149.9 million at December 31, 2021.
- [ ] `6f18a3452839d078` — rank 6 · UMPQ · 10-Q · 2022-05-05 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended March 31, 2022 and December 31, 2021, where applicable, throughout this Management's Discussion and Analysis.  
      > Total deposits were $26.7 billion at March 31, 2022, an increase of $104.9 million, as compared to December 31, 2021. The increase is mainly attributable to growth in demand and savings deposits, offset by a continued decline in time deposits and a decrease in money market deposits. Time deposits continue to decline as the Bank continues to allow these higher-cost deposits to run off.
- [ ] `d7c3848904c1b1cb` — rank 7 · COLB · 10-K · 2022-02-25 · paragraph · Item 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Deposits totaled $18.01 billion at December 31, 2021 compared to $13.87 billion at December 31, 2020. The increase of $4.14 billion was due to the acquisition of Bank of Commerce, which added $1.74 billion, and organic growth. Noninterest-bearing deposits, interest-bearing deposits, and reciprocal money market accounts provide a stable source of low cost funding.
- [ ] `7afac85150b89237` — rank 8 · UMPQ · 10-Q · 2022-05-05 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended March 31, 2022 and December 31, 2021, where applicable, throughout this Management's Discussion and Analysis.  
      > •Total consolidated assets were $30.6 billion as of March 31, 2022 and December 31, 2021. Total consolidated assets remained relatively flat as the increase in loans and leases as well as the MSR asset was offset by a decline in investment securities during the quarter.

---

### `r025` — Under which state's business corporation act are Columbia's directors and officers indemnified?

**Already labelled** `071238bfd78723eb` — COLB · S-4 · 2021-11-22 · section · Item 20. Indemnification of Directors and Officers  
> Item 20. Indemnification of Directors and Officers Sections 23B.08.500 through 23B.08.603 of the WBCA contain specific provisions relating to indemnification of directors and officers of Washington corporations. In general, the statute provides that a corporation may indemnify an individual made a party to a proceeding because the individual is or was a director against liability incurred in the proceeding if: (i) th …

Also answers the question?

- [ ] `ae2ade95b9737fbe` — rank 1 · GBCI · DEF 14A · 2021-03-16 · paragraph  
      > The Board recommends that shareholders adopt an amendment to the Articles to provide for indemnification of directors and officers. Indemnification of directors and officers is currently addressed in the Company’s bylaws. The Montana Business Corporation Act was amended effective June 1, 2020, to permit broader indemnification of a corporation’s directors than had been authorized under the statutory provisions previo …
- [ ] `3ebb3354c0ec2604` — rank 2 · GBCI · S-4 · 2023-09-14 · section · Item 20. Indemnification of Directors and Officers  
      > Item 20. Indemnification of Directors and Officers Sections 35-14-850 through 35-1-858 of the Montana Business Corporation Act (“MBCA”) contain specific provisions relating to indemnification of directors and officers of Montana corporations. In general, the statute provides that (i) a corporation must indemnify a director or officer who is wholly successful in the defense of a proceeding to which the director or off …
- [ ] `0d8e043af363aa4e` — rank 3 · WSBC · S-4 · 2024-10-04 · section · Item 20. Indemnification of Directors and Officers.  
      > Item 20. Indemnification of Directors and Officers. Wesbanco’s amended and restated bylaws (the “Bylaws”) provide, and West Virginia law permits, the indemnification of directors and officers against certain liabilities. Officers and directors of Wesbanco and its subsidiaries are indemnified, to the maximum extent permitted under the West Virginia Business Corporation Act (including advanced indemnification payments) …
- [ ] `710e462c8e361ddf` — rank 4 · GBCI · S-4 · 2021-07-02 · paragraph · Item 20. Indemnification of Directors and Officers  
      > Sections 35-1-451 through 35-1-459 of the Montana Business Corporation Act (“MBCA”) contain specific provisions relating to indemnification of directors and officers of Montana corporations. In general, the statute provides that (i) a corporation must indemnify a director or officer who is wholly successful in his defense of a proceeding to which he is a party because of his status as such, unless limited by the arti …
- [ ] `105f35f7ceb555e0` — rank 5 · GBCI · S-4 · 2021-07-02 · section · Item 20. Indemnification of Directors and Officers  
      > Item 20. Indemnification of Directors and Officers Sections 35-1-451 through 35-1-459 of the Montana Business Corporation Act (“MBCA”) contain specific provisions relating to indemnification of directors and officers of Montana corporations. In general, the statute provides that (i) a corporation must indemnify a director or officer who is wholly successful in his defense of a proceeding to which he is a party becaus …
- [ ] `cac0ad1a842808df` — rank 6 · WSBC · S-4 · 2024-10-04 · paragraph · Item 20. Indemnification of Directors and Officers.  
      > Wesbanco’s amended and restated bylaws (the “Bylaws”) provide, and West Virginia law permits, the indemnification of directors and officers against certain liabilities. Officers and directors of Wesbanco and its subsidiaries are indemnified, to the maximum extent permitted under the West Virginia Business Corporation Act (including advanced indemnification payments), against liabilities incurred in connection with pr …
- [ ] `9e5248fbe7b1f0a1` — rank 7 · GBCI · S-4 · 2023-09-14 · paragraph · Item 20. Indemnification of Directors and Officers  
      > Sections 35-14-850 through 35-1-858 of the Montana Business Corporation Act (“MBCA”) contain specific provisions relating to indemnification of directors and officers of Montana corporations. In general, the statute provides that (i) a corporation must indemnify a director or officer who is wholly successful in the defense of a proceeding to which the director or officer is a party because of the director or officer’ …
- [ ] `e839adfe2ba60b75` — rank 8 · WSBC · S-4 · 2024-10-04 · paragraph · Item 20. Indemnification of Directors and Officers.  
      > SECTION 1. Indemnification. Each director and officer, whether or not then in office, shall be indemnified by the corporation against liability incurred by and imposed upon him in connection with or resulting from any action, suit or proceeding, to which he may be made a party by reason of his being or having been a director or officer of the corporation, or of any other company which he served at the request of the …

---

### `r026` — What was the pro forma combined net loss of Umpqua and Columbia for the year ended December 31, 2020?

**Already labelled** `92ee45a79deb1dd6` — COLB · S-4 · 2021-11-22 · table  
> Year Ended December 31, 2020 (dollars and shares in thousands, except per share data) | Umpqua Historical | Columbia Historical | Transaction Accounting Adjustments | Notes | Pro Forma Combined Income (loss) before provision for income taxes | (1,456,420 | ) | 192392 | (116,773 | ) | (1,380,801 | ) Provision for income taxes | 67000 | 38148 | (30,945 | ) | Z | 74203 Net income (loss) | $ | (1,523,420 | ) | $ | 154244 …

Also answers the question?

- [ ] `4de9d59cb8b59786` — rank 1 · COLB · S-4 · 2021-11-22 · table  
      > Income Statements | Nine Months Ended September 30, 2021 | Year Ended December 31, 2020 (dollars in thousands) Z | Adjustment to income tax provision To reflect the income tax effect of pro forma adjustments at the estimated combined statutory federal and state rate of 26.5%. | $ | (850 | ) | $ | (30,945 | ) AA | Adjustments to weighted average number of common shares outstanding — Basic To reflect acquisition of Ump …
- [ ] `63a501fb0832e5cd` — rank 2 · COLB · 8-K · 2021-12-29 · table  
      > Exhibit No. | Description 23.1 | Consent of Deloitte & Touche USA, LLP, with respect to Umpqua Holdings Corporation. 99.1 | Unaudited pro forma condensed combined financial information of Columbia Banking System, Inc. and Umpqua Holdings Corporation (incorporated by reference to the Company’s prospectus filed pursuant to Rule 424(b)(3) on December 3, 2021 under the Registration Statement on Form S-4 filed November 22 …
- [ ] `63a06e6956a0b02c` — rank 3 · COLB · S-4 · 2021-11-22 · table  
      > Nine Months Ended September 30, 2021 (dollars and shares in thousands, except per share data) | Umpqua Historical | Columbia Historical | Transaction Accounting Adjustments | Notes | Pro Forma Combined Income (loss) before provision for income taxes | 441018 | 200468 | (3,206 | ) | 638280 Provision for income taxes | 109072 | 40559 | (850 | ) | Z | 148781 Net income (loss) | $ | 331946 | $ | 159909 | $ | (2,356 | ) | …
- [ ] `4d25901c5ee41fea` — rank 4 · SSB · 8-K · 2020-06-08 · paragraph · Item 9.01. Financial Statements and Exhibits.  
      > The unaudited pro forma combined condensed consolidated financial statements of South State and CenterState, including (a) the unaudited pro forma combined condensed consolidated statements of income of South State and CenterState for the three months ended March 31, 2020 and for the year ended December 31, 2019, in each case giving effect to the Merger as if it had occurred on January 1, 2019, and (b) the unaudited …
- [ ] `262d64fb9ae92a45` — rank 5 · COLB · 8-K · 2022-01-20 · paragraph · Item 8.01. Other Events.  
      > Pro Forma Combined Dividend Discount Model Analysis. KBW performed a dividend discount model analysis to estimate an illustrative range for the implied equity value of the pro forma combined entity. In this analysis, KBW used financial forecasts and projections relating to the net income and assets of Columbia provided by Columbia management and financial forecasts and projections relating to the net income and asset …
- [ ] `7a2aae0ee595163d` — rank 6 · COLB · 10-K · 2022-02-25 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > For illustrative purposes only, the following table presents certain unaudited pro forma information for the year ended December 31, 2021 and 2020. This unaudited, estimated pro forma financial information was calculated as if Bank of Commerce had been acquired as of the beginning of the year prior to the date of acquisition. This unaudited pro forma information combines the historical results of Bank of Commerce wit …
- [ ] `8963b761d8675614` — rank 7 · COLB · 10-K · 2023-02-24 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > For illustrative purposes only, the following table presents certain unaudited pro forma information for the year ended December 31, 2021 and 2020. This unaudited, estimated pro forma financial information was calculated as if Bank of Commerce had been acquired as of the beginning of the year prior to the date of acquisition. This unaudited pro forma information combines the historical results of Bank of Commerce wit …
- [ ] `d7267dcb035d9f57` — rank 8 · COLB · 8-K · 2021-12-29 · paragraph · Item 8.01. Other Events  
      > Included in this Current Report on Form 8-K are (a) the unaudited pro forma condensed combined financial information contained in the Company’s prospectus filed pursuant to Rule 424(b)(3) on December 3, 2021 under the Registration Statement on Form S-4 (registration no. 333-261281) filed on November 22, 2021, which is included as Exhibit 99.1 hereto and incorporated herein by reference, (b) the financial statements o …

---

### `r027` — What were the implied transaction metrics in the summary transaction multiples analysis of Columbia's S-4?

**Already labelled** `b85093b7ca29cd6f` — COLB · S-4 · 2021-08-06 · table  
> SUMMARY TRANSACTION MULTIPLES Deal Value / Tangible Book Value | Deal Value / Last Twelve Months Earnings | Premium / Core Deposits 75th Percentile | 178% | 21.8x | 9.9% Median | 156% | 14.0x | 6.7% Mean | 171% | 18.1x | 8.4% 25th Percentile | 156% | 12.2x | 6.1% Implied Transaction Metric | 175% | 15.5x | 8.0%

Also answers the question?

- [ ] `a2a2649bcb3a5173` — rank 1 · COLB · S-4 · 2021-08-06 · table  
      > SUMMARY TRANSACTION MULTIPLES Deal Value / Tangible Book Value | Deal Value / Last Twelve Months Earnings | Premium / Core Deposits 75th Percentile | 177% | 21.0x | 9.8% Median | 156% | 16.4x | 6.8% Mean | 162% | 17.4x | 7.7% 25th Percentile | 140% | 14.0x | 5.5% Implied Transaction Metric | 175% | 15.5x | 8.0%
- [ ] `af3c80af8e7f76e2` — rank 2 · COLB · S-4 · 2021-08-06 · paragraph  
      > Furthermore, Raymond James applied the 75th percentile, median, mean and 25th percentile relative valuation multiples for each of the metrics to BOCH’s actual financial results to derive an implied transaction value. Raymond James then compared those implied values to $16.70, the value attributed to the per share merger consideration for the purposes of the Raymond James opinion. The results of this analysis are summ …
- [ ] `446b0bb950b851f4` — rank 3 · COLB · S-4 · 2021-08-06 · table  
      > SUMMARY PRICING MULTIPLES Price / Tangible Book Value Per Share | Last Twelve Months Earnings Per Share | ‘21E EPS | ‘22E EPS 75th Percentile | 133% | 15.8x | 14.2x | 13.1x Median | 123% | 13.4x | 11.4x | 11.9x Mean | 132% | 14.1x | 12.1x | 11.8x 25th Percentile | 115% | 11.0x | 10.2x | 10.7x Implied Transaction Metric | 174% | 15.5x | 15.2x | 15.9x
- [ ] `0f16c40287189523` — rank 4 · UMPQ · 8-K · 2021-10-12 · paragraph · Item 9.01. Financial Statements and Exhibits.  
      > In connection with the proposed transaction (the “Transaction”), Columbia will file with the SEC a Registration Statement on Form S-4 that will include a Joint Proxy Statement of Umpqua and Columbia and a Prospectus of Columbia, as well as other relevant documents concerning the Transaction. Certain matters in respect of the Transaction involving Umpqua and Columbia will be submitted to Umpqua’s and Columbia’s shareh …
- [ ] `4a56a1385991150c` — rank 5 · COLB · 8-K · 2021-10-15 · paragraph  
      > In connection with the proposed transaction (the “Transaction”), Columbia will file with the SEC a Registration Statement on Form S-4 that will include a Joint Proxy Statement of Umpqua and Columbia and a Prospectus of Columbia, as well as other relevant documents concerning the Transaction. Certain matters in respect of the Transaction involving Umpqua and Columbia will be submitted to Umpqua’s and Columbia’s shareh …
- [ ] `660a054905bc46c6` — rank 6 · UMPQ · 8-K · 2021-10-15 · paragraph · Item 9.01. Financial Statements and Exhibits.  
      > In connection with the proposed transaction (the “Transaction”), Columbia will file with the SEC a Registration Statement on Form S-4 that will include a Joint Proxy Statement of Umpqua and Columbia and a Prospectus of Columbia, as well as other relevant documents concerning the Transaction. Certain matters in respect of the Transaction involving Umpqua and Columbia will be submitted to Umpqua’s and Columbia’s shareh …
- [ ] `e5e067f2d836ab78` — rank 7 · COLB · 8-K · 2021-10-12 · paragraph  
      > In connection with the proposed transaction (the “Transaction”), Columbia will file with the SEC a Registration Statement on Form S-4 that will include a Joint Proxy Statement of Umpqua and Columbia and a Prospectus of Columbia, as well as other relevant documents concerning the Transaction. Certain matters in respect of the Transaction involving Umpqua and Columbia will be submitted to Umpqua’s and Columbia’s shareh …
- [ ] `1b6bf26a6b937f1b` — rank 8 · UMPQ · 8-K · 2022-01-20 · paragraph  
      > J.P. Morgan calculated a range of implied values for Columbia common stock by discounting to present value estimates of Columbia’s future dividend stream and terminal value. In performing its analysis, J.P. Morgan utilized, among others, the following assumptions, which were reviewed and approved by Umpqua’s management:

---

### `r028` — What was the liability related to Glacier's non-funded deferred compensation plans at December 31, 2023 and 2022?

**Already labelled** `5bde0b18d3a15523` — GBCI · 10-K · 2024-02-23 · paragraph · Item 8. Financial Statements and Supplementary Data  
> The Company has non-funded deferred compensation plans for directors, eligible employees and certain nonemployee service providers. The plans provide for participants’ elective deferral of cash payments of up to 50 percent of a participants’ salary and 100 percent of bonuses and directors fees. As of December 31, 2023 and 2022, the liability related to the plans was $11,014,000 and $9,159,000, respectively, and was i …

Also answers the question?

- [ ] `48cc9623371fe04c` — rank 1 · GBCI · 10-K · 2023-02-24 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > The Company has non-funded deferred compensation plans for directors, eligible employees and certain nonemployee service providers. The plans provide for participants’ elective deferral of cash payments of up to 50 percent of a participants’ salary and 100 percent of bonuses and directors fees. As of December 31, 2022 and 2021, the liability related to the plans was $9,159,000 and $8,861,000, respectively, and was in …
- [ ] `6457e8a0961156ab` — rank 2 · GBCI · 10-K · 2024-02-23 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > In connection with several acquisitions, the Company assumed the obligations of deferred compensation plans for certain key employees. As of December 31, 2023 and 2022, the liability related to the acquired plans was $17,931,000 and $18,415,000, respectively, and was included in other liabilities. Total expense for the years ended December 31, 2023, 2022, and 2021 for the acquired plans was $1,062,000, $1,444,000 and …
- [ ] `b0e95bc0b7f331ce` — rank 3 · GBCI · 10-K · 2022-02-23 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > The Company has non-funded deferred compensation plans for directors, eligible employees and certain nonemployee service providers. The plans provide for participants’ elective deferral of cash payments of up to 50 percent of a participants’ salary and 100 percent of bonuses and directors fees. As of December 31, 2021 and 2020, the liability related to the plans was $8,861,000 and $9,276,000, respectively, and was in …
- [ ] `babad630463fa356` — rank 4 · GBCI · 10-K · 2023-02-24 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > In connection with several acquisitions, the Company assumed the obligations of deferred compensation plans for certain key employees. As of December 31, 2022 and 2021, the liability related to the acquired plans was $18,415,000 and $18,560,000, respectively, and was included in other liabilities. Total expense for the years ended December 31, 2022, 2021, and 2020 for the acquired plans was $1,444,000, $1,094,000 and …
- [ ] `c110824231e5cdae` — rank 5 · GBCI · 10-K · 2021-03-01 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > The Company has non-funded deferred compensation plans for directors, senior officers and certain nonemployee service providers. The plans provide for participants’ elective deferral of cash payments of up to 50 percent of a participants’ salary and 100 percent of bonuses and directors fees. As of December 31, 2020 and 2019, the liability related to the plans was $9,276,000 and $8,660,000, respectively, and was inclu …
- [ ] `16cae32da5920b7a` — rank 6 · GBCI · 10-K · 2024-02-23 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > The Company has SERP which is intended to supplement payments due to participants upon retirement under the Company’s other qualified plans. The Company credits the participant’s account on an annual basis for an amount equal to employer contributions that would have otherwise been allocated to the participant’s account under the tax-qualified plans were it not for limitations imposed by the IRS or the participation …
- [ ] `5971df5c923ee989` — rank 7 · GBCI · 10-K · 2020-02-21 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > The Company has non-funded deferred compensation plans for directors, senior officers and certain nonemployee service providers. The plans provide for participants’ elective deferral of cash payments of up to 50 percent of a participants’ salary and 100 percent of bonuses and directors fees. As of December 31, 2019 and 2018, the liability related to the plans was $8,660,000 and $8,371,000, respectively, and was inclu …
- [ ] `ec84fa20dec4406a` — rank 8 · GBCI · 10-K · 2023-02-24 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > The Company has SERP which is intended to supplement payments due to participants upon retirement under the Company’s other qualified plans. The Company credits the participant’s account on an annual basis for an amount equal to employer contributions that would have otherwise been allocated to the participant’s account under the tax-qualified plans were it not for limitations imposed by the IRS or the participation …

---

### `r029` — What were Glacier's interest rate lock commitments at December 31, 2020 and 2019?

**Already labelled** `7ed219856bdcc648` — GBCI · 10-K · 2021-03-01 · paragraph · Item 8. Financial Statements and Supplementary Data  
> The Company enters into residential real estate derivatives for commitments (“interest rate locks”) to fund certain residential real estate loans to be sold into the secondary market. At December 31, 2020 and 2019, loan commitments with interest rate lock commitments totaled $229,862,000 and $84,803,000, respectively. At December 31, 2020 and 2019, the fair value of the related derivatives on the interest rate lock c …

Also answers the question?

- [ ] `07f61f2717a2df9b` — rank 1 · GBCI · 10-K · 2020-02-21 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > At December 31, 2019, the Company had residential real estate derivatives for commitments (“interest rate locks”) to fund certain residential real estate loans to be sold into the secondary market. At December 31, 2019 and 2018, loan commitments with interest rate lock commitments totaled $84,803,000 and $59,974,000, respectively, and the fair value of the related derivatives was included in other assets with corresp …
- [ ] `6702429982266b17` — rank 2 · GBCI · 10-K · 2022-02-23 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > The Company enters into residential real estate derivatives for commitments (“interest rate locks”) to fund certain residential real estate loans to be sold into the secondary market. At December 31, 2021 and 2020, loan commitments with interest rate lock commitments totaled $151,038,000 and $229,862,000, respectively. At December 31, 2021 and 2020, the fair value of the related derivatives on the interest rate lock …
- [ ] `3096ccb5ced2da3f` — rank 3 · GBCI · 10-K · 2023-02-24 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > The Company enters into residential real estate derivatives for commitments (“interest rate locks”) to fund certain residential real estate loans to be sold into the secondary market. At December 31, 2022 and 2021, loan commitments with interest rate lock commitments totaled $28,910,000 and $151,038,000, respectively. At December 31, 2022 and 2021, the fair value of the related derivatives on the interest rate lock c …
- [ ] `2b20ed8c7eb04583` — rank 4 · UMPQ · 10-Q · 2020-05-07 · table  
      > (in thousands) | Asset Derivatives | Liability Derivatives Derivatives not designated as hedging instrument | March 31, 2020 | December 31, 2019 | March 31, 2020 | December 31, 2019 Interest rate lock commitments | $ | 23727 | $ | 7056 | $ | — | $ | — Interest rate forward sales commitments | 1161 | 105 | 26092 | 1351 Interest rate swaps | 358204 | 142787 | 8128 | 7001 Foreign currency derivatives | 792 | 626 | 600 | …
- [ ] `e4efc31972859a5d` — rank 5 · UMPQ · 10-K · 2021-02-25 · table  
      > (in thousands) | Asset Derivatives | Liability Derivatives Derivatives not designated as hedging instrument | December 31, 2020 | December 31, 2019 | December 31, 2020 | December 31, 2019 Interest rate lock commitments | $ | 28144 | $ | 7056 | $ | — | $ | — Interest rate forward sales commitments | 7 | 105 | 7257 | 1351 Interest rate swaps | 313090 | 142787 | 370 | 7001 Foreign currency derivatives | 1269 | 626 | 115 …
- [ ] `998933e90b56d20b` — rank 6 · UMPQ · 10-Q · 2020-08-06 · table  
      > (in thousands) | Asset Derivatives | Liability Derivatives Derivatives not designated as hedging instrument | June 30, 2020 | December 31, 2019 | June 30, 2020 | December 31, 2019 Interest rate lock commitments | $ | 25537 | $ | 7056 | $ | — | $ | — Interest rate forward sales commitments | 442 | 105 | 5621 | 1351 Interest rate swaps | 379488 | 142787 | 6977 | 7001 Foreign currency derivatives | 571 | 626 | 413 | 456 …
- [ ] `e7f49b978c8c8a84` — rank 7 · UMPQ · 10-Q · 2020-11-05 · table  
      > (in thousands) | Asset Derivatives | Liability Derivatives Derivatives not designated as hedging instrument | September 30, 2020 | December 31, 2019 | September 30, 2020 | December 31, 2019 Interest rate lock commitments | $ | 28839 | $ | 7056 | $ | — | $ | — Interest rate forward sales commitments | 814 | 105 | 2843 | 1351 Interest rate swaps | 352956 | 142787 | 65 | 7001 Foreign currency derivatives | 562 | 626 | 5 …
- [ ] `2940440f78ce9b2b` — rank 8 · COLB · 10-K · 2021-02-26 · table  
      > Years ended December 31, 2020 | 2019 | 2018 (in thousands) Interest rate lock commitments | $ | 1096 | $ | — | $ | — Interest rate forward loan sales contracts | (165) | — Interest rate swap contracts | (452) | (1) | 8 Total derivative gains (losses) | $ | 479 | $ | (1) | $ | 8

---

### `r030` — How many shareholders of record did Glacier Bancorp have as of December 31, 2020?

**Already labelled** `a16048239bd3b1a2` — GBCI · 10-K · 2021-03-01 · section · Item 5. Market for Registrant’s Common Equity, Related Stockholder Matters  
> Item 5. Market for Registrant’s Common Equity, Related Stockholder Matters The Company’s stock trades on the NASDAQ Global Select Market under the symbol: GBCI. As of December 31, 2020, there were approximately 1,669 shareholders of record for the Company’s common stock. The market range of high and low market prices for the Company’s common stock for the periods indicated are shown below: The following table summari …

Also answers the question?

- [ ] `7249523cd76cba25` — rank 1 · GBCI · DEF 14A · 2021-03-16 · paragraph  
      > A copy of this Proxy Statement and the Annual Report to Shareholders (“Annual Report”) for the year ended December 31, 2020, which includes the Form 10-K (“Form 10-K”), are available at www.glacierbancorp.com. In this Proxy Statement, the terms “we,” “us” and “our” refer to Glacier Bancorp, Inc.
- [ ] `fae512ae44025a95` — rank 2 · UMPQ · 10-K · 2021-02-25 · paragraph · Item 5. MARKET FOR REGISTRANT'S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES.  
      > (a) Our common stock is traded on The NASDAQ Global Select Market under the symbol "UMPQ." As of December 31, 2020, our common stock was held by 4,315 shareholders of record, a number that does not include beneficial owners who hold shares in "street name," or shareholders from previously acquired companies that have not exchanged their stock. At December 31, 2020, a total of 1.3 million shares of unvested restricted …
- [ ] `12f838836cbb09a2` — rank 3 · GBCI · 8-K · 2021-01-28 · section · Item 9.01. FINANCIAL STATEMENTS AND EXHIBITS  
      > Item 9.01. FINANCIAL STATEMENTS AND EXHIBITS 99.1 Glacier Bancorp, Inc. Announces Results for the Quarter and Year Ended December 31, 2020 Pursuant to the requirements of the Securities Exchange Act of 1934, the registrant has duly caused this report to be signed on its behalf by the undersigned hereunto duly authorized.
- [ ] `98f7455e4b385da2` — rank 4 · GBCI · 10-K · 2021-03-01 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > We have audited the accompanying consolidated statements of financial condition of Glacier Bancorp, Inc. (the Company) as of December 31, 2020 and 2019, the related consolidated statements of operations, comprehensive income, changes in stockholders’ equity and cash flows for each of the years in the three-year period ended December 31, 2020, and the related notes (collectively referred to as the “financial statement …
- [ ] `0ce900e1dcf46158` — rank 5 · GBCI · 8-K · 2020-04-07 · paragraph · Item 8.01. OTHER EVENTS  
      > On April 7, 2020, Glacier Bancorp, Inc., Kalispell, Montana, issued a press release announcing that its annual shareholder meeting, scheduled for April 29, 2020 at 9:00 a.m. MT, has been changed to a virtual meeting as a result of the COVID-19 pandemic. A copy of the press release is furnished as Exhibit 99.1 to this report.
- [ ] `bbadb4497cdfe00c` — rank 6 · GBCI · 8-K · 2020-05-04 · paragraph · Item 5.07. SUBMISSION OF MATTERS TO A VOTE OF SECURITY HOLDERS  
      > The 2020 Annual Meeting of Shareholders of Glacier Bancorp, Inc. (the “Company”) was held virtually on April 29, 2020. The following matters were voted upon at the 2020 virtual Annual Meeting:
- [ ] `937ab1c213eae06b` — rank 7 · GBCI · 10-K · 2022-02-23 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > We have audited the accompanying consolidated statements of financial condition of Glacier Bancorp, Inc. (the Company) as of December 31, 2021 and 2020, the related consolidated statements of operations, comprehensive income, changes in stockholders’ equity and cash flows for each of the years in the three-year period ended December 31, 2021, and the related notes (collectively referred to as the “financial statement …
- [ ] `2bca6882674fc379` — rank 8 · GBCI · 8-K · 2021-01-28 · paragraph · Item 9.01. FINANCIAL STATEMENTS AND EXHIBITS  
      > 99.1 Glacier Bancorp, Inc. Announces Results for the Quarter and Year Ended December 31, 2020

---

### `r031` — What subordinated debentures did Glacier owe to trust subsidiaries, and at what rates?

**Already labelled** `e1bc973d830ac939` — GBCI · 10-K · 2023-02-24 · table  
> December 31, 2022 | Rate Structure | Maturity Date (Dollars in thousands) | Balance | Rate 1 | Rate Structure | Maturity Date Subordinated debentures owed to trust subsidiaries First Company Statutory Trust 2001 | $ | 3584 | 7.715 | % | 3 month LIBOR plus 3.30% | 07/31/2031 First Company Statutory Trust 2003 | 2632 | 7.974 | % | 3 month LIBOR plus 3.25% | 03/26/2033 Glacier Capital Trust II | 46393 | 6.829 | % | 3 mo …

Also answers the question?

- [ ] `b8a6fce7d5367cfd` — rank 1 · GBCI · 10-K · 2020-02-21 · table  
      > December 31, 2019 | Rate Structure | Maturity Date (Dollars in thousands) | Balance | Rate | Rate Structure | Maturity Date Subordinated debentures owed to trust subsidiaries First Company Statutory Trust 2001 | $ | 3395 | 5.227 | % | 3 month LIBOR plus 3.30% | 07/31/2031 First Company Statutory Trust 2003 | 2497 | 5.197 | % | 3 month LIBOR plus 3.25% | 03/26/2033 Glacier Capital Trust II | 46393 | 4.736 | % | 3 mont …
- [ ] `a71dc58ec9e4f47d` — rank 2 · GBCI · 10-K · 2021-03-01 · table  
      > December 31, 2020 | Rate Structure | Maturity Date (Dollars in thousands) | Balance | Rate | Rate Structure | Maturity Date Subordinated debentures owed to trust subsidiaries First Company Statutory Trust 2001 | $ | 3458 | 3.514 | % | 3 month LIBOR plus 3.30% | 07/31/2031 First Company Statutory Trust 2003 | 2542 | 3.501 | % | 3 month LIBOR plus 3.25% | 03/26/2033 Glacier Capital Trust II | 46393 | 2.987 | % | 3 mont …
- [ ] `4a1da5aff0213027` — rank 3 · GBCI · 10-K · 2022-02-23 · table  
      > December 31, 2021 | Rate Structure | Maturity Date (Dollars in thousands) | Balance | Rate | Rate Structure | Maturity Date Subordinated debentures owed to trust subsidiaries First Company Statutory Trust 2001 | $ | 3521 | 3.432 | % | 3 month LIBOR plus 3.30% | 07/31/2031 First Company Statutory Trust 2003 | 2587 | 3.470 | % | 3 month LIBOR plus 3.25% | 03/26/2033 Glacier Capital Trust II | 46393 | 2.874 | % | 3 mont …
- [ ] `5d9170274bb0359c` — rank 4 · GBCI · 10-K · 2024-02-23 · table  
      > December 31, 2023 | Rate Structure | Maturity Date (Dollars in thousands) | Balance | Rate 1 | Rate Structure | Maturity Date Subordinated debentures owed to trust subsidiaries First Company Statutory Trust 2001 | $ | 3647 | 8.945 | % | 3 month CME Term SOFR plus 3.30% | 07/31/2031 First Company Statutory Trust 2003 | 2676 | 8.872 | % | 3 month CME Term SOFR plus 3.25% | 03/26/2033 Glacier Capital Trust II | 46393 | …
- [ ] `098db71f167c1a37` — rank 5 · WSBC · 10-K · 2024-02-26 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > Wesbanco currently has $131.0 million in junior subordinated debt in its Consolidated Balance Sheets presented as a separate category of long-term debt. For regulatory purposes, trust preferred securities totaling $126.9 million, issued by unconsolidated trust subsidiaries of Wesbanco underlying such junior subordinated debt, are considered Tier 2 capital in accordance with current regulatory reporting requirements, …
- [ ] `fd2953fa321c40e9` — rank 6 · WSBC · 10-K · 2023-02-27 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > Wesbanco currently has $133.5 million in junior subordinated debt in its Consolidated Balance Sheets presented as a separate category of long-term debt. For regulatory purposes, trust preferred securities totaling $130.0 million, issued by unconsolidated trust subsidiaries of Wesbanco underlying such junior subordinated debt, are considered Tier 2 capital in accordance with current regulatory reporting requirements, …
- [ ] `75ebe83c90b25a45` — rank 7 · GBCI · 10-K · 2020-02-21 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations  
      > In addition to funds obtained in the ordinary course of business, the Company formed or acquired financing subsidiaries for the purpose of issuing trust preferred securities that entitle the investor to receive cumulative cash distributions thereon. Subordinated debentures were issued in conjunction with the trust preferred securities and the terms of the subordinated debentures and trust preferred securities are the …
- [ ] `407eda70b436c832` — rank 8 · GBCI · 10-K · 2022-02-23 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations  
      > In addition to funds obtained in the ordinary course of business, the Company formed or acquired financing subsidiaries for the purpose of issuing trust preferred securities that entitle the investor to receive cumulative cash distributions thereon. Subordinated debentures were issued in conjunction with the trust preferred securities and the terms of the subordinated debentures and trust preferred securities are the …

---

### `r032` — What was Glacier's interest income in 2019 and its five-year compounded annual growth rate?

**Already labelled** `e0f461f72072811e` — GBCI · 10-K · 2020-02-21 · table  
> Years ended December 31, | Compounded Annual Growth Rate (Dollars in thousands, except per share data) | 2019 | 2018 | 2017 | 2016 | 2015 | 1-Year | 5-Year Summary Statements of Operations Interest income | $ | 546177 | $ | 468996 | $ | 375022 | $ | 344153 | $ | 319681 | 16.5 % | 11.3 % Interest expense | 42773 | 35531 | 29864 | 29631 | 29275 | 20.4 % | 7.9 % Net interest income | 503404 | 433465 | 345158 | 314522 | …

Also answers the question?

- [ ] `d5f40621726e64fb` — rank 1 · GBCI · 10-K · 2024-02-23 · table  
      > Years ended December 31, | Compounded Annual Growth Rate (Dollars in thousands, except per share data) | 2023 | 2022 | 2021 | 2020 | 2019 | 1-Year | 5-Year Summary Statements of Operations Interest income | $ | 1017655 | $ | 829640 | $ | 681074 | $ | 627064 | $ | 546177 | 22.7 | % | 13.3 | % Interest expense | 325973 | 41261 | 18558 | 27315 | 42773 | 690.0 | % | 50.1 | % Net interest income | 691682 | 788379 | 662516 …
- [ ] `e5609458fa5fe77f` — rank 2 · GBCI · 10-K · 2021-03-01 · table  
      > Years ended December 31, | Compounded Annual Growth Rate (Dollars in thousands, except per share data) | 2020 | 2019 | 2018 | 2017 | 2016 | 1-Year | 5-Year Summary Statements of Operations Interest income | $ | 627064 | $ | 546177 | $ | 468996 | $ | 375022 | $ | 344153 | 14.8 % | 12.7 % Interest expense | 27315 | 42773 | 35531 | 29864 | 29631 | (36.1) | % | (1.6) | % Net interest income | 599749 | 503404 | 433465 | 3 …
- [ ] `dce663cc6da69b54` — rank 3 · GBCI · 10-K · 2022-02-23 · table  
      > Years ended December 31, | Compounded Annual Growth Rate (Dollars in thousands, except per share data) | 2021 | 2020 | 2019 | 2018 | 2017 | 1-Year | 5-Year Summary Statements of Operations Interest income | $ | 681074 | $ | 627064 | $ | 546177 | $ | 468996 | $ | 375022 | 8.6 | % | 12.7 % Interest expense | 18558 | 27315 | 42773 | 35531 | 29864 | (32.1) | % | (9.1) | % Net interest income | 662516 | 599749 | 503404 | …
- [ ] `eaac313a98c8087a` — rank 4 · GBCI · 10-K · 2023-02-24 · table  
      > Years ended December 31, | Compounded Annual Growth Rate (Dollars in thousands, except per share data) | 2022 | 2021 | 2020 | 2019 | 2018 | 1-Year | 5-Year Summary Statements of Operations Interest income | $ | 829640 | $ | 681074 | $ | 627064 | $ | 546177 | $ | 468996 | 21.8 | % | 12.1 | % Interest expense | 41261 | 18558 | 27315 | 42773 | 35531 | 122.3 | % | 3.0 | % Net interest income | 788379 | 662516 | 599749 | …
- [ ] `85fe5440ae422db4` — rank 5 · UMPQ · 10-K · 2020-02-28 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Net interest income is the largest source of our income. Net interest income for 2019 was $920.6 million, a decrease of $18.0 million or 2% compared to the same period in 2018. The decrease in net interest income in 2019 compared to 2018 was driven by growth in interest-bearing liabilities and an increase in the average cost of funds due to competitive rates and pricing specials on the deposit portfolio, as well as l …
- [ ] `c094723fd225a60d` — rank 6 · GBCI · 10-K · 2020-02-21 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations  
      > Net interest income (tax-equivalent) increased $68.1 million for the year ended December 31, 2019 compared to the same period in 2018. The interest income for 2019 increased over the same period last year primarily from increased loan growth in all categories, with the largest increase in the Company’s commercial loan portfolio. Consistent with the prior year, increases in interest rates on existing variable rate loa …
- [ ] `5fa3a8a5efcd3b3e` — rank 7 · COLB · 10-K · 2022-02-25 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > In January 2019, the Company entered into a $500.0 million notional interest rate collar with a five-year term. In October 2020, the collar was terminated and resulted in a $34.4 million realized gain that was recorded in accumulated other comprehensive income, net of deferred income taxes. The gain will amortize through February 2024 into interest income. The gain will be amortized in this manner as long as the cash …
- [ ] `64c0ec83c512130b` — rank 8 · COLB · 10-K · 2023-02-24 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > In January 2019, the Company entered into a $500.0 million notional interest rate collar with a five-year term. In October 2020, the collar was terminated and resulted in a $34.4 million realized gain that was recorded in accumulated other comprehensive income, net of deferred income taxes. The gain will amortize through February 2024 into interest income. The gain will be amortized in this manner as long as the cash …

---

### `r033` — What did the Paycheck Protection Program and Health Care Enhancement Act provide in additional PPP funding?

**Already labelled** `291cbc9e70a675f7` — GBCI · 10-Q · 2020-05-08 · paragraph · Item 5. Other Information  
> The initial amounts available under the PPP were quickly exhausted in less than two weeks, leaving many pending loan applications in limbo as Congress negotiated additional funding. On April 24, 2020, the Paycheck Protection Program and Health Care Enhancement Act was signed into law to replenish funding to the PPP and to provide other spending for hospitals and virus testing. In part, the bill included an additional …

Also answers the question?

- [ ] `53dd179fc7455dea` — rank 1 · WSBC · 10-K · 2023-02-27 · paragraph · Item 1. BUSINESS  
      > The CARES Act amended the loan program of the U.S. Small Business Administration (the "SBA"), in which the Bank participates, to create a guaranteed, unsecured loan program, the Paycheck Protection Program (“PPP”), to fund operational costs of eligible businesses, organizations and self-employed persons during COVID-19. In June 2020, the Paycheck Protection Program Flexibility Act was enacted, which among other thing …
- [ ] `dbe1b681408773cb` — rank 2 · WSBC · 10-K · 2022-02-28 · paragraph · Item 1. BUSINESS  
      > The CARES Act amended the loan program of the U.S. Small Business Administration (the "SBA"), in which the Bank participates, to create a guaranteed, unsecured loan program, the Paycheck Protection Program (“PPP”), to fund operational costs of eligible businesses, organizations and self-employed persons during COVID-19. In June 2020, the Paycheck Protection Program Flexibility Act was enacted, which among other thing …
- [ ] `8fd30a1d993817e4` — rank 3 · GBCI · 10-K · 2022-02-23 · paragraph · Item 1. Business  
      > Governments at the federal, state, and local levels have taken significant steps over the last two years to address the impact of the COVID-19 pandemic. On March 27, 2020, the historic $2 trillion federal stimulus package known as the Coronavirus Aid, Relief, and Economic Security Act (the “CARES Act”) was signed into law, which included $350 billion in stimulus for small businesses under the so-called Paycheck Prote …
- [ ] `e919b9dac4ad0eb7` — rank 4 · GBCI · 10-K · 2021-03-01 · paragraph · Item 1. Business  
      > Governments at the federal, state, and local levels continue to take steps to address the impact of the COVID-19 pandemic. On March 27, 2020, the historic $2 trillion federal stimulus package known as the Coronavirus Aid, Relief, and Economic Security Act (the “CARES Act”) was signed into law, which included $350 billion in stimulus for small businesses under the so-called Paycheck Protection Program (“PPP”), along w …
- [ ] `460f0ba59df339df` — rank 5 · GBCI · 10-Q · 2020-07-31 · paragraph · Item 5. Other Information  
      > Governments at the federal, state, and local levels continue to take steps to address the impact of the COVID-19 pandemic. On March 27, 2020 the historic $2 trillion federal stimulus package known as the Coronavirus Aid, Relief, and Economic Security Act was signed into law, which included $350 billion in stimulus for small businesses under the so-called “Paycheck Protection Program,” along with direct stimulus payme …
- [ ] `6c4323d1cff11507` — rank 6 · GBCI · 10-Q · 2020-10-30 · paragraph · Item 5. Other Information  
      > Governments at the federal, state, and local levels continue to take steps to address the impact of the COVID-19 pandemic. On March 27, 2020 the historic $2 trillion federal stimulus package known as the Coronavirus Aid, Relief, and Economic Security Act was signed into law, which included $350 billion in stimulus for small businesses under the so-called “Paycheck Protection Program,” along with direct stimulus payme …
- [ ] `1bb3be7222833e0c` — rank 7 · COLB · 10-K · 2021-02-26 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > The Company offered PPP loans to provide financial support to small- and medium-size businesses to cover payroll and certain other expenses during the COVID-19 pandemic. The PPP was established by the CARES Act and is implemented by the U.S. SBA with support from the U.S. Department of Treasury. The program, which was amended by the Paycheck Protection Flexibility Act of 2020, provides small businesses with funds to …
- [ ] `fc5de782daee804a` — rank 8 · COLB · 10-K · 2022-02-25 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > The Company offered PPP loans to provide financial support to small- and medium-size businesses to cover payroll and certain other expenses during the COVID-19 pandemic. The PPP was established by the CARES Act and is implemented by the U.S. SBA with support from the U.S. Department of Treasury. The program, which was amended by the Paycheck Protection Flexibility Act of 2020, provides small businesses with funds to …

---

### `r034` — Who did Glacier appoint as Chief Compliance Officer in 2024, and what role was he expected to take on?

**Already labelled** `8a198aafacc6ffda` — GBCI · 8-K · 2024-11-05 · paragraph · Item 5.02. Departure of Directors or Principal Officers; Election of Directors; Appointment of Principal Officers  
> On October 30, 2024, the Board of Directors (the “Board”) of Glacier Bancorp, Inc. (the “Company” or “Glacier”), appointed Ryan Screnar to serve as an Executive Vice President and Chief Compliance Officer of the Company and Glacier Bank, the Company’s wholly owned banking subsidiary (the “Bank”). Upon Don Chery’s previously announced retirement, now planned for February 2025, Mr. Screnar will become Chief Administrat …

Also answers the question?

- [ ] `af7d6cae4c6868eb` — rank 1 · GBCI · 8-K · 2024-11-05 · section · Item 5.02. Departure of Directors or Principal Officers; Election of Directors; Appointment of Principal Officers  
      > Item 5.02. Departure of Directors or Principal Officers; Election of Directors; Appointment of Principal Officers On October 30, 2024, the Board of Directors (the “Board”) of Glacier Bancorp, Inc. (the “Company” or “Glacier”), appointed Ryan Screnar to serve as an Executive Vice President and Chief Compliance Officer of the Company and Glacier Bank, the Company’s wholly owned banking subsidiary (the “Bank”). Upon Don …
- [ ] `05c0a8f24c944121` — rank 2 · GBCI · 8-K · 2024-11-05 · paragraph · Item 5.02. Departure of Directors or Principal Officers; Election of Directors; Appointment of Principal Officers  
      > Also on October 30, 2024, the Board appointed Lee Groom to serve as Executive Vice President and Chief Experience Officer of the Company and the Bank. Mr. Groom, who currently serves as Senior Vice President and Chief Experience Officer of the Bank and oversees the retail customer experience, commercial card products, and mortgage lending businesses, is being promoted to this expanded position and will assume additio …
- [ ] `ab6e237cedf44dc2` — rank 3 · GBCI · 8-K · 2024-02-02 · section · Item 5.02. Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers; Compensatory Arrangements of Certain Officers  
      > Item 5.02. Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers; Compensatory Arrangements of Certain Officers On January 31, 2024, Don J. Chery, Executive Vice President and Chief Administrative Officer of Glacier Bancorp, Inc., and its wholly owned subsidiary, Glacier Bank, announced that he will retire at the end of 2024 following over 35 years of service. Pursuant to …
- [ ] `d1ae9841ef01b170` — rank 4 · GBCI · 8-K · 2024-02-02 · paragraph · Item 5.02. Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers; Compensatory Arrangements of Certain Officers  
      > On January 31, 2024, Don J. Chery, Executive Vice President and Chief Administrative Officer of Glacier Bancorp, Inc., and its wholly owned subsidiary, Glacier Bank, announced that he will retire at the end of 2024 following over 35 years of service.
- [ ] `8a9c51d534a9bfe3` — rank 5 · GBCI · 8-K · 2024-11-05 · paragraph · Item 5.02. Departure of Directors or Principal Officers; Election of Directors; Appointment of Principal Officers  
      > Mr. Screnar, age 50, previously served as the Bank’s Senior Vice President and Chief Compliance Officer since January 2022. Prior to taking the position of Senior Vice President and Chief Compliance Officer, Mr. Screnar held various positions with increasing responsibilities since joining the Bank as an Internal Auditor in the Internal Audit Department in May 2000, including as Audit Director from October 2000 until …
- [ ] `cef5bf909fe868f8` — rank 6 · GBCI · DEF 14A · 2024-03-15 · paragraph  
      > Don J. Chery Mr. Chery has served as the Chief Administrative Officer since August of 2007, has over 39 years in banking and has served the Company for over 34 years. Prior to 2007, Mr. Chery previously served as President for two divisions of Glacier Bank. Mr. Chery received his education at Carroll College in Helena Montana, graduating with a Bachelor of Science in Business Administration and Economics and also rec …
- [ ] `83b9b5ca54bd68cc` — rank 7 · GBCI · DEF 14A · 2020-03-16 · paragraph  
      > The following table sets forth information with respect to the Named Executive Officers, who are not directors or nominees for director of Glacier, including employment history for the last five years. All executive officers are appointed annually and serve at the discretion of the Board.
- [ ] `ff720ba27d5c27cc` — rank 8 · GBCI · DEF 14A · 2021-03-16 · paragraph  
      > The following table sets forth information with respect to the Named Executive Officers, who are not directors or nominees for director of Glacier, including employment history for the last five years. All executive officers are appointed annually and serve at the discretion of the Board.

---

### `r035` — What was the aggregate value of the merger consideration in Glacier's May 2021 merger agreement?

**Already labelled** `0da02638bdec3648` — GBCI · 8-K · 2021-05-19 · paragraph · Item 1.01. Entry into a Material Definitive Agreement.  
> As of the date of this report, the merger consideration has a total aggregate value of approximately $930.5 million (based on the closing price of $61.51 for GBCI common stock on May 17, 2021), subject to certain adjustments based on the price of GBCI common stock for a specified period before closing.

Also answers the question?

- [ ] `6edd9438518ac535` — rank 1 · GBCI · 8-K · 2021-05-19 · section · Item 1.01. Entry into a Material Definitive Agreement.  
      > Item 1.01. Entry into a Material Definitive Agreement. On May 18, 2021, Glacier Bancorp, Inc., a Montana corporation (“GBCI”) and its wholly owned subsidiary, Glacier Bank, entered into a Plan and Agreement of Merger (the “Merger Agreement”) with Altabancorp, a Utah corporation (“AB”) and its wholly owned subsidiary, Altabank, a Utah state-chartered bank. Under the terms of the Merger Agreement, AB will merge with an …
- [ ] `56b6b75792b46907` — rank 2 · GBCI · 8-K · 2023-08-09 · paragraph · Item 8.01. Other Events  
      > It is estimated that the merger consideration will have a total aggregate value of $80.6 million (based on the closing price of $33.97 for GBCI common stock on August 7, 2023).
- [ ] `25a20c3821023082` — rank 3 · GBCI · 8-K · 2023-08-09 · section · Item 8.01. Other Events  
      > Item 8.01. Other Events On August 8, 2023, GBCI and its wholly owned subsidiary, Glacier Bank, entered into a Plan and Agreement of Merger (the “Merger Agreement”) with Community Financial Group, Inc. (“CFGW”) and its wholly owned subsidiary, Wheatland Bank. Under the terms of the Merger Agreement, CFGW will merge with and into GBCI, with GBCI as the surviving entity (the “Holding Company Merger”). Immediately therea …
- [ ] `dd9ad568e4cfd1a1` — rank 4 · SSB · 8-K · 2022-03-01 · paragraph  
      > The total aggregate consideration payable in the Merger was approximately 7.4 million shares of SouthState Common Stock. The Registration Statement on Form S-4 (File No. 333-259561) filed by Atlantic Capital with the Commission on September 15, 2021, as amended by Amendment No. 1 filed on October 14, 2021, which became effective on October 15, 2021 (the “Proxy Statement/Prospectus”) contains additional information ab …
- [ ] `2040eb3cccd708b7` — rank 5 · GBCI · S-4 · 2021-07-02 · table  
      > GBCI Common Stock | ALTA Common Stock | Implied Value of Merger Consideration May 17, 2021 | $ | 61.51 | $ | 43.44 | $ | 49.03 [ ], 2021 | [ ]
- [ ] `d9ea4f6fffba407c` — rank 6 · COLB · S-4 · 2021-08-06 · paragraph  
      > Under the terms of the merger agreement, BOCH shareholders will have the right to receive 0.40 of a share of Columbia common stock with respect to each of their shares of BOCH common stock (subject to any adjustment as provided in the merger agreement), which we refer to as the merger consideration. As of June 23, 2021, the date the mergers were announced, based on the expected issuance of 6,758,313 Columbia common s …
- [ ] `0266d4eedc50262b` — rank 7 · GBCI · 10-Q · 2021-11-01 · paragraph · Item 6. Exhibits  
      > 2.1 Agreement and Plan of Merger, dated as of May 18, 2021, by and between Glacier Bancorp, Inc., Glacier Bank, Altabancorp and Altabank. Filed as Exhibit 2.1 to Form 8-K, filed on May 19, 2021
- [ ] `f6371db4809e475c` — rank 8 · GBCI · 10-Q · 2021-08-02 · paragraph · Item 6. Exhibits  
      > 2.1 Agreement and Plan of Merger, dated as of May 18, 2021, by and between Glacier Bancorp, Inc., Glacier Bank, Altabancorp and Altabank. Filed as Exhibit 2.1 to Form 8-K, filed on May 19, 2021

---

### `r036` — What amendment to Glacier's articles of incorporation was voted on at the 2022 annual meeting?

**Already labelled** `e58bd8eb75027bae` — GBCI · 8-K · 2022-04-29 · section · Item 5.07. Submission of Matters to a Vote of Security Holders.  
> Item 5.07. Submission of Matters to a Vote of Security Holders. The 2022 Annual Meeting of Shareholders (“Annual Meeting”) of the Company was held virtually on April 27, 2022. The following matters were voted upon at the Annual Meeting: 1.The election of nine directors to serve on the board of directors until the 2023 annual meeting; 2.An amendment to the Restated Articles of Incorporation to increase the authorized …

Also answers the question?

- [ ] `1a2f829982c4c622` — rank 1 · GBCI · 8-K · 2022-04-29 · paragraph · Item 5.03. Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year.  
      > On April 27, 2022, the shareholders of Glacier Bancorp, Inc. (the “Company”), approved an amendment (the “Articles Amendment”) to the Company’s Restated Articles of Incorporation (the “Articles”) to increase the authorized shares of common stock, $0.01 par value per share, from 117,187,500 to 234,000,000.
- [ ] `08f6affa6f3ae60b` — rank 2 · GBCI · 8-K · 2022-04-29 · section · Item 5.03. Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year.  
      > Item 5.03. Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year. On April 27, 2022, the shareholders of Glacier Bancorp, Inc. (the “Company”), approved an amendment (the “Articles Amendment”) to the Company’s Restated Articles of Incorporation (the “Articles”) to increase the authorized shares of common stock, $0.01 par value per share, from 117,187,500 to 234,000,000. The Articles Amendment was f …
- [ ] `be39dbee1040d0ad` — rank 3 · GBCI · 10-Q · 2022-05-02 · paragraph · Item 6. Exhibits  
      > 3.1 Amendment to Restated Articles of Incorporation of Glacier Bancorp, Inc. Filed as Exhibit 3.1 to Form 8-K filed on April 29, 2022
- [ ] `f137dc7a82cbc216` — rank 4 · GBCI · 8-K · 2021-05-04 · paragraph · Item 5.03. Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year.  
      > On April 28, 2021, the shareholders of Glacier Bancorp, Inc. (the “Company”), approved an amendment (the “Articles Amendment”) to the Company’s Amended and Restated Articles of Incorporation (the “Articles”) to provide for indemnification of directors and officers of the Company to the fullest extent authorized or permitted under the Montana Business Corporation Act (the “MBCA”). At a meeting held on April 28, 2021, …
- [ ] `ac7ec11de6f4c376` — rank 5 · GBCI · 8-K · 2021-05-04 · section · Item 5.03. Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year.  
      > Item 5.03. Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year. On April 28, 2021, the shareholders of Glacier Bancorp, Inc. (the “Company”), approved an amendment (the “Articles Amendment”) to the Company’s Amended and Restated Articles of Incorporation (the “Articles”) to provide for indemnification of directors and officers of the Company to the fullest extent authorized or permitted under the …
- [ ] `4e3d7805576fb645` — rank 6 · GBCI · 8-K · 2021-05-04 · paragraph · Item 9.01. FINANCIAL STATEMENTS AND EXHIBITS  
      > 3.1 Amendment to Amended and Restated Articles of Incorporation of Glacier Bancorp, Inc.
- [ ] `b59e539859a56475` — rank 7 · GBCI · 8-K · 2021-05-04 · section · Item 5.07. Submission of Matters to a Vote of Security Holders.  
      > Item 5.07. Submission of Matters to a Vote of Security Holders. The 2021 Annual Meeting of Shareholders (“Annual Meeting”) of the Company was held virtually on April 28, 2021. The following matters were voted upon at the Annual Meeting: 1.The election of 10 directors to serve on the board of directors until the 2022 annual meeting; 2.Amendment to the Amended and Restated Articles of Incorporation to provide for indem …
- [ ] `3ac2db6ea050f18e` — rank 8 · GBCI · 8-K · 2021-05-04 · section · Item 9.01. FINANCIAL STATEMENTS AND EXHIBITS  
      > Item 9.01. FINANCIAL STATEMENTS AND EXHIBITS 3.1 Amendment to Amended and Restated Articles of Incorporation of Glacier Bancorp, Inc. Pursuant to the requirements of the Securities Exchange Act of 1934, the registrant has duly caused this report to be signed on its behalf by the undersigned hereunto duly authorized.

---

### `r037` — How many votes for did Randall Chesler receive at Glacier's 2022 annual meeting?

**Already labelled** `40b6b1e5e8236628` — GBCI · 8-K · 2022-04-29 · table  
> Director’s Name | Votes For | Votes Withheld | Broker Non-Votes David C. Boyles | 70021278 | 11930078 | 8708378 Robert A. Cashell, Jr. | 69948958 | 12002398 | 8708378 Randall M. Chesler | 81511491 | 439865 | 8708378 Sherry L. Cladouhos | 69310569 | 12640787 | 8708378 Annie M. Goodwin | 69409250 | 12542106 | 8708378 Kristen L. Heck | 69996776 | 11954580 | 8708378 Michael B. Hormaechea | 81763219 | 188137 | 8708378 Cra …

Also answers the question?

- [ ] `d9579a820844de1e` — rank 1 · GBCI · DEF 14A · 2020-03-16 · paragraph  
      > Randall M. Chesler, 61, was elected to the Board at the Company’s 2016 annual meeting. From August 1, 2015 to December 31, 2016, Mr. Chesler served as President of Glacier Bank. Since January 1, 2017, he has served as President and CEO of each of Glacier and Glacier Bank. Mr. Chesler has more than 31 years of experience in the financial services industry, most recently as President of CIT Bank, the Salt Lake City-bas …
- [ ] `a35d6a68122f7e19` — rank 2 · GBCI · DEF 14A · 2023-03-15 · paragraph  
      > The following table shows compensation paid or accrued for 2022 to Glacier’s non-employee directors. These directors also serve on the board of directors of Glacier Bank. Mr. Chesler is not included in the table as he was an employee of Glacier in 2022 and thus received no compensation for his services as a director. The footnotes to the table describe the details of each form of compensation paid to directors.
- [ ] `13e1e941c0217f90` — rank 3 · GBCI · 8-K · 2023-05-01 · paragraph · Item 5.07. SUBMISSION OF MATTERS TO A VOTE OF SECURITY HOLDERS  
      > The 2023 Annual Meeting of Shareholders of Glacier Bancorp, Inc. (the “Company”) was held in Kalispell, Montana on April 26, 2023. The following matters were voted upon at the Annual Meeting:
- [ ] `171e46948f305c8e` — rank 4 · GBCI · 8-K · 2024-04-29 · paragraph · Item 5.07. Submission of Matters to a Vote of Security Holders.  
      > The 2024 Annual Meeting of Shareholders of Glacier Bancorp, Inc. (the “Company”) was held in Kalispell, Montana on April 24, 2024. The following matters were voted upon at the Annual Meeting:
- [ ] `8b4003d6e105a31d` — rank 5 · COLB · 8-K · 2022-04-29 · paragraph · Item 5.07. Submission of Matters to a Vote of Security Holders.  
      > On April 27, 2022, Columbia Banking System, Inc. (the “Company”) held its 2022 Annual Meeting of Shareholders (the “2022 Annual Meeting”). There were 78,706,184 shares outstanding and entitled to vote at the 2022 Annual Meeting; of those shares 70,983,256 were present in person or by proxy. The following matters were voted upon at the 2022 Annual Meeting:
- [ ] `38e10548246da7ba` — rank 6 · GBCI · DEF 14A · 2024-03-15 · paragraph  
      > We cordially invite you to attend the 2024 Annual Meeting of Shareholders of Glacier Bancorp, Inc. (the “Company”), to be conducted on April 24, 2024, at 9:00 a.m. Mountain Time (the “Annual Meeting”) at The Hilton Garden Inn, 1840 Highway 93 South, Kalispell, Montana. The purpose of the Annual Meeting is to vote on the following proposals:
- [ ] `3d15d4bec47d5f42` — rank 7 · UMPQ · 10-K · 2023-02-24 · paragraph · Item 11. EXECUTIVE COMPENSATION  
      > Our say-on-pay resolution at the 2021 annual meeting received a favorable vote from over 95% of the shares voted. Our Compensation Committee considers the results of say-on-pay votes in making compensation decisions. Due to the pending Columbia merger, we did not hold an annual shareholder meeting in 2022.
- [ ] `222399f0ff0d8dcf` — rank 8 · GBCI · DEF 14A · 2022-03-15 · paragraph  
      > We cordially invite you to attend the 2022 Annual Meeting of Shareholders of Glacier Bancorp, Inc. (the “Company”), to be conducted virtually on April 27, 2022, at 9:00 a.m. Mountain Time (the “Annual Meeting”). Our Annual Meeting will once again not be held at a physical location and instead will be held solely via the Internet. You will be able to attend the Annual Meeting by logging in at www.virtualshareholdermee …

---

### `r038` — How many votes were withheld for James M. English at Glacier's 2020 annual meeting?

**Already labelled** `d7f57026eca01ff6` — GBCI · 8-K · 2020-05-04 · table  
> Director’s Name | Votes For | Votes Withheld | Broker Non-Votes David C. Boyles | 71069144 | 545136 | 9113796 Randall M. Chesler | 71092194 | 522086 | 9113796 Sherry L. Cladouhos | 71044571 | 569709 | 9113796 James M. English | 68832854 | 2781426 | 9113796 Annie M. Goodwin | 71095775 | 518505 | 9113796 Craig A. Langel | 70261881 | 1352399 | 9113796 Douglas J. McBride | 70259681 | 1354599 | 9113796 John W. Murdoch | 7 …

Also answers the question?

- [ ] `afbcbed10b49e790` — rank 1 · GBCI · 8-K · 2020-05-04 · section · Item 5.07. SUBMISSION OF MATTERS TO A VOTE OF SECURITY HOLDERS  
      > Item 5.07. SUBMISSION OF MATTERS TO A VOTE OF SECURITY HOLDERS The 2020 Annual Meeting of Shareholders of Glacier Bancorp, Inc. (the “Company”) was held virtually on April 29, 2020. The following matters were voted upon at the 2020 virtual Annual Meeting: 1. The election of nine directors to serve on the board of directors until the 2021 annual meeting. 2. Consideration of an advisory (non-binding) resolution to appr …
- [ ] `1b91b3a90c017864` — rank 2 · GBCI · DEF 14A · 2022-03-15 · paragraph  
      > At the close of the Annual Meeting, James M. English, who has been a director of the Company since 2004 and currently serves as a member of each Board committee and as Chair of the Nominating/Governance Committee, and George R. Sutton, who has been a director of the Company since 2017 and also currently serves as a member of each Board committee, will each be retiring from the Board. The Board extends its thanks to J …
- [ ] `26d5ef3ff516b438` — rank 3 · GBCI · 8-K · 2021-05-04 · table  
      > Director’s Name | Votes For | Votes Withheld | Broker Non-Votes David C. Boyles | 73298346 | 1615639 | 7525132 Robert A. Cashell, Jr. | 74748859 | 165126 | 7525132 Randall M. Chesler | 74468317 | 445668 | 7525132 Sherry L. Cladouhos | 73188992 | 1724993 | 7525132 James M. English | 61292859 | 13621126 | 7525132 Annie M. Goodwin | 73306245 | 1607740 | 7525132 Kristen L. Heck | 74776145 | 137840 | 7525132 Craig A. Lang …
- [ ] `bbadb4497cdfe00c` — rank 4 · GBCI · 8-K · 2020-05-04 · paragraph · Item 5.07. SUBMISSION OF MATTERS TO A VOTE OF SECURITY HOLDERS  
      > The 2020 Annual Meeting of Shareholders of Glacier Bancorp, Inc. (the “Company”) was held virtually on April 29, 2020. The following matters were voted upon at the 2020 virtual Annual Meeting:
- [ ] `6854300956e6980c` — rank 5 · GBCI · DEF 14A · 2020-03-16 · paragraph  
      > James M. English, 75, was appointed to the Board in February 2004 and has served as Chairman of the Nominating/Governance Committee since July 2013. He also served as a director of the Company’s former subsidiary, Mountain West Bank in Coeur d’Alene, Idaho, from 1996 until the consolidation of Glacier’s bank subsidiaries in 2012. Mr. English earned a Bachelor of Science degree in finance and a law degree from the Uni …
- [ ] `f6ec21a5bd194bde` — rank 6 · COLB · 8-K · 2020-06-01 · paragraph  
      > On May 27, 2020, Columbia Banking System, Inc. (the “Company”) held its 2020 Annual Meeting of Shareholders (the “2020 Annual Meeting”). There were 71,575,503 shares outstanding and entitled to vote at the 2020 Annual Meeting; of those shares 66,540,919 were present in person or by proxy. The following matters were voted upon at the 2020 Annual Meeting:
- [ ] `263c2a4fe5c4c923` — rank 7 · GBCI · DEF 14A · 2021-03-16 · paragraph  
      > Section 16(a) of the Exchange Act requires our directors and executive officers to file reports of their ownership of Glacier’s common stock to the SEC. Based solely on a review of the filings made with the SEC and written representations from our directors and executive officers, we believe that all Section 16(a) filing requirements that apply to our directors and executive officers were complied with for the fiscal …
- [ ] `812ed8d5506b1030` — rank 8 · COLB · 8-K · 2024-05-09 · paragraph  
      > On May 8, 2024, the Company held the 2024 Annual Meeting. There were 209,311,089 shares outstanding and entitled to vote at the 2024 Annual Meeting; of those shares 187,193,066 were present in person or by proxy. The following matters were voted upon at the 2024 Annual Meeting:

---

### `r039` — At what percentage of target were Glacier's overall 2023 short-term incentive plan performance goals achieved?

**Already labelled** `5f3bc95110eb8f00` — GBCI · DEF 14A · 2024-03-15 · paragraph  
> For 2023, the overall STIP performance goals were achieved at 57.08% of target. The table below details, for each NEO, the 2023 STIP opportunity levels as a percentage of base salary, the STIP bonus achieved as a percentage of base salary, and the STIP bonus achieved as a dollar value. The 2023 target award opportunities were increased by 5% for the CEO and 10% for each of the other NEOs from the 2022 level, as the C …

Also answers the question?

- [ ] `92c503642bca70a8` — rank 1 · GBCI · DEF 14A · 2024-03-15 · paragraph  
      > For 2023, the total of the LTIP goals achieved based on 2022 performance was at 106.39% of target. The table below details, for each NEO, the 2023 LTIP opportunity levels as a percentage of base salary, the RSUs granted as a percentage of base salary, and the number of RSUs granted in February 2023. The long-term incentive award opportunities for the NEOs were increased over 2022 based on the results of the 2022 peer …
- [ ] `5a5746e83f1f8acf` — rank 2 · GBCI · DEF 14A · 2023-03-15 · paragraph  
      > For 2022, the total of the LTIP goals achieved based on 2021 performance was at 111.90% of target. The table below details, for each Named Executive Officer, the 2022 LTIP opportunity levels as a percentage of base salary, the RSUs granted as a percentage of base salary, and the number of RSUs granted in February 2022. The long-term incentive award opportunities for the NEOs were increased over 2021 based on the resu …
- [ ] `436213590f7b2daf` — rank 3 · GBCI · DEF 14A · 2023-03-15 · paragraph  
      > For 2022, the overall STIP performance goals were achieved at 105.71% of target. The table below details, for each Named Executive Officer, the 2022 STIP opportunity levels as a percentage of base salary, the STIP bonus achieved as a percentage of base salary, and the STIP bonus achieved as a dollar value. The 2022 target award opportunity for the CEO was increased by 10% from the 2021 level; which was determined to …
- [ ] `a0c4b3f3e8aa33be` — rank 4 · GBCI · DEF 14A · 2022-03-15 · paragraph  
      > For 2021, the total of the LTIP goals achieved based on 2020 performance was at 114.27% of target. The table below details, for each Named Executive Officer, the 2021 LTIP opportunity levels as a percentage of base salary, the RSUs granted as a percentage of base salary, and the number of RSUs granted in February 2021. The long-term incentive award opportunities were increased over the prior year based on an analysis …
- [ ] `404462df0b17d834` — rank 5 · GBCI · DEF 14A · 2021-03-16 · paragraph  
      > The 2020 goals were approved by the Compensation Committee in late January 2020, before a clear understanding developed regarding the potential impact of COVID-19. As a result of the pandemic and Glacier’s successful participation in the Paycheck Protection Program during 2020, the Company originated 16,090 SBA Paycheck Protection Loans totaling $1.472 billion. Core deposits increased organically by $3.4 billion, or …
- [ ] `d9c0634673d1d547` — rank 6 · GBCI · DEF 14A · 2024-03-15 · paragraph  
      > The Compensation and Human Capital Committee determined the number of RSUs to be granted in 2023 based on the achievement of the performance goals in 2022, as described in the table below, excluding the impact of any acquisitions during the year. The 2022 LTIP goals were selected in light of Glacier’s long-term strategic plan, long-term initiatives and the need to balance risks in executive compensation arrangements. …
- [ ] `73bfc8384e39b035` — rank 7 · GBCI · DEF 14A · 2023-03-15 · table  
      > Short-Term Incentive Program | Threshold | Target | Maximum | Actual Result | Result % of Target | Weighted % of Target Performance Goals | Weight | 80% | 100% | 115% | Actual Result | Result % of Target | Weighted % of Target Return on Tangible Equity (1) | 20.00% | 10.80% | 13.50% | 15.53% | 16.59% | 115.00% | 23.00% Non-performing Assets / Total Subsidiary Assets | 20.00% | 0.74% | 0.50% | 0.32% | 0.12% | 115.00% …
- [ ] `321751ee7d66653b` — rank 8 · UMPQ · 10-K · 2023-02-24 · paragraph · Item 11. EXECUTIVE COMPENSATION  
      > The Committee also assigns a maximum incentive above the target incentive (200% for 2022), and the minimum performance required to receive a payout on financial metrics (50% for 2022). Achievement of the target incentive is based on the success of the Company and the individual executive in certain performance areas. The Committee determined that the weighting would be 20% individual goals and 80% OEPS.

---

### `r040` — What return on tangible equity did Glacier use for its 2021 401(k) discretionary contribution, and what was the contribution rate?

**Already labelled** `455e45e6775ea677` — GBCI · DEF 14A · 2022-03-15 · paragraph  
> The Named Executive Officers participate in the Glacier 401(k) Plan, which includes a 3% safe harbor contribution plus a discretionary contribution. The 401(k) Plan includes a trigger for the discretionary contribution, which is set equal to the 2021 STIP qualifier of NPAs/Total Subsidiary Assets of no greater than 2%. The Company considered return on tangible equity (“ROTE”) as a primary metric in determining its di …

Also answers the question?

- [ ] `984feee650082c92` — rank 1 · GBCI · DEF 14A · 2021-03-16 · paragraph  
      > The Named Executive Officers participate in the Glacier 401(k) Plan, which includes a 3% safe harbor contribution plus a discretionary contribution. The 401(k) Plan includes a trigger for the discretionary contribution, which is set equal to the 2020 STIP qualifier of NPAs/Total Subsidiary Assets no greater than 2%. The Company considered return on tangible equity (“ROTE”) as a primary metric in determining its discr …
- [ ] `f5b355885ed96e26` — rank 2 · GBCI · DEF 14A · 2020-03-16 · paragraph  
      > The Named Executive Officers participate in the Glacier Profit Sharing and 401(k) Plan (the “Profit Sharing Plan”), which includes a 3% safe harbor contribution plus a discretionary contribution. The Profit Sharing Plan includes a trigger for the discretionary contribution, which is set equal to the 2019 STIP qualifier of NPAs / Total Subsidiary Assets no greater than 2%. The Company considered return on tangible equ …
- [ ] `352edbf341a0686f` — rank 3 · GBCI · DEF 14A · 2023-03-15 · paragraph  
      > The Named Executive Officers participate in the Glacier 401(k) Plan, which includes a 3% safe harbor contribution plus a discretionary contribution. The 401(k) Plan includes a trigger for the discretionary contribution, which is set equal to the 2022 STIP qualifier of NPAs/Total Subsidiary Assets of no greater than 2%. The Company considered return on tangible equity (“ROTE”) as a primary metric in determining its di …
- [ ] `37ef2a4d731145d3` — rank 4 · GBCI · DEF 14A · 2024-03-15 · paragraph  
      > The NEOs participate in the Glacier 401(k) Plan, which includes a 3% safe harbor contribution plus a discretionary contribution. The 401(k) Plan includes a trigger for the discretionary contribution, which is set equal to the 2023 STIP qualifier of NPAs/Total Subsidiary Assets of no greater than 2%. The Company considered ROTE (excluding AOCI) as a primary metric in determining its discretionary contribution. Based o …
- [ ] `1824ab0d24b3dbe2` — rank 5 · SSB · 10-K · 2022-02-25 · paragraph · Item 15. Exhibits, Financial Statement Schedules.  
      > compensation as a pre-tax contribution. Employees participating in the plan receive a 100% matching of their 401(k) plan contribution, up to 4% of salary. Effective January 1, 2018, employees are eligible for an additional 2% discretionary matching contribution contingent upon achievement of the Company’s annual financial goals and payable the first quarter of the following year. Based on our financial performance in …
- [ ] `2fecadae3b8243b1` — rank 6 · COLB · 10-K · 2022-02-25 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > The Company maintains defined contribution and profit sharing plans in conformity with the provisions of section 401(k) of the Internal Revenue Code. The Columbia Bank 401(k) Plan, permits Columbia Bank employees who are at least 18 years of age to contribute up to 75% of their eligible compensation to the 401(k) Plan starting on the first day of the month following their hire date. On a per pay period basis the Comp …
- [ ] `eb5b6ffadd6832ef` — rank 7 · GBCI · 10-K · 2024-02-23 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > The 401(k) plan allows eligible employees under the age of 50 to contribute up to 60 percent, and those 50 and older to contribute up to 100 percent of their eligible annual compensation up to the limit set annually by the Internal Revenue Service (“IRS”). The Company matches an amount equal to 50 percent of the first 6 percent of an employee’s contribution. The Company’s contribution to the 401(k) plan for the years …
- [ ] `3b80dbed1bcc4499` — rank 8 · COLB · 10-K · 2023-02-24 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > The Company maintains defined contribution and profit sharing plans in conformity with the provisions of section 401(k) of the Internal Revenue Code. The Columbia Bank 401(k) Plan, permits Columbia Bank employees who are at least 18 years of age to contribute up to 75% of their eligible compensation to the 401(k) Plan starting on the first day of the month following their hire date. On a per pay period basis the Comp …

---

### `r041` — What annual incentive did Glacier's President and CEO actually earn in the year covered by the 2020 proxy?

**Already labelled** `b6fe2e7a89e3adce` — GBCI · DEF 14A · 2020-03-16 · table  
> Position | Annual Incentive Program Opportunity Levels as a % of Base Salary | Actual Earned(%) | Actual Earned ($) Position | Threshold | Target | Maximum | Actual Earned(%) | Actual Earned ($) President & CEO | 0% | 65% | 98% | 83% | $525,707 CFO | 0% | 45% | 68% | 57% | $210,506 CAO | 0% | 45% | 68% | 57% | $148,491

Also answers the question?

- [ ] `4d64e6e365971ae7` — rank 1 · GBCI · DEF 14A · 2021-03-16 · paragraph  
      > •The median of the annual total compensation of all Glacier employees (other than Mr. Chesler, our President and CEO), was $48,340; and
- [ ] `8ce139860522d50f` — rank 2 · GBCI · DEF 14A · 2023-03-15 · paragraph  
      > •The median of the annual total compensation of all Glacier employees (other than Mr. Chesler, our President and CEO), was $56,033; and
- [ ] `96f219cdc8201b2d` — rank 3 · GBCI · DEF 14A · 2020-03-16 · paragraph  
      > •The median of the annual total compensation of all Glacier employees (other than Mr. Chesler, our President and CEO), was $47,566; and
- [ ] `368911ca86759bc2` — rank 4 · GBCI · DEF 14A · 2022-03-15 · paragraph  
      > •The median of the annual total compensation of all Glacier employees (other than Mr. Chesler, our President and CEO), was $65,451; and
- [ ] `031a59e6b4d7d2e5` — rank 5 · GBCI · DEF 14A · 2024-03-15 · paragraph  
      > •The median of the annual total compensation of all Glacier employees (other than Mr. Chesler, our President and CEO), was $58,009; and
- [ ] `7249523cd76cba25` — rank 6 · GBCI · DEF 14A · 2021-03-16 · paragraph  
      > A copy of this Proxy Statement and the Annual Report to Shareholders (“Annual Report”) for the year ended December 31, 2020, which includes the Form 10-K (“Form 10-K”), are available at www.glacierbancorp.com. In this Proxy Statement, the terms “we,” “us” and “our” refer to Glacier Bancorp, Inc.
- [ ] `68c65f15963bce4b` — rank 7 · SSB · DEF 14A · 2021-03-08 · paragraph  
      > CEO Annual Total Compensation. Because Mr. Corbett became our CEO in connection with the Merger, his total compensation reported in the Summary Compensation Table included in this Proxy Statement is calculated based on payments from the Company from the date of Merger through December 31, 2020. Therefore, we annualized his total compensation to provide a more complete approximation of his total compensation for the y …
- [ ] `4d18c3ab5fb94f63` — rank 8 · WSBC · 8-K · 2021-02-18 · paragraph  
      > As discussed in its proxy statement for the 2020 annual meeting of shareholders, as part of its executive compensation program, Wesbanco, Inc. (“Wesbanco”) provides annual cash incentive awards. For 2020, these awards were made under the annual cash incentive plan of the amended and restated Wesbanco, Inc. Key Executive Incentive Bonus, Option and Restricted Stock Plan (“Incentive Plan”). Consistent with Wesbanco’s g …

---

### `r042` — How many restricted stock units were granted to Randall Chesler according to Glacier's 2024 proxy?

**Already labelled** `4854ee251b4443dd` — GBCI · DEF 14A · 2024-03-15 · table  
> Named Executive Officer | Long-Term Incentive Program Opportunity Levels as a % of Base Salary | RSUs Granted as a % of Base Salary | RSUs Granted (#) Named Executive Officer | Threshold | Target | Maximum | RSUs Granted as a % of Base Salary | RSUs Granted (#) Randall M. Chesler | 0% | 110% | 165% | 133.4% | 24778 Ron J. Copher | 0% | 80% | 120% | 97.0% | 9197 Don J. Chery | 0% | 80% | 120% | 97.0% | 8034

Also answers the question?

- [ ] `50fd4a96a20002f1` — rank 1 · SSB · 8-K · 2022-05-31 · paragraph  
      > In connection with these retirements, and in recognition of the long and distinguished service of each of the retiring directors, the Board approved the accelerated vesting of 935 restricted stock units granted to each retiring director on May 2, 2022, which restricted stock units were scheduled to vest in full according to their terms on November 2, 2022. In addition, the Board approved the accelerated vesting of 81 …
- [ ] `d8e0617b680bcb2b` — rank 2 · COLB · DEF 14A · 2022-03-18 · paragraph  
      > For Mr. Deer, represents 2,786 Restricted Stock Units granted on April 27, 2020 that vest 50% each year on February 15, 2022 and 2023 and 2,854 Restricted Stock Units granted on February 25, 2021 that vest one-third each year on February 15, 2022, 2023, and 2024.
- [ ] `b8222092221669a6` — rank 3 · COLB · DEF 14A · 2022-03-18 · paragraph  
      > For Mr. Eid, represents 1,500 shares of Restricted Stock granted on February 28, 2018 that vest 100% on February 28, 2022; 1,547 shares of Restricted Stock granted on March 27, 2019 that vest 100% on January 1, 2022; 2,032 Restricted Stock Units granted on February 27, 2020 that vest 50% each year on February 15, 2022 and 2023; and 2,397 Restricted Stock Units granted on February 25, 2021 that vest one-third each yea …
- [ ] `fc3f6e2d88101225` — rank 4 · COLB · DEF 14A · 2022-03-18 · paragraph  
      > For Mr. Merrywell represents 1,662 shares of Restricted Stock granted on February 28, 2018 that vest 100% on February 28, 2022; 1,580 shares of Restricted Stock granted on March 27, 2019 that vest 100% on January 1, 2022; 3,265 Restricted Stock Units granted on February 27, 2020 that vest 50% each year on February 15, 2022 and 2023; and 3,988 Restricted Stock Units granted on February 25, 2021 that vest one-third eac …
- [ ] `9340cda47cd5719e` — rank 5 · COLB · DEF 14A · 2022-03-18 · paragraph  
      > For Mr. McDonald, represents 1,107 shares of Restricted Stock granted on February 28, 2018 that vest 100% on February 28, 2022; 2,385 shares of Restricted Stock granted on March 27, 2019 that vest 100% on January 1, 2022; 6,000 shares of Restricted Stock granted on January 22, 2020 that vest 100% on January 22, 2022; 2,114 Restricted Stock Units granted on February 27, 2020 that vest 50% each year on February 15, 202 …
- [ ] `90ac47410109e621` — rank 6 · GBCI · DEF 14A · 2023-03-15 · table  
      > Name | Stock Awards Name | Number of Shares or Units of Stock that Have Not Vested (#) | Market Value of Shares or Units of Stock that Have Not Vested ($) (1) Randall M. Chesler | 4,784 (2) | 236425 Randall M. Chesler | 13,772(3) | 680612 Randall M. Chesler | 21,660 (4) | 1070437 Ron J. Copher | 1,586 (2) | 78380 Ron J. Copher | 4,138 (5) | 204500 Ron J. Copher | 7,429 (6) | 367141 Don J. Chery | 1,349(2) | 66668 3,6 …
- [ ] `c3b1845f13bd14b7` — rank 7 · COLB · DEF 14A · 2022-03-18 · paragraph  
      > For Mr. Merrywell, represents the fair market value of 1,250 shares of Restricted Stock granted in 2017 that vested on February 22, 2021, 997 shares of Restricted Stock granted in 2018 that vested on February 28, 2021, 396 shares of Restricted Stock granted in 2019 that vested on March 27, 2021 and 1,683 Restricted Stock Units granted in 2020 that vested on February 15, 2021.
- [ ] `bbe6bde69d0ce5bc` — rank 8 · COLB · DEF 14A · 2022-03-18 · paragraph  
      > For Mr. Eid, represents the fair market value of 1,300 shares of Restricted Stock granted in 2017 that vested on February 22, 2021, 900 shares of Restricted Stock granted in 2018 that vested on February 28, 2021, 387 shares of Restricted Stock granted in 2019 that vested on March 27, 2021 and 1,048 Restricted Stock Units granted in 2020 that vested on February 15, 2021.

---

### `r043` — Under which state's business corporation act are Glacier's directors and officers indemnified?

**Already labelled** `105f35f7ceb555e0` — GBCI · S-4 · 2021-07-02 · section · Item 20. Indemnification of Directors and Officers  
> Item 20. Indemnification of Directors and Officers Sections 35-1-451 through 35-1-459 of the Montana Business Corporation Act (“MBCA”) contain specific provisions relating to indemnification of directors and officers of Montana corporations. In general, the statute provides that (i) a corporation must indemnify a director or officer who is wholly successful in his defense of a proceeding to which he is a party becaus …

Also answers the question?

- [ ] `f137dc7a82cbc216` — rank 1 · GBCI · 8-K · 2021-05-04 · paragraph · Item 5.03. Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year.  
      > On April 28, 2021, the shareholders of Glacier Bancorp, Inc. (the “Company”), approved an amendment (the “Articles Amendment”) to the Company’s Amended and Restated Articles of Incorporation (the “Articles”) to provide for indemnification of directors and officers of the Company to the fullest extent authorized or permitted under the Montana Business Corporation Act (the “MBCA”). At a meeting held on April 28, 2021, …
- [ ] `ac7ec11de6f4c376` — rank 2 · GBCI · 8-K · 2021-05-04 · section · Item 5.03. Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year.  
      > Item 5.03. Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year. On April 28, 2021, the shareholders of Glacier Bancorp, Inc. (the “Company”), approved an amendment (the “Articles Amendment”) to the Company’s Amended and Restated Articles of Incorporation (the “Articles”) to provide for indemnification of directors and officers of the Company to the fullest extent authorized or permitted under the …
- [ ] `ae2ade95b9737fbe` — rank 3 · GBCI · DEF 14A · 2021-03-16 · paragraph  
      > The Board recommends that shareholders adopt an amendment to the Articles to provide for indemnification of directors and officers. Indemnification of directors and officers is currently addressed in the Company’s bylaws. The Montana Business Corporation Act was amended effective June 1, 2020, to permit broader indemnification of a corporation’s directors than had been authorized under the statutory provisions previo …
- [ ] `6394518a352b48ff` — rank 4 · GBCI · S-4 · 2021-07-02 · paragraph · Item 20. Indemnification of Directors and Officers  
      > Glacier’s articles provide, among other things, that the personal liability of the directors and officers of the corporation for monetary damages shall be eliminated to the fullest extent permitted by the MBCA. Glacier’s bylaws provide that the corporation shall indemnify its directors and officers to the fullest extent not prohibited by law, including indemnification for payments in settlement of actions brought aga …
- [ ] `27ab7eb97f5c153b` — rank 5 · GBCI · S-4 · 2023-09-14 · paragraph · Item 20. Indemnification of Directors and Officers  
      > Glacier’s articles provide, among other things, that the personal liability of the directors and officers of the corporation for monetary damages shall be eliminated to the fullest extent permitted by the MBCA. Glacier’s articles and bylaws also provide that the corporation shall indemnify its directors and officers to the fullest extent permitted by the MBCA.
- [ ] `710e462c8e361ddf` — rank 6 · GBCI · S-4 · 2021-07-02 · paragraph · Item 20. Indemnification of Directors and Officers  
      > Sections 35-1-451 through 35-1-459 of the Montana Business Corporation Act (“MBCA”) contain specific provisions relating to indemnification of directors and officers of Montana corporations. In general, the statute provides that (i) a corporation must indemnify a director or officer who is wholly successful in his defense of a proceeding to which he is a party because of his status as such, unless limited by the arti …
- [ ] `3ebb3354c0ec2604` — rank 7 · GBCI · S-4 · 2023-09-14 · section · Item 20. Indemnification of Directors and Officers  
      > Item 20. Indemnification of Directors and Officers Sections 35-14-850 through 35-1-858 of the Montana Business Corporation Act (“MBCA”) contain specific provisions relating to indemnification of directors and officers of Montana corporations. In general, the statute provides that (i) a corporation must indemnify a director or officer who is wholly successful in the defense of a proceeding to which the director or off …
- [ ] `9e5248fbe7b1f0a1` — rank 8 · GBCI · S-4 · 2023-09-14 · paragraph · Item 20. Indemnification of Directors and Officers  
      > Sections 35-14-850 through 35-1-858 of the Montana Business Corporation Act (“MBCA”) contain specific provisions relating to indemnification of directors and officers of Montana corporations. In general, the statute provides that (i) a corporation must indemnify a director or officer who is wholly successful in the defense of a proceeding to which the director or officer is a party because of the director or officer’ …

---

### `r044` — What were Altabancorp's total assets at acquisition, and when did Glacier's acquisition of it close?

**Already labelled** `80d25e010d82ded2` — GBCI · S-4 · 2023-09-14 · table  
> Total Assets | Gross Loans | Total Deposits | Closing Date (Dollars in thousands) Altabancorp, and subsidiary Altabank | $ | 4131662 | $ | 1902321 | $ | 3273819 | 10/1/2021 State Bank Corp. and subsidiary State Bank of Arizona | 745420 | 451702 | 603289 | 2/29/2020 Heritage Bancorp and subsidiary Heritage Bank of Nevada | 977944 | 615279 | 722220 | 7/31/2019 FNB Bancorp and subsidiary The First National Bank of Layto …

Also answers the question?

- [ ] `949a391ac55b725c` — rank 1 · GBCI · DEF 14A · 2022-03-15 · paragraph  
      > Glacier continued its strong performance in 2021. Glacier was able to achieve these accomplishments, despite challenges caused by the COVID-19 pandemic, by meeting both its customers’ and employees’ on-going needs. Glacier focused its business practices on its community banking model, including providing best-in-class customer service for its loan and deposit products and growing organically and through bank acquisit …
- [ ] `5f9b580a692e02a0` — rank 2 · GBCI · 8-K · 2021-10-01 · paragraph · Item 8.01. OTHER EVENTS  
      > On October 1, 2021, Glacier Bancorp, Inc. (“Glacier”), and Altabancorp issued a joint press release announcing the completion of Glacier’s acquisition of Altabancorp and its wholly owned subsidiary Altabank, effective October 1, 2021. A copy of the press release is attached hereto as Exhibit 99.1 and is incorporated by reference.
- [ ] `4905cd69360fe6bf` — rank 3 · GBCI · 10-K · 2022-02-23 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations  
      > During 2021, the Company acquired all the outstanding stock of Altabancorp, the holding company for Altabank (“Alta”) , a community bank based in American Fork, Utah with total assets of $4.132 billion. Alta provides banking services to individuals and businesses primarily in the state of Utah with twenty-five locations from Preston, Idaho south to St. George, Utah. Upon closing of the transaction, Alta became the se …
- [ ] `4fc1a53e18ffbe44` — rank 4 · GBCI · 8-K · 2021-10-01 · section · Item 8.01. OTHER EVENTS  
      > Item 8.01. OTHER EVENTS On October 1, 2021, Glacier Bancorp, Inc. (“Glacier”), and Altabancorp issued a joint press release announcing the completion of Glacier’s acquisition of Altabancorp and its wholly owned subsidiary Altabank, effective October 1, 2021. A copy of the press release is attached hereto as Exhibit 99.1 and is incorporated by reference.
- [ ] `a6148be8572628e2` — rank 5 · GBCI · DEF 14A · 2024-03-15 · paragraph  
      > •Glacier announced the signing of a definitive agreement to acquire Community Financial Group, Inc., the parent company of Wheatland Bank, a leading eastern Washington community bank headquartered in Spokane with total assets of $728 million as of December 31, 2023. The acquisition was completed on January 31, 2024.
- [ ] `cf0e22d955c07bb5` — rank 6 · GBCI · 10-K · 2024-02-23 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > On October 1, 2021, the Company completed the acquisition of Altabancorp, the bank holding company for Altabank, a community bank based in American Fork, Utah (collectively, “Alta”). The business combinations were accounted for using the acquisition method, with the results of operations included in the Company’s consolidated financial statements as of the acquisition dates.
- [ ] `16f19a1b84c9dd59` — rank 7 · GBCI · 10-K · 2023-02-24 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > On October 1, 2021, the Company acquired 100 percent of the outstanding common stock of Altabancorp and its wholly-owned subsidiary, Altabank, a community bank based in American Fork, Utah. Altabank provides banking services to individuals and businesses in Utah with twenty-five banking offices from Preston, Idaho to St. George, Utah. The acquisition significantly increased the Company’s presence in the State of Utah …
- [ ] `e749bccb07115b97` — rank 8 · GBCI · 10-K · 2022-02-23 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > On October 1, 2021, the Company acquired 100 percent of the outstanding common stock of Altabancorp and its wholly-owned subsidiary, Altabank, a community bank based in American Fork, Utah. Altabank provides banking services to individuals and businesses in Utah with twenty-five banking offices from Preston, Idaho to St. George, Utah. The acquisition significantly increased the Company’s presence in the State of Utah …

---

### `r045` — What per-share values did Glacier's discounted cash flow sensitivity analysis produce at a 10% discount rate?

**Already labelled** `7b4c57a6fded64c0` — GBCI · S-4 · 2023-09-14 · table  
> Discount Rate | 6.5x | 7.5x | 8.5x | 9.5x | 10.5x 10.0% | $ | 29.78 | $ | 34.37 | $ | 38.95 | $ | 43.53 | $ | 48.11 11.0% | $ | 28.60 | $ | 32.99 | $ | 37.39 | $ | 41.79 | $ | 46.19 12.0% | $ | 27.46 | $ | 31.69 | $ | 35.91 | $ | 40.14 | $ | 44.37 13.0% | $ | 26.39 | $ | 30.45 | $ | 34.51 | $ | 38.57 | $ | 42.63 14.0% | $ | 25.36 | $ | 29.26 | $ | 33.17 | $ | 37.07 | $ | 40.97

Also answers the question?

- [ ] `1608c7c8cbb94e7b` — rank 1 · COLB · S-4 · 2021-08-06 · paragraph  
      > The resulting range of present equity values was divided by the number of diluted shares outstanding. Raymond James reviewed the range of per share prices derived in the discounted cash flow analysis and compared them to $16.70, the value attributed to the per share merger consideration for purposes of the Raymond James opinion. The results of the discounted cash flow analysis indicated a range of values from $13.62 …
- [ ] `438a8cc7fce5a114` — rank 2 · COLB · S-4 · 2021-08-06 · paragraph  
      > The discounted cash flow analysis was based solely on the projections. Consistent with the periods included in the projections, Raymond James used calendar year 2025 as the final year for the analysis and applied multiples, ranging from 13.0x to 15.0x, to calendar year 2025 adjusted net income in order to derive a range of terminal values for BOCH in 2025. The projected free cash flows and terminal values were discou …
- [ ] `8f3e5fcdb6153979` — rank 3 · WSBC · 10-K · 2024-02-26 · paragraph · Item 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Wesbanco considered the sensitivity of significant assumptions in the impairment analysis including consideration of changes in estimated future cash flows and changes in the discount rate of the reporting units. The hypothetical sensitivity of the estimated fair value of the reporting units to an immediate and isolated increase of 100 basis points in the discount rate assumption at November 30, 2023, without conside …
- [ ] `b711ac21e684bfcc` — rank 4 · COLB · S-4 · 2021-08-06 · paragraph  
      > Discounted Cash Flow Analysis. Raymond James analyzed the discounted present value of BOCH’s projected free cash flows for the nine months ending December 31, 2021 and the 12 months ending December 31, 2022 through December 31, 2025 on a standalone basis, which were provided to Raymond James and approved for its use by BOCH. Raymond James used tangible common equity in excess of a target ratio of 8.0% of tangible ass …
- [ ] `a6ab366cb48580bd` — rank 5 · COLB · 10-Q · 2024-08-06 · table  
      > Financial Instrument | Fair Value (in thousands) | Valuation Technique | Unobservable Input | Range of Inputs | Weighted Average Assets: Residential mortgage servicing rights | $ | 110039 | Discounted cash flow | Constant prepayment rate | 6.03% - 27.36% | 6.76% Discount rate | 9.50% - 16.10% | 10.23% Liabilities: Interest rate lock commitments, net | $ | 452 | Internal pricing model | Pull-through rate | 69.73% - 10 …
- [ ] `374bfd8a6032ad16` — rank 6 · UMPQ · 10-Q · 2020-11-05 · table  
      > Financial Instrument | Fair Value | Valuation Technique | Unobservable Input | Range of Inputs | Weighted Average Residential mortgage servicing rights | $ | 93248 | Discounted cash flow Constant prepayment rate | 9.68 - 79.94% | 18.10% Discount rate | 9.50 - 12.50% | 9.74% Interest rate lock commitments | $ | 28839 | Internal pricing model Pull-through rate | 49.79 - 100.00% | 84.78% Junior subordinated debentures | …
- [ ] `58866cec218f7137` — rank 7 · UMPQ · 10-K · 2022-02-25 · table  
      > Financial Instrument | Fair Value | Valuation Technique | Unobservable Input | Range of Inputs | Weighted Average Residential mortgage servicing rights | $ | 123615 | Discounted cash flow Constant prepayment rate | 10.24 - 35.19% | 12.75% Discount rate | 9.00 - 14.88% | 9.57% Interest rate lock commitments | $ | 4641 | Internal pricing model Pull-through rate | 76.99 - 100.00% | 87.83% Junior subordinated debentures …
- [ ] `6cee4c0b00d48b48` — rank 8 · COLB · 10-Q · 2024-05-07 · table  
      > Financial Instrument | Fair Value (in thousands) | Valuation Technique | Unobservable Input | Range of Inputs | Weighted Average Assets: Residential mortgage servicing rights | $ | 110444 | Discounted cash flow | Constant prepayment rate | 6.07% - 27.52% | 6.74% Discount rate | 9.50% - 16.08% | 10.24% Interest rate lock commitments, net | $ | 16 | Internal pricing model | Pull-through rate | 64.27% - 100.00% | 85.71% …

---

### `r046` — What were SouthState's total deposits at December 31, 2021, and how much did they grow during the year?

**Already labelled** `0969c8ea648ce008` — SSB · 10-K · 2022-02-25 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
> At December 31, 2021 and December 31, 2020, we had $325.0 million and $600.0 million of traditional, out–of-market brokered deposits. At December 31, 2021 and December 31, 2020, we had $900.1 million and $611.1 million, respectively, of reciprocal brokered deposits. Total deposits were $35.1 billion at December 31, 2021, an increase of $4.4 billion from $30.7 billion at December 31, 2020. Our deposit growth since Dec …

Also answers the question?

- [ ] `a86194f6564054f0` — rank 1 · UMPQ · 10-K · 2023-02-24 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Total deposits were $27.1 billion at December 31, 2022, an increase of $470.9 million, or 2%, compared to year-end 2021. The increase is mainly attributable to growth in time and other interest bearing deposits accounts, which reflects an increase in brokered deposits and customer account movements.
- [ ] `14e9d691178c497b` — rank 2 · UMPQ · 10-K · 2022-02-25 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > The Company's total core deposits, which are deposits less time deposits greater than $250,000 and all brokered deposits, were $26.0 billion at December 31, 2021, compared to $23.3 billion at December 31, 2020. The Company's total brokered deposits were $149.9 million or 1% of total deposits at December 31, 2021, compared to $424.1 million or 2% at December 31, 2020.
- [ ] `fe85e47d68dceefd` — rank 3 · UMPQ · 10-Q · 2022-05-05 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended March 31, 2022 and December 31, 2021, where applicable, throughout this Management's Discussion and Analysis.  
      > The Company's total core deposits, which are deposits less time deposits greater than $250,000 and all brokered deposits, were $26.1 billion at March 31, 2022, compared to $26.0 billion at December 31, 2021. The Company's brokered deposits totaled $140.3 million at March 31, 2022, compared to $149.9 million at December 31, 2021.
- [ ] `0fed9e960a3bbb7c` — rank 4 · UMPQ · 10-Q · 2022-10-31 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended September 30, 2022 and June 30, 2022, where applicable, throughout this Management's Discussion and Analysis.  
      > The Company's total core deposits, which are deposits less time deposits greater than $250,000 and all brokered deposits, were $26.3 billion at September 30, 2022, compared to $26.0 billion at December 31, 2021. The Company's brokered deposits totaled $114.4 million at September 30, 2022, compared to $149.9 million at December 31, 2021.
- [ ] `a4902d9af1c55f18` — rank 5 · UMPQ · 10-Q · 2022-07-29 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended June 30, 2022 and March 31, 2022, where applicable, throughout this Management's Discussion and Analysis.  
      > The Company's total core deposits, which are deposits less time deposits greater than $250,000 and all brokered deposits, were $25.6 billion at June 30, 2022, compared to $26.0 billion at December 31, 2021. The Company's brokered deposits totaled $143.9 million at June 30, 2022, compared to $149.9 million at December 31, 2021.
- [ ] `1e7cece9587425a7` — rank 6 · SSB · 10-K · 2022-02-25 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > During 2021, all categories of deposits increased from 2020 except for time deposits. Total deposits increased $4.4 billion, or 14.2%, to $35.1 billion during 2021. The year-over-year growth was primarily due to the federal government pushing funds into the market through stimulus programs, in addition to consumers remaining conservative in their spending habits in reaction to the COVID-19 pandemic. Our deposit growt …
- [ ] `69ef62b5c0837310` — rank 7 · SSB · 10-K · 2022-02-25 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > Under the terms of the Merger Agreement, shareholders of Atlantic Capital will receive 0.36 shares of SouthState’s common stock for each share of Atlantic Capital common stock they own. The transaction is expected to close during the first quarter of 2022. At December 31, 2021, Atlantic Capital reported $3.8 billion in total assets, $2.4 billion in loans and $3.3 billion in deposits.
- [ ] `eabce15d1743619d` — rank 8 · UMPQ · 10-K · 2023-02-24 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Uninsured deposits at December 31, 2022, totaled $10.6 billion, which is an estimated amount based on the methodologies and assumptions used for the Bank's regulatory requirements. The Company's total core deposits, which are deposits less time deposits greater than $250,000 and all brokered deposits, were $25.6 billion at December 31, 2022, compared to $26.0 billion at December 31, 2021. The Company's total brokered …

---

### `r047` — How much did SouthState's deposits increase during 2020, and what drove the increase?

**Already labelled** `4bac33ac25f5ab0f` — SSB · 10-K · 2021-02-26 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
> At December 31, 2020 and December 31, 2019, we had $600.0 million and $0 of traditional, out–of-market brokered deposits. We assumed $804.0 million in traditional, out-of-market brokered deposits in the merger with CSFL in the second quarter of 2020 of which $204.0 million paid out in the third quarter of 2020. At December 31, 2020 and December 31, 2019, we had $611.1 million and $45.8 million, respectively, of recip …

Also answers the question?

- [ ] `1e7cece9587425a7` — rank 1 · SSB · 10-K · 2022-02-25 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > During 2021, all categories of deposits increased from 2020 except for time deposits. Total deposits increased $4.4 billion, or 14.2%, to $35.1 billion during 2021. The year-over-year growth was primarily due to the federal government pushing funds into the market through stimulus programs, in addition to consumers remaining conservative in their spending habits in reaction to the COVID-19 pandemic. Our deposit growt …
- [ ] `41bae02627b50a15` — rank 2 · SSB · 10-K · 2021-02-26 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > During 2020, all categories of deposits increased from 2019. Total deposits increased $18.5 billion, or 152.1%, to $30.7 billion during 2020. The year over year growth was primarily due to $15.6 billion in deposits assumed through the merger with CSFL during the second quarter of 2020. Our deposit growth since December 31, 2019 included an
- [ ] `ed5e4e75a50e856d` — rank 3 · UMPQ · 10-K · 2021-02-25 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Total deposits were $24.6 billion at December 31, 2020, an increase of $2.1 billion, or 10%, compared to year-end 2019. The increase is mainly attributable to growth in non-interest bearing demand deposits, offset by a decline in time deposits. The increase in non-maturity deposit account categories is driven by increased customer savings rates as customers look to increase their own liquidity in this uncertain envir …
- [ ] `c0e51bc44299b06f` — rank 4 · SSB · 10-K · 2021-02-26 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > increase in interest-bearing demand deposits of $8.6 billion, noninterest-bearing transaction account deposits of $6.5 billion, certificates of deposits of $2.1 billion and saving deposits of $1.4 million. During 2020, we continued our focus on increasing core deposits (excluding certificates of deposits and other time deposits), which are normally lower cost funds compared to certificate of deposit balances.
- [ ] `a64306fe534436d9` — rank 5 · SSB · 10-K · 2020-02-21 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > During 2019, all categories of deposits increased from 2018 except for savings deposits and certificates of deposit. Total deposits increased $530.2 million, or 4.6%, to $12.2 billion during 2019. Our deposit growth since December 31, 2018 included an increase in interest-bearing demand deposits of $559.3 million and noninterest-bearing transaction account deposits of $183.5 million while certificates of deposits dec …
- [ ] `4cd35fc0c1f8a98a` — rank 6 · UMPQ · 10-K · 2022-02-25 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Total deposits were $26.6 billion at December 31, 2021, an increase of $2.0 billion, or 8%, compared to year-end 2020. The increase is mainly attributable to growth in demand, money market and savings deposits, offset by a decline in time deposits. The increase in non-maturity deposit account categories is attributable to the impact of economic assistance payments, in addition to increased customer savings rates as c …
- [ ] `2771868227257333` — rank 7 · SSB · 10-K · 2022-02-25 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > Our investment securities portfolio increased $2.7 billion, or 61.3% compared to the balance at December 31, 2020. The increase in investment securities from December 31, 2020 was a result of the Company strategically investing its excess funds from continued deposit growth. During 2021, we purchased $3.9 billion of securities, $975.3 million classified as held to maturity and $2.9 billion classified as available for …
- [ ] `9b8162516327ec71` — rank 8 · GBCI · 10-K · 2021-03-01 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations  
      > Excluding the SBAZ acquisition, core deposits increased $3.433 billion, or 32 percent, from the prior year end, with non-interest bearing deposits increasing $1.616 billion, or 44 percent. The current year significant increase in deposits was attributable to a number of factors including the PPP loan proceeds deposited by customers and the increase in customer savings. Non-interest bearing deposits were 37 percent of …

---

### `r048` — How many securities remained available for future issuance under SouthState's equity compensation plans at December 31, 2021?

**Already labelled** `3c74b1e25d60cbee` — SSB · 10-K · 2022-02-25 · section · Item 12. Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters.  
> Item 12. Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters. The following table contains certain information as of December 31, 2021, relating to securities authorized for issuance under our equity compensation plans: Included within the 3,152,247 number of securities available for future issuance in Column C of the table above are 1,767,422 shares remaining for future gra …

Also answers the question?

- [ ] `d6da7e9d1a3021de` — rank 1 · COLB · 10-K · 2022-02-25 · paragraph · Item 5. MARKET FOR REGISTRANT’S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES  
      > (1)Includes 1,982,124 shares available for future issuance under the current stock option and equity compensation plan and 160,273 shares available for purchase under the Employee Stock Purchase Plan as of December 31, 2021.
- [ ] `5332e3fc12a534ca` — rank 2 · SSB · 10-K · 2020-02-21 · section · Item 12. Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters.  
      > Item 12. Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters. The following table contains certain information as of December 31, 2019, relating to securities authorized for issuance under our equity compensation plans: Included within the 1,011,669 number of securities available for future issuance in Column C of the table above are 961,355 shares remaining for future grant …
- [ ] `462b790a77453922` — rank 3 · SSB · 10-K · 2021-02-26 · section · Item 12. Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters.  
      > Item 12. Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters. The following table contains certain information as of December 31, 2020, relating to securities authorized for issuance under our equity compensation plans: Included within the 3,487,567 number of securities available for future issuance in Column C of the table above are 2,069,729 shares remaining for future gra …
- [ ] `7bb03adc4d8b9177` — rank 4 · SSB · 10-K · 2024-03-04 · section · Item 12. Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters.  
      > Item 12. Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters. The following table contains certain information as of December 31, 2023, relating to securities authorized for issuance under our equity compensation plans: Included within the 2,217,147 number of securities available for future issuance in Column C of the table above are 914,169 shares remaining for future grant …
- [ ] `16aaec374b0f31cb` — rank 5 · COLB · DEF 14A · 2022-03-18 · paragraph  
      > Equity Compensation Plan. The 2018 Plan provides for the grant of restricted stock, incentive stock options, nonqualified stock options, restricted stock units and stock appreciation rights. All eligible employees and directors may participate in the 2018 Plan. As of December 31, 2021, there were 1,982,124 shares remaining available for future grant under the 2018 Plan. The 2018 Plan replaced the 2014 Plan; however, …
- [ ] `df18719461c2e630` — rank 6 · SSB · 10-K · 2023-02-24 · section · Item 12. Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters.  
      > Item 12. Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters. The following table contains certain information as of December 31, 2022, relating to securities authorized for issuance under our equity compensation plans: Included within the 2,678,363 number of securities available for future issuance in Column C of the table above are 1,332,029 shares remaining for future gra …
- [ ] `9254a809aa41adbe` — rank 7 · COLB · 10-K · 2021-02-26 · paragraph · Item 5. MARKET FOR REGISTRANT’S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES  
      > (1)Includes 2,292,751 shares available for future issuance under the current stock option and equity compensation plan and 223,859 shares available for purchase under the Employee Stock Purchase Plan as of December 31, 2020.
- [ ] `7d96af916c2e62f0` — rank 8 · COLB · 10-K · 2023-02-24 · paragraph · Item 5. MARKET FOR REGISTRANT’S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES  
      > (1)Includes 1,691,529 shares available for future issuance under the current stock option and equity compensation plan and 85,646 shares available for purchase under the Employee Stock Purchase Plan as of December 31, 2022.

---

### `r049` — What were SouthState's total loans by amortized cost basis at December 31, 2020?

**Already labelled** `a6fc97690207f016` — SSB · 10-K · 2021-02-26 · table  
> ​ ​ | Term Loans | ​ (Dollars in thousands) | Amortized Cost Basis by Origination Year | ​ As of December 31, 2020 | 2020 | 2019 | 2018 | 2017 | 2016 | Prior | Revolving | Total Total Loans | $ 6,483,423 | $ 4,366,628 | $ 3,114,428 | $ 2,432,489 | $ 2,027,572 | $ 4,529,178 | $ 1,710,416 | $ 24,664,134

Also answers the question?

- [ ] `492d110174a84b4e` — rank 1 · UMPQ · 10-K · 2022-02-25 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > Total loans and leases also include discounts on acquired loans of $9.8 million and $17.9 million as of December 31, 2021 and 2020, respectively. As of December 31, 2021, loans totaling $14.5 billion were pledged to secure borrowings and available lines of credit. The Company elected to exclude accrued interest receivable from the amortized cost basis of loans disclosed throughout this footnote. Interest accrued on l …
- [ ] `86620e1ccfa2bd09` — rank 2 · UMPQ · 10-K · 2021-02-25 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > Net loans also include net discounts on acquired loans of $17.9 million and $30.2 million as of December 31, 2020 and 2019, respectively. As of December 31, 2020, loans totaling $12.1 billion were pledged to secure borrowings and available lines of credit. The Company elected to exclude accrued interest receivable from the amortized cost basis of loans disclosed throughout this footnote. Interest accrued on loans tot …
- [ ] `6cc104d743bc999a` — rank 3 · UMPQ · 10-K · 2022-02-25 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > (1) Loans and leases on non-accrual with an amortized cost basis of $31.1 million had a related allowance for credit losses of $16.7 million at December 31, 2020.
- [ ] `d679691e38c92bc0` — rank 4 · UMPQ · 10-K · 2021-02-25 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > (1) Loans and leases on non-accrual with an amortized cost basis of $31.1 million had a related allowance for credit losses of $16.7 million at December 31, 2020.
- [ ] `408f31b35d2426cb` — rank 5 · UMPQ · 10-K · 2023-02-24 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > As of December 31, 2022 and 2021, the net deferred costs were $84.7 million and $57.5 million, respectively. Total loans and leases also include discounts on acquired loans of $6.1 million and $9.8 million as of December 31, 2022 and 2021, respectively. As of December 31, 2022, loans totaling $14.0 billion were pledged to secure borrowings and available lines of credit. The Company elected to exclude accrued interest …
- [ ] `be29a5ab8856350d` — rank 6 · SSB · 10-Q · 2021-05-07 · table  
      > ​ ​ | Term Loans | ​ (Dollars in thousands) | Amortized Cost Basis by Origination Year | ​ As of December 31, 2020 | 2020 | 2019 | 2018 | 2017 | 2016 | Prior | Revolving | Total Total Loans | $ 6,483,423 | $ 4,366,628 | $ 3,114,428 | $ 2,432,489 | $ 2,027,572 | $ 4,529,178 | $ 1,710,416 | $ 24,664,134
- [ ] `d3694e13e016b1f5` — rank 7 · SSB · 10-Q · 2021-08-06 · table  
      > ​ ​ | Term Loans | ​ (Dollars in thousands) | Amortized Cost Basis by Origination Year | ​ As of December 31, 2020 | 2020 | 2019 | 2018 | 2017 | 2016 | Prior | Revolving | Total Total Loans | $6,483,424 | $4,366,629 | $3,114,426 | $2,432,488 | $2,027,571 | $4,529,180 | $1,710,416 | $24,664,134
- [ ] `359cf56ea78b4990` — rank 8 · COLB · 10-K · 2024-02-27 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > The Company elected to exclude accrued interest receivable from the amortized cost basis of loans disclosed throughout this footnote. Interest accrued on loans totaled $154.9 million and $86.8 million as of December 31, 2023 and December 31, 2022, respectively, and is included in other assets on the Consolidated Balance Sheets. As of December 31, 2023, loans totaling $21.2 billion were pledged to secure borrowings an …

---

### `r050` — How many shares had SouthState repurchased under its 2021 Stock Repurchase Plan through June 30, 2022, and at what average price?

**Already labelled** `921727a311922498` — SSB · 10-Q · 2022-08-05 · paragraph · Item 2. UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS  
> In January 2021, the Board of Directors of the Company approved the authorization of a 3,500,000 share Company stock repurchase plan (the “2021 Stock Repurchase Plan”). During 2021 and through June 30, 2022, we repurchased 3,129,979 shares, at an average price of $81.97 per share (excluding cost of commissions) for a total of $256.6 million. Of this amount, we repurchased 1,312,038 shares, at an average price of $83. …

**Already labelled** `320e062da1c1c211` — SSB · 10-Q · 2022-08-05 · section · Item 2. UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS  
> Item 2. UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS In January 2021, the Board of Directors of the Company approved the authorization of a 3,500,000 share Company stock repurchase plan (the “2021 Stock Repurchase Plan”). During 2021 and through June 30, 2022, we repurchased 3,129,979 shares, at an average price of $81.97 per share (excluding cost of commissions) for a total of $256.6 million. Of this …

Also answers the question?

- [ ] `aeff3f7af4add5e1` — rank 1 · SSB · 10-K · 2022-02-25 · paragraph · Item 5. Market for the Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities.  
      > * For the months ended October 31, 2021, November 30, 2021 and December 31, 2021, total includes 93 shares, 251 shares and 701 shares, respectively, that were repurchased under arrangements, authorized by our stock-based compensation plans and Board of Directors, whereby officers or directors may sell previously owned shares to SouthState in order to pay for the exercises of stock options or for income taxes owed on …
- [ ] `1f52f858cd6e221a` — rank 2 · SSB · 10-Q · 2022-11-04 · paragraph · Item 2. UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS  
      > In January 2021, the Board of Directors of the Company approved the authorization of a 3,500,000 share Company stock repurchase plan (the “2021 Stock Repurchase Plan”). During 2021 and through September 30, 2022, we repurchased 3,129,979 shares under the 2021 Stock Repurchase Plan, at an average price of $81.97 per share (excluding cost of commissions) for a total of $256.6 million. Of this amount, we repurchased 1,3 …
- [ ] `b595b125d3d20e15` — rank 3 · SSB · 10-Q · 2021-08-06 · paragraph · Item 2. UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS  
      > In June 2019, our Board of Directors announced the authorization for the repurchase of up to an additional 2,000,000 shares of our common stock under our 2019 Repurchase Program. Through December 31, 2020 we had repurchased 1,485,000 of the shares authorized. In January 2021, the Board of Directors of the Company approved the authorization of a new 3,500,000 share Company stock repurchase plan (the “2021 Stock Repurc …
- [ ] `536ec1164e5efe79` — rank 4 · SSB · 10-K · 2023-02-24 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > On June 7, 2022, the Company received Federal Reserve Board’s supervisory nonobjection on the 2022 Stock Repurchase Program, which was previously approved by the Board of Directors of the Company in April 2022, contingent upon receipt of such supervisory nonobjection. The aggregate number of shares of common stock the Company is authorized to repurchase totaled 4,120,021 million shares, which includes 370,021 shares …
- [ ] `2580383222da8e67` — rank 5 · SSB · 10-Q · 2021-11-05 · paragraph · Item 2. UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS  
      > In June 2019, our Board of Directors announced the authorization for the repurchase of up to an additional 2,000,000 shares of our common stock under our 2019 Repurchase Program. Through December 31, 2020 we had repurchased 1,485,000 of the shares authorized. In January 2021, the Board of Directors of the Company approved the authorization of a new 3,500,000 share Company stock repurchase plan (the “2021 Stock Repurc …
- [ ] `b51fe0ca9938261e` — rank 6 · SSB · 10-K · 2022-02-25 · paragraph · Item 15. Exhibits, Financial Statement Schedules.  
      > As of February 23, 2022, the Company repurchased an additional 582,239 shares of the Company’s common stock pursuant to the 2021 Stock Repurchase Plan at a weighted average price of $85.55 per share after December 31, 2021. Total stock repurchases to date equal 2,400,180 shares at a weighted average price of $81.73 per share. The Company may repurchase up to an additional 1.1 million shares of common stock under the …
- [ ] `94f573f2800d9c8d` — rank 7 · SSB · 10-K · 2023-02-24 · paragraph · Item 15. Exhibits, Financial Statement Schedules.  
      > On January 27, 2021, the Company’s Board of Directors approved a stock repurchase program (“2021 Stock Repurchase Plan”) authorizing the Company to repurchase up to 3,500,000 of the Company’s common shares. During 2022, the Company repurchased a total of 1,312,038 shares at a weighted average price of $83.99 per share pursuant to the 2021 Stock Repurchase Plan. Life-to-date, the Company repurchased a total of 3,129,9 …
- [ ] `1c05b27625c8c3de` — rank 8 · SSB · 10-K · 2023-02-24 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > In January 2021, the Board of Directors of the Company approved the 2021 Stock Repurchase Plan, which authorized the Company to repurchase 3,500,000 common shares. During 2021 and through December 31, 2022, we repurchased 3,129,979 shares, at an average price of $81.97 per share, excluding cost of commissions, for a total of $256.6 million. Of this amount, we repurchased 1,312,038 shares, at an average price of $83.9 …

---

### `r051` — How many shares had SouthState repurchased under the 2021 Stock Repurchase Plan through March 31, 2022?

**Already labelled** `b74adb06f33ca42d` — SSB · 10-Q · 2022-05-06 · paragraph · Item 2. UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS  
> In January 2021, the Board of Directors of the Company approved the authorization of a 3,500,000 share Company stock repurchase plan (the “2021 Stock Repurchase Plan”). During 2021 and through March 31, 2022, we repurchased 2,829,979 shares, at an average price of $82.27 per share (excluding cost of commissions) for a total of $232.8 million. Of this amount, during the first quarter of 2022, we repurchased 1,012,038 …

Also answers the question?

- [ ] `aeff3f7af4add5e1` — rank 1 · SSB · 10-K · 2022-02-25 · paragraph · Item 5. Market for the Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities.  
      > * For the months ended October 31, 2021, November 30, 2021 and December 31, 2021, total includes 93 shares, 251 shares and 701 shares, respectively, that were repurchased under arrangements, authorized by our stock-based compensation plans and Board of Directors, whereby officers or directors may sell previously owned shares to SouthState in order to pay for the exercises of stock options or for income taxes owed on …
- [ ] `b51fe0ca9938261e` — rank 2 · SSB · 10-K · 2022-02-25 · paragraph · Item 15. Exhibits, Financial Statement Schedules.  
      > As of February 23, 2022, the Company repurchased an additional 582,239 shares of the Company’s common stock pursuant to the 2021 Stock Repurchase Plan at a weighted average price of $85.55 per share after December 31, 2021. Total stock repurchases to date equal 2,400,180 shares at a weighted average price of $81.73 per share. The Company may repurchase up to an additional 1.1 million shares of common stock under the …
- [ ] `1c05b27625c8c3de` — rank 3 · SSB · 10-K · 2023-02-24 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > In January 2021, the Board of Directors of the Company approved the 2021 Stock Repurchase Plan, which authorized the Company to repurchase 3,500,000 common shares. During 2021 and through December 31, 2022, we repurchased 3,129,979 shares, at an average price of $81.97 per share, excluding cost of commissions, for a total of $256.6 million. Of this amount, we repurchased 1,312,038 shares, at an average price of $83.9 …
- [ ] `19224eef24c32ac3` — rank 4 · SSB · 10-K · 2023-02-24 · paragraph · Item 5. Market for the Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities.  
      > In January 2021, the Board of Directors of the Company approved the authorization of a 3,500,000 share Company stock repurchase plan (the “2021 Stock Repurchase Plan”). During 2021 and through December 31, 2022, we repurchased 3,129,979 shares under the 2021 Stock Repurchase Plan, at an average price of $81.97 per share (excluding cost of commissions) for a total of $256.6 million. Of this amount, we repurchased 1,31 …
- [ ] `acbe6a36cd2f96f8` — rank 5 · SSB · 10-K · 2024-03-04 · paragraph · Item 5. Market for the Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities.  
      > In January 2021, the Board of Directors of the Company approved the authorization of a 3,500,000 share Company stock repurchase plan (the “2021 Stock Repurchase Plan”). During 2021 and through December 31, 2022, we repurchased 3,129,979 shares under the 2021 Stock Repurchase Plan, at an average price of $81.97 per share (excluding cost of commissions) for a total of $256.6 million. Of this amount, we repurchased 1,31 …
- [ ] `dea0733456e61f11` — rank 6 · SSB · 10-K · 2023-02-24 · paragraph · Item 5. Market for the Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities.  
      > * For the months ended October 31, 2022, November 30, 2022, and December 31, 2022, total includes 663 shares, 33 shares and 125 shares, respectively, that were repurchased under arrangements, authorized by our stock-based compensation plans and Board of Directors, whereby officers or directors may sell previously owned shares to SouthState in order to pay for the exercises of stock options or for income taxes owed on …
- [ ] `b34fc917828b56cc` — rank 7 · SSB · 10-Q · 2022-05-06 · section · Item 2. UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS  
      > Item 2. UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS In January 2021, the Board of Directors of the Company approved the authorization of a 3,500,000 share Company stock repurchase plan (the “2021 Stock Repurchase Plan”). During 2021 and through March 31, 2022, we repurchased 2,829,979 shares, at an average price of $82.27 per share (excluding cost of commissions) for a total of $232.8 million. Of this …
- [ ] `1f52f858cd6e221a` — rank 8 · SSB · 10-Q · 2022-11-04 · paragraph · Item 2. UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS  
      > In January 2021, the Board of Directors of the Company approved the authorization of a 3,500,000 share Company stock repurchase plan (the “2021 Stock Repurchase Plan”). During 2021 and through September 30, 2022, we repurchased 3,129,979 shares under the 2021 Stock Repurchase Plan, at an average price of $81.97 per share (excluding cost of commissions) for a total of $256.6 million. Of this amount, we repurchased 1,3 …

---

### `r052` — How many shares remained available under SouthState's New Repurchase Program as of September 30, 2020?

**Already labelled** `483f1dec6b2b94ac` — SSB · 10-Q · 2020-11-06 · section · Item 2. UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS  
> Item 2. UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS In January 2019, our Board of Directors approved a share repurchase program allowing us to repurchase up to 1,000,000 shares of our common stock, which replaced and superseded our prior share repurchase program. In June 2019, our Board of Directors announced the authorization for the repurchase of up to an additional 2,000,000 shares of our common st …

Also answers the question?

- [ ] `7359cd0f3e4047f3` — rank 1 · UMPQ · 10-Q · 2020-11-05 · paragraph · Item 2. Unregistered Sales of Equity Securities and Use of Proceeds  
      > (2)The Company's share repurchase plan, which was first approved by its Board of Directors and announced in August 2003, was amended on September 29, 2011 to increase the number of common shares available for repurchase under the plan to 15 million shares. The repurchase program has been extended multiple times by the board with the current expiration date of July 31, 2021. As of September 30, 2020, a total of 9.5 mi …
- [ ] `f3eed8ffd0b8c00d` — rank 2 · UMPQ · 10-Q · 2020-08-06 · paragraph · Item 2. Unregistered Sales of Equity Securities and Use of Proceeds  
      > (2)The Company's share repurchase plan, which was first approved by its Board of Directors and announced in August 2003, was amended on September 29, 2011 to increase the number of common shares available for repurchase under the plan to 15 million shares. The repurchase program has been extended multiple times by the board with the current expiration date of July 31, 2021. As of June 30, 2020, a total of 9.5 million …
- [ ] `35de3b8107603b51` — rank 3 · UMPQ · 10-Q · 2020-05-07 · paragraph · Item 2. Unregistered Sales of Equity Securities and Use of Proceeds  
      > (2)The Company's share repurchase plan, which was first approved by its Board of Directors and announced in August 2003, was amended on September 29, 2011 to increase the number of common shares available for repurchase under the plan to 15 million shares. The repurchase program has been extended multiple times by the board with the current expiration date of July 31, 2021. As of March 31, 2020, a total of 9.5 millio …
- [ ] `4e8833322c59cd44` — rank 4 · UMPQ · 10-K · 2021-02-25 · paragraph · Item 5. MARKET FOR REGISTRANT'S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES.  
      > (2)The Company's share repurchase plan, which was first approved by the Board and announced in August 2003, was amended on September 29, 2011 to increase the number of common shares available for repurchase under the plan to 15 million shares. The repurchase program has been extended multiple times by the board with the current expiration date of July 31, 2021. As of December 31, 2020, a total of 9.5 million shares r …
- [ ] `215766c474046142` — rank 5 · UMPQ · 10-Q · 2021-11-04 · paragraph · Item 2. Unregistered Sales of Equity Securities and Use of Proceeds  
      > (2)As of July 21, 2021, the Company approved a new share repurchase program which authorizes the Company to repurchase up to $400 million of common stock over the next twelve months from time to time in open market transactions, accelerated share repurchases, or in privately negotiated transactions as permitted under applicable rules and regulations. This effectively ended the previous share repurchase plan. As of Se …
- [ ] `52ba2dc909263551` — rank 6 · UMPQ · 10-K · 2022-02-25 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > In July 2021, the Company announced that its Board approved a new share repurchase program, which authorizes the Company to repurchase up to $400 million of common stock over the next twelve months from time to time in open market transactions, accelerated share repurchases, or in privately negotiated transactions as permitted under applicable rules and regulations. The program replaced and supersedes the previously …
- [ ] `3119301b220f9711` — rank 7 · UMPQ · 10-K · 2020-02-28 · paragraph · Item 5. MARKET FOR REGISTRANT'S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES.  
      > (2)The Company's share repurchase plan, which was first approved by the Board and announced in August 2003, was amended on September 29, 2011 to increase the number of common shares available for repurchase under the plan to 15 million shares. The repurchase program has been extended multiple times by the board with the current expiration date of July 31, 2021. As of December 31, 2019, a total of 9.9 million shares r …
- [ ] `17f89f5667126655` — rank 8 · SSB · 10-Q · 2020-11-06 · paragraph · Item 2. UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS  
      > In January 2019, our Board of Directors approved a share repurchase program allowing us to repurchase up to 1,000,000 shares of our common stock, which replaced and superseded our prior share repurchase program. In June 2019, our Board of Directors announced the authorization for the repurchase of up to an additional 2,000,000 shares of our common stock (the “New Repurchase Program”), which began once all shares were …

---

### `r053` — What role did Ms. Cooper hold before joining the Atlanta Committee for Progress?

**Already labelled** `1d812e2e97b23dba` — SSB · 8-K · 2022-02-24 · paragraph  
> From January 2019 to February 2022, Ms. Cooper served as the Executive Director for the Atlanta Committee for Progress, a coalition of leading CEOs focused on critical development and inclusion for the city of Atlanta. Prior to joining Atlanta Committee for Progress, Ms. Cooper served as Chief Transformation Officer for WestRock Company, a corrugated package company (2016 to 2018), and Vice President and General Mana …

Also answers the question?

- [ ] `36a45c626f9fe664` — rank 1 · SSB · DEF 14A · 2023-03-10 · table  
      > ​​​ | ​ Nominee | Age (1) | Principal occupation | Director since | Independent | Other Current U.S.-listed company boards | Committee Membership 2022 (C = Chair) (2) Ronald M. Cofield, Sr. | 64 | Retired, Audit Partner, PricewaterhouseCoopers L.L.P. | 2022 | Y | ​ | Audit – C Risk Shantella E. Cooper | 55 | Former Executive Director, Atlanta Committee for Progress | 2022 | Y | Veritiv Corporation; Intercontinental E …
- [ ] `580f8c46f94180f6` — rank 2 · SSB · DEF 14A · 2022-03-11 · paragraph  
      > To that end, based on the recommendations of the Governance and Nominating Committee, in February 2022, the Board appointed Ron Cofield to the Board of Directors and appointed Ms. Cooper and Mr. Hertz as directors upon the closing of the Atlantic Capital merger.
- [ ] `eae1dca7db6206c9` — rank 3 · SSB · 8-K · 2024-07-25 · paragraph  
      > Since January 2022, Ms. Metz has served as Senior Vice President, General Counsel, Chief Compliance Officer, and Secretary for Publix Super Markets, Inc. (“Publix”). In this role, Ms. Metz is responsible for the legal, risk management, compliance and environmental and sustainability functions for Publix. Prior to January 2022, Ms. Metz acted as Vice President, General Counsel, Chief Compliance Officer, and Secretary …
- [ ] `90de08994c21e29c` — rank 4 · SSB · 8-K · 2022-02-24 · paragraph  
      > At the same meeting, and in accordance with the terms and subject to the conditions of the Agreement and Plan of Merger (the “Merger Agreement”), dated as of July 22, 2021, between the Company and Atlantic Capital Bancshares, Inc. (“Atlantic Capital”), under which the Company has the right to name two directors from the ACBI board of directors to join the Company Board, the Company Board unanimously approved the appo …
- [ ] `083a98a8f4bf909a` — rank 5 · SSB · 8-K · 2022-02-24 · paragraph  
      > person pursuant to which the ACBI Directors were selected as directors. There are no transactions in which Messrs. Cofield and Hertz or Ms. Cooper has an interest requiring disclosure under Item 404(a) of Regulation S-K.
- [ ] `7aed43cbf774e462` — rank 6 · COLB · DEF 14A · 2021-04-12 · paragraph  
      > its search within Columbia Bank’s Northwest footprint. After reviewing a deep and diverse slate, the Committee identified two excellent candidates in Laura Alvarez Schrag and Tracy Mack-Askew. Both of them joined the Board in January 2021. As described above, Ms. Alvarez Schrag and Ms. Mack-Askew bring to the Board extensive leadership experience and strong community ties.
- [ ] `1d4b84d33b5781db` — rank 7 · GBCI · DEF 14A · 2020-03-16 · paragraph  
      > Sherry L. Cladouhos, 64, was appointed to the Board in October 2010. She has served as Chairman of the Compensation Committee since July 2015 and served as the Chairman of the Compliance Committee from May 2013 to July 2015. She was employed by Blue Cross Blue Shield Montana for 36 years and served in a variety of leadership and executive roles, including President and CEO, Co-Chief Operating Officer, Senior Vice Pre …
- [ ] `1c4ad2e1774722ef` — rank 8 · GBCI · DEF 14A · 2020-03-16 · paragraph  
      > Annie M. Goodwin, 61, was appointed to the Board in June 2012 and has served as Chairman of the Risk Oversight Committee since July 2012. Ms. Goodwin is an attorney in Helena, Montana and is the principal of the Goodwin Law Office, L.L.C. She practices banking and regulatory law. Ms. Goodwin served as Montana’s Commissioner of Banking and Financial Institutions from 2001 to 2010, as Chief Legal Counsel with the Monta …

---

### `r054` — What adjustment to the tangible book value growth metric did SouthState's Compensation Committee approve in December 2022?

**Already labelled** `c060e1336a90f3ca` — SSB · 8-K · 2022-12-14 · paragraph  
> On December 13, 2022, the Compensation Committee (the “Committee”) of the Board of Directors of SouthState Corporation (the “Company”) approved an adjustment to the calculation of the Company’s tangible book value growth per share (“TBV Growth”) performance metric under the Performance Share Units (“PSUs”) granted to certain Company employees, including each of the named executive officers (other than Mr. Hill), in e …

Also answers the question?

- [ ] `0bdd492b0a9f6b5a` — rank 1 · SSB · DEF 14A · 2024-03-08 · paragraph  
      > In addition, on December 13, 2022, the Compensation Committee approved an adjustment to the calculation of the TBV Growth performance metric under the PSUs granted to each of the named executive officers (other than Mr. Hill) in each of fiscal years 2021 and 2022 (the “TBV Growth Adjustment”). As approved by the Compensation Committee, the TBV Growth Adjustment excludes from the calculation of TBV Growth changes in a …
- [ ] `fad5580a58f1d3b1` — rank 2 · SSB · DEF 14A · 2023-03-10 · paragraph  
      > On December 13, 2022, the Compensation Committee approved an adjustment to the calculation of the TBV Growth performance metric under the PSUs granted to each of the named executive officers (other than Mr. Hill) in each of fiscal years 2021 and 2022 (the “TBV Growth Adjustment”). As approved by the Compensation Committee, the TBV Growth Adjustment excludes from the calculation of TBV Growth changes in accumulated ot …
- [ ] `5b2ffc468627f2d7` — rank 3 · SSB · DEF 14A · 2023-03-10 · paragraph  
      > In addition, the amounts in this column reflect the incremental fair value as a result of the December 2022 TBV Growth Adjustment to PSUs granted in 2022, calculated as of December 13, 2022, in accordance with FASC ASC Topic 718. For additional information, see the discussion captioned “2022 Compensation Paid or Awarded to our NEOs” beginning on page 37.
- [ ] `255bf41a0adeaba7` — rank 4 · SSB · DEF 14A · 2021-03-08 · paragraph  
      > Pre-Merger SouthState NEOs. AIP awards were granted to the pre-Merger SouthState NEOs in early 2020 with the following performance metrics established and approved by SouthState’s Compensation Committee: Profitability (based on 2020 adjusted diluted EPS) and Soundness (based on 2020 asset quality). The Compensation Committee chose the profitability metric because it believes this metric is a key component in building …
- [ ] `b4d57a9e10816bc3` — rank 5 · GBCI · 10-K · 2024-02-23 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations  
      > Tangible stockholders’ equity of $2.003 billion at December 31, 2023 increased $187 million, or 10 percent, from December 31, 2022, which was primarily due to earnings retention and a decrease in net unrealized losses (after-tax) on AFS debt securities. Tangible book value per common share of $18.06 at the current year end increased $1.66 per share, or 10 percent, from the prior year end.
- [ ] `ba66ec28cfd93d22` — rank 6 · SSB · DEF 14A · 2024-03-08 · paragraph  
      > Each year, the Compensation Committee assesses the appropriateness of the prospective metrics for AIP and LTI awards. For the 2023 AIP, the Compensation Committee approved prospective performance metrics for the NEOs which included (1) removing the Adjusted Earnings Per Share (“EPS”) metric and (2) adjusting the calculation for the Adjusted PPNR metric to exclude Net Charge-offs in order to provide a more appropriate …
- [ ] `66b0735eea456cfc` — rank 7 · SSB · DEF 14A · 2023-03-10 · paragraph  
      > In 2022, the Compensation Committee approved a modification to the performance metrics of the AIP awards granted to Messrs. Corbett and Hill given their unique roles as CEO and Executive Chairman. These changes included (1) the addition of a qualitative metric of 10% based on the Compensation Committee’s evaluation of the Executive Chairman’s and the CEO’s success in providing leadership to support the culture and gr …
- [ ] `3092ede8e6ed7c9f` — rank 8 · SSB · DEF 14A · 2024-03-08 · paragraph  
      > The Compensation Committee is responsible for reviewing, on an annual basis, the compensation paid to our directors and making recommendations to the Board on any adjustments to it. Working with its independent compensation consultant, the Compensation Committee annually assesses SouthState’s director compensation program relative to our peers. In making this assessment, the Compensation Committee reviews (i) the ind …

---

### `r055` — When did South State and CenterState enter into their merger agreement?

**Already labelled** `481bf644e4bcd45d` — SSB · 8-K · 2020-04-29 · section · Item 8.01. Other Events  
> Item 8.01. Other Events As previously disclosed, on January 25, 2020, South State Corporation, a South Carolina corporation (the “Company” or “South State”), and CenterState Bank Corporation, a Florida corporation (“CenterState”), entered into an Agreement and Plan of Merger, providing for the merger of the Company and CenterState (the “Merger”), subject to the terms and conditions set forth therein. On April 27, 202 …

Also answers the question?

- [ ] `c7b66ce14b937df9` — rank 1 · SSB · 10-K · 2020-02-21 · paragraph · Item 15. Exhibits, Financial Statement Schedules.  
      > On January 25, 2020, South State and CenterState Bank Corporation, a Florida corporation (“CenterState”) entered into an Agreement and Plan of Merger (the “merger agreement”), pursuant to which South State and CenterState have agreed to combine their respective companies in an all-stock merger of equals. The merger agreement provides that, upon the terms and subject to the conditions set forth therein, CenterState wi …
- [ ] `40edaa3a313a051c` — rank 2 · SSB · 10-K · 2020-02-21 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > On January 25, 2020, South State and CenterState Bank Corporation, a Florida corporation (“CenterState”) entered into an Agreement and Plan of Merger (the “merger agreement”), pursuant to which South State and CenterState have agreed to combine their respective companies in an all-stock merger of equals. The merger agreement provides that, upon the terms and subject to the conditions set forth therein, CenterState wi …
- [ ] `8bfe5f919541d7d0` — rank 3 · SSB · 10-K · 2020-02-21 · paragraph · Item 1. Business.  
      > On January 25, 2020, South State Corporation, (“South State”) entered into an Agreement and Plan of Merger (the”Merger Agreement”) with CenterState Bank Corporation, a Florida corporation ("CenterState"), and a bank holding company headquartered in Winter Haven, Florida. Under the merger agreement, South State and CenterState have agreed to combine their respective companies in an all-stock merger of equals, pursuant …
- [ ] `4e5b62e54b762514` — rank 4 · SSB · 8-K · 2020-01-29 · paragraph  
      > On January 25, 2020, South State Corporation, a South Carolina corporation (“South State”), entered into an Agreement and Plan of Merger (the “Merger Agreement”) with CenterState Bank Corporation, a Florida corporation (“CenterState”). The Merger Agreement provides that, upon the terms and subject to the conditions set forth therein, CenterState will merge with and into South State (the “Merger”), with South State co …
- [ ] `e672b50eed67f7ea` — rank 5 · SSB · 8-K · 2020-04-29 · paragraph · Item 8.01. Other Events  
      > As previously disclosed, on January 25, 2020, South State Corporation, a South Carolina corporation (the “Company” or “South State”), and CenterState Bank Corporation, a Florida corporation (“CenterState”), entered into an Agreement and Plan of Merger, providing for the merger of the Company and CenterState (the “Merger”), subject to the terms and conditions set forth therein.
- [ ] `1e8689fe60efda7f` — rank 6 · SSB · 8-K · 2020-05-11 · paragraph  
      > As previously reported, on January 27, 2020, South State Corporation (the “Company” or “South State”) and CenterState Bank Corporation (“CenterState”) announced the execution of an Agreement and Plan of Merger, dated as of January 25, 2020 (the “merger agreement”), providing for the merger of the Company and CenterState, subject to the terms and conditions set forth therein. The transaction is expected to close in th …
- [ ] `7ae3fa540285ca73` — rank 7 · SSB · 8-K · 2020-05-21 · paragraph  
      > On May 21, 2020, South State Corporation (“South State”) held a special meeting of shareholders (the “special meeting”) to consider certain proposals related to the Agreement and Plan of Merger, dated as of January 25, 2020 (the “merger agreement”), by and between CenterState Bank Corporation (“CenterState”) and South State, which provides, among other things and subject to the terms and conditions set forth therein, …
- [ ] `4c59697926582876` — rank 8 · SSB · 8-K · 2020-05-22 · paragraph  
      > On May 21, 2020, the Board of Governors of the Federal Reserve System (the “Federal Reserve Board”) approved South State Corporation’s (“South State”) application with respect to the previously announced merger of equals between South State and CenterState Bank Corporation (“CenterState”) pursuant to the Agreement and Plan of Merger, dated as of January 25, 2020, by and between CenterState and South State. All requir …

---

### `r056` — What dividend and share repurchase authorization did SouthState announce in January 2021?

**Already labelled** `5d01303506cd6332` — SSB · 8-K · 2021-01-27 · section · Item 8.01. Other Events  
> Item 8.01. Other Events The Board of Directors of the Company declared a quarterly cash dividend on its common stock of $0.47 per share. The dividend is payable on February 19,2021 to shareholders of record as of February 12, 2021. On January 27, 2021, the Board of Directors of the Company approved the authorization of a new 3.5 million share Company stock repurchase plan (the “New Repurchase Program”). This New Repu …

Also answers the question?

- [ ] `ce9e78208210b7c9` — rank 1 · SSB · 10-K · 2022-02-25 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > On January 27, 2021, the Board of Directors of the Company approved the authorization of a 3.5 million share Company stock repurchase plan (the “2021 Stock Repurchase Plan”). During 2021, the Company repurchased a total of 1,817,941 shares for $146.4 million or $80.51 per share (excluding commission expense).
- [ ] `f6c73103ff4aec23` — rank 2 · SSB · 10-K · 2021-02-26 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > During 2020, the Company repurchased a total of 320,000 shares for $24.7 million or $77.23 per share (excluding commission expense). On January 27, 2021, the Board of Directors of the Company approved the authorization of a new 3.5 million share Company stock repurchase plan (the “2021 Repurchase Program”). This 2021 Repurchase Plan replaced in its entirety the Company’s stock repurchase plan announced on June 13, 20 …
- [ ] `fa9a0eb87913b8d9` — rank 3 · SSB · 10-K · 2021-02-26 · paragraph · Item 15. Exhibits, Financial Statement Schedules.  
      > On January 27, 2021, the Company’s Board of Directors approved the authorization of a new 3.5 million share Company stock repurchase plan (the “New Repurchase Program”). The New Repurchase Plan replaces the Company’s prior stock repurchase plan announced on June 13, 2019 in its entirety. The repurchases under the New Repurchase Program will be made from time to time by the Company in the open market as conditions all …
- [ ] `b74adb06f33ca42d` — rank 4 · SSB · 10-Q · 2022-05-06 · paragraph · Item 2. UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS  
      > In January 2021, the Board of Directors of the Company approved the authorization of a 3,500,000 share Company stock repurchase plan (the “2021 Stock Repurchase Plan”). During 2021 and through March 31, 2022, we repurchased 2,829,979 shares, at an average price of $82.27 per share (excluding cost of commissions) for a total of $232.8 million. Of this amount, during the first quarter of 2022, we repurchased 1,012,038 …
- [ ] `3eb846f6b91920cd` — rank 5 · SSB · 8-K · 2021-07-28 · paragraph  
      > On July 28, 2021, South State Corporation (“SouthState” or the “Company”) announced that the Board of Directors of the Company increased its quarterly cash dividend on its common stock from $0.47 per share to $0.49 per share. The dividend is payable on August 19, 2021 to shareholders of record as of August 12, 2021.
- [ ] `1f52f858cd6e221a` — rank 6 · SSB · 10-Q · 2022-11-04 · paragraph · Item 2. UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS  
      > In January 2021, the Board of Directors of the Company approved the authorization of a 3,500,000 share Company stock repurchase plan (the “2021 Stock Repurchase Plan”). During 2021 and through September 30, 2022, we repurchased 3,129,979 shares under the 2021 Stock Repurchase Plan, at an average price of $81.97 per share (excluding cost of commissions) for a total of $256.6 million. Of this amount, we repurchased 1,3 …
- [ ] `19224eef24c32ac3` — rank 7 · SSB · 10-K · 2023-02-24 · paragraph · Item 5. Market for the Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities.  
      > In January 2021, the Board of Directors of the Company approved the authorization of a 3,500,000 share Company stock repurchase plan (the “2021 Stock Repurchase Plan”). During 2021 and through December 31, 2022, we repurchased 3,129,979 shares under the 2021 Stock Repurchase Plan, at an average price of $81.97 per share (excluding cost of commissions) for a total of $256.6 million. Of this amount, we repurchased 1,31 …
- [ ] `acbe6a36cd2f96f8` — rank 8 · SSB · 10-K · 2024-03-04 · paragraph · Item 5. Market for the Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities.  
      > In January 2021, the Board of Directors of the Company approved the authorization of a 3,500,000 share Company stock repurchase plan (the “2021 Stock Repurchase Plan”). During 2021 and through December 31, 2022, we repurchased 3,129,979 shares under the 2021 Stock Repurchase Plan, at an average price of $81.97 per share (excluding cost of commissions) for a total of $256.6 million. Of this amount, we repurchased 1,31 …

---

### `r057` — When did SouthState enter into a merger agreement with Independent Bank Group (IBTX)?

**Already labelled** `a3cea989f6f95fda` — SSB · 8-K · 2024-05-20 · table  
> ​ (d) Exhibits. | ​ ​ Exhibit No. | ​ | Description of Exhibit ​ 2.1 | ​ | Agreement and Plan of Merger, dated as of May 17, 2024, by and between SouthState and IBTX* ​ 10.1 | ​ | Form of IBTX Support Agreement, dated as of May 17, 2024, by and between SouthState and each director of IBTX and Vincent J. Viola ​ 99.1 | ​ | Joint Press Release of SouthState and IBTX, dated as of May 20, 2024 ​ 99.2 | ​ | Investor Prese …

Also answers the question?

- [ ] `4de1a4e47fb2a96e` — rank 1 · SSB · 8-K · 2024-05-20 · paragraph  
      > On May 17, 2024, SouthState Corporation, a South Carolina corporation (“SouthState”), entered into an Agreement and Plan of Merger (the “Merger Agreement”) with Independent Bank Group, Inc., a Texas corporation (“IBTX”).
- [ ] `2341593e82af9303` — rank 2 · SSB · 8-K · 2024-12-19 · paragraph  
      > On December 19, 2024, and in accordance with the terms and subject to the conditions of the Agreement and Plan of Merger (the “Merger Agreement”), dated as of May 17, 2024, between the Company and Independent Bank Group., Inc. (“IBTX”), the Board of Directors (the “Company Board”) of SouthState Corporation (“SouthState” or the “Company”) unanimously approved the appointment of David R. Brooks, the current Chairman an …
- [ ] `b8f9ee8e5fa8897f` — rank 3 · SSB · 8-K · 2024-08-14 · paragraph  
      > On August 14, 2024, SouthState Corporation (“SouthState”) held a special meeting of shareholders (the “special meeting”) to consider certain proposals related to the Agreement and Plan of Merger, dated as of May 17, 2024 (the “merger agreement”), by and between SouthState and Independent Bank Group, Inc. (“Independent”), which provides, among other things and subject to the terms and conditions set forth therein, tha …
- [ ] `84349373c3e3cbbf` — rank 4 · SSB · 8-K · 2024-12-13 · paragraph  
      > On December 13, 2024, the Board of Governors of the Federal Reserve System (the “Federal Reserve Board”) approved SouthState Corporation’s (“SouthState”) application with respect to the previously announced merger (the “holding company merger”) between SouthState and Independent Bank Group, Inc. (“Independent”) pursuant to the Agreement and Plan of Merger, dated as of May 17, 2024, by and between SouthState and Indep …
- [ ] `7f9e6607b0d2cf9d` — rank 5 · SSB · 8-K · 2024-05-20 · paragraph  
      > On May 20, 2024, SouthState and IBTX issued a joint press release announcing the execution of the Merger Agreement. A copy of the joint press release is attached hereto as Exhibit 99.1 and is incorporated by reference herein.
- [ ] `8b02e975d1069d67` — rank 6 · SSB · 8-K · 2021-07-26 · paragraph  
      > On July 22, 2021, South State Corporation, a South Carolina corporation (“SouthState”), entered into an Agreement and Plan of Merger (the “Merger Agreement”) with Atlantic Capital Bancshares, Inc., a Georgia corporation (“Atlantic Capital”). The Merger Agreement provides that, upon the terms and subject to the conditions set forth therein, Atlantic Capital will merge with and into SouthState (the “Merger”), with Sout …
- [ ] `a666b0c1ca033d31` — rank 7 · SSB · 8-K · 2024-05-20 · paragraph  
      > The Merger Agreement provides that, among other things and on the terms and subject to the conditions set forth therein, SouthState will acquire IBTX in an all-stock transaction by means of a merger of IBTX with and into SouthState (the “Merger”) with SouthState surviving the Merger. Immediately following the Merger, IBTX’s wholly owned banking subsidiary, Independent Bank (d/b/a Independent Financial), will merge wi …
- [ ] `36ff24ca615fb887` — rank 8 · SSB · 10-K · 2022-02-25 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > On July 23, 2021, SouthState and Atlantic Capital announced that the two companies had entered into a Merger Agreement, which provides that upon the terms and subject to the conditions set forth in the Merger Agreement, Atlantic Capital will merge with and into SouthState, with SouthState continuing as the surviving corporation in the merger. The Merger Agreement was unanimously approved by the Board of Directors of …

---

### `r058` — Who was appointed SouthState's President in connection with the CenterState merger, and what was his prior role?

**Already labelled** `9447976527f12da8` — SSB · DEF 14A · 2020-08-11 · paragraph  
> Richard Murray, IV, age 58, was appointed as our President on June 7, 2020 in connection with the Merger. Before that, he served as Executive Vice President and Chief Executive Officer of CenterState Bank, N.A. (2019 to June 7, 2020); Chair and Chief Executive Officer of NCOM (May 2017 to April 2019); NCOM Board member (2010 to April 2019); President and Chief Executive Officer of National Bank of Commerce (NBC) (201 …

Also answers the question?

- [ ] `d907116884146344` — rank 1 · SSB · 8-K · 2020-06-08 · paragraph · Item 5.02. Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers; Compensatory Arrangements of Certain Officers.  
      > Pursuant to the Merger Agreement, effective as of the Effective Time, (i) Robert R. Hill, Jr., the Chief Executive Officer of South State prior to the Effective Time, was appointed Executive Chairman of the Board and (ii) Charles W. McPherson, the Lead Independent Director of CenterState prior to the Effective Time, was appointed Lead Independent Director of the Board.
- [ ] `be6f1bb1f2040891` — rank 2 · SSB · DEF 14A · 2020-08-11 · paragraph  
      > Stephen D. Young, age 44, was appointed as our Senior Executive Vice President and Chief Strategy Officer on June 7, 2020 in connection with the Merger. Before that, he served as Executive Vice President, and Chief Operating Officer of CenterState (2016 to June 7, 2020) and CenterState Bank, N.A. (May 2010 to June 7, 2020); Executive Vice President and Chief Financial Officer of CenterState Bank, N.A. (2002 to 2010); …
- [ ] `2c74c9612a7f692b` — rank 3 · SSB · 8-K · 2020-06-08 · paragraph · Item 5.02. Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers; Compensatory Arrangements of Certain Officers.  
      > Pursuant to the Merger Agreement, effective as of the Effective Time, (i) Robert R. Hill, Jr., the Chief Executive Officer of South State prior to the Effective Time, was appointed to serve as the Executive Chairman of the Company, (ii) John C. Corbett, the Chief Executive Officer of CenterState prior to the Effective Time, was appointed to serve as the Chief Executive Officer of the Company, (iii) Richard Murray, IV …
- [ ] `c16974213f0047c5` — rank 4 · SSB · DEF 14A · 2020-08-11 · paragraph  
      > Daniel E. Bockhorst, age 56, was appointed as our Chief Credit Officer on June 7, 2020 in connection with the Merger. Before that, he served as Executive Vice President and Chief Credit Officer of CenterState (2017 to June 7, 2020) and CenterState Bank, N.A. (2010 to 2017), and as Chief Risk Officer of CenterState (2010 – 2017); director of special loans, Florida, for the Royal Bank of Canada, USA (2008 – 2010); Exec …
- [ ] `2f10b5d7e1fc822a` — rank 5 · SSB · DEF 14A · 2020-08-11 · paragraph  
      > William E. Matthews, V, age 56, was appointed as our Chief Financial Officer on June 7, 2020 in connection with the Merger. Before that, he served as Executive Vice President and Chief Financial Officer of CenterState and CenterState Bank, N.A. (2019 to June 7, 2020); President and Chief Financial Officer of NCOM (2018 to 2019); Chief Financial Officer of NCOM and NBC (2011 to 2019); NCOM Board member (2010 to 2019), …
- [ ] `39b28c084f70c6ae` — rank 6 · SSB · DEF 14A · 2023-03-10 · paragraph  
      > In connection with the completion of the CenterState Merger, our Bylaws included merger-specific provisions detailing Board membership which were to remain in place for three years following the closing date. These provisions were designed to provide equity to each side in the CenterState Merger, giving both legal companies equal representation on the Board. Due to (i) the appointment of a highly qualified director i …
- [ ] `2661c5c33aed9df5` — rank 7 · SSB · DEF 14A · 2020-08-11 · paragraph  
      > Beth S. DeSimone, age 60, was appointed as our Chief Risk Officer and General Counsel on June 7, 2020 in connection with the Merger, Before that, she served as Executive Vice President, Chief Risk Officer and General Counsel of CenterState and CenterState Bank, N.A. (2018 to June 7, 2020); as General Counsel of CenterState and CenterState Bank, N.A. (November 2016 to 2018); Executive Vice President, General Counsel a …
- [ ] `2b1818c1d30b756c` — rank 8 · SSB · DEF 14A · 2024-03-08 · paragraph  
      > Effective as of April 26, 2023, as part of our ongoing effort to enhance the independence of our Board and overall governance structure that was initially put in place in connection with the CenterState Merger and was scheduled to expire by its terms in June 2023, the Company eliminated the role of Executive Chairman as an officer of the Company, as disclosed in the Company’s Current Report on Form 8-K filed with the …

---

### `r059` — What restricted stock unit awards did SouthState's non-employee directors receive in 2023, and at what value did they vest?

**Already labelled** `582144c24aa5cfbe` — SSB · DEF 14A · 2024-03-08 · paragraph  
> (2)RSUs were awarded to non-employee directors on May 1, 2023, in the amount of $85,000. These awards vested on November 1, 2023. The market value of the shares is determined by the closing market price of our common stock on the vesting date ($66.78 on November 1, 2023). The assumptions used in the calculation of these amounts for awards granted in 2023 are included in Note 19 in the “Notes to Consolidated Financial …

Also answers the question?

- [ ] `fed4021aacfad1d4` — rank 1 · COLB · DEF 14A · 2024-03-27 · paragraph  
      > For service through the closing of the Merger on February 28, 2023, non-employee directors’ annual equity grant of $70,000 for the 2022-2023 Board service year was prorated through February 28, 2023. The prorated restricted stock awards granted to the non-employee directors automatically vested upon the closing of the Merger, which was a “change in control” as defined in the 2018 Plan. For service from March 1, 2023, …
- [ ] `2223c7cce79fb8da` — rank 2 · GBCI · 10-K · 2024-02-23 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > The fair value of restricted stock units that vested during the years ended December 31, 2023, 2022 and 2021 was $7,410,000, $5,624,000 and $4,535,000, respectively, and the income tax benefit related to these awards was $1,691,000, $1,585,000 and $1,369,000, respectively. Upon vesting of restricted stock units, the shares are issued from the Company’s authorized stock balance.
- [ ] `42b5962fcb49a6a8` — rank 3 · GBCI · 10-K · 2024-02-23 · paragraph · Item 8. Financial Statements and Supplementary Data  
      > The average remaining contractual term on non-vested restricted stock units at December 31, 2023 is 0.9 years. The aggregate intrinsic value of the non-vested restricted stock units at December 31, 2023 was $11,445,000.
- [ ] `32269f798793e57b` — rank 4 · SSB · 10-K · 2023-02-24 · paragraph · Item 15. Exhibits, Financial Statement Schedules.  
      > From time-to-time, we also grant performance RSUs and time-vested RSUs to key employees, and time-vested RSUs to non-employee directors. These awards help align the interests of these employees with the interests of our shareholders by providing economic value directly related to our performance. Some performance RSU grants contain a three-year performance period while others contain a one to two-year performance per …
- [ ] `0c997b603427a9e1` — rank 5 · SSB · 10-K · 2020-02-21 · paragraph · Item 15. Exhibits, Financial Statement Schedules.  
      > The Company routinely also grants shares of restricted stock to key employees and non-employee directors. These awards help align the interests of these employees and directors with the interests of the shareholders of the Company by providing economic value directly related to increases in the value of the Company’s stock. The value of the stock awarded is established as the fair market value of the stock at the tim …
- [ ] `f8699f315c60fffb` — rank 6 · SSB · 10-K · 2021-02-26 · paragraph · Item 15. Exhibits, Financial Statement Schedules.  
      > We from time-to-time also grant shares of restricted stock to key employees and non-employee directors. These awards help align the interests of these employees and directors with the interests of our shareholders by providing economic value directly related to increases in the value of our stock. The value of the stock awarded is established as the fair market value of the stock at the time of the grant. We recogniz …
- [ ] `d55a4e273b254e2c` — rank 7 · SSB · 10-K · 2022-02-25 · paragraph · Item 15. Exhibits, Financial Statement Schedules.  
      > We, from time-to-time, grant shares of restricted stock to key employees and non-employee directors. These awards help align the interests of these employees and directors with the interests of our shareholders by providing economic value directly related to increases in the value of our stock. The value of the stock awarded is established as the fair market value of the stock at the time of the grant. We recognize e …
- [ ] `d7a4b5c5149e5a84` — rank 8 · SSB · 10-K · 2024-03-04 · paragraph · Item 15. Exhibits, Financial Statement Schedules.  
      > From time-to-time, we also grant performance RSUs and time-vested RSUs to key employees, and time-vested RSUs to non-employee directors. These awards help align the interests of these employees with the interests of our shareholders by providing economic value directly related to our performance. Some performance RSU grants contain a three-year performance period while others contain a one to two-year performance per …

---

### `r060` — What was SouthState's combined-business-basis total adjusted revenue for full-year 2020?

**Already labelled** `cd2fa31369158fb5` — SSB · DEF 14A · 2021-03-08 · table  
> ​ | Combined Business Basis | Sep. 30, 2020 | Dec. 31, 2020 | ​ | 2020 Year-to-Date ​ | Mar. 31, 2020 | Jun. 30, 2020 | Sep. 30, 2020 | Dec. 31, 2020 | ​ | 2020 Year-to-Date ​ | SSB | CSFL | Combined (1) | SSB | CSFL (2) | Combined (1) | Sep. 30, 2020 | Dec. 31, 2020 | ​ | 2020 Year-to-Date Net interest income (GAAP) | 128013 | 153353 | $281,366 | 162557 | $111,624 | $274,181 | $270,348 | $265,547 | ​ | 1091442 Plus: …

Also answers the question?

- [ ] `4a24d037cd572c33` — rank 1 · SSB · 10-K · 2023-02-24 · paragraph · Item 15. Exhibits, Financial Statement Schedules.  
      > The Company maintains contracts to provide services, primarily for investment advisory and/or custody of assets. Through the Company’s wholly owned subsidiaries, the Bank, and SouthState Advisory, Inc., the Company contracts with its customers to perform IRA, Trust, and/or Custody and Agency advisory services. Total revenue recognized from these contracts with customers was $39.0 million, $37.0 million and $29.4 mill …
- [ ] `b3698b055e35f256` — rank 2 · SSB · 10-K · 2022-02-25 · paragraph · Item 15. Exhibits, Financial Statement Schedules.  
      > The following disclosures related to ASU Topic 606 involve income derived from contracts with customers. Within the scope of ASU Topic 606, the Company maintains contracts to provide services, primarily for investment advisory and/or custody of assets. Through the Company’s wholly owned subsidiaries, the Bank, and SouthState Advisory, Inc., the Company contracts with its customers to perform IRA, Trust, and/or Custod …
- [ ] `126d88b38a1f5276` — rank 3 · SSB · 10-K · 2022-02-25 · paragraph · Item 5. Market for the Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities.  
      > current earnings. The approval of the OCC is required if the total of all dividends declared by the Bank in any calendar year exceeds the total of its net profits for that year combined with its retained net profits for the preceding two years, less any required transfers to surplus. During 2021, the Bank paid dividends to SouthState totaling $200.0 million. We used these funds and excess cash to pay our dividend to …
- [ ] `99c9047a5ecce000` — rank 4 · SSB · 10-K · 2022-02-25 · table  
      > ​ ​ | Pro Forma ​ | Year Ended (Dollars in thousands) | ​ | December 31, 2020 Total revenues (net interest income plus noninterest income) | $ | 1522434 Net interest income | ​ | $ | 1061233 Net adjusted income available to the common shareholder | ​ | $ | 329827 EPS - basic | ​ | $ | 4.66 EPS - diluted | ​ | $ | 4.64
- [ ] `8ff0ea19b4803a2d` — rank 5 · SSB · 10-K · 2021-02-26 · table  
      > ​ ​ | Pro Forma | ​ | Pro Forma ​ | Year Ended | ​ | Year Ended (Dollars in thousands) | ​ | December 31, 2020 | ​ | December 31, 2019 Total revenues (net interest income plus noninterest income) | $ | 1508215 | $ | 1368452 Net interest income | ​ | $ | 1047014 | ​ | $ | 1058827 Net adjusted income available to the common shareholder | ​ | $ | 385390 | ​ | $ | 412515 EPS - basic | ​ | $ | 5.44 | ​ | $ | 5.85 EPS - di …
- [ ] `35dfd9ae70d2d7ba` — rank 6 · SSB · 8-K · 2024-10-23 · paragraph  
      > Because forward-looking statements relate to future results and occurrences, they are subject to inherent uncertainties, risks and changes in circumstances that are difficult to predict and many of which are beyond the control of IBTX and SouthState. IBTX’s, SouthState’s and the combined company’s actual results may differ materially from those contemplated by the forward-looking statements, which are neither stateme …
- [ ] `dc428cd9e60d3dc0` — rank 7 · SSB · 8-K · 2024-07-24 · paragraph  
      > Because forward-looking statements relate to future results and occurrences, they are subject to inherent uncertainties, risks and changes in circumstances that are difficult to predict and many of which are beyond the control of IBTX and SouthState. IBTX’s, SouthState’s and the combined company’s actual results may differ materially from those contemplated by the forward-looking statements, which are neither stateme …
- [ ] `2c70efedea7d5b4f` — rank 8 · SSB · 8-K · 2024-12-19 · paragraph  
      > Because forward-looking statements relate to future results and occurrences, they are subject to inherent uncertainties, risks and changes in circumstances that are difficult to predict and many of which are beyond the control of Independent and SouthState. Independent’s, SouthState’s and the combined company’s actual results may differ materially from those contemplated by the forward-looking statements, which are n …

---

### `r061` — What were John Corbett's annual incentive and long-term incentive opportunity levels as a percentage of base salary?

**Already labelled** `5c54ffc337310d44` — SSB · DEF 14A · 2024-03-08 · table  
> ​ ​ Name | AIP Opportunity (Cash) (1) | LTI Opportunity60% PSUs 40% RSUs (2) John C. Corbett, Chief Executive Officer | 115% | 280% William E. Matthews V, Chief Financial Officer | 70% | 125% Richard Murray IV, President of the Company | 70% | 100% Renee R. Brooks, Chief Operating Officer | 70% | 100% Stephen D. Young, Chief Strategy Officer | 100% | 150% Robert R. Hill, Jr., Executive Chairman (3) | 115% | 280%

Also answers the question?

- [ ] `5992c0955f534383` — rank 1 · GBCI · DEF 14A · 2022-03-15 · table  
      > Position | Long-Term Incentive Program Opportunity Levels as a % of Base Salary | RSUs Granted as a % of Base Salary | RSUs Granted (#) Position | Threshold | Target | Maximum | RSUs Granted as a % of Base Salary | RSUs Granted (#) President & CEO | 0% | 90.0% | 135.0% | 132.8% | 20658 CFO | 0% | 50.0% | 75.0% | 73.8% | 6207 CAO | 0% | 50.0% | 75.0% | 73.8% | 5423
- [ ] `41ef945332b7072e` — rank 2 · GBCI · DEF 14A · 2021-03-16 · table  
      > Position | Long-Term Incentive Program Opportunity Levels as a % of Base Salary | Actual Earned | RSUs Granted Position | Threshold | Target | Maximum | Actual Earned President & CEO | 0% | 75% | 112.5% | 83.4% | 14351 CFO | 0% | 45% | 67.5% | 50.0% | 4758 CAO | 0% | 45% | 67.5% | 50.0% | 4046
- [ ] `4854ee251b4443dd` — rank 3 · GBCI · DEF 14A · 2024-03-15 · table  
      > Named Executive Officer | Long-Term Incentive Program Opportunity Levels as a % of Base Salary | RSUs Granted as a % of Base Salary | RSUs Granted (#) Named Executive Officer | Threshold | Target | Maximum | RSUs Granted as a % of Base Salary | RSUs Granted (#) Randall M. Chesler | 0% | 110% | 165% | 133.4% | 24778 Ron J. Copher | 0% | 80% | 120% | 97.0% | 9197 Don J. Chery | 0% | 80% | 120% | 97.0% | 8034
- [ ] `f91609a4da9c3075` — rank 4 · GBCI · DEF 14A · 2023-03-15 · table  
      > Position | Long-Term Incentive Program Opportunity Levels as a % of Base Salary | RSUs Granted as a % of Base Salary | RSUs Granted (#) Position | Threshold | Target | Maximum | RSUs Granted as a % of Base Salary | RSUs Granted (#) President & CEO | 0% | 100% | 150% | 139.7% | 21660 CFO | 0% | 65% | 98% | 91.2% | 7429 CAO | 0% | 65% | 98% | 91.2% | 6490
- [ ] `9c4ee39b3d7ee5b6` — rank 5 · GBCI · DEF 14A · 2020-03-16 · table  
      > Position | Long-Term Incentive Program Opportunity Levels as a % of Base Salary | Actual Earned Position | Threshold | Target | Maximum | Actual Earned President & CEO | 0% | 60% | 90% | 74% CFO and CAO | 0% | 40% | 60% | 49%
- [ ] `742759eeee5a84ec` — rank 6 · GBCI · DEF 14A · 2023-03-15 · table  
      > Position | Annual Incentive Program Opportunity Levels as a % of Base Salary | Achieved Bonus As % of Base Salary (1) | Achieved Bonus ($) (1) Position | Threshold | Target | Maximum | Achieved Bonus As % of Base Salary (1) | Achieved Bonus ($) (1) President and CEO | 0% | 85% | 128% | 101.4% | $893,362 CFO | 0% | 55% | 83% | 65.7% | $295,333 CAO | 0% | 55% | 83% | 65.7% | $257,973
- [ ] `a4c627071cd51674` — rank 7 · COLB · DEF 14A · 2020-04-17 · paragraph  
      > The target long-term equity incentive award opportunities granted in early 2019 represented, in the aggregate, approximately 90% of base salary for Mr. Robbins, approximately 65% of base salary for Mr. Stein and approximately 55% of base salary for our other NEOs. Mr. Robbins’ total long-term incentive opportunity was granted 75% in the form of Performance Shares and 25% in the form of Restricted Stock, in order to t …
- [ ] `a0c4b3f3e8aa33be` — rank 8 · GBCI · DEF 14A · 2022-03-15 · paragraph  
      > For 2021, the total of the LTIP goals achieved based on 2020 performance was at 114.27% of target. The table below details, for each Named Executive Officer, the 2021 LTIP opportunity levels as a percentage of base salary, the RSUs granted as a percentage of base salary, and the number of RSUs granted in February 2021. The long-term incentive award opportunities were increased over the prior year based on an analysis …

---

### `r062` — Under which state's law and which bylaw provision are SouthState's directors and officers indemnified?

**Already labelled** `784e33d052cabbd1` — SSB · S-4 · 2020-03-16 · section · Item 20. Indemnification of Directors and Officers  
> Item 20. Indemnification of Directors and Officers Article VII of South State's Amended and Restated Bylaws, as amended, provides that South State shall indemnify any person who at any time serves or has served as a director or officer of South State, or who, while serving as a director or officer of South State, serves or has served, at the request of South State, as a director, officer, partner, trustee, employee o …

Also answers the question?

- [ ] `26f4e8064b3d90c1` — rank 1 · SSB · S-4 · 2021-09-15 · section · Item 20. Indemnification of Directors and Officers  
      > Item 20. Indemnification of Directors and Officers Article VII of SouthState’s Amended and Restated Bylaws, as amended, provides that SouthState shall indemnify any person who at any time serves or has served as a director or officer of SouthState, or who, while serving as a director or officer of SouthState, serves or has served, at the request of SouthState, as a director, officer, partner, trustee, employee or age …
- [ ] `29fda6eea1eefadf` — rank 2 · SSB · S-4 · 2024-06-27 · section · Item 20. Indemnification of Directors and Officers  
      > Item 20. Indemnification of Directors and Officers Article VII of SouthState’s Amended and Restated Bylaws, as amended, provides that SouthState shall indemnify any person who at any time serves or has served as a director or officer of SouthState, or who, while serving as a director or officer of SouthState, serves or has served, at the request of SouthState, as a director, officer, partner, trustee, employee or age …
- [ ] `82853d7c68024db9` — rank 3 · SSB · S-4 · 2020-03-16 · paragraph · Item 20. Indemnification of Directors and Officers  
      > Article VII of South State's Amended and Restated Bylaws, as amended, provides that South State shall indemnify any person who at any time serves or has served as a director or officer of South State, or who, while serving as a director or officer of South State, serves or has served, at the request of South State, as a director, officer, partner, trustee, employee or agent of another corporation, partnership, joint …
- [ ] `4f9735e9a5528211` — rank 4 · SSB · S-4 · 2024-06-27 · paragraph · Item 20. Indemnification of Directors and Officers  
      > Article VII of SouthState’s Amended and Restated Bylaws, as amended, provides that SouthState shall indemnify any person who at any time serves or has served as a director or officer of SouthState, or who, while serving as a director or officer of SouthState, serves or has served, at the request of SouthState, as a director, officer, partner, trustee, employee or agent of another corporation, partnership, joint ventu …
- [ ] `bfe4d76892f0d12f` — rank 5 · SSB · S-4 · 2021-09-15 · paragraph · Item 20. Indemnification of Directors and Officers  
      > Article VII of SouthState’s Amended and Restated Bylaws, as amended, provides that SouthState shall indemnify any person who at any time serves or has served as a director or officer of SouthState, or who, while serving as a director or officer of SouthState, serves or has served, at the request of SouthState, as a director, officer, partner, trustee, employee or agent of another corporation, partnership, joint ventu …
- [ ] `5599fd257113ceff` — rank 6 · SSB · 8-K · 2022-05-31 · paragraph  
      > The Bylaws Amendment removed provisions requiring that the Company Board be comprised of specified numbers of Legacy South State Directors (as defined in the former Amended and Restated Bylaws) and Legacy CenterState Directors (as defined in the former Amended and Restated Bylaws), as well as provisions requiring equal numbers of Legacy South State Directors and Legacy CenterState Directors on certain committees of t …
- [ ] `50a4cf53ddf3be08` — rank 7 · GBCI · 8-K · 2021-05-04 · paragraph · Item 5.03. Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year.  
      > The Articles Amendment provides for indemnification of directors and officers in the Articles, which was previously addressed in the Bylaws. The MBCA was amended effective June 1, 2020, to permit broader indemnification of a corporation’s directors than had been authorized under the statutory provisions previously in effect, provided that the corporation’s articles of incorporation include such authority. The Article …
- [ ] `0d8e043af363aa4e` — rank 8 · WSBC · S-4 · 2024-10-04 · section · Item 20. Indemnification of Directors and Officers.  
      > Item 20. Indemnification of Directors and Officers. Wesbanco’s amended and restated bylaws (the “Bylaws”) provide, and West Virginia law permits, the indemnification of directors and officers against certain liabilities. Officers and directors of Wesbanco and its subsidiaries are indemnified, to the maximum extent permitted under the West Virginia Business Corporation Act (including advanced indemnification payments) …

---

### `r063` — How did South State's and CenterState's stock price to tangible book value per share compare in the merger analysis?

**Already labelled** `6af6dd2ddee7b381` — SSB · S-4 · 2020-03-16 · table  
> Selected Companies South State | CenterState | 25th Percentile | Median | Average | 75th Percentile One-Year Stock Price Change | 31.4 | % | (1.6 | )% | (0.1 | )% | 6.5 | % | 4.1 | % | 9.7 | % One-Year Total Return | 34.4 | % | 0.2 | % | 2.4 | % | 10.0 | % | 6.9 | % | 12.7 | % Stock Price / Tangible Book Value per Share | 224 | % | 189 | % | 166 | % | 177 | % | 177 | % | 197 | % Stock Price / LTM EPS | 16.2x | 12.7x …

Also answers the question?

- [ ] `91e6ad9ebcf166e9` — rank 1 · SSB · 8-K · 2020-01-29 · paragraph  
      > Upon the terms and subject to the conditions set forth in the Merger Agreement, at the effective time of the Merger (the “Effective Time”), each share of common stock, par value $0.01 per share, of CenterState (“CenterState Common Stock”) outstanding immediately prior to the Effective Time, other than certain shares held by CenterState or South State, will be converted into the right to receive 0.3001 shares of commo …
- [ ] `5ee562182e5e9634` — rank 2 · SSB · 10-K · 2020-02-21 · paragraph · Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.  
      > Under the terms of the merger agreement, shareholders of CenterState will receive 0.3001 shares of South State common stock for each share of CenterState common stock they own. After the merger, it is anticipated that CenterState shareholders will own approximately 53% and South State shareholders will own approximately 47% of the combined company. The aggregate consideration, including “in the money” outstanding sto …
- [ ] `e14e25ba14dc6d7b` — rank 3 · SSB · 10-K · 2020-02-21 · paragraph · Item 15. Exhibits, Financial Statement Schedules.  
      > Under the terms of the merger agreement, shareholders of CenterState will receive 0.3001 shares of South State common stock for each share of CenterState common stock they own. After the merger, it is anticipated that CenterState shareholders will own approximately 53% and South State shareholders will own approximately 47% of the combined company. The aggregate consideration, including “in the money” outstanding sto …
- [ ] `c4edc76030269286` — rank 4 · SSB · S-4 · 2020-03-16 · table  
      > Selected Companies South State | CenterState | 25th Percentile | Median | Average | 75th Percentile One-Year Stock Price Change | 31.4 | % | (1.6 | )% | (1.9 | )% | 3.6 | % | 5.5 | % | 12.9 | % One-Year Total Return | 34.4 | % | 0.2 | % | 1.1 | % | 7.7 | % | 8.4 | % | 15.2 | % Stock Price / Tangible Book Value per Share | 224 | % | 189 | % | 148 | % | 164 | % | 166 | % | 179 | % Stock Price / LTM EPS | 16.2x | 12.7x …
- [ ] `125b6aef862e6a78` — rank 5 · SSB · S-4 · 2020-03-16 · table  
      > South State Historical | CenterState Historical | Pro Forma Combined | Equivalent Pro Forma Per Share of CenterState(a) (Unaudited) Comparative Per Share Data Book value per share As of December 31, 2019 | $ | 70.32 | $ | 23.14 | $ | 65.30 | $ | 19.60 Cash dividends paid For the year ended December 31, 2019 | $ | 1.67 | $ | 0.44 | $ | 1.67 | $ | 0.50 Basic earnings For the year ended December 31, 2019 | $ | 5.40 | $ …
- [ ] `3bb1d6caa3ccf503` — rank 6 · SSB · S-4 · 2020-03-16 · table  
      > Selected Transactions South State / CenterState | 25th Percentile | Median | Average | 75th Percentile Price / Tangible Book Value | 202 | % | 154 | % | 160 | 169 | % | 178 | % Price / LTM Operating EPS(1) | 12.6x | 10.8x | 13.7x | 18.2x | 23.7x Price / Estimated EPS | 12.8x | 10.6x | 11.2x | 14.8x | 14.0x Core Deposit Premium | 13.1 | % | 6.5 | % | 9.0 | % | 9.9 | % | 11.7 | % One-Day Market Premium | 10.0 | % | 0.0 …
- [ ] `8bfe5f919541d7d0` — rank 7 · SSB · 10-K · 2020-02-21 · paragraph · Item 1. Business.  
      > On January 25, 2020, South State Corporation, (“South State”) entered into an Agreement and Plan of Merger (the”Merger Agreement”) with CenterState Bank Corporation, a Florida corporation ("CenterState"), and a bank holding company headquartered in Winter Haven, Florida. Under the merger agreement, South State and CenterState have agreed to combine their respective companies in an all-stock merger of equals, pursuant …
- [ ] `1684587066017f34` — rank 8 · COLB · S-4 · 2021-08-06 · paragraph  
      > Furthermore, Raymond James applied the 75th percentile, median, mean and 25th percentile relative valuation multiples for the selected regional and national transactions to BOCH’s tangible book value, last twelve months earnings, and core deposits. Raymond James then compared those implied values to $16.70, the value attributed to the per share merger consideration for the purposes of the Raymond James opinion. The r …

---

### `r064` — What per-share values did South State's sensitivity analysis produce at a 13.0x multiple and no estimate variance?

**Already labelled** `a7de6504370458e2` — SSB · S-4 · 2020-03-16 · table  
> Annual Estimate Variance | 11.0x | 12.0x | 13.0x | 14.0x | 15.0x | 16.0x (10.0%) | $ | 52.01 | $ | 55.66 | $ | 59.32 | $ | 62.97 | $ | 66.62 | $ | 70.27 (5.0%) | 55.16 | 59.02 | 62.87 | 66.72 | 70.57 | 74.43 0.0% | 58.32 | 62.37 | 66.42 | 70.47 | 74.52 | 78.58 5.0% | 61.47 | 65.72 | 69.97 | 74.23 | 78.48 | 82.73 10.0% | 64.63 | 69.08 | 73.53 | 77.98 | 82.43 | 86.88

Also answers the question?

- [ ] `bf5f4d06840311b9` — rank 1 · SSB · 8-K · 2020-05-21 · paragraph  
      > As of April 14, 2020, the record date for the special meeting, there were 33,464,420 shares of common stock, par value $2.50 per share, of South State (“Common Stock”) outstanding, each of which was entitled to one vote for each proposal at the special meeting. At the special meeting, a total of 26,383,056 shares of Common Stock, representing approximately 78.84% of the shares of Common Stock outstanding and entitled …
- [ ] `162e3ffff18cbe5e` — rank 2 · SSB · DEF 14A · 2020-08-11 · paragraph  
      > Common Stock shall mean the Common Stock, par value $2.50 per share, of South State.
- [ ] `125b6aef862e6a78` — rank 3 · SSB · S-4 · 2020-03-16 · table  
      > South State Historical | CenterState Historical | Pro Forma Combined | Equivalent Pro Forma Per Share of CenterState(a) (Unaudited) Comparative Per Share Data Book value per share As of December 31, 2019 | $ | 70.32 | $ | 23.14 | $ | 65.30 | $ | 19.60 Cash dividends paid For the year ended December 31, 2019 | $ | 1.67 | $ | 0.44 | $ | 1.67 | $ | 0.50 Basic earnings For the year ended December 31, 2019 | $ | 5.40 | $ …
- [ ] `6af6dd2ddee7b381` — rank 4 · SSB · S-4 · 2020-03-16 · table  
      > Selected Companies South State | CenterState | 25th Percentile | Median | Average | 75th Percentile One-Year Stock Price Change | 31.4 | % | (1.6 | )% | (0.1 | )% | 6.5 | % | 4.1 | % | 9.7 | % One-Year Total Return | 34.4 | % | 0.2 | % | 2.4 | % | 10.0 | % | 6.9 | % | 12.7 | % Stock Price / Tangible Book Value per Share | 224 | % | 189 | % | 166 | % | 177 | % | 177 | % | 197 | % Stock Price / LTM EPS | 16.2x | 12.7x …
- [ ] `c4edc76030269286` — rank 5 · SSB · S-4 · 2020-03-16 · table  
      > Selected Companies South State | CenterState | 25th Percentile | Median | Average | 75th Percentile One-Year Stock Price Change | 31.4 | % | (1.6 | )% | (1.9 | )% | 3.6 | % | 5.5 | % | 12.9 | % One-Year Total Return | 34.4 | % | 0.2 | % | 1.1 | % | 7.7 | % | 8.4 | % | 15.2 | % Stock Price / Tangible Book Value per Share | 224 | % | 189 | % | 148 | % | 164 | % | 166 | % | 179 | % Stock Price / LTM EPS | 16.2x | 12.7x …
- [ ] `91e6ad9ebcf166e9` — rank 6 · SSB · 8-K · 2020-01-29 · paragraph  
      > Upon the terms and subject to the conditions set forth in the Merger Agreement, at the effective time of the Merger (the “Effective Time”), each share of common stock, par value $0.01 per share, of CenterState (“CenterState Common Stock”) outstanding immediately prior to the Effective Time, other than certain shares held by CenterState or South State, will be converted into the right to receive 0.3001 shares of commo …
- [ ] `3eb846f6b91920cd` — rank 7 · SSB · 8-K · 2021-07-28 · paragraph  
      > On July 28, 2021, South State Corporation (“SouthState” or the “Company”) announced that the Board of Directors of the Company increased its quarterly cash dividend on its common stock from $0.47 per share to $0.49 per share. The dividend is payable on August 19, 2021 to shareholders of record as of August 12, 2021.
- [ ] `05d6109985034427` — rank 8 · COLB · 8-K · 2022-01-20 · paragraph · Item 8.01. Other Events.  
      > The low and high stock price-to-tangible book value per share multiples of the selected companies were 1.51x and 3.39x, respectively, the low and high stock price-to-2021 estimated EPS multiples of the selected companies were 9.7x and 20.4x, respectively, the low and high stock price-to-2022 estimated EPS multiples of the selected companies were 11.0x and 19.7x, respectively, and the low and high stock price-to-2023 …

---

### `r065` — What economic forecast and macroeconomic variables did Umpqua use to estimate its allowance for credit losses at December 31, 2021?

**Already labelled** `1da1c38ba18769a8` — UMPQ · 10-K · 2022-02-25 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
> To calculate the ACL, the CECL models use a forecast of future economic conditions and are dependent upon specific macroeconomic variables that are relevant to each of the Bank's loan and lease portfolios. The forward-looking assumptions revert to historical data when they reach the point where future assumptions are no longer estimated. As of December 31, 2021, the Bank used Moody's Analytics November consensus econ …

Also answers the question?

- [ ] `ec84c6d72e0197ef` — rank 1 · WSBC · 10-K · 2022-02-28 · paragraph · Item 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > The allowance for credit losses by loan category, presented in Note 5, “Loans and the Allowance for Credit Losses” of the Consolidated Financial Statements, summarizes the impact of changes in various factors that affect the allowance for credit losses in each segment of the portfolio. The allowance for credit losses under CECL is calculated utilizing the PD/LGD, which is then discounted to net present value. PD is t …
- [ ] `465d257242a301e8` — rank 2 · WSBC · 10-K · 2022-02-28 · paragraph · Item 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > If forecasted projections of national unemployment remain consistent with the forecast utilized by Wesbanco as of December 31, 2021 throughout next year, this may result in less significant future quarterly fluctuations in the allowance for credit losses, assuming other model variables remain relatively constant.
- [ ] `9563f96b2a6f25ab` — rank 3 · UMPQ · 10-K · 2023-02-24 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > •The allowance for credit losses was $315.4 million, as of December 31, 2022, an increase of $54.2 million, as compared to December 31, 2021. The increase is due to the growth of the loan portfolio, as well as deterioration in the economic forecasts used in the credit models.
- [ ] `28156eed2ccd5f6e` — rank 4 · UMPQ · 10-Q · 2022-05-05 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended March 31, 2022 and December 31, 2021, where applicable, throughout this Management's Discussion and Analysis.  
      > •The allowance for credit losses was $261.5 million as of March 31, 2022, which was relatively consistent with December 31, 2021. The increase in the allowance for credit losses is due to the growth of the loan portfolio, as well as changes in the economic forecasts used in the credit models.
- [ ] `349d43befb9539a8` — rank 5 · UMPQ · 10-K · 2022-02-25 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > The following is a discussion of the changes in the factors that influenced management's current estimate of expected credit losses. The changes in the ACL estimate for all portfolio segments, during the year ended December 31, 2021, were primarily related to changes in the economic assumptions. The Bank opted to use Moody's Analytics' November consensus economic forecast for estimating the ACL as of December 31, 202 …
- [ ] `99cf8c5b9d10b564` — rank 6 · WSBC · 10-K · 2024-02-26 · paragraph · Item 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA  
      > The allowance for credit losses under CECL is calculated utilizing the probability of default ("PD")/ loss given default ("LGD"), which is then discounted to net present value. PD is the probability the asset will default within a given time frame and LGD is the percentage of the asset not expected to be collected due to default. The primary macroeconomic drivers of the quantitative model include forecasts of nationa …
- [ ] `ba6287ed5afa7c30` — rank 7 · UMPQ · 10-Q · 2022-07-29 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended June 30, 2022 and March 31, 2022, where applicable, throughout this Management's Discussion and Analysis.  
      > •The allowance for credit losses was $273.9 million as of June 30, 2022, an increase of $12.8 million compared to December 31, 2021. The increase in the allowance for credit losses is due to the growth of the loan portfolio, as well as changes in the economic forecasts used in the credit models.
- [ ] `92c679258e1ab63f` — rank 8 · UMPQ · 10-Q · 2022-10-31 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended September 30, 2022 and June 30, 2022, where applicable, throughout this Management's Discussion and Analysis.  
      > •The allowance for credit losses was $294.9 million as of September 30, 2022, an increase of $33.7 million compared to December 31, 2021. The increase in the allowance for credit losses is due to the growth of the loan portfolio, as well as changes in the economic forecasts used in the credit models.

---

### `r066` — What did Umpqua's net cash provided by financing activities consist of during 2019?

**Already labelled** `b8f4e4b85a8bc50d` — UMPQ · 10-K · 2020-02-28 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
> Net cash of $1.4 billion provided by financing activities during 2019 primarily consisted of $1.4 billion increase in net deposits and proceeds from borrowings of $940.7 million, partially offset by repayment of debt of $785.7 million and dividends paid on common stock of $185.1 million. This compares to net cash of $982.3 million provided by financing activities during 2018, which consisted primarily of $1.2 billion …

Also answers the question?

- [ ] `8f27e683eeaf7ed9` — rank 1 · UMPQ · 10-K · 2021-02-25 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Net cash of $2.1 billion provided by financing activities during 2020 primarily consisted of $2.3 billion increase in net deposits and proceeds from borrowings of $600.0 million, partially offset by repayment of debt of $735.0 million and dividends paid on common stock of $185.0 million. This compares to net cash of $1.4 billion provided by financing activities during 2019, which consisted primarily of $1.4 billion i …
- [ ] `45d451bfae54059a` — rank 2 · UMPQ · 10-Q · 2020-05-07 · table  
      > UMPQUA HOLDINGS CORPORATION AND SUBSIDIARIES CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS (Continued) (UNAUDITED) Three Months Ended (in thousands) | March 31, 2020 | March 31, 2019 CASH FLOWS FROM FINANCING ACTIVITIES: Net increase in deposit liabilities | $ | 217973 | $ | 155937 Net increase (decrease) in securities sold under agreements to repurchase | 34937 | (8,207) Proceeds from borrowings | 600000 | 230670 …
- [ ] `47d59f70c286e346` — rank 3 · UMPQ · 10-Q · 2020-08-06 · table  
      > UMPQUA HOLDINGS CORPORATION AND SUBSIDIARIES CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS (Continued) (UNAUDITED) Six Months Ended (in thousands) | June 30, 2020 | June 30, 2019 CASH FLOWS FROM FINANCING ACTIVITIES: Net increase in deposit liabilities | $ | 2363045 | $ | 731192 Net increase in securities sold under agreements to repurchase | 87106 | 10901 Proceeds from borrowings | 600000 | 330670 Repayment of bor …
- [ ] `dac553a9703f1d60` — rank 4 · UMPQ · 10-Q · 2020-11-05 · table  
      > UMPQUA HOLDINGS CORPORATION AND SUBSIDIARIES CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS (Continued) (UNAUDITED) Nine Months Ended (in thousands) | September 30, 2020 | September 30, 2019 CASH FLOWS FROM FINANCING ACTIVITIES: Net increase in deposit liabilities | $ | 2288262 | $ | 1347046 Net increase in securities sold under agreements to repurchase | 76720 | (434) Proceeds from borrowings | 600000 | 810670 Repa …
- [ ] `daea2b0e6fa86bcc` — rank 5 · UMPQ · 10-K · 2020-02-28 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > As disclosed in the Consolidated Statements of Cash Flows, net cash used in operating activities was $80.5 million during 2019, with the difference between cash provided by operating activities and net income largely consisting of originations of loans held for sale of $3.1 billion, the increase in other assets of $141.8 million, the gain on sale of loans of $95.4 million, and the gain on equity securities of $83.5 m …
- [ ] `4beedf655df34ff3` — rank 6 · UMPQ · 10-Q · 2022-05-05 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended March 31, 2022 and December 31, 2021, where applicable, throughout this Management's Discussion and Analysis.  
      > Net cash of $62.6 million provided by financing activities during the three months ended March 31, 2022, primarily consisted of $104.9 million net increase in deposits, offset by $45.5 million of dividends paid on common stock. This compares to net cash of $771.1 million provided by financing activities during the three months ended March 31, 2021, which primarily consisted of $1.3 billion net increase in deposits an …
- [ ] `caa2c4c214ab4603` — rank 7 · UMPQ · 10-K · 2022-02-25 · table  
      > (in thousands) | 2021 | 2021.0 | 2020 | 2020.0 | 2019 | 2019.0 OPERATING ACTIVITIES: Net income (loss) | $ | 420300 | $ | (1,523,420) | $ | 354095 Adjustment to reconcile net income to net cash provided by operating activities: Gain on sale of Umpqua Investments, Inc. | (4,444) | — Equity in undistributed (earnings) losses of subsidiaries | (23,876) | 1722081 | (155,683) Depreciation, amortization and accretion | (22 …
- [ ] `22920f9774407527` — rank 8 · UMPQ · 10-K · 2022-02-25 · paragraph · Item 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS  
      > Net cash of $1.1 billion provided by financing activities during 2021 primarily consisted of the $2.0 billion increase in net deposits and the net increase in securities sold under agreements to repurchase of $116.9 million, partially offset by repayment of borrowings of $765.0 million, dividends paid on common stock of $183.7 million, and the repurchase and retirement of common stock of $80.7 million. This compares …

---

### `r067` — How many shareholders of record did Umpqua have at December 31, 2020, and on what exchange did its stock trade?

**Already labelled** `92c64321311afb9c` — UMPQ · 10-K · 2021-02-25 · section · Item 5. MARKET FOR REGISTRANT'S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES.  
> Item 5. MARKET FOR REGISTRANT'S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES. (a) Our common stock is traded on The NASDAQ Global Select Market under the symbol "UMPQ." As of December 31, 2020, our common stock was held by 4,315 shareholders of record, a number that does not include beneficial owners who hold shares in "street name," or shareholders from previously acquired com …

Also answers the question?

- [ ] `fae512ae44025a95` — rank 1 · UMPQ · 10-K · 2021-02-25 · paragraph · Item 5. MARKET FOR REGISTRANT'S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES.  
      > (a) Our common stock is traded on The NASDAQ Global Select Market under the symbol "UMPQ." As of December 31, 2020, our common stock was held by 4,315 shareholders of record, a number that does not include beneficial owners who hold shares in "street name," or shareholders from previously acquired companies that have not exchanged their stock. At December 31, 2020, a total of 1.3 million shares of unvested restricted …
- [ ] `f0e76d1b6d867b65` — rank 2 · UMPQ · 10-K · 2020-02-28 · section · Item 5. MARKET FOR REGISTRANT'S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES.  
      > Item 5. MARKET FOR REGISTRANT'S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES. (a) Our common stock is traded on The NASDAQ Global Select Market under the symbol "UMPQ." As of December 31, 2019, our common stock was held by approximately 4,419 shareholders of record, a number that does not include beneficial owners who hold shares in "street name," or shareholders from previousl …
- [ ] `6ecc1ba6f8673e86` — rank 3 · UMPQ · DEF 14A · 2020-03-05 · paragraph · Item 3. : Advisory (non-binding) vote on the Company’s executive compensation program (“say on pay”).  
      > A: Holders of record of Umpqua common stock at the close of business on February 12, 2020 are eligible to vote at Umpqua’s annual meeting of shareholders. As of that date, there were 220,438,367 shares of Umpqua common stock outstanding held by 4,390 holders of record, a number that does not include beneficial owners who hold shares in “street name.”
- [ ] `11e07168f6b011c6` — rank 4 · UMPQ · 10-K · 2020-02-28 · paragraph · Item 5. MARKET FOR REGISTRANT'S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES.  
      > (a) Our common stock is traded on The NASDAQ Global Select Market under the symbol "UMPQ." As of December 31, 2019, our common stock was held by approximately 4,419 shareholders of record, a number that does not include beneficial owners who hold shares in "street name," or shareholders from previously acquired companies that have not exchanged their stock. At December 31, 2019, a total of 1.2 million shares of unves …
- [ ] `a69ebe401970746c` — rank 5 · UMPQ · 10-K · 2022-02-25 · paragraph · Item 5. MARKET FOR REGISTRANT'S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES.  
      > (a)Our common stock is traded on The NASDAQ Global Select Market under the symbol "UMPQ." As of December 31, 2021, our common stock was held by 4,131 shareholders of record, a number that does not include beneficial owners who hold shares in "street name," or shareholders from previously acquired companies that have not exchanged their stock. At December 31, 2021, a total of 1.4 million shares of unvested restricted …
- [ ] `a6c846b9b4864c80` — rank 6 · UMPQ · 10-K · 2023-02-24 · paragraph · Item 5. MARKET FOR REGISTRANT'S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES.  
      > (a)Our common stock is traded on the Nasdaq Global Select Market under the symbol "UMPQ." As of December 31, 2022, our common stock was held by 4,028 shareholders of record, a number that does not include beneficial owners who hold shares in "street name," or shareholders from previously acquired companies that have not exchanged their stock. At December 31, 2022, a total of 1.2 million shares of unvested restricted …
- [ ] `05b18664d6f781bb` — rank 7 · GBCI · 10-K · 2021-03-01 · paragraph · Item 5. Market for Registrant’s Common Equity, Related Stockholder Matters  
      > The Company’s stock trades on the NASDAQ Global Select Market under the symbol: GBCI. As of December 31, 2020, there were approximately 1,669 shareholders of record for the Company’s common stock. The market range of high and low market prices for the Company’s common stock for the periods indicated are shown below:
- [ ] `ec1b262f810e8013` — rank 8 · COLB · 10-K · 2023-02-24 · paragraph · Item 1. BUSINESS  
      > Consistent with that strategy, on October 12, 2021, we announced a definitive agreement to combine with Umpqua Holdings Corporation, the parent company of Umpqua Bank, headquartered in Lake Oswego, Oregon, with $31.85 billion in assets as of December 31, 2022. Following the consummation of our merger with Umpqua, the combined company will have over 300 banking offices throughout Washington, Oregon, Idaho, California …

---

### `r068` — What was Cort O'Haver's total compensation in 2021?

**Already labelled** `82dcb0fdb5ed03c3` — UMPQ · 10-K · 2022-02-25 · table  
> Name and Principal Position | Year | Salary | Bonus | StockAwards | OptionAwards | Non-EquityIncentive PlanCompensation | Change inPension ValueandNonqualifiedDeferredCompensationEarnings | All OtherCompensation | Total (a) | (b) | (c) | (d) | (e)(1) | (f) | (g)(2) | (h) | (i)(3) | (j) O'Haver, Cort | 2021 | $1,050,000 | — | $2,179,438 | — | $1,522,500 | — | $8,769 | $4,760,707 President and CEO | 2020 | $1,000,000 | …

Also answers the question?

- [ ] `164ec144521403cc` — rank 1 · UMPQ · 10-K · 2022-02-25 · paragraph · Item 11. EXECUTIVE COMPENSATION  
      > In January 2021, the Compensation Committee approved awards to Mr. O'Haver of 40,630 ROATCE-based PSAs, 40,630 TSR-based PSAs and 34,825 RSUs with an accounting value at grant of $2.2 million. After reviewing competitive data for equity awards to, and total compensation of, the CEO position, the Committee determined that the aggregate equity awards to the CEO should be valued at not less than his base salary and targ …
- [ ] `f151177e6c47ff20` — rank 2 · UMPQ · 10-K · 2023-02-24 · paragraph · Item 11. EXECUTIVE COMPENSATION  
      > In January 2022, the Compensation Committee approved awards to Mr. O'Haver of 98,360 RSUs with an accounting value at grant of $2.1 million. After reviewing competitive data for equity awards to, and total compensation of, the CEO position, the Committee determined that the aggregate equity awards to the CEO should be valued at not less than his base salary and target cash incentive. CEO O'Haver recommended the amoun …
- [ ] `99542efd592af12e` — rank 3 · UMPQ · 10-K · 2022-02-25 · paragraph · Item 11. EXECUTIVE COMPENSATION  
      > (1) Fair value of stock awards issued during the year(s) shown; no option awards were issued. The assumptions made in calculating these values are disclosed in Notes 1 (Stock-Based Compensation discussion) and 20 to our Consolidated Financial Statements in our 2021 annual report on Form 10-K. The maximum value of the stock awards with performance conditions was: O'Haver $2,315,301; Farnsworth $511,839; Nixon $866,229 …
- [ ] `a9d670e44f6e6b0f` — rank 4 · COLB · DEF 14A · 2024-03-27 · table  
      > 2023 Termination/Change-in-Control Payments – Cort L. O’Haver Death | Disability | Termination w/o Cause (Not Due to CIC) | Termination Due to CIC(1) | Retirement Cash/Severance(2) | $7,250,000 | $12,666,667 | $13,500,000 | $— Deferred Compensation | — Benefits payable under SERPs, Unit Plans, or Split Dollar Life Insurance | — Bank Owned Life Insurance | — Healthcare and Other Benefits(3) | 40969 | — FMV of Accelera …
- [ ] `2a6330cda2688d8c` — rank 5 · COLB · DEF 14A · 2024-03-27 · table  
      > Name and Principal Position | Year | Salary | Bonus | Stock Awards | Non-Equity Incentive Plan Compensation | Change in Pension Value and Nonqualified Deferred Compensation Earnings | All Other Compensation | Total (1) | (2) | (3) (4) | (2) (5) | (6) | (7) Clint E. Stein, President, Chief Executive Officer | 2023 | $ | 1150000 | - | $ | 3042229 | $ | 1269600 | $ | 218435 | $ | 663986 | $ | 6344250 Clint E. Stein, Pre …
- [ ] `af64956ddb145e0f` — rank 6 · UMPQ · DEF 14A · 2020-03-05 · table  
      > % of Total Annual Compensation that was | % of Total Compensation paid in Executive Officer | Fixed | At Risk | Cash | Equity Cort O’Haver | 27% | 73% | 47% | 53% Ron Farnsworth | 35% | 65% | 59% | 41% Rilla Delorier | 35% | 65% | 59% | 41% Tory Nixon | 34% | 66% | 57% | 43% David Shotwell | 33% | 67% | 53% | 47%
- [ ] `1d9e0b0f03d3498c` — rank 7 · UMPQ · DEF 14A · 2021-03-05 · table  
      > % of Total Annual Compensation that was | % of Total Compensation paid in Fixed | At Risk | Cash | Equity O’Haver, Cort | 24% | 76% | 52% | 48% Farnsworth, Ron | 31% | 69% | 60% | 40% Nixon, Tory | 30% | 70% | 59% | 41% Ognall, Andrew | 39% | 61% | 70% | 30% Shotwell, David | 36% | 64% | 36% Delorier, Rilla | 46% | 54% | 46% | 54%
- [ ] `b046041080d0c2bf` — rank 8 · UMPQ · DEF 14A · 2020-03-05 · table  
      > Name and Principal Position | Year | Salary | Bonus | Stock Awards | Option Awards | Non-Equity Incentive Plan Compensation | Change in Pension Value and Nonqualified Deferred Compensation Earnings | All Other Compensation | Total (a) | (b) | (c)(1) | (d)(2) | (e)(3) | (f) | (g)(4) | (h) | (i)(5) | (j) O'Haver, Cort President and CEO | 2019 | $950,000 | — | $1,892,548 | — | $741,000 | — | $21,298 | $3,604,846 O'Haver …

---

### `r069` — How did Umpqua's cumulative total return compare with the NASDAQ U.S. index from 2014 through 2019?

**Already labelled** `25d63f441b0d1250` — UMPQ · 10-K · 2020-02-28 · table  
> Period Ending 12/31/2014 | 12/31/2015 | 12/31/2016 | 12/31/2017 | 12/31/2018 | 12/31/2019 Umpqua Holdings Corporation | $100.00 | $96.96 | $119.16 | $136.76 | $108.94 | $127.45 NASDAQ U.S. | $100.00 | $106.96 | $116.45 | $150.96 | $146.67 | $200.49 S&P 500 | $100.00 | $101.38 | $113.51 | $138.29 | $132.23 | $173.86 SNL U.S. Bank NASDAQ | $100.00 | $107.95 | $149.68 | $157.58 | $132.82 | $166.75

Also answers the question?

- [ ] `0c0aeb9c1df23f18` — rank 1 · UMPQ · DEF 14A · 2020-03-05 · chart_description  
      > This image is a line chart titled "Total Return Performance" that compares the cumulative total return of Umpqua Holdings Corporation against the KRX (KBW Regional Bank Index). The vertical axis represents the "Index Value," while the horizontal axis covers five annual time periods from December 31, 2014, to December 31, 2019. Starting at an identical baseline index value of 100 in late 2014, both entities generally …
- [ ] `f1100c0252fdf924` — rank 2 · UMPQ · 10-K · 2020-02-28 · paragraph · Item 5. MARKET FOR REGISTRANT'S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES.  
      > The following chart, which is furnished not filed, compares the yearly percentage changes in the cumulative shareholder return on our common stock during the five fiscal years ended December 31, 2019, with (i) the Total Return Index for The NASDAQ Stock Market (U.S. Companies) (ii) the Standard and Poor's 500 and (iii) the SNL U.S. Bank NASDAQ. This comparison assumes $100.00 was invested on December 31, 2014, in our …
- [ ] `59a1307879d0d11a` — rank 3 · COLB · 10-K · 2020-02-27 · chart_description  
      > This line chart titled "Total Return Performance" plots cumulative index values across annual periods ending from December 31, 2014, to December 31, 2019. It compares the total returns of Columbia Banking System, Inc. against the NASDAQ Composite and the KBW Regional Banking Index. All three series start at a baseline value of 100 and show an overall upward trend over the five-year span, with Columbia Banking System …
- [ ] `dc444707e09d057b` — rank 4 · UMPQ · DEF 14A · 2020-03-05 · chart_description  
      > This is a bar chart titled "Total Return Performance" that compares the performance of Umpqua against the KBW Regional Banking Index (KRX). The horizontal axis covers four time horizons—1 year, 3 year, 5 year, and 10 year—while the vertical axis measures total return percentages from 0.0% to 250.0%. Overall, while total returns remain low across the 1-year and 3-year intervals, both categories experience significant …
- [ ] `981661be34775c49` — rank 5 · UMPQ · 10-K · 2021-02-25 · paragraph · Item 5. MARKET FOR REGISTRANT'S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES.  
      > The following chart, which is furnished as part of our annual report to shareholders and not filed, compares the yearly percentage changes in the cumulative shareholder return on our common stock during the five fiscal years ended December 31, 2020, with (i) the Total Return Index for The NASDAQ Stock Market (U.S. Companies) (ii) the Standard and Poor's 500 and (iii) the NASDAQ Bank Index. This comparison assumes $10 …
- [ ] `f3242ddde250fd17` — rank 6 · GBCI · 10-K · 2020-02-21 · paragraph · Item 5. Market for Registrant’s Common Equity, Related Stockholder Matters  
      > The following graph compares the yearly cumulative total return of the Company’s common stock over a five-year measurement period with the yearly cumulative total return on the stocks included in 1) the Russell 2000 Index; and 2) the KBW NASDAQ Regional Banking Index (“KBW Regional Banking Index”). Total return includes appreciation in market value of the stock as well as the actual cash and stock dividends paid to s …
- [ ] `3f104be7b905edfe` — rank 7 · UMPQ · 10-K · 2022-02-25 · paragraph · Item 5. MARKET FOR REGISTRANT'S COMMON EQUITY, RELATED STOCKHOLDER MATTERS AND ISSUER PURCHASES OF EQUITY SECURITIES.  
      > The following chart, which is furnished as part of our annual report to shareholders and not filed, compares the yearly percentage changes in the cumulative shareholder return on our common stock during the five fiscal years ended December 31, 2021, with (i) the Total Return Index for The NASDAQ Stock Market (U.S. Companies) (ii) the Standard and Poor's 500 and (iii) the NASDAQ Bank Index. This comparison assumes $10 …
- [ ] `d1663ec68ce6b81e` — rank 8 · SSB · 10-K · 2020-02-21 · paragraph · Item 5. Market for the Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities.  
      > The following stock performance graph compares South State’s cumulative total shareholder return on our common stock over the most recent five-year period with the NASDAQ Composite and the SNL Southeast Bank Index, a banking industry performance index for the Southeastern United States. The stock performance graph assumes $100 was invested in our commons stock and the above indexes on December 31, 2014. The cumulativ …

---

### `r070` — What were Umpqua's net cash flows from financing activities for the nine months ended September 30, 2022?

**Already labelled** `0497993c455328fe` — UMPQ · 10-Q · 2022-10-31 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended September 30, 2022 and June 30, 2022, where applicable, throughout this Management's Discussion and Analysis.  
> Net cash of $723.0 million provided by financing activities during the nine months ended September 30, 2022, primarily consisted of $750.0 million proceeds from borrowings and $222.4 million net increase in deposit liabilities, partially offset by $136.7 million of dividends paid on common stock and the net decrease in securities sold under agreements to repurchase of $108.7 million. This compares to net cash of $1.4 …

Also answers the question?

- [ ] `02cb12cdb2214a65` — rank 1 · UMPQ · 10-Q · 2022-10-31 · table  
      > UMPQUA HOLDINGS CORPORATION AND SUBSIDIARIES CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS (Continued) (UNAUDITED) Nine Months Ended (in thousands) | September 30, 2022 | September 30, 2021 CASH FLOWS FROM FINANCING ACTIVITIES: Net increase in deposit liabilities | $ | 222437 | $ | 2286225 Net (decrease) increase in securities sold under agreements to repurchase | (108,678) | 92376 Proceeds from borrowings | 750000 …
- [ ] `c0de791ca8cd77ef` — rank 2 · UMPQ · 10-Q · 2021-11-04 · table  
      > UMPQUA HOLDINGS CORPORATION AND SUBSIDIARIES CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS (Continued) (UNAUDITED) Nine Months Ended (in thousands) | September 30, 2021 | September 30, 2020 CASH FLOWS FROM FINANCING ACTIVITIES: Net increase in deposit liabilities | $ | 2286225 | $ | 2288262 Net increase in securities sold under agreements to repurchase | 92376 | 76720 Proceeds from borrowings | — | 600000 Repayment …
- [ ] `dac553a9703f1d60` — rank 3 · UMPQ · 10-Q · 2020-11-05 · table  
      > UMPQUA HOLDINGS CORPORATION AND SUBSIDIARIES CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS (Continued) (UNAUDITED) Nine Months Ended (in thousands) | September 30, 2020 | September 30, 2019 CASH FLOWS FROM FINANCING ACTIVITIES: Net increase in deposit liabilities | $ | 2288262 | $ | 1347046 Net increase in securities sold under agreements to repurchase | 76720 | (434) Proceeds from borrowings | 600000 | 810670 Repa …
- [ ] `fd14baedaf7d1fde` — rank 4 · UMPQ · 10-Q · 2022-10-31 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended September 30, 2022 and June 30, 2022, where applicable, throughout this Management's Discussion and Analysis.  
      > As disclosed in the Condensed Consolidated Statements of Cash Flows, net cash provided by operating activities was $904.7 million during the nine months ended September 30, 2022, with the difference between cash provided by operating activities and net income consisting primarily of proceeds from the sale of loans held for sale of $1.8 billion, the increase in other liabilities of $248.4 million, and the decrease in …
- [ ] `256d8c7ea797a565` — rank 5 · UMPQ · 10-Q · 2022-10-31 · paragraph · Item 303. of Regulation S-K allows registrants to compare the results of the most recently completed quarter to the results of either the immediately preceding quarter or the corresponding quarter of the preceding year. Umpqua has elected to compare our results for the three months ended September 30, 2022 and June 30, 2022, where applicable, throughout this Management's Discussion and Analysis.  
      > Net cash of $2.8 billion used in investing activities during the nine months ended September 30, 2022, consisted principally of net change in loans of $3.1 billion, purchases of available for sale investment securities of $175.7 million and purchases of restricted equity securities of $164.3 million offset by proceeds from available for sale investment securities of $328.7 million, redemption of restricted equity sec …
- [ ] `61252e2c728b951c` — rank 6 · UMPQ · 10-Q · 2022-07-29 · table  
      > UMPQUA HOLDINGS CORPORATION AND SUBSIDIARIES CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS (Continued) (UNAUDITED) Six Months Ended (in thousands) | June 30, 2022 | June 30, 2021 CASH FLOWS FROM FINANCING ACTIVITIES: Net (decrease) increase in deposit liabilities | $ | (462,251) | $ | 1531374 Net increase in securities sold under agreements to repurchase | 35714 | 104918 Repayment of borrowings | — | (660,000) Net …
- [ ] `ea97bf6d6a86be6a` — rank 7 · UMPQ · 10-Q · 2021-08-05 · table  
      > UMPQUA HOLDINGS CORPORATION AND SUBSIDIARIES CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS (Continued) (UNAUDITED) Six Months Ended (in thousands) | June 30, 2021 | June 30, 2020 CASH FLOWS FROM FINANCING ACTIVITIES: Net increase in deposit liabilities | $ | 1531374 | $ | 2363045 Net increase in securities sold under agreements to repurchase | 104918 | 87106 Proceeds from borrowings | — | 600000 Repayment of borrow …
- [ ] `e8be3fb8a7e7b4ae` — rank 8 · UMPQ · 10-Q · 2022-05-05 · table  
      > UMPQUA HOLDINGS CORPORATION AND SUBSIDIARIES CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS (Continued) (UNAUDITED) Three Months Ended (in thousands) | March 31, 2022 | March 31, 2021 CASH FLOWS FROM FINANCING ACTIVITIES: Net increase in deposit liabilities | $ | 104906 | $ | 1264645 Net increase in securities sold under agreements to repurchase | 7292 | 45018 Repayment of borrowings | — | (490,000) Dividends paid o …

---
