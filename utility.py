def calculate_revenue(vnr):
    """Project-level VNR revenue used in the worked example."""
    return sum(vnr["nodes"].values()) + sum(vnr["links"].values())

def calculate_cost(vnr, paths, cpu_price, bw_price):
    cpu_cost = sum(vnr["nodes"].values()) * cpu_price
    bw_cost = 0.0
    for (u, v), required_bw in vnr["links"].items():
        path = paths[(u, v)]
        bw_cost += required_bw * (len(path) - 1) * bw_price
    return cpu_cost + bw_cost, cpu_cost, bw_cost

def calculate_utility(revenue, total_cost):
    return revenue - total_cost
