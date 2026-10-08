import sys
import time

from logger import (
    write_execution_log,
    write_current_run_log
)

from physical_network import PhysicalNetwork

from game import LowerLevelGame

from differential_evolution import (
    DifferentialEvolution
)

from excel_writer import write_results

# ALIB modules are imported only when their corresponding switch is True.
# You can independently choose the physical-network source and VNR source.


# ==========================================================
# CONFIGURATION
# ==========================================================

PICKLE_FILE = (
    r"D:\minwith log\input\senario_RedBestel.pickle"
)

ALIB_ROOT = (
    r"D:\mini project resources"
    r"\P3_ALIB_MASTER\P3_ALIB_MASTER"
)

NUMBER_OF_PHYSICAL_NETWORKS = 1

# ==========================================================
# INPUT SOURCES
# ==========================================================
# These TWO switches are independent.
#
# USE_ALIB_PHYSICAL = True
#     -> use ALIB physical network
# USE_ALIB_PHYSICAL = False
#     -> use your custom physical network
#
# USE_ALIB_VNR = True
#     -> use ALIB-generated VNRs
# USE_ALIB_VNR = False
#     -> use your VNRs from vnr_data.py
#
# This gives four combinations:
# 1. True,  True  = ALIB physical + ALIB VNR
# 2. True,  False = ALIB physical + YOUR VNR
# 3. False, True  = YOUR physical + ALIB VNR
# 4. False, False = YOUR physical + YOUR VNR

USE_ALIB_PHYSICAL = True
USE_ALIB_VNR = True

# Default experiment sizes. You can also pass sizes on the command line,
# for example: python main.py 10 20 30 40
DEFAULT_VNR_COUNTS = [1, 2, 3, 4]

MAX_NASH_ITERATIONS = 20

MAX_STRATEGIES = 200


# ==========================================================
# GLOBAL VNR SET
# ==========================================================

# VNRs are generated once per program run.
# The same VNR set is used for every DE price evaluation.

CURRENT_VNRS = []


# ==========================================================
# BUILD PHYSICAL NETWORK POOL
# ==========================================================

# ======================================================
# EDIT ONLY THIS LINE TO CHANGE VNR EXPERIMENTS
# ======================================================
VNR_EXPERIMENTS = [1, 2, 3, 4]

def create_physical_networks():
    """
    Build the physical-network list according to USE_ALIB_PHYSICAL.

    USE_ALIB_PHYSICAL = True:
        Loads PN1 from the ALIB substrate.

    USE_ALIB_PHYSICAL = False:
        Loads PN1 from custom_physical_network.py.
        ALIB physical-network code is not imported or accessed.
    """

    if USE_ALIB_PHYSICAL:
        base_network = PhysicalNetwork.from_alib(
            pickle_file=PICKLE_FILE,
            alib_root=ALIB_ROOT,
            scenario_index=0,
            name="PN1"
        )
    else:
        from custom_physical_network import get_custom_physical_network

        base_network = get_custom_physical_network(
            name="PN1"
        )

    return [base_network]


# ==========================================================
# PRINT NETWORK INFORMATION
# ==========================================================

def print_network_information(networks):

    print()
    print("=" * 70)
    print("PHYSICAL NETWORK POOL")
    print("=" * 70)

    for network in networks:

        info = network.summary()

        print(
            f"{info['name']} "
            f"| Nodes: {info['nodes']} "
            f"| Links: {info['links']} "
            f"| CPU: {info['cpu']:.2f} "
            f"| BW: {info['bandwidth']:.2f}"
        )

    print()


# ==========================================================
# LOWER LEVEL
# ==========================================================

def run_lower_level(
    cpu_price,
    bw_price,
    physical_networks
):
    """Run the lower-level Nash game on the single ALIB physical network."""

    start = time.perf_counter()

    game = LowerLevelGame(
        physical_networks,
        cpu_price=cpu_price,
        bw_price=bw_price,
        max_iterations=MAX_NASH_ITERATIONS,
        max_strategies=MAX_STRATEGIES
    )

    result = game.play(
        CURRENT_VNRS
    )

    elapsed_ms = (
        time.perf_counter()
        - start
    ) * 1000

    # ======================================================
    # ACCEPTED VNRs
    # ======================================================

    accepted_rows = [
        row
        for row in result["accepted"]
        if row["Accepted"] == "YES"
    ]

    # ======================================================
    # TOTAL REVENUE
    # ======================================================

    total_revenue = sum(
        row.get("Revenue", 0)
        for row in accepted_rows
    )

    # ======================================================
    # TOTAL COST
    # ======================================================

    total_cost = sum(
        row.get("Cost", 0)
        for row in accepted_rows
    )

    # ======================================================
    # COUNTS
    # ======================================================

    accepted_count = len(
        accepted_rows
    )

    total_requests = len(
        CURRENT_VNRS
    )

    rejected_count = (
        total_requests
        - accepted_count
    )

    # ======================================================
    # CPU UTILIZATION
    # ======================================================

    pre_cpu = sum(
        sum(
            network.original_nodes.values()
        )
        for network in physical_networks
    )

    post_cpu = sum(
        sum(
            network.nodes.values()
        )
        for network in physical_networks
    )

    consumed_cpu = (
        pre_cpu
        - post_cpu
    )

    avg_crb = (
        consumed_cpu
        / pre_cpu
        * 100
        if pre_cpu
        else 0
    )

    # ======================================================
    # BANDWIDTH UTILIZATION
    # ======================================================

    pre_bw = sum(
        sum(
            network.original_links.values()
        )
        for network in physical_networks
    )

    post_bw = sum(
        sum(
            network.links.values()
        )
        for network in physical_networks
    )

    consumed_bw = (
        pre_bw
        - post_bw
    )

    avg_link = (
        consumed_bw
        / pre_bw
        * 100
        if pre_bw
        else 0
    )

    # ======================================================
    # REQUESTED BANDWIDTH
    # ======================================================

    requested_bw = []

    for vnr in CURRENT_VNRS:

        links = vnr.get(
            "links",
            {}
        )

        if isinstance(
            links,
            dict
        ):

            for bandwidth in links.values():

                requested_bw.append(
                    bandwidth
                )

        else:

            for link in links:

                if len(link) >= 3:

                    requested_bw.append(
                        link[2]
                    )

    avg_bw = (
        sum(requested_bw)
        / len(requested_bw)
        if requested_bw
        else 0
    )

    # ======================================================
    # PATH / NODE METRICS
    # ======================================================

    all_paths = []

    unique_nodes = set()

    unique_links = set()

    node_counts = []

    for row in accepted_rows:

        # --------------------------------------------------
        # Mapping
        # --------------------------------------------------

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

            _, physical = item.split(
                "->",
                1
            )

            physical = physical.strip()

            unique_nodes.add(
                physical
            )

            node_count += 1

        node_counts.append(
            node_count
        )

        # --------------------------------------------------
        # Paths
        # --------------------------------------------------

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

            if len(path_nodes) > 1:

                all_paths.append(
                    len(path_nodes) - 1
                )

            for a, b in zip(
                path_nodes,
                path_nodes[1:]
            ):

                unique_links.add(
                    tuple(
                        sorted(
                            (
                                a.strip(),
                                b.strip()
                            )
                        )
                    )
                )

    avg_node = (
        sum(node_counts)
        / len(node_counts)
        if node_counts
        else 0
    )

    avg_path = (
        sum(all_paths)
        / len(all_paths)
        if all_paths
        else 0
    )

    # ======================================================
    # RATIOS
    # ======================================================

    revenue_to_cost_ratio = (
        total_revenue
        / total_cost
        if total_cost
        else 0
    )

    embedding_ratio = (
        accepted_count
        / total_requests
        * 100
        if total_requests
        else 0
    )

    avg_execution = (
        elapsed_ms
        / total_requests
        if total_requests
        else 0
    )

    # ======================================================
    # SUMMARY
    # ======================================================

    summary = {

        "algorithm":
            "SINGLE_PHYSICAL_NETWORK_TWO_LEVEL_GAME",

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
                revenue_to_cost_ratio * 100,
                4
            ),

        "accepted":
            accepted_count,

        "rejected":
            rejected_count,

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
            len(unique_links),

        "avg_node":
            round(
                avg_node,
                4
            ),

        "No_of_Nodes_used":
            len(unique_nodes),

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
            sum(
                len(network.nodes)
                for network in physical_networks
            ),

        "total_links":
            sum(
                len(network.links)
                for network in physical_networks
            ),

        "physical_networks":
            len(physical_networks),

        "nash_iterations":
            result.get(
                "iterations",
                0
            )
    }

    # ======================================================
    # RESOURCE ROWS
    # ======================================================

    resource_rows = []

    for network in physical_networks:

        # --------------------------------------------------
        # CPU
        # --------------------------------------------------

        for node, before in (
            network.original_nodes.items()
        ):

            after = network.nodes[node]

            resource_rows.append({

                "Network":
                    network.name,

                "Resource":
                    "CPU",

                "Item":
                    node,

                "Before":
                    before,

                "After":
                    after,

                "Consumed":
                    before - after
            })

        # --------------------------------------------------
        # BANDWIDTH
        # --------------------------------------------------

        for link, before in (
            network.original_links.items()
        ):

            after = network.links[link]

            resource_rows.append({

                "Network":
                    network.name,

                "Resource":
                    "BW",

                "Item":
                    f"{link[0]}-{link[1]}",

                "Before":
                    before,

                "After":
                    after,

                "Consumed":
                    before - after
            })

    # ======================================================
    # RETURN
    # ======================================================

    return (
        summary,
        result,
        resource_rows
    )


# ==========================================================
# PROVIDER OBJECTIVE
# ==========================================================

def provider_objective(price_vector):
    """
    DE minimizes this objective.

    The same VNR set is evaluated for every price vector.

    A fresh physical-network pool is created for every
    candidate price vector so that resource consumption
    from one DE candidate does not affect another.
    """

    cpu_price = price_vector[0]

    bw_price = price_vector[1]

    physical_networks = (
        create_physical_networks()
    )

    summary, _, _ = run_lower_level(
        cpu_price,
        bw_price,
        physical_networks
    )

    provider_revenue = (
        summary["total_cost"]
    )

    rejected = (
        summary["total_request"]
        -
        summary["accepted"]
    )

    rejection_penalty = (
        rejected * 1000
    )

    objective = (
        -provider_revenue
        + rejection_penalty
    )

    return objective


# ==========================================================
# DIFFERENTIAL EVOLUTION
# ==========================================================

def run_upper_level_de():

    de = DifferentialEvolution(

        objective=
            provider_objective,

        bounds=[

            (0.10, 0.90),

            (0.05, 0.40)
        ],

        population_size=4,

        generations=3,

        seed=42
    )

    best_prices, objective = (
        de.run()
    )

    return (
        best_prices,
        objective
    )


# ==========================================================
# EXPERIMENT RUNNER
# ==========================================================

def run_experiment(vnr_count, experiment_number=None):
    """Run one independent experiment using one fresh PN1."""

    global CURRENT_VNRS

    print()
    print("=" * 70)
    if experiment_number is not None:
        print(f"EXPERIMENT {experiment_number}: {vnr_count} VNRs")
    else:
        print(f"EXPERIMENT: {vnr_count} VNRs")
    print("ONE PHYSICAL NETWORK: PN1")
    print(f"PHYSICAL SOURCE   : {'ALIB' if USE_ALIB_PHYSICAL else 'CUSTOM'}")
    print(f"VNR SOURCE        : {'ALIB' if USE_ALIB_VNR else 'CUSTOM'}")
    print("=" * 70)

    # ======================================================
    # GENERATE VNRs
    # ======================================================

    if USE_ALIB_VNR:
        print(f"GENERATING {vnr_count} RANDOM ALIB VNRS")
        from alib_vnr_converter import generate_random_alib_requests

        CURRENT_VNRS = generate_random_alib_requests(
            pickle_file=PICKLE_FILE,
            alib_root=ALIB_ROOT,
            number_of_requests=vnr_count,
            scenario_index=0
        )
    else:
        print(f"LOADING CUSTOM VNRS (requested: {vnr_count})")
        from vnr_data import get_vnrs

        custom_vnrs = get_vnrs()

        if vnr_count > len(custom_vnrs):
            raise ValueError(
                f"Custom mode has only {len(custom_vnrs)} VNRs, "
                f"but {vnr_count} were requested. "
                f"Add more VNRs to vnr_data.py or run a smaller count."
            )

        CURRENT_VNRS = custom_vnrs[:vnr_count]

    print(f"Generated VNRs: {len(CURRENT_VNRS)}")

    # ======================================================
    # VNR DETAILS
    # ======================================================

    print()
    print("GENERATED VNR DETAILS")
    print("-" * 70)

    for vnr in CURRENT_VNRS:
        cpu = sum(vnr["nodes"].values())
        bw = sum(vnr["links"].values())
        print(
            f"{vnr['id']} | Nodes: {len(vnr['nodes'])} | "
            f"CPU: {cpu:.2f} | Links: {len(vnr['links'])} | BW: {bw:.2f}"
        )

    # ======================================================
    # DIFFERENTIAL EVOLUTION
    # ======================================================

    print()
    print("STARTING DIFFERENTIAL EVOLUTION")
    print("-" * 70)

    best_prices, de_objective = run_upper_level_de()
    best_cpu_price = best_prices[0]
    best_bw_price = best_prices[1]

    # ======================================================
    # FINAL LOWER LEVEL
    # ======================================================

    print()
    print("FINAL LOWER-LEVEL NASH GAME")
    print("-" * 70)

    # This is a fresh PN1 for this experiment.
    # Experiment 1, 2, 3 and 4 therefore do not share resources.
    physical_networks = create_physical_networks()

    summary, result, resource_rows = run_lower_level(
        best_cpu_price,
        best_bw_price,
        physical_networks
    )

    # ======================================================
    # EXPERIMENT LOG DATA
    # ======================================================

    log_arguments = dict(
        cpu_price=best_cpu_price,
        bw_price=best_bw_price,
        physical_networks=physical_networks,
        ordered_vnrs=result["ordered_vnrs"],
        strategy_rows=result["strategies"],
        accepted_rows=result["accepted"],
        resource_history=result.get("resource_history", []),
        summary=summary,
        de_objective=de_objective,
        nash_iterations=result.get("iterations", 0),
    )

    # Build the complete text for this experiment.
    # It is returned to main(), which writes all four experiments together.
    from logger import build_experiment_log_content

    experiment_log = build_experiment_log_content(
        experiment_number=experiment_number,
        vnr_count=vnr_count,
        **log_arguments
    )

    # ======================================================
    # PRICING ROW
    # ======================================================

    pricing_rows = [{
        "Level": "Upper",
        "Method": "Differential Evolution",
        "CPU_Price": round(best_cpu_price, 6),
        "BW_Price": round(best_bw_price, 6),
        "Role": "Best price vector found by DE",
        "Objective": round(de_objective, 6)
    }]

    # ======================================================
    # CONSOLE RESULTS
    # ======================================================

    print()
    print("=" * 70)
    print("SINGLE-PHYSICAL-NETWORK TWO-LEVEL VNE RESULTS")
    print("=" * 70)
    print("Physical Networks : 1 (PN1)")
    print(f"VNRs              : {summary['total_request']}")
    print(f"Best CPU price    : {best_cpu_price:.6f}")
    print(f"Best BW price     : {best_bw_price:.6f}")
    print(f"Revenue           : {summary['revenue']}")
    print(f"Cost              : {summary['total_cost']}")
    print(f"R/C ratio         : {summary['revenuetocostratio']}%")
    print(f"Accepted          : {summary['accepted']}/{summary['total_request']}")
    print(f"Rejected          : {summary['rejected']}")
    print(f"Embedding         : {summary['embeddingratio']}%")
    print(f"Nash iterations   : {summary['nash_iterations']}")

    print()
    print("FINAL VNR RESULTS")
    print("-" * 70)

    for row in result["accepted"]:
        if row["Accepted"] == "YES":
            print(
                f"{row['VNR']} -> PN1 | Utility: {row['Utility']:.4f} | "
                f"Mapping: {row['Mapping']}"
            )
        else:
            print(
                f"{row['VNR']} -> REJECTED | {row.get('Reason', '')}"
            )

    print()
    print(f"DE best CPU price: {best_cpu_price:.6f}")
    print(f"DE best BW price : {best_bw_price:.6f}")
    print(f"DE objective     : {de_objective:.6f}")

    return {
        "experiment_number": experiment_number,
        "vnr_count": vnr_count,
        "summary": summary,
        "strategies": result["strategies"],
        "accepted": result["accepted"],
        "resource_rows": resource_rows,
        "pricing_rows": pricing_rows,
        "logs": result.get("logs", []),
        "experiment_log": experiment_log,
        "de_objective": de_objective,
        "cpu_price": best_cpu_price,
        "bw_price": best_bw_price,
    }


def main():
    """
    Run four independent VNR-size experiments by default:

        Experiment 1 -> 1 VNR
        Experiment 2 -> 2 VNRs
        Experiment 3 -> 3 VNRs
        Experiment 4 -> 4 VNRs

    One python main.py command therefore processes 10 VNR entries in total.
    Every experiment starts with a fresh copy of PN1.

    All four experiments are written into ONE Results.xlsx file.
    Current_Run_Log.txt is overwritten with the complete current run.
    Execution_Log.txt appends the complete current run to its history.
    """

    if len(sys.argv) > 1:
        try:
            counts = [int(value) for value in sys.argv[1:]]
        except ValueError:
            print("Invalid VNR count(s).")
            print("Use: python main.py")
            print("or : python main.py 1 2 3 4")
            return
    else:
        counts = VNR_EXPERIMENTS

    if any(count <= 0 for count in counts):
        print("All VNR counts must be greater than 0.")
        return

    print()
    print("VNR EXPERIMENTS:", counts)
    print(f"PHYSICAL SOURCE : {'ALIB' if USE_ALIB_PHYSICAL else 'CUSTOM'}")
    print(f"VNR SOURCE      : {'ALIB' if USE_ALIB_VNR else 'CUSTOM'}")
    print("PHYSICAL NETWORKS: 1 (fresh PN1 for each experiment)")
    print("TOTAL VNR ENTRIES:", sum(counts))

    experiment_results = []

    # ======================================================
    # RUN ALL EXPERIMENTS
    # ======================================================

    for experiment_number, vnr_count in enumerate(counts, start=1):
        result = run_experiment(
            vnr_count,
            experiment_number
        )
        experiment_results.append(result)

    # ======================================================
    # COMBINED TEXT LOGS
    # ======================================================

    # The same complete four-experiment content is used for both files.
    # Current_Run_Log -> overwrite latest run
    # Execution_Log   -> append latest run
    from logger import (
        write_combined_execution_log,
        write_combined_current_run_log
    )

    experiment_logs = [
        item["experiment_log"]
        for item in experiment_results
    ]

    try:
        write_combined_current_run_log(
            filename="Current_Run_Log.txt",
            experiment_logs=experiment_logs
        )
    except Exception as error:
        print(
            "Warning: Current_Run_Log.txt failed:",
            error
        )

    try:
        write_combined_execution_log(
            filename="Execution_Log.txt",
            experiment_logs=experiment_logs
        )
    except Exception as error:
        print(
            "Warning: Execution_Log.txt failed:",
            error
        )

    # ======================================================
    # COMBINED EXCEL DATA
    # ======================================================

    all_summary_rows = []
    all_strategy_rows = []
    all_accepted_rows = []
    all_resource_rows = []
    all_pricing_rows = []
    all_log_lines = []

    for item in experiment_results:
        experiment_number = item["experiment_number"]
        vnr_count = item["vnr_count"]

        # Summary rows
        summary_row = dict(item["summary"])
        summary_row["experiment"] = experiment_number
        summary_row["vnr_count"] = vnr_count
        all_summary_rows.append(summary_row)

        # VNR strategy rows
        for row in item["strategies"]:
            new_row = dict(row)
            new_row["Experiment"] = experiment_number
            new_row["VNR_Count"] = vnr_count
            all_strategy_rows.append(new_row)

        # Complete VNR result rows
        for row in item["accepted"]:
            new_row = dict(row)
            new_row["Experiment"] = experiment_number
            new_row["VNR_Count"] = vnr_count
            all_accepted_rows.append(new_row)

        # Resource rows
        for row in item["resource_rows"]:
            new_row = dict(row)
            new_row["Experiment"] = experiment_number
            new_row["VNR_Count"] = vnr_count
            all_resource_rows.append(new_row)

        # DE pricing rows
        for row in item["pricing_rows"]:
            new_row = dict(row)
            new_row["Experiment"] = experiment_number
            new_row["VNR_Count"] = vnr_count
            all_pricing_rows.append(new_row)

        # Preserve the detailed result log lines in Excel too.
        all_log_lines.append(
            f"EXPERIMENT {experiment_number} : {vnr_count} VNRs"
        )
        all_log_lines.extend(item["logs"])
        all_log_lines.extend(["", "", "", "", "", "", "", ""])

    # ======================================================
    # ONE RESULTS FILE
    # ======================================================

    output = "Results.xlsx"

    try:
        write_results(
            output,
            all_summary_rows,
            all_strategy_rows,
            all_accepted_rows,
            all_resource_rows,
            all_pricing_rows,
            all_log_lines
        )

        print()
        print("=" * 70)
        print("ALL EXPERIMENTS COMPLETED")
        print("=" * 70)
        print("Experiments      :", len(experiment_results))
        print("VNR counts       :", counts)
        print("Total VNR entries:", sum(counts))
        print("Excel saved to   : Results.xlsx")
        print("Current run log  : Current_Run_Log.txt")
        print("Execution log    : Execution_Log.txt")

    except Exception as error:
        print(
            "Warning: Excel writing failed:",
            error
        )


# ==========================================================
# START PROGRAM
# ==========================================================

if __name__ == "__main__":
    main()
