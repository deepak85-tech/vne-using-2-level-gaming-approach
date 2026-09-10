from datetime import datetime


def write_execution_log(
    filename,
    cpu_price,
    bw_price,
    ordered_vnrs,
    strategy_rows,
    accepted_rows,
    resources_before,
    resources_after,
    resource_history=None
):

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "=" * 80 + "\n"
        )

        file.write(
            "TWO-LEVEL VNE EXECUTION LOG\n"
        )

        file.write(
            "=" * 80 + "\n\n"
        )

        file.write(
            "Execution time: "
            + datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            + "\n"
        )

        file.write(
            f"CPU Price: {cpu_price}\n"
        )

        file.write(
            f"Bandwidth Price: {bw_price}\n\n"
        )

        # ======================================================
        # PROCESSING ORDER
        # ======================================================

        file.write(
            "=" * 80 + "\n"
        )

        file.write(
            "VNR PROCESSING ORDER\n"
        )

        file.write(
            "=" * 80 + "\n\n"
        )

        file.write(
            "Rule: CPU + BW demand, highest to lowest\n\n"
        )

        for number, vnr in enumerate(
            ordered_vnrs,
            start=1
        ):

            rows = [
                row
                for row in strategy_rows
                if row.get("VNR") == vnr
            ]

            if rows:

                cpu = rows[0].get(
                    "CPU_Demand",
                    0
                )

                bw = rows[0].get(
                    "BW_Demand",
                    0
                )

                total = rows[0].get(
                    "Total_Demand",
                    cpu + bw
                )

            else:

                cpu = 0
                bw = 0
                total = 0

            file.write(
                f"{number}. {vnr}\n"
            )

            file.write(
                f"   CPU Demand : {cpu}\n"
            )

            file.write(
                f"   BW Demand  : {bw}\n"
            )

            file.write(
                f"   CPU + BW   : {total}\n\n"
            )

        # ======================================================
        # EACH VNR
        # ======================================================

        for vnr in ordered_vnrs:

            file.write(
                "=" * 80 + "\n"
            )

            file.write(
                f"VNR: {vnr}\n"
            )

            file.write(
                "=" * 80 + "\n\n"
            )

            rows = [
                row
                for row in strategy_rows
                if row.get("VNR") == vnr
            ]

            # --------------------------------------------------
            # DEMAND
            # --------------------------------------------------

            if rows:

                cpu_demand = rows[0].get(
                    "CPU_Demand",
                    0
                )

                bw_demand = rows[0].get(
                    "BW_Demand",
                    0
                )

                total_demand = rows[0].get(
                    "Total_Demand",
                    cpu_demand + bw_demand
                )

            else:

                cpu_demand = 0
                bw_demand = 0
                total_demand = 0

            file.write(
                "RESOURCE DEMAND\n"
            )

            file.write(
                "-" * 45 + "\n"
            )

            file.write(
                f"CPU Demand : {cpu_demand}\n"
            )

            file.write(
                f"BW Demand  : {bw_demand}\n"
            )

            file.write(
                f"CPU + BW   : {total_demand}\n\n"
            )

            # --------------------------------------------------
            # MAPPING COUNTS
            # --------------------------------------------------

            generated = len(rows)

            feasible = sum(
                row.get("Feasible") == "YES"
                for row in rows
            )

            rejected = sum(
                row.get("Feasible") == "NO"
                for row in rows
            )

            file.write(
                "MAPPING STATISTICS\n"
            )

            file.write(
                "-" * 45 + "\n"
            )

            file.write(
                f"Mappings Generated : {generated}\n"
            )

            file.write(
                f"Mappings Feasible  : {feasible}\n"
            )

            file.write(
                f"Mappings Rejected  : {rejected}\n\n"
            )

            # --------------------------------------------------
            # FINAL ACCEPTED MAPPING
            # --------------------------------------------------

            selected = next(
                (
                    row
                    for row in rows
                    if row.get("Decision")
                    == "SELECTED"
                ),
                None
            )

            if selected:

                file.write(
                    "FINAL ACCEPTED MAPPING\n"
                )

                file.write(
                    "-" * 45 + "\n"
                )

                file.write(
                    f"Mapping: "
                    f"{selected.get('Mapping', 'N/A')}\n"
                )

                if selected.get("Paths"):

                    file.write(
                        f"Physical Paths: "
                        f"{selected.get('Paths')}\n"
                    )

                file.write(
                    f"Revenue: "
                    f"{selected.get('Revenue', 0)}\n"
                )

                file.write(
                    f"CPU Cost: "
                    f"{selected.get('CPU_Cost', 0)}\n"
                )

                file.write(
                    f"Bandwidth Cost: "
                    f"{selected.get('BW_Cost', 0)}\n"
                )

                file.write(
                    f"Total Cost: "
                    f"{selected.get('Total_Cost', 0)}\n"
                )

                file.write(
                    f"Utility: "
                    f"{selected.get('Utility', 0)}\n"
                )

                file.write(
                    "Decision: ACCEPTED\n\n"
                )

                # ------------------------------------------
                # SAME UTILITY
                # ------------------------------------------

                selected_utility = (
                    selected.get("Utility")
                )

                same_utility = []

                for row in rows:

                    if (
                        row.get("Feasible")
                        != "YES"
                    ):
                        continue

                    utility = row.get(
                        "Utility"
                    )

                    if utility is None:
                        continue

                    try:

                        if round(
                            float(utility),
                            8
                        ) == round(
                            float(
                                selected_utility
                            ),
                            8
                        ):

                            same_utility.append(
                                row
                            )

                    except (
                        TypeError,
                        ValueError
                    ):

                        pass

                if len(same_utility) > 1:

                    file.write(
                        "MAPPINGS WITH SAME UTILITY\n"
                    )

                    file.write(
                        "-" * 45 + "\n"
                    )

                    file.write(
                        f"Utility: "
                        f"{selected_utility}\n"
                    )

                    for number, row in enumerate(
                        same_utility,
                        start=1
                    ):

                        file.write(
                            f"{number}. "
                            f"{row.get('Mapping', 'N/A')}\n"
                        )

                    file.write("\n")

            # --------------------------------------------------
            # REJECTED VNR
            # --------------------------------------------------

            else:

                file.write(
                    "FINAL DECISION\n"
                )

                file.write(
                    "-" * 45 + "\n"
                )

                file.write(
                    "Decision: REJECTED\n"
                )

                reasons = []

                for row in rows:

                    if (
                        row.get("Feasible")
                        == "NO"
                    ):

                        reason = row.get(
                            "Reason",
                            "No feasible mapping"
                        )

                        if reason not in reasons:

                            reasons.append(
                                reason
                            )

                if reasons:

                    file.write(
                        "Rejection Reason:\n"
                    )

                    for reason in reasons:

                        file.write(
                            f"- {reason}\n"
                        )

                else:

                    file.write(
                        "Rejection Reason: "
                        "No feasible complete "
                        "embedding was found.\n"
                    )

                file.write("\n")

            # ==================================================
            # RESOURCES FOR THIS VNR
            # ==================================================

            history = None

            if resource_history:

                history = next(
                    (
                        item
                        for item in resource_history
                        if item["VNR"] == vnr
                    ),
                    None
                )

            if history:

                before = history["before"]
                after = history["after"]

            else:

                before = resources_before
                after = resources_after

            # --------------------------------------------------
            # CPU BEFORE
            # --------------------------------------------------

            file.write(
                "CPU BEFORE MAPPING\n"
            )

            file.write(
                "-" * 45 + "\n"
            )

            for node, value in (
                before["cpu"].items()
            ):

                file.write(
                    f"{node}: {value}\n"
                )

            file.write("\n")

            # --------------------------------------------------
            # BW BEFORE
            # --------------------------------------------------

            file.write(
                "BANDWIDTH BEFORE MAPPING\n"
            )

            file.write(
                "-" * 45 + "\n"
            )

            for link, value in (
                before["bw"].items()
            ):

                file.write(
                    f"{link[0]}-{link[1]}: "
                    f"{value}\n"
                )

            file.write("\n")

            # --------------------------------------------------
            # CPU AFTER
            # --------------------------------------------------

            file.write(
                "CPU AFTER MAPPING\n"
            )

            file.write(
                "-" * 45 + "\n"
            )

            for node, value in (
                after["cpu"].items()
            ):

                old_value = (
                    before["cpu"][node]
                )

                file.write(
                    f"{node}: "
                    f"Before={old_value}, "
                    f"After={value}, "
                    f"Consumed="
                    f"{old_value - value}\n"
                )

            file.write("\n")

            # --------------------------------------------------
            # BW AFTER
            # --------------------------------------------------

            file.write(
                "BANDWIDTH AFTER MAPPING\n"
            )

            file.write(
                "-" * 45 + "\n"
            )

            for link, value in (
                after["bw"].items()
            ):

                old_value = (
                    before["bw"][link]
                )

                file.write(
                    f"{link[0]}-{link[1]}: "
                    f"Before={old_value}, "
                    f"After={value}, "
                    f"Consumed="
                    f"{old_value - value}\n"
                )

            file.write("\n")

        # ======================================================
        # FINAL REMAINING RESOURCES
        # ======================================================

        file.write(
            "=" * 80 + "\n"
        )

        file.write(
            "FINAL REMAINING RESOURCES\n"
        )

        file.write(
            "=" * 80 + "\n\n"
        )

        file.write("CPU:\n")

        for node, value in (
            resources_after["cpu"].items()
        ):

            file.write(
                f"{node}: {value}\n"
            )

        file.write("\n")

        file.write("Bandwidth:\n")

        for link, value in (
            resources_after["bw"].items()
        ):

            file.write(
                f"{link[0]}-{link[1]}: "
                f"{value}\n"
            )

        file.write("\n")

        total_cpu = sum(
            resources_after["cpu"].values()
        )

        total_bw = sum(
            resources_after["bw"].values()
        )

        file.write(
            f"Total Remaining CPU: "
            f"{total_cpu}\n"
        )

        file.write(
            f"Total Remaining BW: "
            f"{total_bw}\n"
        )

        file.write("\n")

        file.write(
            "=" * 80 + "\n"
        )

        file.write(
            "END OF EXECUTION LOG\n"
        )

        file.write(
            "=" * 80 + "\n"
        )