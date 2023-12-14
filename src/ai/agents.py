from autogen import UserProxyAgent, config_list_from_dotenv
from autogen.agentchat.contrib.gpt_assistant_agent import GPTAssistantAgent

from src.handler.game_handler import ResistanceCoupGameHandler
from src.models.action import ActionType
from src.models.card import Card



# SEED = 42

def create_game_master_agent(handler: ResistanceCoupGameHandler, config_list: list) -> UserProxyAgent:
    game_master_llm_config = {
        "config_list": config_list,
        # "seed": SEED,
        "temperature": 0,
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_game_state",
                    "description": "Get the current state of the game",
                    "parameters": {
                        "type": "object",
                        "properties": {
                        },
                    }
                },
            }
        ]
    }

    user_proxy = UserProxyAgent(
        name="GameMaster",
        llm_config=game_master_llm_config,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        system_message="""
            You are facilitating a game of The Resistance: Coup between five players. Respond with TERMINATE once the game has a winner.
            At the start of the game, you will inform the starting player that it is their turn.
            In between each player's turn you have to retrieve the game state and provide it to the players.
            """,
        code_execution_config=False,
        human_input_mode="TERMINATE",
        max_consecutive_auto_reply=10
    )
    user_proxy.register_function(
        function_map={
            "get_game_state": handler.get_game_state,
        }
    )
    return user_proxy


def create_player_agent(name: str, other_player_names: list[str], cards: list[Card],
                        handler: ResistanceCoupGameHandler, config_list: list) -> GPTAssistantAgent:
    player_llm_config = {
        "config_list": config_list,
        # "seed": SEED,
        "temperature": 0,
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "perform_action",
                    "description": "Perform a valid action for Resistance: Coup",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action_name": {
                                "type": "string",
                                "description": "The name of the action to perform.",
                                "enum": [ActionType.income, ActionType.foreign_aid, ActionType.tax, ActionType.coup,
                                         ActionType.steal, ActionType.assassinate, ActionType.exchange]
                            },
                            "target_player_name": {
                                "type": "string",
                                "description": "The name player to target.",
                            },
                        },
                        "required": [
                            "action_name"
                        ]
                    }
                },
            }
        ]
    }


    instructions = f"""Your name is {name} and you are a player in the game The Resistance: Coup. 
        You are playing against {", ".join(other_player_names)}. 
        
        You start with a {str(cards[0])} card and a {str(cards[1])} card, as well as 2 coins.
        
        On your turn you have to pick a valid action based on your current available cards and coins.
        
        If your action was invalid, you have to pick another action.
        
        You also chit-chat with your opponent when you communicate an action to light up the mood.

        You should ensure both you and your opponents are making valid actions. Also that everyone is only taking actions when it is their turn.

        Do not apologize for making invalid actions."""

    player = GPTAssistantAgent(
        name=name,
        instructions=instructions,
        llm_config=player_llm_config,
        function_map={}
    )

    player.register_function(
        function_map={
            "perform_action": handler.perform_action,
        }
    )
    return player
