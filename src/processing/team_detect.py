from typing import Tuple
from state import GameState

"""
Team Detection and Possession Finder

This module contains functions that will find the best team split. It will
also create a list of players in the order of ball possession.
"""


# def connections(pos_lst, players):
#     """
#     Input:
#         pos_lst [list]: list of player ids in the order of ball possession
#                         throughout the video
#         players [list]: list of player ids
#     Output:
#         connects [dict]: dictionary of connections between players
#     """
#     connects = {}
#     for i, player in enumerate(players):
#         for j, player2 in enumerate(players):
#             if i == j:
#                 continue
#             name = player + player2
#             connects.update({name: 0})

#     curr = pos_lst[0]
#     for i in range(1, len(pos_lst)):
#         name = curr + pos_lst[i]
#         connects[name] += 1
#     return connects


def connections(pos_lst, players, player_idx):
    """
    Input:
        pos_lst [list]: list of player ids in the order of ball possession
                        throughout the video
        players [list]: list of player ids
        player_idx [dict]: dictionary of player ids to their index in the
                            players list
    Output:
        connects [list of lists]: 2D array of connections between players where
                                    connects[i][j] is the number of times
                                    player i passes to player j
    """
    connects = [[0 for _ in range(len(players))] for _ in range(len(players))]
    for i in range(0, len(pos_lst) - 1):
        connects[player_idx.get(pos_lst[i][0])][player_idx.get(pos_lst[i + 1][0])] += 1
    return connects


def possible_teams(players):
    """
    Input:
        players [list]: list of player ids
    Output:
        acc [list]: list of possible team splits
    """
    num_people = len(players)

    acc = []

    def permutation(i, t):
        if i >= num_people:
            return
        if len(t) == ppl_per_team:
            acc.append((t, (set(players) - set(t))))
        else:
            permutation(i + 1, t.copy())
            t.add(players[i])
            permutation(i + 1, t.copy())

    if num_people % 2 != 0:
        ppl_per_team = int(num_people / 2) + 1
        permutation(0, set())
        ppl_per_team -= 1
        permutation(0, set())
    else:
        ppl_per_team = int(num_people / 2)
        permutation(0, set())
    return acc


def team_split(state: GameState):
    """
    Input:
        state: a StatState class that holds all sorts of information
                on the video
    Output:
        best_team [tuple]: tuple of two sets of player ids that are the best
                            team split
        pos_lst [list[tuple]]: list of player ids in the order of ball
                                possession with start and finish frames
    """
    player_list = state.players.keys()
    pos_lst = possession_list(state.frames, player_list, thresh=11)
    player_idx = {player: i for i, player in enumerate(player_list)}
    connects = connections(pos_lst, player_list, player_idx)
    teams = possible_teams(player_list)
    best_team = None
    min_count = 100000
    for team in teams:
        count = 0
        team1 = list(team[0])
        team2 = list(team[1])
        for player1 in team1:
            for player2 in team2:
                count += connects[player_idx.get(player1)][player_idx.get(player2)]
                count += connects[player_idx.get(player2)][player_idx.get(player1)]
        if count < min_count:
            min_count = count
            best_team = team
    return best_team, pos_lst, player_list


def compute_possession(player_pos, team1) -> Tuple[float, float]:
    """
    Input: player possession, list of players on team 1
    Computes and returns team1 possession, team2 possession.
    """
    # total frames of each team's possession
    team1_pos = 0
    team2_pos = 0
    for player, pos in player_pos.items():
        for intervals in pos:
            pos_time = intervals[1] - intervals[0]
            if player in team1:
                team1_pos += pos_time
            else:
                team2_pos += pos_time
    total_pos = team1_pos + team2_pos

    return team1_pos / total_pos, team2_pos / total_pos
