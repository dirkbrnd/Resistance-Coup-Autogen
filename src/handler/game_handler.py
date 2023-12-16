import random
from enum import Enum
from typing import List, Optional

from src.models.action import (
    Action,
    ActionType,
    AssassinateAction,
    CoupAction,
    ExchangeAction,
    ForeignAidAction,
    IncomeAction,
    StealAction,
    TaxAction,
)
from src.models.card import Card, CardType
from src.models.player import Player, PlayerStrategy


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

    _deck: List[Card] = []
    _treasury: int = 0

    # Turn state
    _current_player_index = 0
    _current_action: Optional[Action]
    _current_action_is_countered: bool = False
    _current_action_is_challenged: bool = False
    _current_action_target_player_name: Optional[str]
    _current_counter_action_player_name: Optional[str]

    def __init__(self, number_of_players: int):
        strategies = [PlayerStrategy.conservative, PlayerStrategy.aggressive, PlayerStrategy.coup_freak]
        for i in range(number_of_players):
            player_name = f"Player_{str(i + 1)}"
            strategy = strategies[i % number_of_players]
            self._players[player_name] = Player(name=player_name, strategy=strategy)
            self._player_names.append(player_name)

        self.initialize_game()

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
                players_str += (
                    f" - {player_name} with {len(player.cards)} cards and {player.coins} coins\n"
                )

        return {
            "active_players": [
                {"name": player_name, "coins": player.coins, "cards": len(player.cards)}
                for player_name, player in self._players.items()
                if player.is_active
            ],
            "treasury_coin": self._treasury,
            "next_player": self.current_player.name,
        }

    def get_game_state_str(self) -> str:
        players_str = ""
        for player_name, player in self._players.items():
            if player.is_active:
                players_str += (
                    f"  - {player_name} [{player.strategy.value}] "
                    f"{len(player.cards)} cards | "
                    f"{player.coins} coins\n"
                )

        return f"""
The remaining players are:
{players_str}
The number of coins in the treasury: {self._treasury}
        """

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
        self._current_player_index = random.randint(0, len(self._players) - 1)

    def _shuffle_deck(self) -> None:
        random.shuffle(self._deck)

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

    def _validate_action(
        self, action: Action, current_player: Player, target_player: Optional[Player]
    ):
        if current_player.coins >= 10 and action.action_type != ActionType.coup:
            raise Exception(
                f"Invalid action: You have 10 or more coins and have to perform "
                f"{ActionType.coup.value} action."
            )

        if (
            action.action_type in [ActionType.coup, ActionType.steal, ActionType.assassinate]
            and not target_player
        ):
            raise Exception(
                f"Invalid action: You need a `target_player` for the action {action.action_type.value}"
            )

        # Can't take coin if the treasury has none
        if (
            action.action_type in [ActionType.income, ActionType.foreign_aid, ActionType.tax]
            and self._treasury == 0
        ):
            raise Exception("Invalid action: The treasury has no coin to give")

        # You can only do a coup if you have at least 7 coins.
        if action.action_type == ActionType.coup and current_player.coins < 7:
            raise Exception(
                f"Invalid action: You need more coins to be able to perform the "
                f"{ActionType.coup.value} action."
            )

        # You can only do an assassination if you have at least 3 coins.
        if action.action_type == ActionType.assassinate and current_player.coins < 3:
            raise Exception(
                f"Invalid action: You need more coins to be able to perform the "
                f"{ActionType.assassinate.value} action."
            )

        # Can't steal from player with 0 coins
        if action.action_type == ActionType.steal and target_player.coins == 0:
            raise Exception("Invalid action: You cannot steal from a player with no coins.")

        return True

    def _challenge_against_player_failed(
        self, player_being_challenged: Player, card: Card, challenger: Player
    ):
        # Player being challenged reveals the card
        print(f"{player_being_challenged} reveals their {card} card!")
        print(f"{challenger} loses the challenge")

        # Challenge player loses influence (chooses a card to remove)
        challenger.remove_card()

        # Player puts card into the deck and gets a new card
        print(f"{player_being_challenged} gets a new card")
        self._swap_card(player_being_challenged, card)

    def _challenge_against_player_succeeded(self, player_being_challenged: Player):
        print(f"{player_being_challenged} bluffed! They do not have the required card!")

        # Player being challenged loses influence (chooses a card to remove)
        player_being_challenged.remove_card()

    def _end_turn(self):
        print(self.get_game_state_str())

        # Is any player out of the game?
        while player := self._deactivate_player():
            print(f"{player} was defeated! They can no longer play")

        # Have we reached a winner?
        if self._determine_win_state():
            print("\n" + f"The game is over! {self.current_player} has won!")
            return {"turn_complete": True, "game_over": True}

        # Next player
        self._next_player()

        return {
            "turn_complete": True,
            "action_can_be_countered": False,
            "action_can_be_challenged": False,
            "next_player": self.current_player.name,
            "game_over": False,
        }

    def perform_action(
        self, player_name: str, action_name: ActionType, target_player_name: Optional[str] = ""
    ) -> dict:
        if self._determine_win_state():
            raise Exception(
                f"You can't play anymore, the game has already ended. {self.current_player} won already."
            )

        # Reset current action
        self._current_action = None
        self._current_action_target_player_name = None
        self._current_counter_action_player_name = None
        self._current_action_is_countered = False
        self._current_action_is_challenged = False

        action = ACTIONS_MAP[action_name]
        target_player = None
        if target_player_name:
            target_player = self._players[target_player_name]

        if not self._players[player_name].is_active:
            raise Exception(
                f"You have been defeated and can't play anymore! "
                f"It is currently {self.current_player.name}'s turn."
            )

        if player_name != self.current_player.name:
            raise Exception(f"Wrong player, it is currently {self.current_player.name}'s turn.")

        self._validate_action(action, self.current_player, target_player)

        # Keep track of the currently played action
        self._current_action = action
        self._current_action_target_player_name = target_player_name

        if action.can_be_countered or action.can_be_challenged:
            return {"turn_complete": False,
                    "action_can_be_countered": action.can_be_countered,
                    "action_can_be_challenged": action.can_be_challenged,
                    "game_over": False}
        else:
            return self.execute_action(
                self.current_player.name, action.action_type, target_player_name
            )

    def counter_action(self, countering_player_name: str):
        countering_player = self._players[countering_player_name]
        if not countering_player.is_active:
            raise Exception(f"You have been eliminated {countering_player_name}! You cannot counter.")

        self._current_action_is_countered = True
        self._current_counter_action_player_name = countering_player_name

        print(
            f"{countering_player} is countering the previous action: {self._current_action.action_type.value}"
        )

        return {
            "turn_complete": False,
            "action_can_be_countered": False,
            "action_can_be_challenged": self._current_action.can_be_challenged,
            "game_over": False,
        }

    def challenge_action(self, challenging_player_name: str):
        challenger = self._players[challenging_player_name]
        if not challenger.is_active:
            raise Exception(f"You have been eliminated {challenging_player_name}! You cannot challenge.")

        self._current_action_is_challenged = True

        print(
            f"{challenger} is challenging the previous action: {self._current_action.action_type.value}."
        )
        # Player being challenged has the card
        if card := self.current_player.find_card(
                self._current_action.associated_card_type
        ):
            self._challenge_against_player_failed(
                player_being_challenged=self.current_player,
                card=card,
                challenger=challenger,
            )
            # Go ahead with action execution
            return self.execute_action(
                player_name=self.current_player.name,
                action_name=self._current_action.action_type,
                target_player_name=self._current_action_target_player_name,
            )
        else:
            # Player being challenged bluffed
            self._challenge_against_player_succeeded(self.current_player)
            # Immediately end the turn
            return self._end_turn()

    def challenge_counter_action(self, challenging_player_name: str):
        challenger = self._players[challenging_player_name]
        if not challenger.is_active:
            raise Exception(f"You have been eliminated {challenging_player_name}! You cannot challenge.")

        print(
            f"{challenger} is challenging the previous counter action."
        )
        countering_player = self._players[self._current_counter_action_player_name]

        # Player being challenged has the card
        if card := self.current_player.find_card(
                self._current_action.associated_card_type
        ):
            self._challenge_against_player_failed(
                player_being_challenged=countering_player,
                card=card,
                challenger=challenger,
            )
        else:
            # Player being challenged bluffed (counter doesn't happen)
            self._current_action_is_countered = False
            self._challenge_against_player_succeeded(countering_player)

        # Go ahead with action and counter execution
        return self.execute_action(
            player_name=self.current_player.name,
            action_name=self._current_action.action_type,
            target_player_name=self._current_action_target_player_name,
        )

    def execute_action(
        self, player_name: str, action_name: ActionType, target_player_name: Optional[str] = ""
    ) -> dict:
        result_action_str = ""

        action = ACTIONS_MAP[action_name]
        target_player = None
        if target_player_name:
            target_player = self._players[target_player_name]

        if player_name != self.current_player.name:
            raise Exception(f"Wrong player, it is currently {self.current_player.name}'s turn.")

        match action.action_type:
            case ActionType.income:
                # Player gets 1 coin
                self.current_player.coins += self._take_coin_from_treasury(1)
                result_action_str = f"{self.current_player}'s coins are increased by 1"
            case ActionType.foreign_aid:
                if not self._current_action_is_countered:
                    # Player gets 2 coin
                    taken_coin = self._take_coin_from_treasury(2)
                    self.current_player.coins += taken_coin
                    result_action_str = (
                        f"{self.current_player}'s coins are increased by {taken_coin}"
                    )
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
                if not self._current_action_is_countered and target_player.cards:
                    result_action_str = f"{self.current_player} assassinates {target_player}"
                    target_player.remove_card()
            case ActionType.steal:
                if not self._current_action_is_countered:
                    # Take 2 (or all) coins from a player
                    steal_amount = min(target_player.coins, 2)
                    target_player.coins -= steal_amount
                    self.current_player.coins += steal_amount
                    result_action_str = (
                        f"{self.current_player} steals {steal_amount} coins from {target_player}"
                    )

            case ActionType.exchange:
                # Get 2 random cards from deck
                # TODO: Make interactive
                cards = [self._deck.pop(), self._deck.pop()]

                self.current_player.cards += cards
                random.shuffle(self.current_player.cards)

                first_card, second_card = (
                    self.current_player.cards.pop(),
                    self.current_player.cards.pop(),
                )
                self._deck.append(first_card)
                self._deck.append(second_card)

        print(result_action_str)

        return self._end_turn()
