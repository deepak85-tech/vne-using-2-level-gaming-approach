import sys
import networkx as nx

from alib_converter import (
    load_alib_pickle,
    get_scenario
)


# ==========================================================
# CHECK WHETHER A VNR IS CONNECTED
# ==========================================================

def is_connected_vnr(vnr):
    """
    Check whether the VNR is a connected virtual network.

    A valid VNR must:
    1. Have at least 2 virtual nodes.
    2. Have at least 1 virtual link.
    3. All virtual nodes must belong to one connected graph.
    """

    nodes = vnr.get(
        "nodes",
        {}
    )

    links = vnr.get(
        "links",
        {}
    )

    # ------------------------------------------------------
    # Need at least 2 virtual nodes
    # ------------------------------------------------------

    if len(nodes) < 2:
        return False

    # ------------------------------------------------------
    # Need at least 1 virtual link
    # ------------------------------------------------------

    if len(links) == 0:
        return False

    # ------------------------------------------------------
    # Build VNR graph
    # ------------------------------------------------------

    graph = nx.Graph()

    # Add all virtual nodes
    for node in nodes:
        graph.add_node(node)

    # Add all virtual links
    for (u, v) in links:
        graph.add_edge(
            u,
            v
        )

    # ------------------------------------------------------
    # Check connectivity
    # ------------------------------------------------------

    return nx.is_connected(graph)


# ==========================================================
# CONVERT ALIB REQUESTS
# ==========================================================

def convert_alib_requests(
    pickle_file,
    alib_root,
    scenario_index=0
):
    """
    Convert the requests already present in
    the ALIB scenario into the project's VNR format.

    Only CONNECTED VNRs are returned.
    """

    data = load_alib_pickle(
        pickle_file,
        alib_root
    )

    scenario = get_scenario(
        data,
        scenario_index
    )

    vnrs = []

    rejected_count = 0

    for request in scenario.requests:

        # --------------------------------------------------
        # Virtual nodes
        # --------------------------------------------------

        nodes = {}

        allowed_nodes = {}

        for node_id, attributes in (
            request.node.items()
        ):

            virtual_node = int(
                node_id
            )

            nodes[
                virtual_node
            ] = attributes[
                "demand"
            ]

            allowed_nodes[
                virtual_node
            ] = [
                str(node)
                for node in attributes.get(
                    "allowed_nodes",
                    []
                )
            ]

        # --------------------------------------------------
        # Virtual links
        # --------------------------------------------------

        links = {}

        for (
            u,
            v
        ), attributes in request.edge.items():

            u = int(u)
            v = int(v)

            key = tuple(
                sorted(
                    (u, v)
                )
            )

            if key not in links:

                links[
                    key
                ] = attributes[
                    "demand"
                ]

        # --------------------------------------------------
        # Create VNR
        # --------------------------------------------------

        vnr = {

            "id":
                request.name,

            "nodes":
                nodes,

            "links":
                links,

            "allowed_nodes":
                allowed_nodes
        }

        # --------------------------------------------------
        # Connectivity check
        # --------------------------------------------------

        if is_connected_vnr(vnr):

            vnrs.append(
                vnr
            )

        else:

            rejected_count += 1

            print(
                f"Rejected ALIB VNR "
                f"{request.name}: "
                f"VNR is disconnected "
                f"or has no virtual links."
            )

    print()
    print(
        "ALIB REQUEST CONVERSION"
    )
    print(
        f"Valid connected VNRs : "
        f"{len(vnrs)}"
    )
    print(
        f"Rejected VNRs         : "
        f"{rejected_count}"
    )

    return vnrs


# ==========================================================
# GENERATE RANDOM ALIB REQUESTS
# ==========================================================

def generate_random_alib_requests(
    pickle_file,
    alib_root,
    number_of_requests=50,
    scenario_index=0
):
    """
    Generate random ALIB VNRs.

    IMPORTANT:
    Only connected VNRs are returned.

    If ALIB generates a VNR with:
        - zero links
        - disconnected nodes

    it is rejected and another request is generated.

    The function continues until the requested number
    of VALID connected VNRs is obtained.
    """

    if number_of_requests <= 0:

        raise ValueError(
            "number_of_requests "
            "must be greater than 0."
        )

    # ------------------------------------------------------
    # Make ALIB available
    # ------------------------------------------------------

    if alib_root not in sys.path:

        sys.path.insert(
            0,
            alib_root
        )

    # ------------------------------------------------------
    # Import ALIB generator
    # ------------------------------------------------------

    from alib.scenariogeneration import (
        UniformRequestGenerator
    )

    # ------------------------------------------------------
    # Load ALIB scenario
    # ------------------------------------------------------

    data = load_alib_pickle(
        pickle_file,
        alib_root
    )

    scenario = get_scenario(
        data,
        scenario_index
    )

    substrate = scenario.substrate

    # ------------------------------------------------------
    # Storage
    # ------------------------------------------------------

    valid_vnrs = []

    total_generated = 0

    total_rejected = 0

    # ------------------------------------------------------
    # Generate until enough VALID VNRs
    # ------------------------------------------------------

    while len(valid_vnrs) < number_of_requests:

        remaining = (
            number_of_requests
            - len(valid_vnrs)
        )

        # Generate extra requests because
        # some may be rejected.

        batch_size = max(
            remaining * 2,
            10
        )

        parameters = {

            "number_of_requests":
                batch_size,

            "min_number_of_nodes":
                2,

            "max_number_of_nodes":
                8,

            "probability":
                0.2,

            "variability":
                0.3,

            "node_resource_factor":
                0.3,

            "edge_resource_factor":
                10.0,

            "normalize":
                True
        }

        generator = (
            UniformRequestGenerator()
        )

        requests = (
            generator.generate_request_list(

                parameters,

                substrate,

                normalize=True
            )
        )

        # --------------------------------------------------
        # Process generated requests
        # --------------------------------------------------

        for request in requests:

            total_generated += 1

            # ==============================================
            # VIRTUAL NODES
            # ==============================================

            nodes = {}

            allowed_nodes = {}

            for (
                node_id,
                attributes
            ) in request.node.items():

                virtual_node = int(
                    node_id
                )

                nodes[
                    virtual_node
                ] = attributes[
                    "demand"
                ]

                allowed_nodes[
                    virtual_node
                ] = [

                    str(node)

                    for node in attributes.get(
                        "allowed_nodes",
                        []
                    )
                ]

            # ==============================================
            # VIRTUAL LINKS
            # ==============================================

            links = {}

            for (
                u,
                v
            ), attributes in request.edge.items():

                u = int(u)

                v = int(v)

                key = tuple(
                    sorted(
                        (u, v)
                    )
                )

                if key not in links:

                    links[
                        key
                    ] = attributes[
                        "demand"
                    ]

            # ==============================================
            # CREATE VNR
            # ==============================================

            vnr = {

                "id":
                    request.name,

                "nodes":
                    nodes,

                "links":
                    links,

                "allowed_nodes":
                    allowed_nodes
            }

            # ==============================================
            # CONNECTIVITY CHECK
            # ==============================================

            if is_connected_vnr(vnr):

                valid_vnrs.append(
                    vnr
                )

                print(
                    f"Accepted VNR "
                    f"{request.name} "
                    f"| Nodes: "
                    f"{len(nodes)} "
                    f"| Links: "
                    f"{len(links)}"
                )

            else:

                total_rejected += 1

                print(
                    f"Rejected VNR "
                    f"{request.name} "
                    f"| Nodes: "
                    f"{len(nodes)} "
                    f"| Links: "
                    f"{len(links)} "
                    f"| Reason: "
                    f"Disconnected VNR"
                )

            # ==============================================
            # Stop once enough valid VNRs
            # ==============================================

            if len(valid_vnrs) >= (
                number_of_requests
            ):

                break

        # --------------------------------------------------
        # Progress
        # --------------------------------------------------

        print(
            f"Progress: "
            f"{len(valid_vnrs)}/"
            f"{number_of_requests} "
            f"valid connected VNRs"
        )

    # ------------------------------------------------------
    # Final result
    # ------------------------------------------------------

    valid_vnrs = valid_vnrs[
        :number_of_requests
    ]

    print()
    print("=" * 70)
    print("VNR GENERATION COMPLETE")
    print("=" * 70)

    print(
        f"Requested VNRs       : "
        f"{number_of_requests}"
    )

    print(
        f"Generated VNRs       : "
        f"{total_generated}"
    )

    print(
        f"Rejected VNRs        : "
        f"{total_rejected}"
    )

    print(
        f"Valid connected VNRs : "
        f"{len(valid_vnrs)}"
    )

    print("=" * 70)

    return valid_vnrs


# ==========================================================
# OPTIONAL VALIDATION OF ALL VNRs
# ==========================================================

def validate_vnrs(vnrs):
    """
    Final safety check.

    Returns only connected VNRs.
    """

    valid_vnrs = []

    for vnr in vnrs:

        if is_connected_vnr(vnr):

            valid_vnrs.append(
                vnr
            )

        else:

            print(
                f"Rejected VNR "
                f"{vnr.get('id', 'UNKNOWN')}: "
                f"not connected."
            )

    return valid_vnrs


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    PICKLE_FILE = (
        r"D:\minwith log"
        r"\input"
        r"\senario_RedBestel.pickle"
    )

    ALIB_ROOT = (
        r"D:\mini project resources"
        r"\P3_ALIB_MASTER"
        r"\P3_ALIB_MASTER"
    )

    vnrs = generate_random_alib_requests(

        pickle_file=
            PICKLE_FILE,

        alib_root=
            ALIB_ROOT,

        number_of_requests=
            5,

        scenario_index=
            0
    )

    print()
    print("=" * 70)
    print("FINAL GENERATED VNR DETAILS")
    print("=" * 70)

    for vnr in vnrs:

        cpu = sum(
            vnr["nodes"].values()
        )

        bw = sum(
            vnr["links"].values()
        )

        print(
            f"{vnr['id']} | "
            f"Nodes: {len(vnr['nodes'])} | "
            f"CPU: {cpu:.2f} | "
            f"Links: {len(vnr['links'])} | "
            f"BW: {bw:.2f}"
        )