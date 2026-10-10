"""Nothing Vybe sends may carry another company's account.

The founder runs more than one company. Until 10 Oct 2026 the booking link in
every drafted opener and follow-up pointed at the other company's Calendly,
because it was hardcoded in two places (params.toml [outreach] calendly and
build.py CALENDLY, used by followup_body). No instruction to the agent could
remove it -- it was compiled into the text -- and it reached about fifty
partner organisations before anyone noticed.

These tests fail the build if that class of mistake comes back. They scan the
source, the config and the generated dashboard for any account that is not
Vybe Health's, so a wrong link cannot reach a draft even if someone edits only
one of the two constants.
"""

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build", ROOT / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

# The only Calendly account Vybe outreach may name. Read from the Vybe Health
# Calendly through Composio (account calendly_saxe-sparm, jeremy@vybe.health);
# "30 Minute Meeting" is its one active event type.
VYBE_CALENDLY = "https://calendly.com/jeremy-vybe/30min"

# Accounts belonging to the founder's other ventures. Spelled in pieces so that
# this file is not itself a copyable source of the wrong strings.
FOREIGN = [
    "jeremylahn" + "-i-grow",
    "i" + "-grow.co",
    "lscops" + ".com",
    "debouillet" + ".com",
]

# Everything an outreach body or the published dashboard is built from.
SCANNED = [
    ROOT / "build.py",
    ROOT / "params.toml",
    ROOT / "template.html",
    ROOT / "data" / "targets.json",
    ROOT / "site" / "index.html",
    ROOT / "site" / "data.json",
]


def _present():
    """Every (file, foreign account) pair found, so a failure names all of them."""
    hits = []
    for path in SCANNED:
        if not path.exists():
            continue
        text = path.read_text(errors="replace")
        for needle in FOREIGN:
            if needle in text:
                hits.append(f"{path.relative_to(ROOT)} contains {needle!r}")
    return hits


def test_no_foreign_account_anywhere():
    assert _present() == []


def test_calendly_constants_are_the_vybe_account():
    # Both constants, because followup_body reads build.CALENDLY while the
    # rest of the pipeline reads the params file: changing one and not the
    # other is how a wrong link survives a fix.
    assert build.CALENDLY == VYBE_CALENDLY
    assert build.load_params()["outreach"]["calendly"] == VYBE_CALENDLY


def test_every_booking_link_in_generated_text_is_the_vybe_one():
    # The dashboard carries the drafted openers and follow-ups verbatim, so it
    # is the closest thing to reading what a partner would receive.
    page = ROOT / "site" / "index.html"
    if not page.exists():
        return  # build.py has not run yet; the constants above still apply
    links = set(re.findall(r"https://calendly\.com/[A-Za-z0-9/_-]+", page.read_text(errors="replace")))
    assert links <= {VYBE_CALENDLY}, f"non-Vybe booking links in the dashboard: {sorted(links - {VYBE_CALENDLY})}"
