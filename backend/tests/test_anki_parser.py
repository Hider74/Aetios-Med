import pytest
from app.parsers.anki_parser import AnkiParser, AnkiCard

def test_anki_card_stability():
    card = AnkiCard(1, 1, "Test", "Q", "A", [], 10, 2.5, 5, 0, None)
    assert card.stability == 10.0

def test_anki_parser_init():
    parser = AnkiParser()
    assert parser.cards == []
