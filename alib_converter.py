
import os
import sys
import pickle
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
PICKLE_FILE = PROJECT_DIR / "input" / "senario_RedBestel.pickle"
ALIB_ROOT = Path.home() / "alib-py3"


def load_alib_pickle(pickle_file=PICKLE_FILE, alib_root=ALIB_ROOT):
    """Load the ALIB scenario pickle."""

    alib_root = str(alib_root)
    pickle_file = Path(pickle_file)

    if alib_root not in sys.path:
        sys.path.insert(0, alib_root)

    if not pickle_file.exists():
        raise FileNotFoundError(
            f"Pickle file not found: {pickle_file}"
        )

    with open(pickle_file, "rb") as file:
        data = pickle.load(file)

    return data


def get_scenario(data, scenario_index=0):
    """Get one scenario from the ALIB ScenarioParameterContainer."""

    if not hasattr(data, "scenario_list"):
        raise ValueError("The pickle does not contain scenario_list.")

    if scenario_index >= len(data.scenario_list):
        raise IndexError(
            f"Scenario {scenario_index} does not exist. "
            f"Available scenarios: 0 to {len(data.scenario_list) - 1}"
        )

    return data.scenario_list[scenario_index]


def convert_alib_substrate(
    pickle_file=PICKLE_FILE,
    alib_root=ALIB_ROOT,
    scenario_index=0
):
    data = load_alib_pickle(pickle_file, alib_root)
    scenario = get_scenario(data, scenario_index)
    substrate = scenario.substrate

    # Physical nodes
    nodes = []

    for node in sorted(substrate.nodes, key=lambda x: str(x)):
        cpu_capacity = 290.0
        nodes.append((str(node), cpu_capacity))

    # Physical links
    unique_links = set()

    for u, v in substrate.edges:
        if u == v:
            continue

        link = tuple(sorted((str(u), str(v))))
        unique_links.add(link)

    links = []

    for u, v in sorted(unique_links):
        bandwidth = 180.0
        links.append((u, v, bandwidth))

    return nodes, links


def print_alib_summary(nodes, links):
    print()
    print("=" * 70)
    print("ALIB SUBSTRATE")
    print(f"Physical nodes: {len(nodes)}")
    print(f"Physical links: {len(links)}")

    print("\nFirst 10 physical nodes:")
    for node in nodes[:10]:
        print(node)

    print("\nFirst 10 physical links:")
    for link in links[:10]:
        print(link)

    print("=" * 70)


if __name__ == "__main__":
    nodes, links = convert_alib_substrate()
    print_alib_summary(nodes, links)
