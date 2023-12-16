from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from src.models.card import CardType


class ActionType(str, Enum):
    income = "Income"
    foreign_aid = "Foreign Aid"
    coup = "Coup"
    tax = "Tax"
    assassinate = "Assassinate"
    steal = "Steal"
    exchange = "Exchange"


class CounterActionType(str, Enum):
    block_foreign_aid = "Block Foreign Aid"
    block_assassination = "Block Assassination"
    block_steal = "Block Steal"


class Action(BaseModel):
    action_type: ActionType
    associated_card_type: Optional[CardType] = None
    requires_target: bool = False
    can_be_challenged: bool = False
    can_be_countered: bool = False

    def __str__(self):
        return f"{self.action_type.value}"


class IncomeAction(Action):
    action_type: ActionType = ActionType.income


class ForeignAidAction(Action):
    action_type: ActionType = ActionType.foreign_aid
    can_be_countered: bool = True


class CoupAction(Action):
    action_type: ActionType = ActionType.coup
    requires_target: bool = True


class TaxAction(Action):
    action_type: ActionType = ActionType.tax
    associated_card_type: CardType = CardType.duke
    can_be_challenged: bool = True


class AssassinateAction(Action):
    action_type: ActionType = ActionType.assassinate
    associated_card_type: CardType = CardType.assassin
    requires_target: bool = True
    can_be_challenged: bool = True
    can_be_countered: bool = True


class StealAction(Action):
    action_type: ActionType = ActionType.steal
    associated_card_type: CardType = CardType.captain
    requires_target: bool = True
    can_be_challenged: bool = True
    can_be_countered: bool = True


class ExchangeAction(Action):
    action_type: ActionType = ActionType.exchange
    associated_card_type: CardType = CardType.ambassador
    can_be_challenged: bool = True
