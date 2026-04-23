"""Tests for classify.py — Nest file track classifier."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from classify import classify


# ── Journal ──────────────────────────────────────────────────────────────────

def test_journal_date_md():
    assert classify("2026-04-22.md") == "journal"

def test_journal_not_matching_non_date():
    assert classify("2026-04-22-notes.md") != "journal"


# ── Legal ─────────────────────────────────────────────────────────────────────

def test_legal_earnings_statement():
    assert classify("Earnings_Statement_Apr_24_2025_109065965_decrypted.pdf") == "legal"

def test_legal_bankruptcy():
    assert classify("DebtorCC-Receipt-2381170.pdf") == "legal"

def test_legal_loa():
    assert classify("2026-02-10_TJ_LOA_Extension_Approved.pdf") == "legal"

def test_legal_adobe_scan():
    assert classify("Adobe Scan Mar 11, 2026.pdf") == "legal"


# ── Handoffs ──────────────────────────────────────────────────────────────────

def test_handoff_session():
    assert classify("SESSION_HANDOFF_20260422_hanuman_f.md") == "handoffs"

def test_handoff_master():
    assert classify("master_handoff_april.md") == "handoffs"


# ── Narrative ─────────────────────────────────────────────────────────────────

def test_narrative_regarding_jane():
    assert classify("regarding jane - part 4.md") == "narrative"

def test_narrative_chapter():
    assert classify("chapter_12_draft.md") == "narrative"

def test_narrative_dispatch():
    assert classify("dispatch_003.md") == "narrative"


# ── Specs ─────────────────────────────────────────────────────────────────────

def test_specs_architecture():
    assert classify("willow_architecture_v2.md") == "specs"

def test_specs_working_paper():
    assert classify("working_paper_13.md") == "specs"

def test_specs_utety():
    assert classify("utety_world_bible.md") == "specs"


# ── Photos ────────────────────────────────────────────────────────────────────

def test_photos_camera_timestamp():
    assert classify("20260228_175540.jpg") == "photos_camera"

def test_photos_personal_feeld():
    assert classify("feeld_match_20260101.jpg") == "photos_personal"

def test_photos_screenshot_reddit():
    assert classify("reddit_post_screenshot.png") == "screenshots"

def test_photos_untagged_png_defaults_screenshots():
    assert classify("random_image.png") == "screenshots"


# ── Unknown ───────────────────────────────────────────────────────────────────

def test_unknown_returns_none():
    assert classify("some_random_file_xyz.pdf") is None

def test_unknown_binary():
    assert classify("data.bin") is None


# ── Priority: legal beats narrative ──────────────────────────────────────────

def test_legal_beats_narrative():
    # "return to work" is legal; also contains common words
    assert classify("return to work chapter summary.pdf") == "legal"
