from nord_ranking import get_top_physical_nodes


def get_candidate_strategies(
    vnr,
    physical_network,
    max_physical_nodes=10,
    max_strategies=200
):
    """
    Generate a bounded set of candidate VNE node mappings.

    The physical nodes are first ranked using the NORD-style
    resource/topology ranking.

    ALIB allowed_nodes restrictions are respected.

    Only node mappings are generated here.
    Virtual-link paths are checked later using Dijkstra.
    """

    # ---------------------------------------------------------
    # GET VIRTUAL NODES
    # ---------------------------------------------------------

    if isinstance(vnr["nodes"], dict):
        virtual_nodes = list(vnr["nodes"].keys())
    else:
        virtual_nodes = [
            vn_id
            for vn_id, _ in vnr["nodes"]
        ]

    if not virtual_nodes:
        return []

    # ---------------------------------------------------------
    # RANK PHYSICAL NODES
    # ---------------------------------------------------------

    ranked_nodes = get_top_physical_nodes(
        physical_network,
        len(physical_network.nodes)
    )

    # ---------------------------------------------------------
    # ALIB ALLOWED-NODE RESTRICTIONS
    # ---------------------------------------------------------

    allowed_nodes = vnr.get("allowed_nodes", {})
    candidate_lists = {}

    for virtual_node in virtual_nodes:

        if allowed_nodes:
            allowed = {
                str(node)
                for node in allowed_nodes.get(
                    virtual_node,
                    []
                )
            }

            candidates = [
                node
                for node in ranked_nodes
                if str(node) in allowed
            ]

        else:
            candidates = list(ranked_nodes)

        # Limit physical nodes considered.
        candidate_count = max(
            max_physical_nodes,
            len(virtual_nodes)
        )

        candidates = candidates[:candidate_count]

        if not candidates:
            return []

        candidate_lists[virtual_node] = candidates

    # ---------------------------------------------------------
    # GENERATE MAPPINGS
    # ---------------------------------------------------------

    strategies = []

    mapping = {}
    used_nodes = set()

    def generate(index):

        if len(strategies) >= max_strategies:
            return

        if index == len(virtual_nodes):

            strategies.append({
                "name": f"S{len(strategies) + 1}",
                "mapping": dict(mapping)
            })

            return

        virtual_node = virtual_nodes[index]

        for physical_node in candidate_lists[virtual_node]:

            if len(strategies) >= max_strategies:
                return

            # VNE node mapping is one-to-one.
            if physical_node in used_nodes:
                continue

            mapping[virtual_node] = physical_node
            used_nodes.add(physical_node)

            generate(index + 1)

            used_nodes.remove(physical_node)
            del mapping[virtual_node]

    generate(0)

    return strategies