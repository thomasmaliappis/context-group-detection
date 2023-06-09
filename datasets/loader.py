from collections import Counter

import numpy as np
import pandas as pd


def read_sim(directory, sample_frequency):
    """
    Reads a data.csv file from the given directory and converts it to a dataframe
    :param directory: name of the directory
    :return: dataframe
    """
    df = pd.read_csv(directory + '/data.csv')

    d_frame = np.diff(pd.unique(df["frame_id"]))
    fps = d_frame[0] * 1
    df["timestamp"] = df["frame_id"] / fps

    df['frame_id'] += df['sim'] * sample_frequency

    df.sort_values(by=['agent_id', 'frame_id'], inplace=True)
    df['measurement'] = df[['pos_x', 'pos_y', 'v_x', 'v_y']].apply(tuple, axis=1)

    return df


def read_obsmat(directory):
    """
    Reads an obsmat.txt file from the given directory and converts it to a dataframe
    :param directory: name of the directory
    :return: dataframe
    """
    columns = ['frame_id', 'agent_id', 'pos_x', 'pos_z', 'pos_y', 'v_x', 'v_z', 'v_y']
    df = pd.read_csv(directory + '/obsmat.txt', sep='\s+', names=columns, header=None)
    df.drop(columns=['pos_z', 'v_z'], inplace=True)
    # modify data types
    df["frame_id"] = df["frame_id"].astype(int)
    if str(df["agent_id"].iloc[0]).replace('.', '', 1).isdigit():
        df["agent_id"] = df["agent_id"].astype(int)
    df["pos_x"] = df["pos_x"].astype(float)
    df["pos_y"] = df["pos_y"].astype(float)

    d_frame = np.diff(pd.unique(df["frame_id"]))
    fps = d_frame[0] * 2.5  # 2.5 is the common annotation fps for all (ETH+UCY) datasets
    df["timestamp"] = df["frame_id"] / fps

    df.sort_values(by=['agent_id', 'frame_id'], inplace=True)
    df['measurement'] = df[['pos_x', 'pos_y', 'v_x', 'v_y']].apply(tuple, axis=1)

    return df


def merge_groups_with_common_agents(agents_in_multiple_groups, groups):
    """
    Merge groups with common agents.
    :param agents_in_multiple_groups: list of agents that appear in multiple groups
    :param groups: list of lists representing the agent groups
    :return: list of lists without agents being in multiple groups
    """
    for agent in agents_in_multiple_groups:
        group_indices = []
        for i, group in enumerate(groups):
            if agent in group:
                group_indices.append(i)
        groups_to_be_merged = [groups[i] for i in group_indices]
        merged_group = list(set(agent for group in groups_to_be_merged for agent in group))
        for c, i in enumerate(group_indices):
            groups.pop(i - c)
        groups.append(merged_group)
    return groups


def read_groups(directory):
    """
    Reads a groups.txt file from the given directory and
    converts it to pairs of pedestrians in the same group
    :param directory: name of the directory
    :return: pairs
    """

    with open(directory + '/groups.txt') as f:
        groups = [[int(x) for x in line.split()] for line in f if not line.isspace()]

    # merge groups with common agents
    count_dict = Counter([agent for group in groups for agent in group])
    agents_in_multiple_groups = [key for key, value in count_dict.items() if value > 1]
    if len(agents_in_multiple_groups) > 0:
        groups_with_duplicate_agents_indices = \
            set(i for i, group in enumerate(groups) for agent in agents_in_multiple_groups if agent in group)
        groups_without_duplicate_agents = \
            [group for i, group in enumerate(groups) if i not in groups_with_duplicate_agents_indices]
        groups_with_duplicate_agents = \
            [group for i, group in enumerate(groups) if i in groups_with_duplicate_agents_indices]
        groups = \
            groups_without_duplicate_agents + merge_groups_with_common_agents(agents_in_multiple_groups,
                                                                              groups_with_duplicate_agents)

    return groups


def read_multi_groups(directory):
    """
    Reads a groups.txt file from the given directory and
    converts it to pairs of pedestrians in the same group
    :param directory: name of the directory
    :return: pairs
    """

    groups = []
    scene_groups = []
    with open(directory + '/groups.txt') as f:
        for line in f:
            if not line.isspace():
                if line == '-\n':
                    groups.append(scene_groups)
                    scene_groups = []
                    continue
                scene_groups.append([int(x) for x in line.split()])

    return groups


if __name__ == '__main__':
    dataset_path = './UCY/students03'
    eth_df = read_obsmat(dataset_path)
    eth_groups = read_groups(dataset_path)
