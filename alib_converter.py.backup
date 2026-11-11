import os
import sys
import pickle


def load_alib_pickle(pickle_file, alib_root):
    """
    Load the ALIB scenario pickle.
    """

    if alib_root not in sys.path:
        sys.path.insert(0, alib_root)

    if not os.path.exists(pickle_file):
        raise FileNotFoundError(
            f"Pickle file not found:\n{pickle_file}"
        )

    with open(pickle_file, "rb") as file:
        data = pickle.load(file)

    return data


def get_scenario(data, scenario_index=0):
    """
    Get one scenario from the ALIB ScenarioParameterContainer.
    """

    if not hasattr(data, "scenario_list"):
        raise ValueError(
            "The pickle does not contain scenario_list."
        )

    if scenario_index >= len(data.scenario_list):
        raise IndexError(
            f"Scenario {scenario_index} does not exist. "
            f"Available scenarios: 0 to {len(data.scenario_list) - 1}"
        )

    return data.scenario_list[scenario_index]


def convert_alib_substrate(
    pickle_file,
    alib_root,
    scenario_index=0
):
    """
    Convert an ALIB substrate into the format used
    by PhysicalNetwork.

    Returns:

        nodes = [
            (node_id, cpu_capacity),
            ...
        ]

        links = [
            (node1, node2, bandwidth_capacity),
            ...
        ]
    """

    data = load_alib_pickle(
        pickle_file,
        alib_root
    )

    scenario = get_scenario(
        data,
        scenario_index
    )

    substrate = scenario.substrate

    # ---------------------------------------------------------
    # PHYSICAL NODES
    # ---------------------------------------------------------

    nodes = []

    for node in sorted(
        substrate.nodes,
        key=lambda x: str(x)
    ):

        # The ALIB RedBestel substrate in this scenario
        # uses 100 CPU capacity per physical node.
        cpu_capacity = 1000.0

        nodes.append(
            (str(node), cpu_capacity)
        )

    # ---------------------------------------------------------
    # PHYSICAL LINKS
    # ---------------------------------------------------------

    unique_links = set()

    for u, v in substrate.edges:

        if u == v:
            continue

        link = tuple(
            sorted(
                (str(u), str(v))
            )
        )

        unique_links.add(link)

    links = []

    for u, v in sorted(unique_links):

        # ALIB RedBestel scenario uses
        # 100 bandwidth capacity per physical edge.
        bandwidth = 1000.0

        links.append(
            (u, v, bandwidth)
        )

    return nodes, links

def print_alib_summary(nodes, links):

    print()
    print("=" * 70)
    print("ALIB SUBSTRATE")
    print("=" * 70)

    print(f"Physical nodes : {len(nodes)}")
    print(f"Physical links : {len(links)}")

    print()
    print("First 10 physical nodes:")

    for node in nodes[:10]:
        print(node)

    print()
    print("First 10 physical links:")

    for link in links[:10]:
        print(link)

    print()
    print("=" * 70)


if __name__ == "__main__":

    # ---------------------------------------------------------
    # CHANGE THESE TWO PATHS IF REQUIRED
    # ---------------------------------------------------------

    PICKLE_FILE = r"input\senario_RedBestel.pickle"

    ALIB_ROOT = r"D:\mini project resources\P3_ALIB_MASTER\P3_ALIB_MASTER"

    # Scenario:
    # 0 = scenario_0.0_rep_0
    # 1 = scenario_1.0_rep_0

    SCENARIO_INDEX = 0

    nodes, links = convert_alib_substrate(
        PICKLE_FILE,
        ALIB_ROOT,
        SCENARIO_INDEX
    )

    print_alib_summary(
        nodes,
        links
    )