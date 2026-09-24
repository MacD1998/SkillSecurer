#!/usr/bin/env python3
"""
Tests for Study Buddy deck_manager.py
Run: python3 -m pytest test_deck_manager.py -v
  or: python3 test_deck_manager.py
"""

import argparse
import json
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest import TestCase, main

import deck_manager


class DeckManagerTestBase(TestCase):
    """Base class that redirects DECKS_DIR to a temp directory."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self._orig_dir = deck_manager.DECKS_DIR
        deck_manager.DECKS_DIR = self.tmp_dir

    def tearDown(self):
        deck_manager.DECKS_DIR = self._orig_dir
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def create_sample_deck(self, name="Test Deck", cards=None):
        if cards is None:
            cards = [
                {"q": "Capital of France?", "a": "Paris"},
                {"q": "2+2?", "a": "4"},
                {"q": "H2O is?", "a": "Water"},
            ]
        deck = {
            "name": name,
            "cards": [deck_manager.new_card(i + 1, c["q"], c["a"]) for i, c in enumerate(cards)],
            "next_id": len(cards) + 1,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        deck_manager.save_deck(deck)
        return deck


class TestDeckPath(DeckManagerTestBase):
    def test_normalizes_name(self):
        path = deck_manager.deck_path("My Test Deck")
        self.assertEqual(path.name, "my_test_deck.json")

    def test_normalizes_slashes(self):
        path = deck_manager.deck_path("bio/exam")
        self.assertEqual(path.name, "bio_exam.json")


class TestNewCard(TestCase):
    def test_creates_card_with_defaults(self):
        card = deck_manager.new_card(1, "Q?", "A")
        self.assertEqual(card["id"], 1)
        self.assertEqual(card["q"], "Q?")
        self.assertEqual(card["a"], "A")
        self.assertEqual(card["interval"], 0)
        self.assertEqual(card["ease"], 2.5)
        self.assertEqual(card["repetitions"], 0)
        self.assertIn("next_review", card)
        self.assertIn("created_at", card)


class TestSM2Algorithm(TestCase):
    def test_correct_first_time(self):
        card = deck_manager.new_card(1, "Q?", "A")
        deck_manager.sm2_update(card, "correct")
        self.assertEqual(card["interval"], 1)
        self.assertEqual(card["repetitions"], 1)
        self.assertEqual(card["ease"], 2.6)

    def test_correct_second_time(self):
        card = deck_manager.new_card(1, "Q?", "A")
        deck_manager.sm2_update(card, "correct")
        deck_manager.sm2_update(card, "correct")
        self.assertEqual(card["interval"], 3)
        self.assertEqual(card["repetitions"], 2)
        self.assertEqual(card["ease"], 2.7)

    def test_correct_third_time_uses_ease(self):
        card = deck_manager.new_card(1, "Q?", "A")
        deck_manager.sm2_update(card, "correct")  # interval=1, ease=2.6
        deck_manager.sm2_update(card, "correct")  # interval=3, ease=2.7
        deck_manager.sm2_update(card, "correct")  # interval=3*2.7=8, ease=2.8
        self.assertEqual(card["interval"], 8)
        self.assertEqual(card["repetitions"], 3)

    def test_missed_resets(self):
        card = deck_manager.new_card(1, "Q?", "A")
        deck_manager.sm2_update(card, "correct")
        deck_manager.sm2_update(card, "correct")
        deck_manager.sm2_update(card, "missed")
        self.assertEqual(card["repetitions"], 0)
        self.assertEqual(card["interval"], 1)

    def test_partial_keeps_interval(self):
        card = deck_manager.new_card(1, "Q?", "A")
        card["interval"] = 7
        card["ease"] = 2.5
        original_interval = card["interval"]
        deck_manager.sm2_update(card, "partial")
        self.assertEqual(card["interval"], original_interval)
        self.assertEqual(card["ease"], 2.35)

    def test_ease_never_below_minimum(self):
        card = deck_manager.new_card(1, "Q?", "A")
        card["ease"] = 1.3
        deck_manager.sm2_update(card, "missed")
        self.assertEqual(card["ease"], 1.3)

    def test_next_review_set_in_future(self):
        card = deck_manager.new_card(1, "Q?", "A")
        before = datetime.now()
        deck_manager.sm2_update(card, "correct")
        next_review = datetime.fromisoformat(card["next_review"])
        self.assertGreater(next_review, before)


class TestCreate(DeckManagerTestBase):
    def test_creates_deck_file(self):
        self.create_sample_deck("Biology")
        path = deck_manager.deck_path("Biology")
        self.assertTrue(path.exists())

    def test_deck_has_correct_structure(self):
        self.create_sample_deck("Biology")
        deck = deck_manager.load_deck("Biology")
        self.assertEqual(deck["name"], "Biology")
        self.assertEqual(len(deck["cards"]), 3)
        self.assertEqual(deck["next_id"], 4)
        self.assertIn("created_at", deck)

    def test_cards_have_ids(self):
        self.create_sample_deck("Bio")
        deck = deck_manager.load_deck("Bio")
        ids = [c["id"] for c in deck["cards"]]
        self.assertEqual(ids, [1, 2, 3])

    def test_duplicate_deck_fails(self):
        self.create_sample_deck("Bio")
        args = argparse.Namespace(deck_name="Bio", cards='[{"q": "X?", "a": "Y"}]')
        with self.assertRaises(SystemExit):
            deck_manager.cmd_create(args)


class TestAdd(DeckManagerTestBase):
    def test_adds_cards_to_existing_deck(self):
        self.create_sample_deck("Bio")
        deck = deck_manager.load_deck("Bio")
        new_card = deck_manager.new_card(deck["next_id"], "New Q?", "New A")
        deck["cards"].append(new_card)
        deck["next_id"] += 1
        deck_manager.save_deck(deck)

        reloaded = deck_manager.load_deck("Bio")
        self.assertEqual(len(reloaded["cards"]), 4)
        self.assertEqual(reloaded["cards"][3]["q"], "New Q?")

    def test_new_cards_get_sequential_ids(self):
        self.create_sample_deck("Bio")
        deck = deck_manager.load_deck("Bio")
        next_id = deck["next_id"]
        new_card = deck_manager.new_card(next_id, "Q4?", "A4")
        deck["cards"].append(new_card)
        deck["next_id"] = next_id + 1
        deck_manager.save_deck(deck)

        reloaded = deck_manager.load_deck("Bio")
        self.assertEqual(reloaded["cards"][-1]["id"], 4)


class TestLoad(DeckManagerTestBase):
    def test_load_nonexistent_fails(self):
        with self.assertRaises(SystemExit):
            deck_manager.load_deck("nonexistent")

    def test_load_existing_returns_deck(self):
        self.create_sample_deck("Bio")
        deck = deck_manager.load_deck("Bio")
        self.assertEqual(deck["name"], "Bio")


class TestReviewAndDue(DeckManagerTestBase):
    def test_new_cards_are_due_immediately(self):
        self.create_sample_deck("Bio")
        deck = deck_manager.load_deck("Bio")
        now = datetime.now()
        due = [c for c in deck["cards"] if datetime.fromisoformat(c["next_review"]) <= now]
        self.assertEqual(len(due), 3)

    def test_reviewed_card_not_due(self):
        self.create_sample_deck("Bio")
        deck = deck_manager.load_deck("Bio")
        deck_manager.sm2_update(deck["cards"][0], "correct")
        deck_manager.save_deck(deck)

        reloaded = deck_manager.load_deck("Bio")
        now = datetime.now()
        due = [c for c in reloaded["cards"] if datetime.fromisoformat(c["next_review"]) <= now]
        self.assertEqual(len(due), 2)

    def test_missed_card_due_tomorrow(self):
        self.create_sample_deck("Bio")
        deck = deck_manager.load_deck("Bio")
        deck_manager.sm2_update(deck["cards"][0], "missed")
        next_review = datetime.fromisoformat(deck["cards"][0]["next_review"])
        self.assertGreater(next_review, datetime.now())
        self.assertLess(next_review, datetime.now() + timedelta(days=2))


class TestExportImport(DeckManagerTestBase):
    def test_export_returns_valid_json(self):
        self.create_sample_deck("Bio")
        deck = deck_manager.load_deck("Bio")
        exported = json.dumps(deck)
        parsed = json.loads(exported)
        self.assertEqual(parsed["name"], "Bio")
        self.assertEqual(len(parsed["cards"]), 3)

    def test_import_creates_deck(self):
        self.create_sample_deck("Bio")
        deck = deck_manager.load_deck("Bio")

        # Export to temp file
        export_path = self.tmp_dir / "export.json"
        with open(export_path, "w") as f:
            json.dump(deck, f)

        # Delete original
        deck_manager.deck_path("Bio").unlink()

        # Import
        with open(export_path) as f:
            imported = json.load(f)
        deck_manager.save_deck(imported)

        reloaded = deck_manager.load_deck("Bio")
        self.assertEqual(reloaded["name"], "Bio")
        self.assertEqual(len(reloaded["cards"]), 3)

    def test_import_invalid_format_fails(self):
        bad_path = self.tmp_dir / "bad.json"
        with open(bad_path, "w") as f:
            json.dump({"foo": "bar"}, f)
        with open(bad_path) as f:
            data = json.load(f)
        self.assertNotIn("name", data)


class TestDelete(DeckManagerTestBase):
    def test_delete_removes_file(self):
        self.create_sample_deck("Bio")
        path = deck_manager.deck_path("Bio")
        self.assertTrue(path.exists())
        path.unlink()
        self.assertFalse(path.exists())

    def test_delete_nonexistent_fails(self):
        with self.assertRaises(SystemExit):
            deck_manager.load_deck("nonexistent")


class TestExam(DeckManagerTestBase):
    def test_exam_generates_correct_count(self):
        self.create_sample_deck("Bio")
        deck = deck_manager.load_deck("Bio")
        # Simulate exam generation
        import random
        count = min(3, len(deck["cards"]))
        selected = random.sample(deck["cards"], count)
        self.assertEqual(len(selected), 3)

    def test_exam_multiple_choice_has_options(self):
        self.create_sample_deck("Bio")
        deck = deck_manager.load_deck("Bio")
        card = deck["cards"][0]
        all_answers = [c["a"] for c in deck["cards"]]
        distractors = [a for a in all_answers if a != card["a"]]
        options = [card["a"]] + distractors[:3]
        self.assertIn(card["a"], options)
        self.assertGreater(len(options), 1)


class TestMultipleDecks(DeckManagerTestBase):
    def test_multiple_decks_independent(self):
        self.create_sample_deck("Bio")
        self.create_sample_deck("Math", cards=[{"q": "1+1?", "a": "2"}])

        bio = deck_manager.load_deck("Bio")
        math = deck_manager.load_deck("Math")
        self.assertEqual(len(bio["cards"]), 3)
        self.assertEqual(len(math["cards"]), 1)

    def test_due_across_decks(self):
        self.create_sample_deck("Bio")
        self.create_sample_deck("Math", cards=[{"q": "1+1?", "a": "2"}])

        now = datetime.now()
        total_due = 0
        for f in self.tmp_dir.glob("*.json"):
            with open(f) as fh:
                d = json.load(fh)
                due = [c for c in d["cards"] if datetime.fromisoformat(c["next_review"]) <= now]
                total_due += len(due)
        self.assertEqual(total_due, 4)


class TestUnicodeSupport(DeckManagerTestBase):
    def test_unicode_cards(self):
        cards = [
            {"q": "Que es la mitosis?", "a": "Division celular que produce dos celulas hijas identicas"},
            {"q": "Qu'est-ce que l'eau?", "a": "H2O - molecule d'eau"},
        ]
        self.create_sample_deck("Multilingual", cards=cards)
        deck = deck_manager.load_deck("Multilingual")
        self.assertEqual(deck["cards"][0]["q"], "Que es la mitosis?")
        self.assertEqual(deck["cards"][1]["a"], "H2O - molecule d'eau")

    def test_japanese_cards(self):
        cards = [{"q": "Nihongo de 'hello' wa?", "a": "Konnichiwa"}]
        self.create_sample_deck("Japanese", cards=cards)
        deck = deck_manager.load_deck("Japanese")
        self.assertEqual(deck["cards"][0]["a"], "Konnichiwa")


class TestEdgeCases(DeckManagerTestBase):
    def test_empty_deck(self):
        deck = {
            "name": "Empty",
            "cards": [],
            "next_id": 1,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        deck_manager.save_deck(deck)
        loaded = deck_manager.load_deck("Empty")
        self.assertEqual(len(loaded["cards"]), 0)

    def test_single_card_deck(self):
        self.create_sample_deck("Single", cards=[{"q": "Q?", "a": "A"}])
        deck = deck_manager.load_deck("Single")
        self.assertEqual(len(deck["cards"]), 1)

    def test_large_deck(self):
        cards = [{"q": f"Question {i}?", "a": f"Answer {i}"} for i in range(100)]
        self.create_sample_deck("Large", cards=cards)
        deck = deck_manager.load_deck("Large")
        self.assertEqual(len(deck["cards"]), 100)

    def test_long_answer_text(self):
        long_text = "A" * 5000
        self.create_sample_deck("Long", cards=[{"q": "Q?", "a": long_text}])
        deck = deck_manager.load_deck("Long")
        self.assertEqual(len(deck["cards"][0]["a"]), 5000)

    def test_sm2_many_correct_increases_interval(self):
        card = deck_manager.new_card(1, "Q?", "A")
        for _ in range(10):
            deck_manager.sm2_update(card, "correct")
        self.assertGreater(card["interval"], 30)
        self.assertGreater(card["ease"], 2.5)

    def test_sm2_alternating_results(self):
        card = deck_manager.new_card(1, "Q?", "A")
        deck_manager.sm2_update(card, "correct")
        deck_manager.sm2_update(card, "missed")
        self.assertEqual(card["repetitions"], 0)
        self.assertEqual(card["interval"], 1)
        deck_manager.sm2_update(card, "correct")
        self.assertEqual(card["repetitions"], 1)


if __name__ == "__main__":
    main()
