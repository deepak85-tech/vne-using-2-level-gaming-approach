import networkx as nx


def rank_physical_nodes(network):
    """
    Rank physical nodes using resource and topology information.

    Factors:
    1. CPU capacity
    2. Node degree
    3. Betweenness centrality
    4. Eigenvector centrality

    Returns:
        List of physical node IDs ordered from highest score
        to lowest score.
    """

    graph = nx.Graph()

    # ---------------------------------------------------------
    # ADD PHYSICAL NODES
    # ---------------------------------------------------------

    for node, cpu in network.nodes.items():
        graph.add_node(
            node,
            cpu=cpu
        )

    # ---------------------------------------------------------
    # ADD PHYSICAL LINKS
    # ---------------------------------------------------------

    for (u, v), bandwidth in network.links.items():
        graph.add_edge(
            u,
            v,
            bandwidth=bandwidth
        )

    # ---------------------------------------------------------
    # TOPOLOGY METRICS
    # ---------------------------------------------------------

    degree = dict(graph.degree())

    betweenness = nx.betweenness_centrality(
        graph,
        normalized=True
    )

    try:
        eigenvector = nx.eigenvector_centrality(
            graph,
            max_iter=1000
        )
    except nx.PowerIterationFailedConvergence:
        eigenvector = {
            node: 0.0
            for node in graph.nodes
        }

    # ---------------------------------------------------------
    # NORMALIZATION FUNCTION
    # ---------------------------------------------------------

    def normalize(values):

        if not values:
            return {}

        minimum = min(values.values())
        maximum = max(values.values())

        if maximum == minimum:
            return {
                node: 1.0
                for node in values
            }

        return {
            node: (
                (value - minimum)
                / (maximum - minimum)
            )
            for node, value in values.items()
        }

    # ---------------------------------------------------------
    # NORMALIZE FACTORS
    # ---------------------------------------------------------

    cpu_score = normalize(network.nodes)
    degree_score = normalize(degree)
    betweenness_score = normalize(betweenness)
    eigenvector_score = normalize(eigenvector)

    # ---------------------------------------------------------
    # COMBINED SCORE
    # ---------------------------------------------------------

    scores = {}

    for node in graph.nodes:

        scores[node] = (
            0.25 * cpu_score[node]
            + 0.25 * degree_score[node]
            + 0.25 * betweenness_score[node]
            + 0.25 * eigenvector_score[node]
        )

    # ---------------------------------------------------------
    # SORT NODES
    # ---------------------------------------------------------

    ranked_nodes = sorted(
        scores,
        key=lambda node: scores[node],
        reverse=True
    )

    return ranked_nodes


def get_top_physical_nodes(
    network,
    max_physical_nodes=10
):
    """
    Return the top-ranked physical nodes.
    """

    ranked_nodes = rank_physical_nodes(network)

    return ranked_nodes[:max_physical_nodes]