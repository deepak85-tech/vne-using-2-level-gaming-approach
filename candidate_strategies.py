from itertools import permutations


def get_candidate_strategies(vnr, physical_nodes):
    """Generate all one-to-one virtual-node to physical-node mappings."""
    virtual_nodes = list(vnr["nodes"].keys())
    physical_nodes = list(physical_nodes)

    if len(virtual_nodes) > len(physical_nodes):
        return []

    strategies = []

    for i, physical_mapping in enumerate(
        permutations(physical_nodes, len(virtual_nodes)),
        start=1
    ):
        mapping = dict(zip(virtual_nodes, physical_mapping))
        strategies.append({
            "name": f"S{i}",
            "mapping": mapping
        })

    return strategies
