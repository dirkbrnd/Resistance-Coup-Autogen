import sys

from autogen import (
    AssistantAgent,
    GroupChat,
    GroupChatManager,
    UserProxyAgent,
    config_list_from_dotenv,
)

from src.ai.agents import (
    create_game_master_agent,
    create_player_agent,
    create_user_proxy,
)
from src.handler.game_handler import ResistanceCoupGameHandler

config_list = config_list_from_dotenv(
    dotenv_file_path=".env",
    filter_dict={
        "model": {
            "gpt-4",
            # "gpt-3.5-turbo",
        }
    },
)


def main():
    # Create game handler with 3 players
    handler = ResistanceCoupGameHandler(3)
    print(f"First player is {handler.current_player}")

    # Create AI players
    agent_players = []
    for ind, player in enumerate(handler.players):
        agent_players.append(
            create_player_agent(
                name=player.name,
                other_player_names=[
                    other_player.name
                    for other_player in handler.players
                    if other_player.name != player.name
                ],
                cards=player.cards,
                strategy=player.strategy,
                handler=handler,
                config_list=config_list,
            )
        )

    # Game master
    game_master: AssistantAgent = create_game_master_agent(handler, config_list)

    # Game master
    user_proxy: UserProxyAgent = create_user_proxy(config_list)

    # Define group chat
    group_chat = GroupChat(
        agents=[user_proxy, game_master, *agent_players],
        messages=[],
        admin_name=game_master.name,
        max_round=1000,
    )
    manager = GroupChatManager(groupchat=group_chat, llm_config={"config_list": config_list})

    task = """
    Play a game of The Resistance: Coup until there is a single winner.
    """

    game_master.initiate_chat(manager, message=task)
    print("GAME OVER")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("GAME OVER")
        sys.exit(130)
