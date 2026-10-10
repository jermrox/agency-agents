# Sweep rules for subagents (from the v2 board brief, 13 SEP 2026)

Hand this file to every sweep subagent. It lives in the repo because scratch space is wiped when
the cloud container restarts. The full brief is summarised at the top of `../SKILL.md`.

## Window
The board shows the last 30 days by `date_published`. A daily sweep looks for items published since
the previous run (the caller gives the dates) that are not already in `research-board/findings.json`.

## Tools
- `mcp__Exa__web_fetch_exa` reads pages and PDFs, including .mil. Check it first: if it returns
  HTTP 402 (out of credits), do not use it and say so.
- `mcp__PubMed__search_articles` (with `date_from`) and `mcp__PubMed__get_article_metadata` read
  paper abstracts. These have worked every day so far.
- `WebSearch` and `mcp__Exa__web_search_exa` for discovery only.
- WebFetch and curl are blocked in the sandbox.

## The document is the item, never the coverage
- Resolve every sighting to its official host by identifier: DoDI/DoWI → esd.whs.mil; Army
  Directive/AR → armypubs.army.mil; MARADMIN/NAVADMIN → marines.mil / mynavyhr.navy.mil;
  DOI/PMID → journal or PubMed; NFPA number → nfpa.org; docket → regulations.gov /
  federalregister.gov; GAO number → gao.gov.
- One item per document. Articles about it go in `coverage_urls` (FireRescue1, Police1, JEMS,
  Firehouse, Fire Engineering, EMS1, Military Times, Task and Purpose). Never make an item from
  an article when a primary document exists.
- **Write the blurb from the primary document you read.** If you cannot read it, there is no
  item — list it under `unverified_leads` instead.
- A change message is the same item as its base; a document that replaces another sets
  `supersedes` to the older `primary_url`.
- Events and program announcements with no underlying document may stand on the official page.
- Official channels, associations and event pages only. No vendors, coaching blogs or
  aggregators. Publicly releasable only: drop anything marked CUI, FOUO or CAC-gated.

## Voice
A well-informed peer, not a journal. Plain-English headline (not the document title). Two to four
sentences: what happened, who it affects, why it matters to a strength coach, PT, athletic
trainer, dietitian, performance psychologist or program leader. Say "reported" once if
unconfirmed. Program and funding items are hiring signals — say so.

## Output
`{"items": [...], "skipped": [{"url","why"}], "coverage_additions": [{"primary_url","coverage_url"}],
"unverified_leads": [{"title","url","why"}]}`. Each item:

```
{"headline", "blurb", "primary_url", "date_published": "YYYY-MM-DD" (from the document),
 "type": "Research"|"Policy"|"News", "sector": "MIL"|"FIRE"|"EMS"|"LE"|"CROSS",
 "tags": 1-3 of the 14 in research-board/tactical_research/models.py TAGS,
 "first_seen": today, "identifier", "coverage_urls": [], "score": 0-10, "supersedes": ""}
```

Validate before finishing:

```
cd research-board && python3 -c "import json,sys;sys.path.insert(0,'.');from tactical_research.models import BoardItem;d=json.load(open('FILE'));print(len(d['items']),[(i['headline'],p) for i in d['items'] for p in BoardItem(**i).validate()])"
```

Then merge with `python3 research-board/merge_items.py FILE ...` (run by the caller).
