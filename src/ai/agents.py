from autogen import AssistantAgent, UserProxyAgent

from src.handler.game_handler import ResistanceCoupGameHandler
from src.models.action import ActionType
from src.models.card import Card
from src.models.player import PlayerStrategy


def create_user_proxy(config_list: list) -> UserProxyAgent:
    llm_config = {
        "config_list": config_list,
        "temperature": 0,
    }

    user_proxy = UserProxyAgent(
        name="User_Proxy",
        llm_config=llm_config,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        system_message="""
            You are facilitating a game of The Resistance: Coup between five players. 
            Respond with TERMINATE once the game has a winner.
            At the start of the game, you will inform the starting player that it is their turn.
            In between each player's turn you have to retrieve the game state and provide it to the players.
            """,
        code_execution_config=False,
        default_auto_reply="Reply TERMINATE when the initial request has been fulfilled.",
        human_input_mode="NEVER",
        # max_consecutive_auto_reply=10
    )
    return user_proxy


def create_game_master_agent(
    handler: ResistanceCoupGameHandler, config_list: list
) -> AssistantAgent:
    llm_config = {
        "config_list": config_list,
        "temperature": 1,
        "functions": [
            {
                "name": "get_game_state",
                "description": "Get the current state of the game",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        ],
    }

    instructions = f"""
    You are the game master in a game of The Resistance: Coup between {len(handler.players)} players.
    
    At the start of the game, you will inform the starting player that it is their turn and announce to 
    everyone the starting game state.
    
    In between each player's turn you have to retrieve the game state and provide it to the current player.
    
    Make sure the correct player is taking their next turn based on the game state.
    
    Players can counter another player's action if action_can_be_countered is "True" after they 
    tried to perform an action.
    
    Once there is only one active player left in the game, you can declare the game is over and we have a winner.
    Don't start another game after it has ended. Don't offer to the other players to play another game.
    """

    game_master = AssistantAgent(
        name="Game_Master",
        system_message=instructions,
        llm_config=llm_config,
        function_map={
            "get_game_state": handler.get_game_state,
        },
        description="The game master in a game of The Resistance Coup.",
    )
    return game_master


def create_player_agent(
    name: str,
    other_player_names: list[str],
    cards: list[Card],
    strategy: PlayerStrategy,
    handler: ResistanceCoupGameHandler,
    config_list: list,
) -> AssistantAgent:
    llm_config = {
        "config_list": config_list,
        "temperature": 0.5,
        "functions": [
            {
                "name": "perform_action",
                "description": "Perform a valid action for Resistance: Coup",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "player_name": {
                            "type": "string",
                            "description": "Send your own name.",
                            "enum": [name],
                        },
                        "action_name": {
                            "type": "string",
                            "description": "The name of the action to perform.",
                            "enum": [
                                ActionType.income,
                                ActionType.foreign_aid,
                                ActionType.tax,
                                ActionType.coup,
                                ActionType.steal,
                                ActionType.assassinate,
                                ActionType.exchange,
                            ],
                        },
                        "target_player_name": {
                            "type": "string",
                            "description": "The player name to target.",
                        },
                    },
                    "required": ["player_name", "action_name"],
                },
            },
            {
                "name": "counter_action",
                "description": "Counter the previous action that was performed",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "countering_player_name": {
                            "type": "string",
                            "description": "Send your own name.",
                            "enum": [name],
                        },
                    },
                    "required": ["countering_player_name"],
                },
            },
            {
                "name": "challenge_action",
                "description": "Challenge the previous action that was performed by another player "
                "if you think that the player that performed the action does not have the required card.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "challenging_player_name": {
                            "type": "string",
                            "description": "Send your own name.",
                            "enum": [name],
                        },
                    },
                    "required": ["challenging_player_name"],
                },
            },
            {
                "name": "challenge_counter_action",
                "description": "Challenge the previous counter-action that was performed by another player "
                "if you think that the player that performed the counter-action does not "
                "have the required card.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "challenging_player_name": {
                            "type": "string",
                            "description": "Send your own name.",
                            "enum": [name],
                        },
                    },
                    "required": ["challenging_player_name"],
                },
            },
            {
                "name": "execute_action",
                "description": "Execute the action that was performed and complete the turn.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "player_name": {
                            "type": "string",
                            "description": "Send your own name.",
                            "enum": [name],
                        },
                        "action_name": {
                            "type": "string",
                            "description": "The name of the action to perform.",
                            "enum": [
                                ActionType.income,
                                ActionType.foreign_aid,
                                ActionType.tax,
                                ActionType.coup,
                                ActionType.steal,
                                ActionType.assassinate,
                                ActionType.exchange,
                            ],
                        },
                        "target_player_name": {
                            "type": "string",
                            "description": "The player name to target.",
                        },
                    },
                    "required": ["player_name", "action_name"],
                },
            },
        ],
    }

    if strategy == PlayerStrategy.aggressive:
        strategy_str = (
            "Your strategy is to play aggressive. Try to assassinate, coup, or steal as soon as you can. "
            "Don't be scared to bluff to get more coins."
            "If you keep getting blocked, rather get income on your next turn, before playing aggressive again. "
            "Always challenge other players if you don't think they have the card they claim to have."
        )
    elif strategy == PlayerStrategy.conservative:
        strategy_str = (
            "Your strategy is to play conservative. "
            "Build up your money, avoid bluffing, and wait for the opportunity to perform a coup."
            "Don't be too reckless with challenging other players after an action or counteraction, but feel free"
            "to do it if you are pretty sure."
        )
    else:
        strategy_str = (
            "Your strategy is to perform a coup as soon as you have enough coins, otherwise gather money as "
            "fast as possible by taking foreign aid or tax. However be careful not to bluff too much, otherwise "
            "you might lose your cards and be eliminated."
        )

    instructions = f"""Your name is {name} and you are a player in the game The Resistance: Coup. 
        You are playing against {", ".join(other_player_names)}. 
        
        You start with a {str(cards[0])} card and a {str(cards[1])} card, as well as 2 coins.
        
        On your turn you have to pick a valid action based on your current available cards and coins. 
        Also provide your own name to the function. 
        
        Never announce what cards you have, they are secret.
        
        If your action was invalid, you have to pick another action. However feel free to bluff and perform an 
        action even if you don't have the card, but be careful because it could be challenged.
        
        You can counter another player's action if action_can_be_countered is "True", 
        after they tried to perform their action.
        
        Feel free to challenge another player's action if action_can_be_challenged is "True", 
        after they tried to perform their action, and if you think they are bluffing, by using the
        challenge_action function.
        
        Feel free to challenge another player's counter-action if you think they are bluffing, by using the
        challenge_counter_action function.
        
        If no one counters or challenges your action, you have the call "execute_action" to complete the turn. 
        If after perform_action you find that turn_complete is "True", you don't have to execute your action.
                
        You also chit-chat with your opponent when you communicate an action to light up the mood.

        You should ensure both you and your opponents are making valid actions. 
        Also that everyone is only taking actions when it is their turn.
        
        {strategy_str}
        
        Don't hoard up coins, but rather try the assassinate or coup actions when you have a chance. 

        Do not apologize for making invalid actions.
        
        If the game is over, stop playing."""

    player = AssistantAgent(
        name=name,
        system_message=instructions,
        llm_config=llm_config,
        function_map={
            "perform_action": handler.perform_action,
            "counter_action": handler.counter_action,
            "challenge_action": handler.challenge_action,
            "challenge_counter_action": handler.challenge_counter_action,
            "execute_action": handler.execute_action,
        },
        max_consecutive_auto_reply=100,
        description=f"The player named {name} the game of The Resistance Coup",
    )

    return player
