import random
from abc import ABC
from typing import List, Optional

from pydantic import BaseModel

from src.models.card import Card, CardType


class Player(BaseModel, ABC):
    name: str
    coins: int = 0
    cards: List[Card] = []
    is_active: bool = False

    def __str__(self):
        return f"{self.name}"

    def reset_player(self):
        self.coins = 0
        self.cards = []

    def find_card(self, card_type: CardType) -> Optional[Card]:
        for ind, card in enumerate(self.cards):
            if card.card_type == card_type:
                return self.cards.pop(ind)

        return None

    def remove_card(self) -> None:
        """Remove a random card"""
        # Remove a random card
        self.cards.pop(random.randrange(len(self.cards)))
