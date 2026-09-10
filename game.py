from copy import deepcopy
from collections import Counter

from dijkstra import edge_key, shortest_feasible_path
from utility import calculate_revenue, calculate_cost, calculate_utility
from candidate_strategies import get_candidate_strategies


class LowerLevelGame:

    def __init__(
        self,
        physical_network,
        cpu_price=0.50,
        bw_price=0.20
    ):
        self.network = physical_network
        self.cpu_price = cpu_price
        self.bw_price = bw_price

    @staticmethod
    def normalize_vnr(vnr):

        return {
            "id": vnr["id"],

            "nodes": dict(
                vnr["nodes"]
            ),

            "links": {
                (u, v): bw
                for u, v, bw in vnr["links"]
            }
        }

    def check_and_evaluate(
        self,
        vnr,
        strategy,
        resources
    ):

        mapping = strategy["mapping"]

        cpu = resources["cpu"]
        bw = resources["bw"]

        revenue = calculate_revenue(vnr)

        node_used = {}

        for virtual_node, required_cpu in vnr["nodes"].items():

            physical_node = mapping[
                virtual_node
            ]

            if physical_node not in cpu:

                return {
                    "feasible": False,
                    "reason":
                        f"Unknown physical node "
                        f"{physical_node}",
                    "mapping": mapping,
                    "paths": {},
                    "utility": None,
                    "revenue": revenue,
                    "total_cost": None,
                }

            node_used[
                physical_node
            ] = (
                node_used.get(
                    physical_node,
                    0
                )
                + required_cpu
            )

            if (
                node_used[physical_node]
                > cpu[physical_node]
            ):

                return {
                    "feasible": False,
                    "reason":
                        f"CPU violation at "
                        f"{physical_node}: "
                        f"required "
                        f"{node_used[physical_node]} > "
                        f"available "
                        f"{cpu[physical_node]}",
                    "mapping": mapping,
                    "paths": {},
                    "utility": None,
                    "revenue": revenue,
                    "total_cost": None,
                }

        temp_bw = deepcopy(bw)

        paths = {}

        for (
            virtual_u,
            virtual_v
        ), required_bw in vnr["links"].items():

            source = mapping[
                virtual_u
            ]

            target = mapping[
                virtual_v
            ]

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
                        f"No BW-feasible path "
                        f"for {virtual_u}-{virtual_v} "
                        f"requiring "
                        f"{required_bw} BW",
                    "mapping": mapping,
                    "paths": {},
                    "utility": None,
                    "revenue": revenue,
                    "total_cost": None,
                }

            paths[
                (virtual_u, virtual_v)
            ] = path

            for a, b in zip(
                path,
                path[1:]
            ):

                key = edge_key(
                    a,
                    b
                )

                temp_bw[key] -= required_bw

                if temp_bw[key] < 0:

                    return {
                        "feasible": False,
                        "reason":
                            f"Bandwidth violation "
                            f"on {a}-{b}",
                        "mapping": mapping,
                        "paths": paths,
                        "utility": None,
                        "revenue": revenue,
                        "total_cost": None,
                    }

        total_cost, cpu_cost, bw_cost = calculate_cost(
            vnr,
            paths,
            self.cpu_price,
            self.bw_price
        )

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

    def best_response(
        self,
        vnr,
        resources
    ):

        physical_nodes = list(
            resources["cpu"].keys()
        )

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

            evaluations.append(
                result
            )

        feasible = [
            x
            for x in evaluations
            if x["feasible"]
        ]

        if not feasible:

            return None, evaluations

        best = max(
            feasible,
            key=lambda x: x["utility"]
        )

        return best, evaluations

    @staticmethod
    def _mapping_text(mapping):

        return " | ".join(
            f"{k}->{v}"
            for k, v in mapping.items()
        )

    @staticmethod
    def _paths_text(paths):

        return " | ".join(
            f"{u}-{v}:"
            f"{'->'.join(path)}"
            f" ({len(path) - 1} hop(s))"
            for (u, v), path
            in paths.items()
        )

    def play(self, vnrs):

        resources = self.network.copy_resources()

        all_strategy_rows = []

        accepted_rows = []

        log_lines = []

        resource_history = []

        vnrs = [
            self.normalize_vnr(vnr)
            for vnr in vnrs
        ]

        # ======================================================
        # ORDER VNRs BY CPU + BANDWIDTH
        # ======================================================

        ordered = sorted(
            vnrs,
            key=lambda v: (
                sum(v["nodes"].values())
                +
                sum(v["links"].values())
            ),
            reverse=True
        )

        log_lines.append(
            "=" * 78
        )

        log_lines.append(
            "TWO-LEVEL VNE LOWER-LEVEL DECISION LOG"
        )

        log_lines.append(
            "=" * 78
        )

        log_lines.append("")

        log_lines.append(
            f"CPU price = {self.cpu_price} | "
            f"BW price = {self.bw_price}"
        )

        log_lines.append("")

        log_lines.append(
            "PROCESSING ORDER"
        )

        log_lines.append(
            "VNRs are processed from higher "
            "CPU + BW demand to lower demand."
        )

        log_lines.append("")

        for index, vnr in enumerate(
            ordered,
            start=1
        ):

            cpu_request = sum(
                vnr["nodes"].values()
            )

            bw_request = sum(
                vnr["links"].values()
            )

            total_request = (
                cpu_request
                + bw_request
            )

            log_lines.append(
                f"{index}. {vnr['id']} -> "
                f"CPU={cpu_request}, "
                f"BW={bw_request}, "
                f"CPU+BW={total_request}"
            )

        log_lines.append("")

        # ======================================================
        # PROCESS EACH VNR
        # ======================================================

        for vnr in ordered:

            # ----------------------------------------------
            # SAVE RESOURCES BEFORE THIS VNR
            # ----------------------------------------------

            vnr_resources_before = {
                "cpu": dict(
                    resources["cpu"]
                ),
                "bw": dict(
                    resources["bw"]
                )
            }

            best, evaluations = self.best_response(
                vnr,
                resources
            )

            cpu_request = sum(
                vnr["nodes"].values()
            )

            bw_request = sum(
                vnr["links"].values()
            )

            total_request = (
                cpu_request
                + bw_request
            )

            revenue = calculate_revenue(
                vnr
            )

            feasible = [
                e
                for e in evaluations
                if e["feasible"]
            ]

            infeasible = [
                e
                for e in evaluations
                if not e["feasible"]
            ]

            log_lines.append(
                "-" * 78
            )

            log_lines.append(
                f"VNR: {vnr['id']}"
            )

            log_lines.append(
                f"CPU requested: {cpu_request}"
            )

            log_lines.append(
                f"BW requested: {bw_request}"
            )

            log_lines.append(
                f"CPU + BW: {total_request}"
            )

            log_lines.append(
                f"Revenue: {revenue}"
            )

            log_lines.append(
                f"Candidate mappings generated: "
                f"{len(evaluations)}"
            )

            log_lines.append(
                f"Feasible mappings: "
                f"{len(feasible)}"
            )

            log_lines.append(
                f"Rejected mappings: "
                f"{len(infeasible)}"
            )

            # ----------------------------------------------
            # REJECTED
            # ----------------------------------------------

            if best is None:

                reason_counts = Counter(
                    e["reason"]
                    for e in infeasible
                )

                log_lines.append("")

                log_lines.append(
                    "DECISION: REJECTED"
                )

                log_lines.append(
                    "Reason: No complete feasible "
                    "embedding was found."
                )

                if reason_counts:

                    log_lines.append(
                        "Rejection reasons:"
                    )

                    for reason, count in (
                        reason_counts.most_common()
                    ):

                        log_lines.append(
                            f"  - {count} candidate(s): "
                            f"{reason}"
                        )

                vnr_resources_after = {
                    "cpu": dict(
                        resources["cpu"]
                    ),
                    "bw": dict(
                        resources["bw"]
                    )
                }

                resource_history.append({
                    "VNR": vnr["id"],
                    "before": vnr_resources_before,
                    "after": vnr_resources_after
                })

                log_lines.append("")

            # ----------------------------------------------
            # ACCEPTED
            # ----------------------------------------------

            else:

                log_lines.append("")

                log_lines.append(
                    "DECISION: ACCEPTED"
                )

                log_lines.append(
                    f"Selected strategy: "
                    f"{best['strategy']}"
                )

                log_lines.append(
                    "FINAL ACCEPTED MAPPING: "
                    f"{self._mapping_text(best['mapping'])}"
                )

                log_lines.append(
                    "Physical paths: "
                    f"{self._paths_text(best['paths'])}"
                )

                log_lines.append(
                    f"Revenue: "
                    f"{best['revenue']}"
                )

                log_lines.append(
                    f"CPU cost: "
                    f"{best['cpu_cost']}"
                )

                log_lines.append(
                    f"BW cost: "
                    f"{best['bw_cost']}"
                )

                log_lines.append(
                    f"Total cost: "
                    f"{best['total_cost']}"
                )

                log_lines.append(
                    f"Utility: "
                    f"{best['utility']}"
                )

                # ------------------------------------------
                # SAME UTILITY MAPPINGS
                # ------------------------------------------

                same_utility = []

                for evaluation in feasible:

                    if evaluation["utility"] is None:
                        continue

                    if round(
                        float(evaluation["utility"]),
                        8
                    ) == round(
                        float(best["utility"]),
                        8
                    ):

                        same_utility.append(
                            evaluation
                        )

                if len(same_utility) > 1:

                    log_lines.append("")

                    log_lines.append(
                        "MAPPINGS WITH SAME UTILITY:"
                    )

                    for number, evaluation in enumerate(
                        same_utility,
                        start=1
                    ):

                        log_lines.append(
                            f"{number}. "
                            f"{self._mapping_text(evaluation['mapping'])}"
                        )

                    log_lines.append(
                        f"Same utility value: "
                        f"{best['utility']}"
                    )

                # ------------------------------------------
                # UPDATE CPU
                # ------------------------------------------

                resources["cpu"] = dict(
                    resources["cpu"]
                )

                for physical, used in (
                    best["cpu_used"].items()
                ):

                    resources["cpu"][physical] -= used

                # ------------------------------------------
                # UPDATE BW
                # ------------------------------------------

                resources["bw"] = dict(
                    best["resulting_bw"]
                )

                # ------------------------------------------
                # SAVE RESOURCES AFTER THIS VNR
                # ------------------------------------------

                vnr_resources_after = {
                    "cpu": dict(
                        resources["cpu"]
                    ),
                    "bw": dict(
                        resources["bw"]
                    )
                }

                resource_history.append({
                    "VNR": vnr["id"],
                    "before": vnr_resources_before,
                    "after": vnr_resources_after
                })

                log_lines.append("")

            # ==================================================
            # STRATEGY ROWS
            # ==================================================

            for e in evaluations:

                decision = "REJECTED"

                if (
                    best
                    and e is best
                ):
                    decision = "SELECTED"

                elif e["feasible"]:
                    decision = "NOT SELECTED"

                all_strategy_rows.append({

                    "VNR":
                        vnr["id"],

                    "CPU_Demand":
                        cpu_request,

                    "BW_Demand":
                        bw_request,

                    "Total_Demand":
                        total_request,

                    "Strategy":
                        e["strategy"],

                    "Feasible":
                        "YES"
                        if e["feasible"]
                        else "NO",

                    "Decision":
                        decision,

                    "Mapping":
                        self._mapping_text(
                            e["mapping"]
                        ),

                    "Paths":
                        self._paths_text(
                            e["paths"]
                        )
                        if e["paths"]
                        else "",

                    "Revenue":
                        e["revenue"],

                    "CPU_Cost":
                        e.get("cpu_cost"),

                    "BW_Cost":
                        e.get("bw_cost"),

                    "Total_Cost":
                        e.get("total_cost"),

                    "Utility":
                        e.get("utility"),

                    "Reason":
                        e["reason"],
                })

            # ==================================================
            # ACCEPTED ROW
            # ==================================================

            if best is None:

                accepted_rows.append({

                    "VNR":
                        vnr["id"],

                    "Accepted":
                        "NO",

                    "Revenue":
                        0,

                    "Cost":
                        0,

                    "Utility":
                        0,

                    "Mapping":
                        "",

                    "Paths":
                        "",
                })

            else:

                accepted_rows.append({

                    "VNR":
                        vnr["id"],

                    "Accepted":
                        "YES",

                    "Revenue":
                        best["revenue"],

                    "Cost":
                        best["total_cost"],

                    "Utility":
                        best["utility"],

                    "Mapping":
                        self._mapping_text(
                            best["mapping"]
                        ),

                    "Paths":
                        self._paths_text(
                            best["paths"]
                        ),
                })

        # ======================================================
        # FINAL LOG
        # ======================================================

        log_lines.append(
            "-" * 78
        )

        log_lines.append(
            "FINAL REMAINING RESOURCES"
        )

        log_lines.append(
            "CPU: "
            + ", ".join(
                f"{node}={value}"
                for node, value
                in resources["cpu"].items()
            )
        )

        log_lines.append(
            "BW: "
            + ", ".join(
                f"{u}-{v}={value}"
                for (u, v), value
                in resources["bw"].items()
            )
        )

        log_lines.append("")

        return {

            "resources":
                resources,

            "strategies":
                all_strategy_rows,

            "accepted":
                accepted_rows,

            "ordered_vnrs":
                [
                    v["id"]
                    for v in ordered
                ],

            "logs":
                log_lines,

            "resource_history":
                resource_history,
        }