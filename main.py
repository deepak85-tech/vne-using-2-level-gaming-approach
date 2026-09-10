import time

from logger import write_execution_log
from physical_network import PhysicalNetwork
from vnr_data import get_vnrs
from game import LowerLevelGame
from differential_evolution import DifferentialEvolution
from excel_writer import write_results


CPU_PRICE = 1.00
BW_PRICE = 0.70


# ======================================================
# GENERIC VNR HELPERS
# ======================================================

def get_vnr_links(vnr):
    return vnr.get("links", [])


def get_link_bandwidth(link):
    if isinstance(link, dict):
        if "bw" in link:
            return link["bw"]

        if "bandwidth" in link:
            return link["bandwidth"]

        raise ValueError(
            f"Bandwidth field not found in link: {link}"
        )

    if isinstance(link, (tuple, list)):
        if len(link) >= 3:
            return link[2]

        raise ValueError(
            f"Link must contain source, destination and bandwidth: {link}"
        )

    raise TypeError(
        f"Unsupported link format: {type(link)} -> {link}"
    )


def get_link_source(link):
    if isinstance(link, dict):
        if "src" in link:
            return link["src"]

        if "source" in link:
            return link["source"]

        raise ValueError(
            f"Source field not found in link: {link}"
        )

    if isinstance(link, (tuple, list)):
        return link[0]

    raise TypeError(
        f"Unsupported link format: {type(link)}"
    )


def get_link_destination(link):
    if isinstance(link, dict):
        if "dst" in link:
            return link["dst"]

        if "destination" in link:
            return link["destination"]

        raise ValueError(
            f"Destination field not found in link: {link}"
        )

    if isinstance(link, (tuple, list)):
        return link[1]

    raise TypeError(
        f"Unsupported link format: {type(link)}"
    )


# ======================================================
# PATH HELPERS
# ======================================================

def path_hops(path):
    return max(0, len(path) - 1)


# ======================================================
# LOWER LEVEL
# ======================================================

def run_lower_level(cpu_price, bw_price):

    network = PhysicalNetwork.from_default()

    vnrs = get_vnrs()

    start = time.perf_counter()

    resources_before = network.copy_resources()

    game = LowerLevelGame(
        network,
        cpu_price,
        bw_price
    )

    result = game.play(vnrs)

    resources_after = result["resources"]

    elapsed_ms = (
        time.perf_counter() - start
    ) * 1000

    # --------------------------------------------------
    # Accepted VNRs
    # --------------------------------------------------

    accepted_rows = [
        row
        for row in result["accepted"]
        if row["Accepted"] == "YES"
    ]

    total_revenue = sum(
        row["Revenue"]
        for row in accepted_rows
    )

    total_cost = sum(
        row["Cost"]
        for row in accepted_rows
    )

    accepted_count = len(
        accepted_rows
    )

    total_requests = len(vnrs)

    # --------------------------------------------------
    # CPU resources
    # --------------------------------------------------

    pre_cpu = sum(
        network.nodes.values()
    )

    post_cpu = sum(
        result["resources"]["cpu"].values()
    )

    consumed_cpu = (
        pre_cpu - post_cpu
    )

    # --------------------------------------------------
    # Bandwidth resources
    # --------------------------------------------------

    pre_bw = sum(
        network.links.values()
    )

    post_bw = sum(
        result["resources"]["bw"].values()
    )

    consumed_bw = (
        pre_bw - post_bw
    )

    # --------------------------------------------------
    # Requested bandwidth
    # --------------------------------------------------

    requested_bw = []

    for vnr in vnrs:

        for link in get_vnr_links(vnr):

            bandwidth = get_link_bandwidth(link)

            requested_bw.append(
                bandwidth
            )

    avg_bw = (
        sum(requested_bw)
        / len(requested_bw)
        if requested_bw
        else 0
    )

    # --------------------------------------------------
    # CPU resource utilization
    # --------------------------------------------------

    avg_crb = (
        consumed_cpu
        / pre_cpu
        * 100
        if pre_cpu
        else 0
    )

    # --------------------------------------------------
    # Link utilization
    # --------------------------------------------------

    avg_link = (
        consumed_bw
        / pre_bw
        * 100
        if pre_bw
        else 0
    )

    # --------------------------------------------------
    # Path metrics
    # --------------------------------------------------

    all_paths = []

    for row in accepted_rows:

        paths_text = row.get(
            "Paths",
            ""
        )

        if not paths_text:
            continue

        for item in paths_text.split(
            " | "
        ):

            if ":" not in item:
                continue

            _, path = item.split(
                ":",
                1
            )

            path_nodes = path.split(
                "->"
            )

            hops = path_hops(
                path_nodes
            )

            all_paths.append(
                hops
            )

    # --------------------------------------------------
    # Node and link usage
    # --------------------------------------------------

    unique_links = set()

    unique_nodes = set()

    node_counts = []

    for row in accepted_rows:

        # ----------------------------------------------
        # Node mapping
        # ----------------------------------------------

        mapping_text = row.get(
            "Mapping",
            ""
        )

        node_count = 0

        for item in mapping_text.split(
            " | "
        ):

            if "->" not in item:
                continue

            parts = item.split(
                "->",
                1
            )

            if len(parts) != 2:
                continue

            physical = parts[1].strip()

            unique_nodes.add(
                physical
            )

            node_count += 1

        node_counts.append(
            node_count
        )

        # ----------------------------------------------
        # Link mapping
        # ----------------------------------------------

        paths_text = row.get(
            "Paths",
            ""
        )

        for item in paths_text.split(
            " | "
        ):

            if ":" not in item:
                continue

            _, path = item.split(
                ":",
                1
            )

            path_nodes = path.split(
                "->"
            )

            for a, b in zip(
                path_nodes,
                path_nodes[1:]
            ):

                a = a.strip()
                b = b.strip()

                unique_links.add(
                    tuple(
                        sorted(
                            (a, b)
                        )
                    )
                )

    # --------------------------------------------------
    # Average node usage
    # --------------------------------------------------

    avg_node = (
        sum(node_counts)
        / len(node_counts)
        if node_counts
        else 0
    )

    # --------------------------------------------------
    # Average path length
    # --------------------------------------------------

    avg_path = (
        sum(all_paths)
        / len(all_paths)
        if all_paths
        else 0
    )

    # --------------------------------------------------
    # Revenue / Cost ratio
    # --------------------------------------------------

    revenue_to_cost_ratio = (
        total_revenue
        / total_cost
        if total_cost
        else 0
    )

    # --------------------------------------------------
    # Embedding ratio
    # --------------------------------------------------

    embedding_ratio = (
        accepted_count
        / total_requests
        * 100
        if total_requests
        else 0
    )

    # --------------------------------------------------
    # Execution time per VNR
    # --------------------------------------------------

    avg_execution = (
        elapsed_ms
        / total_requests
        if total_requests
        else 0
    )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    summary = {

        "algorithm":
            "TWO_LEVEL_GAME",

        "revenue":
            round(
                total_revenue,
                4
            ),

        "total_cost":
            round(
                total_cost,
                4
            ),

        "revenuetocostratio":
            round(
                revenue_to_cost_ratio
                * 100,
                4
            ),

        "accepted":
            accepted_count,

        "total_request":
            total_requests,

        "embeddingratio":
            round(
                embedding_ratio,
                4
            ),

        "pre_resource":
            pre_cpu,

        "post_resource":
            post_cpu,

        "consumed":
            consumed_cpu,

        "avg_bw":
            round(
                avg_bw,
                4
            ),

        "avg_crb":
            round(
                avg_crb,
                4
            ),

        "avg_link":
            round(
                avg_link,
                4
            ),

        "No_of_Links_used":
            len(
                unique_links
            ),

        "avg_node":
            round(
                avg_node,
                4
            ),

        "No_of_Nodes_used":
            len(
                unique_nodes
            ),

        "avg_path":
            round(
                avg_path,
                4
            ),

        "avg_exec":
            round(
                avg_execution,
                4
            ),

        "total_nodes":
            len(
                network.nodes
            ),

        "total_links":
            len(
                network.links
            ),
    }

    # ==================================================
    # RESOURCE ROWS
    # ==================================================

    resource_rows = []

    # --------------------------------------------------
    # CPU
    # --------------------------------------------------

    for node, before in network.nodes.items():

        after = (
            result["resources"]
            ["cpu"][node]
        )

        resource_rows.append({

            "Resource":
                "CPU",

            "Item":
                node,

            "Before":
                before,

            "After":
                after,

            "Consumed":
                before - after,
        })

    # --------------------------------------------------
    # BANDWIDTH
    # --------------------------------------------------

    for link, before in network.links.items():

        after = (
            result["resources"]
            ["bw"][link]
        )

        resource_rows.append({

            "Resource":
                "BW",

            "Item":
                f"{link[0]}-{link[1]}",

            "Before":
                before,

            "After":
                after,

            "Consumed":
                before - after,
        })

    # ==================================================
    # EXECUTION LOG
    # ==================================================

    write_execution_log(
    "Execution_Log.txt",
    cpu_price,
    bw_price,
    result["ordered_vnrs"],
    result["strategies"],
    result["accepted"],
    resources_before,
    resources_after,
    result.get("resource_history")
)

    return (
        summary,
        result,
        resource_rows
    )


# ======================================================
# PROVIDER OBJECTIVE
# ======================================================

def provider_objective(
    price_vector
):

    cpu_price = price_vector[0]

    bw_price = price_vector[1]

    summary, _, _ = run_lower_level(
        cpu_price,
        bw_price
    )

    # Provider revenue

    provider_revenue = (
        summary["total_cost"]
    )

    # Rejection penalty

    rejected = (
        summary["total_request"]
        - summary["accepted"]
    )

    rejection_penalty = (
        rejected * 1000
    )

    objective = (
        -provider_revenue
        + rejection_penalty
    )

    return objective


# ======================================================
# UPPER LEVEL DIFFERENTIAL EVOLUTION
# ======================================================

def run_upper_level_de():

    de = DifferentialEvolution(

        objective=
            provider_objective,

        bounds=[
            (0.10, 0.90),
            (0.05, 0.40)
        ],

        population_size=8,

        generations=8,

        seed=42,
    )

    best_prices, objective = (
        de.run()
    )

    return (
        best_prices,
        objective
    )


# ======================================================
# MAIN
# ======================================================

def main():

    # --------------------------------------------------
    # Fixed price example
    # --------------------------------------------------

    summary, result, resource_rows = (
        run_lower_level(
            CPU_PRICE,
            BW_PRICE
        )
    )

    # --------------------------------------------------
    # Differential Evolution
    # --------------------------------------------------

    best_prices, de_objective = (
        run_upper_level_de()
    )

    # --------------------------------------------------
    # Pricing rows
    # --------------------------------------------------

    pricing_rows = [

        {
            "Level":
                "Upper",

            "Method":
                "Differential Evolution",

            "CPU_Price":
                CPU_PRICE,

            "BW_Price":
                BW_PRICE,

            "Role":
                "Initial/fixed prices used for the worked example",

            "Objective":
                "",
        },

        {
            "Level":
                "Upper",

            "Method":
                "Differential Evolution",

            "CPU_Price":
                round(
                    best_prices[0],
                    6
                ),

            "BW_Price":
                round(
                    best_prices[1],
                    6
                ),

            "Role":
                "Best candidate found by DE",

            "Objective":
                round(
                    de_objective,
                    6
                ),
        },
    ]

    # --------------------------------------------------
    # Excel
    # --------------------------------------------------

    output = "Results.xlsx"

    write_results(

        output,

        [summary],

        result["strategies"],

        result["accepted"],

        resource_rows,

        pricing_rows,

        result["logs"]
    )

    # --------------------------------------------------
    # Console output
    # --------------------------------------------------

    print("=" * 70)

    print(
        "TWO-LEVEL VNE GAME RESULTS"
    )

    print("=" * 70)

    print(
        f"CPU price : {CPU_PRICE}"
    )

    print(
        f"BW price  : {BW_PRICE}"
    )

    print(
        f"Revenue   : "
        f"{summary['revenue']}"
    )

    print(
        f"Cost      : "
        f"{summary['total_cost']}"
    )

    print(
        f"R/C ratio : "
        f"{summary['revenuetocostratio']}%"
    )

    print(
        f"Accepted  : "
        f"{summary['accepted']}/"
        f"{summary['total_request']}"
    )

    print(
        f"Embedding : "
        f"{summary['embeddingratio']}%"
    )

    print()

    # --------------------------------------------------
    # VNR results
    # --------------------------------------------------

    for row in result["accepted"]:

        print(

            row["VNR"],

            "->",

            row["Accepted"],

            "| Utility:",

            round(
                row["Utility"],
                4
            ),

            "|",

            row["Mapping"]
        )

    print()

    # --------------------------------------------------
    # DE result
    # --------------------------------------------------

    print(
        "DE best CPU price:",
        round(
            best_prices[0],
            6
        )
    )

    print(
        "DE best BW price :",
        round(
            best_prices[1],
            6
        )
    )

    print()

    print(
        f"Excel saved to: "
        f"{output}"
    )

    print(
        "Log saved to: "
        "Execution_Log.txt"
    )


# ======================================================
# START
# ======================================================

if __name__ == "__main__":
    main()