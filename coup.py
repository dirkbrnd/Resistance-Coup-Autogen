import sys

from autogen import GroupChat, GroupChatManager, UserProxyAgent, config_list_from_dotenv

from src.ai.agents import create_player_agent, create_game_master_agent
from src.handler.game_handler import ResistanceCoupGameHandler

# SEED = 42
config_list = config_list_from_dotenv(
                    dotenv_file_path='.env',
                    filter_dict={
                                  "model": {
                                      # "gpt-4",
                                      "gpt-3.5-turbo",
                                  }
                              }
                    )

base_llm_config = {
    "config_list": config_list,
    # "seed": SEED,
}


def main():
    # Create game handler with 5 players
    handler = ResistanceCoupGameHandler(5)
    print(f"First player is {handler.current_player}")

    # Create AI players
    agent_players = []
    for ind, player in enumerate(handler.players):
        agent_players.append(create_player_agent(player.name, [other_player.name for other_player in handler.players if other_player.name != player.name], player.cards, handler, config_list))

    # Game master
    game_master: UserProxyAgent = create_game_master_agent(handler, config_list)

    # Define group chat
    group_chat = GroupChat(agents=[game_master] + agent_players, messages=[])
    manager = GroupChatManager(groupchat=group_chat, llm_config=base_llm_config)

    task = """
    Play a game of The Resistance: Coup until there is a single winner.
    """

    game_master.initiate_chat(manager, message=task)
    # handler.perform_action(ActionType.income)
    print("GAME OVER")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("GAME OVER")
        sys.exit(130)
