from state import GameState
import numpy as np
from sklearn.cluster import SpectralClustering

"""
Team Detection

This module contains functions that will find the best team split. 
"""


def passing_matrix(state: GameState, p_list: list):
    "computes passing matrix of a state"
    n = len(p_list)
    graph = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            graph[i][j] = state.passes[p_list[i]][p_list[j]]
    graph = graph + graph.T  # directed -> undirected
    return graph


def sparest_cut_weighted(graph):
    "get sparest cut given pass frequency matrix"
    # Perform spectral clustering
    clustering = SpectralClustering(
        n_clusters=2, affinity="precomputed", random_state=0, eigen_solver="arpack"
    )
    labels = clustering.fit_predict(graph)

    # Calculate sparsity cut for weighted graph
    cut_size = np.sum(graph[labels == 0][:, labels == 1])
    sparsity = cut_size / min(np.sum(labels == 0), np.sum(labels == 1))

    return labels, sparsity


def split_team(state: GameState):
    "splits players into two teams"
    n = len(state.players)
    p_list = list(state.players.keys())

    graph = passing_matrix(state, p_list)
    labels, _ = sparest_cut_weighted(graph)
    assert len(labels) == n

    state.team1.players.clear()
    state.team2.players.clear()
    for i in range(n):
        if labels[i] == 0:
            state.team1.players.add(p_list[i])
        else:  # label[i] == 1
            state.team2.players.add(p_list[i])
