import heapq

def edge_key(u, v):
    return (min(u, v), max(u, v))

def build_adjacency(link_bw):
    adj = {}
    for (u, v) in link_bw:
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)
    return adj

def shortest_feasible_path(link_bw, source, target, required_bw):
    """
    Dijkstra with unit hop weight.
    Only physical links whose residual bandwidth is >= required_bw
    are considered. Bandwidth is a feasibility constraint, not the
    shortest-path weight.
    """
    if source == target:
        return [source]

    adj = build_adjacency(link_bw)
    pq = [(0, source, [source])]
    best = {source: 0}

    while pq:
        hops, node, path = heapq.heappop(pq)
        if node == target:
            return path

        for nxt in adj.get(node, []):
            key = edge_key(node, nxt)
            if link_bw.get(key, -1) < required_bw:
                continue
            new_hops = hops + 1
            if new_hops < best.get(nxt, float("inf")):
                best[nxt] = new_hops
                heapq.heappush(pq, (new_hops, nxt, path + [nxt]))

    return None
