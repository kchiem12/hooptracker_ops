# results_formatter.py
from ..state import GameState  # Adjust the import according to your project structure

def results(game_state: GameState) -> str:
    """
    Formats the results from a GameState object into a readable string.

    Args:
        game_state (GameState): The game state object containing all game data.

    Returns:
        str: A formatted string of the game results.
    """
    results_str = "Game Statistics:\n"
    
    # Format general game statistics
    results_str += "\nGeneral Game Stats:\n"
    results_str += f"Total Frames: {len(game_state.frames)}\n"
    results_str += f"Number of Possessions: {len(game_state.possessions)}\n"
    results_str += f"Number of Shot Attempts: {len(game_state.shot_attempts)}\n"
    
    # Format player statistics
    results_str += "\nPlayer Stats:\n"
    for player_id, player_state in game_state.players.items():
        results_str += f"Player {player_id}:\n"
        results_str += f"  Total Frames: {player_state.frames}\n"
        results_str += f"  Field Goals Attempted: {player_state.field_goals_attempted}\n"
        results_str += f"  Field Goals Made: {player_state.field_goals}\n"
        results_str += f"  Points Scored: {player_state.points}\n"
        results_str += f"  Field Goal Percentage: {player_state.field_goal_percentage:.2f}\n"
        results_str += f"  Passes Made: {sum(player_state.passes.values())}\n"

    # Format team statistics
    results_str += "\nTeam Stats:\n"
    for team_id, team in [('Team 1', game_state.team1), ('Team 2', game_state.team2)]:
        results_str += f"{team_id}:\n"
        results_str += f"  Shots Attempted: {team.shots_attempted}\n"
        results_str += f"  Shots Made: {team.shots_made}\n"
        results_str += f"  Points: {team.points}\n"
        results_str += f"  Field Goal Percentage: {team.field_goal_percentage:.2f}\n"

    # Format ball statistics
    results_str += "\nBall Stats:\n"
    results_str += f"Ball Frames: {game_state.ball.frames}\n"

    return results_str
