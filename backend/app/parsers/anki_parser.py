"""
Anki .apkg Parser
Extracts cards, maps to curriculum topics, prepares for vector store.
"""
import sqlite3
import zipfile
import tempfile
import json
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict
from bs4 import BeautifulSoup


@dataclass
class AnkiCard:
    """Represents a single Anki flashcard."""
    card_id: int
    note_id: int
    deck_name: str
    front: str
    back: str
    tags: List[str]
    interval: int  # Days until next review
    ease_factor: float  # 2.5 = normal, lower = harder
    reviews: int
    lapses: int  # Times forgotten
    last_review: Optional[int]  # Unix timestamp
    
    @property
    def stability(self) -> float:
        """Estimate memory stability in days (for retention prediction)."""
        if self.reviews == 0:
            return 1.0
        return self.interval * (self.ease_factor / 2.5)
    
    @property
    def clean_front(self) -> str:
        """Strip HTML from front."""
        return self._strip_html(self.front)
    
    @property
    def clean_back(self) -> str:
        """Strip HTML from back."""
        return self._strip_html(self.back)
    
    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove HTML tags and clean whitespace."""
        soup = BeautifulSoup(text, "html.parser")
        return " ".join(soup.get_text().split())
    
    def to_embedding_text(self) -> str:
        """Generate text for vector embedding."""
        return f"Question: {self.clean_front}\nAnswer: {self.clean_back}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "card_id": self.card_id,
            "note_id": self.note_id,
            "deck_name": self.deck_name,
            "front": self.clean_front,
            "back": self.clean_back,
            "tags": self.tags,
            "interval": self.interval,
            "ease_factor": self.ease_factor,
            "reviews": self.reviews,
            "lapses": self.lapses,
            "stability": self.stability
        }


class AnkiParser:
    """Parser for Anki .apkg files."""
    
    def __init__(self):
        self.cards: List[AnkiCard] = []
        self.decks: Dict[int, str] = {}
    
    def parse(self, apkg_path: Path) -> List[AnkiCard]:
        """Parse an .apkg file and extract all cards."""
        self.cards = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            with zipfile.ZipFile(apkg_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            
            db_path = tmpdir / "collection.anki2"
            if not db_path.exists():
                db_path = tmpdir / "collection.anki21"
            
            if not db_path.exists():
                raise ValueError(f"No Anki database found in {apkg_path}")
            
            self._parse_database(db_path)
        
        return self.cards
    
    def _parse_database(self, db_path: Path):
        """Parse the SQLite database inside the .apkg."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get deck information
        cursor.execute("SELECT decks FROM col")
        col_row = cursor.fetchone()
        if col_row:
            decks_json = json.loads(col_row["decks"])
            self.decks = {int(k): v["name"] for k, v in decks_json.items()}
        
        # Query cards with note information
        query = """
        SELECT 
            c.id as card_id,
            c.nid as note_id,
            c.did as deck_id,
            c.ivl as interval,
            c.factor as ease_factor,
            c.reps as reviews,
            c.lapses as lapses,
            n.flds as fields,
            n.tags as tags
        FROM cards c
        JOIN notes n ON c.nid = n.id
        """
        
        cursor.execute(query)
        
        for row in cursor.fetchall():
            # Parse fields (separated by \x1f)
            fields = row["fields"].split("\x1f")
            front = fields[0] if len(fields) > 0 else ""
            back = fields[1] if len(fields) > 1 else ""
            
            # Parse tags
            tags = row["tags"].strip().split() if row["tags"] else []
            
            # Get deck name
            deck_name = self.decks.get(row["deck_id"], "Unknown")
            
            # Get last review timestamp
            last_review = None
            try:
                cursor.execute(
                    "SELECT id FROM revlog WHERE cid = ? ORDER BY id DESC LIMIT 1",
                    (row["card_id"],)
                )
                revlog_row = cursor.fetchone()
                if revlog_row:
                    # Anki timestamps are in milliseconds
                    last_review = revlog_row["id"] // 1000
            except Exception:
                pass
            
            card = AnkiCard(
                card_id=row["card_id"],
                note_id=row["note_id"],
                deck_name=deck_name,
                front=front,
                back=back,
                tags=tags,
                interval=row["interval"],
                ease_factor=row["ease_factor"] / 1000,  # Anki stores as integer
                reviews=row["reviews"],
                lapses=row["lapses"],
                last_review=last_review
            )
            
            self.cards.append(card)
        
        conn.close()
    
    def get_cards_by_deck(self, deck_name: str) -> List[AnkiCard]:
        """Filter cards by deck name."""
        return [c for c in self.cards if c.deck_name == deck_name]
    
    def get_cards_by_tag(self, tag: str) -> List[AnkiCard]:
        """Filter cards by tag."""
        return [c for c in self.cards if tag in c.tags]
    
    def get_weak_cards(self, max_ease: float = 2.0, min_lapses: int = 2) -> List[AnkiCard]:
        """Get cards the student struggles with."""
        return [
            c for c in self.cards 
            if c.ease_factor < max_ease or c.lapses >= min_lapses
        ]
    
    def get_deck_statistics(self) -> Dict[str, Dict]:
        """Get statistics per deck."""
        stats = {}
        for card in self.cards:
            if card.deck_name not in stats:
                stats[card.deck_name] = {
                    "total": 0,
                    "reviewed": 0,
                    "avg_ease": 0,
                    "total_lapses": 0
                }
            
            stats[card.deck_name]["total"] += 1
            if card.reviews > 0:
                stats[card.deck_name]["reviewed"] += 1
            stats[card.deck_name]["avg_ease"] += card.ease_factor
            stats[card.deck_name]["total_lapses"] += card.lapses
        
        # Calculate averages
        for deck in stats:
            if stats[deck]["total"] > 0:
                stats[deck]["avg_ease"] /= stats[deck]["total"]
        
        return stats
