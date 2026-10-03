#!/usr/bin/env python3
"""Deterministic guardrail for Vybe Health marketing outputs.

Scans markdown, JSON and HTML marketing files for things that must never ship,
regardless of how good the rest of the work is:

  claims    wording that moves a general-wellness product into medical-device
            territory (diagnose, detect a condition, clinical-grade, cure ...)
  privacy   private contact details (emails, phone numbers) of people who are
            not Vybe, which a targeting list must never hold
  hipaa     "HIPAA-compliant" in consumer copy
  targeting health-interest or sensitive-category ad targeting, which Meta and
            Google prohibit for this kind of advertiser
  partner   wording that implies a partnership that is not signed

Lines that discuss a rule rather than make a claim (for example the Claim
Register saying "never write diagnose") are allowed when they carry one of the
ALLOW_MARKERS. Every finding prints file:line and the rule, and the script
exits 1 if any finding is not allowed, so it can run in CI or before a commit.

Usage: python3 vybe-marketing/evals/check_marketing.py [paths...]
       (defaults to vybe-marketing/, which includes the hub and scoreboard)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = [ROOT / "vybe-marketing"]
SKIP_PARTS = {"evals"}  # the rubric and this checker quote the rules on purpose

RULES = [
    ("claims", re.compile(
        r"\b(diagnos(e|es|is|ing)|cure[sd]?|treat(s|ment)? (of|for)|clinical[- ]grade|"
        r"medical[- ]grade|detects? (afib|atrial fibrillation|arrhythmia|apnea|"
        r"sleep apnea|disease|illness|covid)|fda[- ](approved|cleared) (vybe|band))\b", re.I)),
    ("hipaa", re.compile(r"\bhipaa[- ]compliant\b", re.I)),
    ("targeting", re.compile(
        r"\b(target(ing)?|audience|interest)s?\b[^.\n]{0,40}\b(health condition|"
        r"heart disease|diabetes|depression|anxiety disorder|insomnia sufferers|"
        r"pregnan|sexual orientation|religion)\b", re.I)),
    ("risk-term", re.compile(r"\b(ecg|ekg|heart rhythm|afib|atrial fibrillation|arrhythmia)\b", re.I)),
    ("roadmap", re.compile(
        r"\b(sdk|api|devkit|dev kit|developer api|ring)\b[^.\n]{0,30}\b(is |are )?"
        r"(available now|now available|is live|are live|live now|ships? (today|now)|"
        r"in stock|order (it )?now)\b|"
        r"\b(available now|now available|order now)\b[^.\n]{0,30}\b(sdk|api|devkit|ring)\b", re.I)),
    ("partner", re.compile(
        r"\b(official|exclusive) (wearable|partner|sponsor)\b[^.\n]{0,40}\b(vybe)\b|"
        r"\bvybe\b[^.\n]{0,40}\b(official|exclusive) (wearable|partner|sponsor)\b", re.I)),
]
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE = re.compile(r"(?<!\d)(\+?1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)")
OWN_DOMAINS = ("vybe.health", "example.com", "hydrox.app")  # hydrox: published support address
ALLOW_MARKERS = ("never", "do not", "don't", "avoid", "must not", "not a medical",
                 "outside wellness", "prohibit", "counsel", "unsafe", "banned",
                 "no diagnosis", "never write", "rule", "not available", "never say", "nothing is", "no dates", '"available now"', "'available now'")


def iter_files(paths):
    for p in paths:
        p = Path(p)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.suffix in {".md", ".json", ".html"} and not SKIP_PARTS & set(f.parts):
                    yield f
        elif p.exists():
            yield p


def scan(path):
    findings = []
    para_allowed = False  # a rule stated at the start of a paragraph covers its wrapped lines
    for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        low = line.lower()
        if not line.strip():
            para_allowed = False
        if any(m in low for m in ALLOW_MARKERS):
            para_allowed = True
        allowed = para_allowed
        for name, rx in RULES:
            if rx.search(line):
                findings.append((name, n, line.strip()[:140], allowed))
        for m in EMAIL.finditer(line):
            if not m.group(0).lower().endswith(OWN_DOMAINS):
                findings.append(("privacy", n, m.group(0), False))
        if PHONE.search(line):
            findings.append(("privacy", n, PHONE.search(line).group(0), False))
    return findings


def main(argv):
    paths = argv or DEFAULT
    blocking = 0
    report = []
    for f in iter_files(paths):
        for name, n, text, allowed in scan(f):
            tag = "ok  " if allowed else "FAIL"
            blocking += 0 if allowed else 1
            shown = f.resolve().relative_to(ROOT) if f.resolve().is_relative_to(ROOT) else f.name
            report.append(f"{tag} {name:9} {shown}:{n}  {text}")
    print("\n".join(report) if report else "No findings.")
    print(f"\n{blocking} blocking finding(s).")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
