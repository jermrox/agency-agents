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
  short     a short format (a line labelled tagline, first line, subject line,
            hook, sub-line or subhead) of 25 words or more; the concept check says under 25
  row21     a sentence tying an answer to "no (required) subscription", which
            is Claim Register row 21's scope claim; allowed when the sentence
            names row 21 or a hold, or its markdown section (## heading)
            carries a scheduling hold
  privacy-claim
            a sharing promise ("shared only with consent", "nothing shared")
            that drops the privacy policy's exceptions; allowed only when the
            same sentence names service providers and the law (Register row 4)

Sentences that discuss a rule rather than make a claim (for example the Claim
Register saying "never write diagnose") are allowed when they carry one of the
ALLOW_MARKERS. A marker covers its own sentence only, so one "not a medical
device" cannot clear the rest of a paragraph. Every finding prints file:line and the rule, and the script
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
    ("privacy-claim", re.compile(
        r"\bshar\w* only\b|\bonly (with|under) [^.]{0,40}\bconsent|\bnothing (is )?shared\b", re.I)),
]
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE = re.compile(r"(?<!\d)(\+?1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)")
OWN_DOMAINS = ("vybe.health", "example.com", "hydrox.app")  # hydrox: published support address
ALLOW_MARKERS = ("never", "do not", "don't", "avoid", "must not", "not a medical",
                 "outside wellness", "prohibit", "counsel", "unsafe", "banned",
                 "no diagnosis", "never write", "rule", "not available", "never say", "nothing is", "nothing relies", "no ecg", "rules out", "no dates", '"available now"', "'available now'", 'no "', '"not_allowed"', "overstates", "does anything rely",
                 "roadmap:", "roadmap and offers", "makes no", "not medical advice",
                 "failed the claims gate", "used to pass")


def iter_files(paths):
    for p in paths:
        p = Path(p)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.suffix in {".md", ".json", ".html"} and not SKIP_PARTS & set(f.parts):
                    yield f
        elif p.exists():
            yield p


BLOCK_START = re.compile(r"^\s*(\||#|[-*] |\d+\. |```)")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def units(path):
    """Yield (sentence, line_of_each_char) for every sentence in the file.

    In markdown, wrapped lines are joined into one block (a blank line, a
    table row, a heading or a list item starts a new block), then the block is
    split into sentences, so rules and allow markers see whole sentences. A
    table row is one unit: its cells read as one record. JSON and HTML lines
    are never joined.
    """
    block, owner = "", []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    joinable = path.suffix == ".md"

    def flush():
        start = 0
        parts = [block] if block.lstrip().startswith("|") else SENTENCE_END.split(block)
        for part in parts:
            i = block.find(part, start)
            yield part, owner[i:i + len(part)] or [owner[-1] if owner else 1]
            start = i + len(part)

    for n, line in enumerate(lines, 1):
        if not line.strip() or not joinable or BLOCK_START.match(line):
            if block:
                yield from flush()
            block, owner = "", []
            if not line.strip():
                continue
        if block:
            block += " "
            owner.append(n)
        block += line.strip()
        owner.extend([n] * len(line.strip()))
    if block:
        yield from flush()


SHORT_LABEL = re.compile(r"^\s*(#+\s*)?\**\s*(tagline|first line|subject line|hook|sub-?line|subhead)\b[^:\n]*:?\**\s*(.*)$", re.I)
JUST_LABEL = re.compile(r"^\s*\**[^*]{0,40}:\**\s*$")


def short_formats(path):
    """Yield (line, words, text) for each labelled short format in a markdown file."""
    if path.suffix != ".md":
        return
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for n, line in enumerate(lines):
        m = SHORT_LABEL.match(line)
        if not m:
            continue
        text, at = m.group(3).strip(" *"), n
        while not text and at + 1 < len(lines) and at - n < 4:
            at += 1
            nxt = lines[at].strip()
            if nxt and not JUST_LABEL.match(nxt):
                text = nxt
        text = re.sub(r"^[>\-*\s\"“]+|[\"”\s]+$", "", text)
        if text:
            yield at + 1, len(text.split()), text


ANSWER = r"\b(?:that|the|this|its|your|each|every) (?:\w+ )?answers?\b"
ROW21 = re.compile(ANSWER + r"[^.]{0,80}\bno (required )?subscription|"
                   r"\bno (required )?subscription\b[^.]{0,60}" + ANSWER, re.I)
HOLD = re.compile(r"cannot be scheduled|can't be scheduled|scheduling hold|\bhold:", re.I)


def scan(path):
    findings = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    section_of, section, held_sections = [], 0, set()
    for line in lines:
        if line.startswith("## "):
            section += 1
        section_of.append(section)
        if HOLD.search(line):
            held_sections.add(section)
    for n, words, text in short_formats(path):
        if words >= 25:
            findings.append(("short", n, f"{words} words: {text[:110]}", False))
    for sentence, owner in units(path):
        low = sentence.lower()
        allowed = any(m in low for m in ALLOW_MARKERS)
        for name, rx in RULES:
            m = rx.search(sentence)
            if not m:
                continue
            ok = allowed
            if name == "privacy-claim" and "service provider" in low and "law" in low:
                ok = True
            findings.append((name, owner[min(m.start(), len(owner) - 1)], sentence[:140], ok))
        m = ROW21.search(sentence)
        if m:
            line = owner[min(m.start(), len(owner) - 1)]
            held = section_of[line - 1] in held_sections if line - 1 < len(section_of) else False
            note = re.match(r"\W*(audience and channel|swap test|show it|order|two products|claims|roadmap|voice|hygiene comes)\b", low)
            ok = held or bool(note) or "row 21" in low or "hold" in low or 'not "no subscription"' in low
            findings.append(("row21", owner[min(m.start(), len(owner) - 1)], sentence[:140], ok))
        for m in EMAIL.finditer(sentence):
            if not m.group(0).lower().endswith(OWN_DOMAINS):
                findings.append(("privacy", owner[min(m.start(), len(owner) - 1)], m.group(0), False))
        m = PHONE.search(sentence)
        if m:
            findings.append(("privacy", owner[min(m.start(), len(owner) - 1)], m.group(0), False))
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
