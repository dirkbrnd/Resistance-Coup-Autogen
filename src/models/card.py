from enum import Enum

from pydantic import BaseModel


class CardType(str, Enum):
    contessa = "Contessa"
    duke = "Duke"
    assassin = "Assassin"
    captain = "Captain"
    ambassador = "Ambassador"


class Card(BaseModel):
    card_type: CardType

    def __str__(self):
        return f"{self.card_type.value}"
