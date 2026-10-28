import os
import sys

sys.path.append(os.getcwd())

from scripts.backfill_template_index import _index_values, _needs_backfill

TEMPLATE_ID = "6f1c3b0e-1d2a-4c5b-9e8f-0a1b2c3d4e5f"


def _item(**overrides):
    item = {"PK": "form#abc", "SK": "METADATA", "template": TEMPLATE_ID, "created_at": 946407600000}
    item.update(overrides)
    return item


def test_form_from_template_without_index_needs_backfill():
    assert _needs_backfill(_item())
    assert _index_values(_item()) == {
        "GSI4PK": f"template#{TEMPLATE_ID}",
        "GSI4SK": "created_at#0946407600000#abc",
        "template_version": 1,
    }


def test_skips_what_does_not_belong_in_the_index():
    assert not _needs_backfill(_item(GSI4PK="template#x"))
    assert not _needs_backfill(_item(template="TEMPLATE"))
    assert not _needs_backfill(_item(PK="template#abc"))
    assert not _needs_backfill(_item(created_at=None))


def test_keeps_existing_template_version():
    assert "template_version" not in _index_values(_item(template_version=3))
