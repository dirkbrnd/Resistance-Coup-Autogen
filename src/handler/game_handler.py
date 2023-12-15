import random
from enum import Enum
from typing import List, Optional

from src.models.action import Action, ActionType, TaxAction, ForeignAidAction, StealAction, AssassinateAction, \
    ExchangeAction, IncomeAction, CoupAction
from src.models.card import Card, CardType
from src.models.player import Player


class ChallengeResult(Enum):
    no_challenge = 0
    challenge_failed = 1
    challenge_succeeded = 2


ACTIONS_MAP: dict[ActionType, Action] = {
    ActionType.income: IncomeAction(),
    ActionType.foreign_aid: ForeignAidAction(),
    ActionType.coup: CoupAction(),
    ActionType.tax: TaxAction(),
    ActionType.steal: StealAction(),
    ActionType.exchange: ExchangeAction(),
    ActionType.assassinate: AssassinateAction(),
}


def build_deck() -> List[Card]:
    def _create_card(card_type: CardType):
        return Card(
            card_type=card_type,
        )

    return [
        _create_card(CardType.contessa),
        _create_card(CardType.contessa),
        _create_card(CardType.contessa),
        _create_card(CardType.duke),
        _create_card(CardType.duke),
        _create_card(CardType.duke),
        _create_card(CardType.assassin),
        _create_card(CardType.assassin),
        _create_card(CardType.assassin),
        _create_card(CardType.ambassador),
        _create_card(CardType.ambassador),
        _create_card(CardType.ambassador),
        _create_card(CardType.captain),
        _create_card(CardType.captain),
        _create_card(CardType.captain),
    ]


class ResistanceCoupGameHandler:
    _players: dict[str, Player] = {}
    _player_names: list[str] = []
    _current_player_index = 0
    _deck: List[Card] = []
    _number_of_players: int = 0
    _treasury: int = 0

    def __init__(self, number_of_players: int):
        self._number_of_players = number_of_players

        for i in range(number_of_players):
            player_name = f"Player_{str(i + 1)}"
            self._players[player_name] = Player(name=player_name)
            self._player_names.append(player_name)

        self.initialize_game()

    @property
    def number_of_players(self):
        return self._number_of_players

    @property
    def current_player(self) -> Player:
        return self._players[self._player_names[self._current_player_index]]

    @property
    def players(self) -> list[Player]:
        return [player for player in self._players.values()]

    def get_game_state(self) -> dict:
        players_str = ""
        for player_name, player in self._players.items():
            if player.is_active:
                players_str += f" - {player_name} with {len(player.cards)} cards and {player.coins} coins\n"

        return {
            "active_players": [player_name for player_name, player in self._players.items() if player.is_active],
            "treasury_coin": self._treasury,
            "next_player": self.current_player.name
        }

    def get_game_state_str(self) -> str:
        players_str = ""
        for player_name, player in self._players.items():
            if player.is_active:
                players_str += f"  - {player_name} {len(player.cards)} cards | {player.coins} coins\n"

        return f"""
The remaining players are:
{players_str}
The number of coins in the treasury: {self._treasury}
        """

    def _shuffle_deck(self) -> None:
        random.shuffle(self._deck)

    def initialize_game(self) -> None:
        self._deck = build_deck()
        self._shuffle_deck()

        self._treasury = 50

        for player in self._players.values():
            player.reset_player()

            # Deal 2 cards to each player
            player.cards.append(self._deck.pop())
            player.cards.append(self._deck.pop())

            # Gives each player 2 coins
            player.coins = self._take_coin_from_treasury(2)

            # Includes the player in the game
            player.is_active = True

        # Random starting player
        self._current_player_index = random.randint(0, self._number_of_players - 1)

    def _swap_card(self, player: Player, card: Card) -> None:
        self._deck.append(card)
        self._shuffle_deck()
        player.cards.append(self._deck.pop())

    def _take_coin_from_treasury(self, number_of_coins: int) -> int:
        if number_of_coins <= self._treasury:
            self._treasury -= number_of_coins
            return number_of_coins
        else:
            coins = self._treasury
            self._treasury = 0
            return coins

    def _give_coin_to_treasury(self, number_of_coins: int):
        self._treasury += number_of_coins
        return number_of_coins

    def _next_player(self):
        self._current_player_index = (self._current_player_index + 1) % len(self._players)
        while not self.current_player.is_active:
            self._current_player_index = (self._current_player_index + 1) % len(self._players)

    def _deactivate_player(self) -> Optional[Player]:
        for player in self._players.values():
            if not player.cards and player.is_active:
                player.is_active = False
                player.coins -= self._give_coin_to_treasury(player.coins)

                return player
        return None

    def _determine_win_state(self) -> bool:
        return sum(player.is_active for player in self._players.values()) == 1

    def validate_action(self, action: Action, current_player: Player, target_player: Optional[Player]) -> bool:
        if action.action_type in [ActionType.coup, ActionType.steal, ActionType.assassinate] and not target_player:
            return False

        # Can't take coin if the treasury has none

        # You can only do a coup if you have at least 7 coins.
        if action.action_type == ActionType.coup and current_player.coins < 7:
            return False

        # You can only do an assassination if you have at least 3 coins.
        if action.action_type == ActionType.assassinate and current_player.coins < 3:
            return False

        # Can't steal from player with 0 coins
        if action.action_type == ActionType.steal and target_player.coins == 0:
            return False

        return True

    def perform_action(self, player_name: str, action_name: ActionType, target_player_name: Optional[str] = "",
                       countered: bool = False) -> dict:

        action = ACTIONS_MAP[action_name]
        target_player = None
        if target_player_name:
            target_player = self._players[target_player_name]

        if player_name != self.current_player.name:
            raise Exception(f"Wrong player, it is currently {self.current_player.name}'s turn.")

        if not self.validate_action(action, self.current_player, target_player):
            raise Exception("Invalid action")

        result_action_str = ""

        match action.action_type:
            case ActionType.income:
                # Player gets 1 coin
                self.current_player.coins += self._take_coin_from_treasury(1)
                result_action_str = f"{self.current_player}'s coins are increased by 1"
            case ActionType.foreign_aid:
                if not countered:
                    # Player gets 2 coin
                    taken_coin = self._take_coin_from_treasury(2)
                    self.current_player.coins += taken_coin
                    result_action_str = f"{self.current_player}'s coins are increased by {taken_coin}"
            case ActionType.coup:
                # Player pays 7 coin
                self.current_player.coins -= self._give_coin_to_treasury(7)
                result_action_str = f"{self.current_player} pays 7 coins and performs the coup against {target_player}"

                if target_player.cards:
                    # Target player loses influence
                    target_player.remove_card()
            case ActionType.tax:
                # Player gets 3 coins
                taken_coin = self._take_coin_from_treasury(3)
                self.current_player.coins += taken_coin
                result_action_str = f"{self.current_player}'s coins are increased by {taken_coin}"
            case ActionType.assassinate:
                # Player pays 3 coin
                self.current_player.coins -= self._give_coin_to_treasury(3)
                if not countered and target_player.cards:
                    result_action_str = f"{self.current_player} assassinates {target_player}"
                    target_player.remove_card()
            case ActionType.steal:
                if not countered:
                    # Take 2 (or all) coins from a player
                    steal_amount = min(target_player.coins, 2)
                    target_player.coins -= steal_amount
                    self.current_player.coins += steal_amount
                    result_action_str = f"{self.current_player} steals {steal_amount} coins from {target_player}"

            case ActionType.exchange:
                # Get 2 random cards from deck
                # TODO: Make interactive
                cards = [self._deck.pop(), self._deck.pop()]

                self.current_player.cards += cards
                random.shuffle(self.current_player.cards)

                first_card, second_card = self.current_player.cards.pop(), self.current_player.cards.pop()
                self._deck.append(first_card)
                self._deck.append(second_card)

        # Is any player out of the game?
        while player := self._deactivate_player():
            result_action_str += f"\n{player} was defeated! They can no longer play"

        # Have we reached a winner?
        if self._determine_win_state():
            print(f"The game is over! {self.current_player} has won!")
            return {
                "success": True,
                "game_over": True
            }

        # Next player
        self._next_player()

        print(result_action_str + "\n" + self.get_game_state_str())

        return {
            "success": True,
            "next_player": self.current_player.name,
            "game_over": False
        }
