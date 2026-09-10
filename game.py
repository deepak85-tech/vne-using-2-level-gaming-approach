from copy import deepcopy

from dijkstra import edge_key, shortest_feasible_path
from utility import calculate_revenue, calculate_cost, calculate_utility
from candidate_strategies import get_candidate_strategies


class LowerLevelGame:

    def __init__(self, physical_network, cpu_price=0.50, bw_price=0.20):
        self.network = physical_network
        self.cpu_price = cpu_price
        self.bw_price = bw_price

    def check_and_evaluate(self, vnr, strategy, resources):

        mapping = strategy["mapping"]

        cpu = resources["cpu"]
        bw = resources["bw"]

        revenue = calculate_revenue(vnr)

        # -------------------------------------------------
        # 1. CPU FEASIBILITY
        # -------------------------------------------------

        node_used = {}

        for virtual_node, required_cpu in vnr["nodes"].items():

            physical_node = mapping[virtual_node]

            if physical_node not in cpu:
                return {
                    "feasible": False,
                    "reason": f"Unknown physical node {physical_node}",
                    "mapping": mapping,
                    "paths": {},
                    "utility": None,
                    "revenue": revenue,
                    "total_cost": None,
                }

            node_used[physical_node] = (
                node_used.get(physical_node, 0)
                + required_cpu
            )

            if node_used[physical_node] > cpu[physical_node]:

                return {
                    "feasible": False,
                    "reason":
                        f"CPU violation at {physical_node}: "
                        f"required {node_used[physical_node]} "
                        f"> available {cpu[physical_node]}",
                    "mapping": mapping,
                    "paths": {},
                    "utility": None,
                    "revenue": revenue,
                    "total_cost": None,
                }

        # -------------------------------------------------
        # 2. BANDWIDTH FEASIBILITY + DIJKSTRA
        # -------------------------------------------------

        # Temporary copy.
        # We don't modify the real network until
        # the strategy is finally selected.
        temp_bw = deepcopy(bw)

        paths = {}

        for (virtual_u, virtual_v), required_bw in vnr["links"].items():

            source = mapping[virtual_u]
            target = mapping[virtual_v]

            # Find shortest path having enough bandwidth.
            path = shortest_feasible_path(
                temp_bw,
                source,
                target,
                required_bw
            )

            if path is None:

                return {
                    "feasible": False,
                    "reason":
                        f"No BW-feasible path for "
                        f"{virtual_u}-{virtual_v} "
                        f"requiring {required_bw}",
                    "mapping": mapping,
                    "paths": {},
                    "utility": None,
                    "revenue": revenue,
                    "total_cost": None,
                }

            paths[(virtual_u, virtual_v)] = path

            # Temporarily reserve bandwidth.
            for a, b in zip(path, path[1:]):

                key = edge_key(a, b)

                temp_bw[key] -= required_bw

                if temp_bw[key] < 0:

                    return {
                        "feasible": False,
                        "reason":
                            f"Bandwidth violation on {a}-{b}",
                        "mapping": mapping,
                        "paths": paths,
                        "utility": None,
                        "revenue": revenue,
                        "total_cost": None,
                    }

        # -------------------------------------------------
        # 3. CALCULATE COST
        # -------------------------------------------------

        total_cost, cpu_cost, bw_cost = calculate_cost(
            vnr,
            paths,
            self.cpu_price,
            self.bw_price
        )

        # -------------------------------------------------
        # 4. CALCULATE UTILITY
        # -------------------------------------------------

        utility = calculate_utility(
            revenue,
            total_cost
        )

        return {
            "feasible": True,
            "reason": "Feasible",

            "mapping": mapping,

            "paths": paths,

            "utility": utility,

            "revenue": revenue,

            "total_cost": total_cost,

            "cpu_cost": cpu_cost,

            "bw_cost": bw_cost,

            "resulting_bw": temp_bw,

            "cpu_used": node_used,
        }

    # -----------------------------------------------------
    # BEST RESPONSE
    # -----------------------------------------------------

    def best_response(self, vnr, resources):

        # Get physical node names automatically.
        physical_nodes = list(resources["cpu"].keys())

        candidates = get_candidate_strategies(
        vnr,
        physical_nodes
        )

        evaluations = []

        for strategy in candidates:

            result = self.check_and_evaluate(
                vnr,
                strategy,
                resources
            )

            result["strategy"] = strategy["name"]

            evaluations.append(result)

        # Keep only feasible strategies.
        feasible = [
            x for x in evaluations
            if x["feasible"]
        ]

        # No feasible strategy.
        if not feasible:
            return None, evaluations

        # Highest utility = best response.
        best = max(
            feasible,
            key=lambda x: x["utility"]
        )

        return best, evaluations

    # -----------------------------------------------------
    # PLAY LOWER-LEVEL GAME
    # -----------------------------------------------------

    def play(self, vnrs):

        resources = self.network.copy_resources()

        all_strategy_rows = []

        accepted_rows = []

        # Larger CPU request acts first.
        ordered = sorted(
            vnrs,
            key=lambda v: sum(v["nodes"].values()),
            reverse=True
        )

        for vnr in ordered:

            best, evaluations = self.best_response(
                vnr,
                resources
            )

            # ---------------------------------------------
            # Store every evaluated strategy
            # ---------------------------------------------

            for e in evaluations:

                mapping_text = " | ".join(
                    f"{k}->{v}"
                    for k, v in e["mapping"].items()
                )

                paths_text = " | ".join(
                    f"{u}-{v}:{'->'.join(path)}"
                    for (u, v), path
                    in e["paths"].items()
                )

                if best and e["strategy"] == best["strategy"]:
                    decision = "SELECTED"

                elif not e["feasible"]:
                    decision = "REJECTED"

                else:
                    decision = "NOT SELECTED"

                all_strategy_rows.append({

                    "VNR": vnr["id"],

                    "Strategy": e["strategy"],

                    "Feasible":
                        "YES" if e["feasible"] else "NO",

                    "Decision": decision,

                    "Mapping": mapping_text,

                    "Paths": paths_text,

                    "Revenue": e["revenue"],

                    "CPU_Cost": e.get("cpu_cost"),

                    "BW_Cost": e.get("bw_cost"),

                    "Total_Cost": e.get("total_cost"),

                    "Utility": e.get("utility"),

                    "Reason": e["reason"],
                })

            # ---------------------------------------------
            # If no feasible mapping
            # ---------------------------------------------

            if best is None:

                accepted_rows.append({

                    "VNR": vnr["id"],

                    "Accepted": "NO",

                    "Revenue": 0,

                    "Cost": 0,

                    "Utility": 0,

                    "Mapping": "",

                    "Paths": "",
                })

                continue

            # ---------------------------------------------
            # RESERVE CPU
            # ---------------------------------------------

            resources["cpu"] = dict(
                resources["cpu"]
            )

            for physical, used in best["cpu_used"].items():

                resources["cpu"][physical] -= used

            # ---------------------------------------------
            # RESERVE BANDWIDTH
            # ---------------------------------------------

            resources["bw"] = dict(
                best["resulting_bw"]
            )

            # ---------------------------------------------
            # STORE ACCEPTED VNR
            # ---------------------------------------------

            mapping_text = " | ".join(
                f"{k}->{v}"
                for k, v in best["mapping"].items()
            )

            paths_text = " | ".join(
                f"{u}-{v}:{'->'.join(path)}"
                for (u, v), path
                in best["paths"].items()
            )

            accepted_rows.append({

                "VNR": vnr["id"],

                "Accepted": "YES",

                "Revenue": best["revenue"],

                "Cost": best["total_cost"],

                "Utility": best["utility"],

                "Mapping": mapping_text,

                "Paths": paths_text,
            })

        return {

            "resources": resources,

            "strategies": all_strategy_rows,

            "accepted": accepted_rows,

            "ordered_vnrs":
                [v["id"] for v in ordered],
        }