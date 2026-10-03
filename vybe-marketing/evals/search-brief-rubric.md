# Search brief rubric

Scores a page brief made with the `vybe-search-content` skill. Six
dimensions, 0 to 3 each. Pass is 14 of 18 or more, with dimensions 2 and 5
at 2 or more, and `check_marketing.py` passing.

| # | Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|---|
| 1 | **Demand evidence** | No numbers | Volumes with no source or date | Volume, KD and source, dated | Volume, KD, CPC, trend and Search Console status, dated, with merged variants not double-counted |
| 2 | **Answer first** *(gate)* | Opens on the product | Answer buried | Answer in the opening paragraph | A plain 40-to-60-word answer with no product mention, usable as an AI Overview |
| 3 | **Searcher fit** | Wrong page type for the intent | Right type, People Also Ask ignored | Right type, most People Also Ask covered | Right type, every People Also Ask covered, and the gap left by the current results named |
| 4 | **Vybe angle** | Absent, or an ad | Hygiene claims only | One unclaimed idea | One section, unclaimed ideas first, shown with a calibrated example labelled as prototype sample data |
| 5 | **Claim and health safety** *(gate)* | A diagnostic threshold, "detects" or medical wording | An unapproved claim | Register claims only | Register claims at the right status, with "designed to" where needed, and a source beside every health statement |
| 6 | **Measurability** | No measure | A target with no date | Target and review date | Current position, target, review date and decision rule |

## Fixed cases

| Case | Prompt |
|---|---|
| S1 | Brief the page for "what is a good hrv". |
| S2 | Brief a fair "whoop vs oura" comparison page. |
| S3 | Brief the "screenless fitness tracker" category page. |
| S4 | Brief a Nourish explainer on meal timing and sleep. |
