from datetime import datetime


def _fmt(value):
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _format_mapping(mapping):
    if not mapping:
        return "None"

    return "\n".join(
        f"VNode {virtual_node} -> Physical Node {physical_node}"
        for virtual_node, physical_node
        in mapping.items()
    )


def _format_virtual_nodes(nodes):
    if not nodes:
        return "None"

    return "\n".join(
        f"VNode {node} : CPU = {float(cpu):.4f}"
        for node, cpu in nodes.items()
    )


def _format_virtual_links(links):
    if not links:
        return "None"

    lines = []

    for link, bandwidth in links.items():
        if isinstance(link, str) and "->" in link:
            u, v = link.split("->", 1)
        else:
            u, v = link

        lines.append(
            f"VNode {u} -> VNode {v} : "
            f"B/W = {float(bandwidth):.4f}"
        )

    return "\n".join(lines)


def _format_paths(paths, virtual_links=None):
    if not paths:
        return "None"

    lines = []

    virtual_links = virtual_links or {}

    for link, path in paths.items():
        if isinstance(link, str) and "->" in link:
            u, v = link.split("->", 1)
        else:
            u, v = link

        required_bw = virtual_links.get(
            f"{u}->{v}",
            virtual_links.get(
                (u, v),
                0
            )
        )

        path_text = " -> ".join(
            str(node)
            for node in path
        )

        hops = max(
            len(path) - 1,
            0
        )

        lines.append(
            f"VNode {u} -> VNode {v}\n"
            f"Required B/W : {float(required_bw):.4f}\n"
            f"Physical Path : {path_text}\n"
            f"Hops          : {hops}"
        )

    return "\n".join(lines)


def _format_resources(resources):
    if not resources:
        return "None"

    return "\n".join(
        f"{key} : {float(value):.4f}"
        for key, value in resources.items()
    )


def build_log_content(
    cpu_price,
    bw_price,
    physical_networks,
    ordered_vnrs,
    strategy_rows,
    accepted_rows,
    resource_history,
    summary,
    de_objective,
    nash_iterations=None
):
    lines = []

    lines.append("=" * 80)
    lines.append("TWO-LEVEL VNE EXECUTION LOG")
    lines.append("=" * 80)
    lines.append(
        f"DATE/TIME : "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    lines.append("")
    lines.append(
        f"CPU PRICE : {float(cpu_price):.6f}"
    )
    lines.append(
        f"B/W PRICE : {float(bw_price):.6f}"
    )
    lines.append("")
    lines.append(
        f"NUMBER OF PHYSICAL NETWORKS : "
        f"{len(physical_networks)}"
    )
    lines.append(
        f"NUMBER OF VNRS              : "
        f"{len(ordered_vnrs)}"
    )
    lines.append(
        "LOWER LEVEL : NON-COOPERATIVE GAME"
    )
    lines.append(
        "UPPER LEVEL : DIFFERENTIAL EVOLUTION"
    )
    lines.append("=" * 80)

    # ----------------------------------------------------------
    # VNR PROCESSING ORDER
    # ----------------------------------------------------------

    lines.append("")
    lines.append("VNR PROCESSING ORDER")
    lines.append("=" * 80)

    for order, vnr in enumerate(
        ordered_vnrs,
        start=1
    ):
        display_vnr = vnr.get(
            "display_id",
            f"VNR{order}"
        )

        cpu = sum(
            vnr.get("nodes", {}).values()
        )
        bw = sum(
            vnr.get("links", {}).values()
        )

        lines.append(
            f"{order}. {display_vnr}"
        )
        lines.append(
            f"   Original ID : {vnr.get('id', '')}"
        )
        lines.append(
            f"   CPU Demand  : {float(cpu):.4f}"
        )
        lines.append(
            f"   B/W Demand  : {float(bw):.4f}"
        )
        lines.append(
            f"   Nodes       : "
            f"{len(vnr.get('nodes', {}))}"
        )
        lines.append(
            f"   Links       : "
            f"{len(vnr.get('links', {}))}"
        )
        lines.append("")

    # ----------------------------------------------------------
    # DETAILED PER-VNR RESULTS
    # ----------------------------------------------------------

    history_by_vnr = {
        row.get("Display_VNR"): row
        for row in resource_history
    }

    for order, vnr in enumerate(
        ordered_vnrs,
        start=1
    ):
        display_vnr = vnr.get(
            "display_id",
            f"VNR{order}"
        )

        row = history_by_vnr.get(
            display_vnr,
            {}
        )

        lines.append("")
        lines.append("=" * 80)
        lines.append(f"{display_vnr} DETAILS")
        lines.append("=" * 80)

        lines.append(
            f"ORIGINAL ID : {vnr.get('id', '')}"
        )
        lines.append(
            f"CPU DEMAND  : "
            f"{float(row.get('CPU_Demand', sum(vnr.get('nodes', {}).values()))):.4f}"
        )
        lines.append(
            f"B/W DEMAND  : "
            f"{float(row.get('BW_Demand', sum(vnr.get('links', {}).values()))):.4f}"
        )

        lines.append("")
        lines.append("VIRTUAL NODES")
        lines.append("-" * 40)
        lines.append(
            _format_virtual_nodes(
                row.get(
                    "Virtual_Nodes",
                    vnr.get("nodes", {})
                )
            )
        )

        lines.append("")
        lines.append("VIRTUAL LINKS")
        lines.append("-" * 40)
        lines.append(
            _format_virtual_links(
                row.get(
                    "Virtual_Links",
                    vnr.get("links", {})
                )
            )
        )

        lines.append("")
        lines.append(
            f"SELECTED PHYSICAL NETWORK : "
            f"{row.get('Network', 'NONE')}"
        )
        lines.append(
            f"SELECTED STRATEGY          : "
            f"{row.get('Strategy', '')}"
        )

        lines.append("")
        lines.append("VIRTUAL NODE MAPPING")
        lines.append("-" * 40)
        lines.append(
            _format_mapping(
                row.get(
                    "Mapping",
                    {}
                )
            )
        )

        lines.append("")
        lines.append("VIRTUAL LINK MAPPING")
        lines.append("-" * 40)
        lines.append(
            _format_paths(
                row.get(
                    "Paths",
                    {}
                ),
                row.get(
                    "Virtual_Links",
                    {}
                )
            )
        )

        lines.append("")
        lines.append("PHYSICAL CPU BEFORE")
        lines.append("-" * 40)
        lines.append(
            _format_resources(
                row.get(
                    "CPU_Before",
                    {}
                )
            )
        )

        lines.append("")
        lines.append("PHYSICAL B/W BEFORE")
        lines.append("-" * 40)
        lines.append(
            _format_resources(
                row.get(
                    "BW_Before",
                    {}
                )
            )
        )

        lines.append("")
        lines.append("PHYSICAL CPU AFTER")
        lines.append("-" * 40)
        lines.append(
            _format_resources(
                row.get(
                    "CPU_After",
                    {}
                )
            )
        )

        lines.append("")
        lines.append("PHYSICAL B/W AFTER")
        lines.append("-" * 40)
        lines.append(
            _format_resources(
                row.get(
                    "BW_After",
                    {}
                )
            )
        )

        lines.append("")
        lines.append("RESOURCE CONSUMPTION")
        lines.append("-" * 40)
        lines.append(
            f"CPU Consumed : "
            f"{float(row.get('CPU_Consumed', 0)):.4f}"
        )
        lines.append(
            f"B/W Consumed : "
            f"{float(row.get('BW_Consumed', 0)):.4f}"
        )
        lines.append(
            f"CPU Price    : "
            f"{float(cpu_price):.6f}"
        )
        lines.append(
            f"B/W Price    : "
            f"{float(bw_price):.6f}"
        )
        lines.append(
            f"CPU Cost     : "
            f"{float(row.get('CPU_Cost', 0)):.4f}"
        )
        lines.append(
            f"B/W Cost     : "
            f"{float(row.get('BW_Cost', 0)):.4f}"
        )
        lines.append(
            f"Total Cost   : "
            f"{float(row.get('Cost', 0)):.4f}"
        )
        lines.append(
            f"Revenue      : "
            f"{float(row.get('Revenue', 0)):.4f}"
        )
        lines.append(
            f"Utility      : "
            f"{float(row.get('Utility', 0)):.4f}"
        )

        lines.append("")
        lines.append(
            f"STATUS : {row.get('Status', 'UNKNOWN')}"
        )
        lines.append(
            f"REASON : {row.get('Reason', '')}"
        )

    # ----------------------------------------------------------
    # NASH INFORMATION
    # ----------------------------------------------------------

    lines.append("")
    lines.append("=" * 80)
    lines.append("NASH GAME INFORMATION")
    lines.append("=" * 80)
    lines.append(
        f"Nash Iterations : "
        f"{nash_iterations if nash_iterations is not None else 'N/A'}"
    )

    # ----------------------------------------------------------
    # FINAL RESULTS
    # ----------------------------------------------------------

    lines.append("")
    lines.append("=" * 80)
    lines.append("FINAL RESULTS")
    lines.append("=" * 80)

    for key, value in summary.items():
        lines.append(
            f"{str(key).upper()} : {value}"
        )

    lines.append("")
    lines.append("SELECTED NETWORKS")
    lines.append("-" * 40)

    for row in accepted_rows:
        lines.append(
            f"{row.get('VNR', '')} -> "
            f"{row.get('Network', 'NONE')} | "
            f"Strategy: {row.get('Strategy', '')}"
        )

    # ----------------------------------------------------------
    # STRATEGY SUMMARY
    # ----------------------------------------------------------

    lines.append("")
    lines.append("=" * 80)
    lines.append("SELECTED STRATEGY SUMMARY")
    lines.append("=" * 80)

    for row in strategy_rows:
        lines.append(
            f"{row.get('VNR', '')} | "
            f"Network: {row.get('Network', 'NONE')} | "
            f"Strategy: {row.get('Strategy', '')} | "
            f"Utility: {row.get('Utility', 0)}"
        )

    # ----------------------------------------------------------
    # DIFFERENTIAL EVOLUTION
    # ----------------------------------------------------------

    lines.append("")
    lines.append("=" * 80)
    lines.append("DIFFERENTIAL EVOLUTION")
    lines.append("=" * 80)
    lines.append(
        f"BEST CPU PRICE : {float(cpu_price):.6f}"
    )
    lines.append(
        f"BEST B/W PRICE : {float(bw_price):.6f}"
    )
    lines.append(
        f"DE OBJECTIVE   : {de_objective}"
    )

    lines.append("")
    lines.append("=" * 80)

    return "\n".join(lines)


def write_execution_log(
    filename,
    cpu_price,
    bw_price,
    physical_networks,
    ordered_vnrs,
    strategy_rows,
    accepted_rows,
    resource_history,
    summary,
    de_objective,
    nash_iterations=None
):
    content = build_log_content(
        cpu_price,
        bw_price,
        physical_networks,
        ordered_vnrs,
        strategy_rows,
        accepted_rows,
        resource_history,
        summary,
        de_objective,
        nash_iterations
    )

    with open(
        filename,
        "a",
        encoding="utf-8"
    ) as file:
        file.write("\n\n")
        file.write(content)
        file.write("\n")


def write_current_run_log(
    filename,
    cpu_price,
    bw_price,
    physical_networks,
    ordered_vnrs,
    strategy_rows,
    accepted_rows,
    resource_history,
    summary,
    de_objective,
    nash_iterations=None
):
    content = build_log_content(
        cpu_price,
        bw_price,
        physical_networks,
        ordered_vnrs,
        strategy_rows,
        accepted_rows,
        resource_history,
        summary,
        de_objective,
        nash_iterations
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(content)
        file.write("\n")
