# results_formatter.py
import json
from state import GameState  # Assuming GameState class is in state.py
class Format:
    def results():
        return format_results_for_api(GameState)
def format_results_for_api(game_state: GameState) -> str:
    """
    Takes a GameState object and formats the results into a JSON string for API output.
    Args:
        game_state (GameState): The game state object containing all the game data.
    
    Returns:
        str: A JSON string containing the formatted results.
    """
    # Use the methods from GameState to gather statistics
    game_state.populate_team_stats()
    game_state.populate_players_stats()
    
    # Construct the result dictionary
    general_stats = {
        'Number of frames': len(game_state.frames),
        'Duration': game_state.calculate_game_duration(),
        'Highest scoring player': game_state.identify_highest_scoring_player()
    }

    player_stats = {player_id: {
        'Points': player_state.points,
        'Rebounds': 0,  # Assuming you have a method to calculate this
        'Assists': sum(player_state.passes.values())
    } for player_id, player_state in game_state.players.items()}

    team_stats = {
        'Team 1': {
            'Score': game_state.team1.points,
            # 'Possession': game_state.team1.calculate_possession_percentage()  # If you have such a method
        },
        'Team 2': {
            'Score': game_state.team2.points,
            # 'Possession': game_state.team2.calculate_possession_percentage()
        }
    }

    # Combine all the stats into one dictionary
    results = {
        'general_stats': general_stats,
        'player_stats': player_stats,
        'team_stats': team_stats
    }

    # Convert the dictionary into a JSON string
    results_json = json
    return results_json
