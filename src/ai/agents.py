from autogen import UserProxyAgent, AssistantAgent
from autogen.agentchat.contrib.gpt_assistant_agent import GPTAssistantAgent

from src.handler.game_handler import ResistanceCoupGameHandler
from src.models.action import ActionType
from src.models.card import Card



# SEED = 42

def create_user_proxy(config_list: list) -> UserProxyAgent:
    llm_config = {
        "config_list": config_list,
        # "seed": SEED,
        "temperature": 0,
    }

    user_proxy = UserProxyAgent(
        name="User_Proxy",
        llm_config=llm_config,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        system_message="""
            You are facilitating a game of The Resistance: Coup between five players. Respond with TERMINATE once the game has a winner.
            At the start of the game, you will inform the starting player that it is their turn.
            In between each player's turn you have to retrieve the game state and provide it to the players.
            """,
        code_execution_config=False,
        default_auto_reply="Reply TERMINATE when the initial request has been fulfilled.",
        human_input_mode="NEVER",
        # max_consecutive_auto_reply=10
    )
    return user_proxy


def create_game_master_agent(handler: ResistanceCoupGameHandler, config_list: list) -> AssistantAgent:
    llm_config = {
        "config_list": config_list,
        # "seed": SEED,
        "temperature": 1,
        "functions": [
            {
                "name": "get_game_state",
                "description": "Get the current state of the game",
                "parameters": {
                    "type": "object",
                    "properties": {
                    },
                }
            },
        ]
    }

    instructions = f"""
    You are the game master in a game of The Resistance: Coup between {handler.number_of_players} players.
    
    At the start of the game, you will inform the starting player that it is their turn and announce to everyone the starting game state.
    
    In between each player's turn you have to retrieve the game state and provide it to the current player.
    
    Make sure the correct player is taking their next turn based on the game state.
    
    Once there is only one active player left in the game, you can declare the game is over and we have a winner.
    """

    game_master = AssistantAgent(
        name="Game_Master",
        system_message=instructions,
        llm_config=llm_config,
        function_map={
            "get_game_state": handler.get_game_state,
        },
        # max_consecutive_auto_reply=100,
        description="The game master in a game of The Resistance Coup"
    )
    return game_master


def create_player_agent(name: str, other_player_names: list[str], cards: list[Card],
                        handler: ResistanceCoupGameHandler, config_list: list) -> AssistantAgent:
    llm_config = {
        "config_list": config_list,
        # "seed": SEED,
        "temperature": 0.3,
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
                            "enum": [name]
                        },
                        "action_name": {
                            "type": "string",
                            "description": "The name of the action to perform.",
                            "enum": [ActionType.income, ActionType.foreign_aid, ActionType.tax, ActionType.coup,
                                     ActionType.steal, ActionType.assassinate, ActionType.exchange]
                        },
                        "target_player_name": {
                            "type": "string",
                            "description": "The player name to target.",
                        },
                    },
                    "required": [
                        "player_name",
                        "action_name"
                    ]
                }
            }
        ]
    }


    instructions = f"""Your name is {name} and you are a player in the game The Resistance: Coup. 
        You are playing against {", ".join(other_player_names)}. 
        
        You start with a {str(cards[0])} card and a {str(cards[1])} card, as well as 2 coins.
        
        On your turn you have to pick a valid action based on your current available cards and coins. Also provide your own name to the function. 
        
        Never announce what cards you have, they are secret.
        
        If your action was invalid, you have to pick another action. However feel free to bluff and perform an action even if you don't have the card.
        
        The possible actions are {[ActionType.income, ActionType.foreign_aid, ActionType.tax, ActionType.coup, ActionType.steal, ActionType.assassinate, ActionType.exchange]}
        
        You also chit-chat with your opponent when you communicate an action to light up the mood.

        You should ensure both you and your opponents are making valid actions. Also that everyone is only taking actions when it is their turn.

        Do not apologize for making invalid actions.
        
        If the game is over, stop playing."""

    player = AssistantAgent(
        name=name,
        system_message=instructions,
        llm_config=llm_config,
        function_map={
            "perform_action": handler.perform_action,
        },
        max_consecutive_auto_reply=100,
        description=f"The player named {name} the game of The Resistance Coup"
    )

    return player
