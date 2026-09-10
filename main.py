import time
from physical_network import PhysicalNetwork
from vnr_data import get_vnrs
from game import LowerLevelGame
from differential_evolution import DifferentialEvolution
from excel_writer import write_results

CPU_PRICE = 1
BW_PRICE = 0.7

def path_hops(path):
    return max(0, len(path) - 1)

def run_lower_level(cpu_price, bw_price):
    network = PhysicalNetwork.from_default()
    vnrs = get_vnrs()

    start = time.perf_counter()
    game = LowerLevelGame(network, cpu_price, bw_price)
    result = game.play(vnrs)
    elapsed_ms = (time.perf_counter() - start) * 1000

    total_revenue = sum(r["Revenue"] for r in result["accepted"])
    total_cost = sum(r["Cost"] for r in result["accepted"])
    accepted_count = sum(r["Accepted"] == "YES" for r in result["accepted"])
    total_requests = len(vnrs)

    pre_cpu = sum(network.nodes.values())
    post_cpu = sum(result["resources"]["cpu"].values())
    consumed_cpu = pre_cpu - post_cpu

    pre_bw = sum(network.links.values())
    post_bw = sum(result["resources"]["bw"].values())
    consumed_bw = pre_bw - post_bw

    # Metrics are based on the accepted embeddings.
    all_paths = []
    requested_bw = []
    for row in result["accepted"]:
        if row["Accepted"] != "YES":
            continue
        # Read path lengths from the string representation.
        for item in row["Paths"].split(" | "):
            if ":" in item:
                _, p = item.split(":", 1)
                all_paths.append(max(0, len(p.split("->")) - 1))

    for vnr in vnrs:
        requested_bw.extend(vnr["links"].values())

    avg_bw = sum(requested_bw) / len(requested_bw)
    avg_crb = consumed_cpu / pre_cpu * 100
    avg_link = consumed_bw / pre_bw * 100
    unique_links = set()
    unique_nodes = set()
    node_counts = []
    for row in result["accepted"]:
        if row["Accepted"] != "YES":
            continue
        node_count = 0
        for item in row["Mapping"].split(" | "):
            if "->" in item:
                _, physical = item.split("->")
                unique_nodes.add(physical)
                node_count += 1
        node_counts.append(node_count)
        for item in row["Paths"].split(" | "):
            if ":" not in item:
                continue
            _, p = item.split(":", 1)
            parts = p.split("->")
            for a, b in zip(parts, parts[1:]):
                unique_links.add(tuple(sorted((a, b))))

    avg_node = sum(node_counts) / len(node_counts) if node_counts else 0
    avg_path = sum(all_paths) / len(all_paths) if all_paths else 0
    rcr = total_revenue / total_cost if total_cost else 0
    embedding_ratio = accepted_count / total_requests * 100

    summary = {
        "algorithm": "TWO_LEVEL_GAME",
        "revenue": round(total_revenue, 4),
        "total_cost": round(total_cost, 4),
        "revenuetocostratio": round(rcr * 100, 4),
        "accepted": accepted_count,
        "total_request": total_requests,
        "embeddingratio": round(embedding_ratio, 4),
        "pre_resource": pre_cpu,
        "post_resource": post_cpu,
        "consumed": consumed_cpu,
        "avg_bw": round(avg_bw, 4),
        "avg_crb": round(avg_crb, 4),
        "avg_link": round(avg_link, 4),
        "No_of_Links_used": len(unique_links),
        "avg_node": round(avg_node, 4),
        "No_of_Nodes_used": len(unique_nodes),
        "avg_path": round(avg_path, 4),
        "avg_exec": round(elapsed_ms / total_requests, 4),
        "total_nodes": len(network.nodes),
        "total_links": len(network.links),
    }

    resource_rows = []
    for n, before in network.nodes.items():
        resource_rows.append({
            "Resource": "CPU",
            "Item": n,
            "Before": before,
            "After": result["resources"]["cpu"][n],
            "Consumed": before - result["resources"]["cpu"][n],
        })
    for e, before in network.links.items():
        resource_rows.append({
            "Resource": "BW",
            "Item": f"{e[0]}-{e[1]}",
            "Before": before,
            "After": result["resources"]["bw"][e],
            "Consumed": before - result["resources"]["bw"][e],
        })

    return summary, result, resource_rows

def provider_objective(price_vector):
    cpu_price, bw_price = price_vector
    summary, _, _ = run_lower_level(cpu_price, bw_price)

    # Provider earns the resource-price cost charged to accepted VNRs.
    # Penalize rejection and negative/zero utility situations.
    provider_revenue = summary["total_cost"]
    rejection_penalty = (summary["total_request"] - summary["accepted"]) * 1000
    return -(provider_revenue) + rejection_penalty

def run_upper_level_de():
    de = DifferentialEvolution(
        objective=provider_objective,
        bounds=[(0.10, 0.90), (0.05, 0.40)],
        population_size=8,
        generations=8,
        seed=42,
    )
    best_prices, objective = de.run()
    return best_prices, objective

def main():
    # First phase: run the agreed fixed-price example.
    summary, result, resource_rows = run_lower_level(CPU_PRICE, BW_PRICE)

    # Optional upper-level DE demonstration.
    best_prices, de_objective = run_upper_level_de()

    pricing_rows = [
        {
            "Level": "Upper",
            "Method": "Differential Evolution",
            "CPU_Price": CPU_PRICE,
            "BW_Price": BW_PRICE,
            "Role": "Initial/fixed prices used for the worked example",
            "Objective": "",
        },
        {
            "Level": "Upper",
            "Method": "Differential Evolution",
            "CPU_Price": round(best_prices[0], 6),
            "BW_Price": round(best_prices[1], 6),
            "Role": "Best candidate found by DE",
            "Objective": round(de_objective, 6),
        },
    ]

    output = "Results.xlsx"
    write_results(
        output,
        [summary],
        result["strategies"],
        result["accepted"],
        resource_rows,
        pricing_rows,
    )

    print("=" * 70)
    print("TWO-LEVEL VNE GAME RESULTS")
    print("=" * 70)
    print(f"CPU price : {CPU_PRICE}")
    print(f"BW price  : {BW_PRICE}")
    print(f"Revenue   : {summary['revenue']}")
    print(f"Cost      : {summary['total_cost']}")
    print(f"R/C ratio : {summary['revenuetocostratio']}%")
    print(f"Accepted  : {summary['accepted']}/{summary['total_request']}")
    print(f"Embedding : {summary['embeddingratio']}%")
    print()
    for row in result["accepted"]:
        print(row["VNR"], "->", row["Accepted"],
              "| Utility:", round(row["Utility"], 4),
              "|", row["Mapping"])
    print()
    print("DE best CPU price:", round(best_prices[0], 6))
    print("DE best BW price :", round(best_prices[1], 6))
    print(f"Excel saved to: {output}")

if __name__ == "__main__":
    main()
