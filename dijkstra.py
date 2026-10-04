import heapq


def edge_key(u, v):
    return tuple(sorted((u, v)))


def build_adjacency(link_bw):

    adjacency = {}

    for u, v in link_bw:

        adjacency.setdefault(
            u, []
        ).append(v)

        adjacency.setdefault(
            v, []
        ).append(u)

    return adjacency


def shortest_feasible_path(
    link_bw,
    source,
    target,
    required_bw
):
    """
    Find the shortest-hop physical path.

    Only physical links having enough residual
    bandwidth are considered.
    """

    if source == target:
        return [source]

    adjacency = build_adjacency(link_bw)

    queue = [
        (0, source, [source])
    ]

    best_hops = {
        source: 0
    }

    while queue:

        hops, current, path = heapq.heappop(queue)

        if current == target:
            return path

        for nxt in adjacency.get(
            current,
            []
        ):

            key = edge_key(
                current,
                nxt
            )

            residual_bw = link_bw.get(
                key,
                -1
            )

            if residual_bw < required_bw:
                continue

            new_hops = hops + 1

            if new_hops < best_hops.get(
                nxt,
                float("inf")
            ):

                best_hops[nxt] = new_hops

                heapq.heappush(
                    queue,
                    (
                        new_hops,
                        nxt,
                        path + [nxt]
                    )
                )

    return None