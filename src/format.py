#potential way to format the game stats --> need to figure out where
#to retrieve info from

def format_results(self):
        """
        Formats the game statistics into a structured dictionary.
        Returns:
            dict: A dictionary containing structured results.
        """
        self.populate_team_stats()
        self.populate_players_stats()

        general_stats = {
            'Number of frames': len(self.frames),
            'Duration': self.calculate_game_duration(),
            'Highest scoring player': self.identify_highest_scoring_player()
        }

        player_stats = {player_id: {
            'Points': player_state.points,
            'Rebounds': 0, 
            'Assists': sum(player_state.passes.values())
        } for player_id, player_state in self.players.items()}

        team_stats = {
            'Team 1': {
                'Score': self.team1.points,
                'Possession': 0  
            },
            'Team 2': {
                'Score': self.team2.points,
                'Possession': 0   }
        }

        return {
            'general_stats': general_stats,
            'player_stats': player_stats,
            'team_stats': team_stats
        }