from openpyxl import Workbook


SUMMARY_HEADERS = [
    "experiment",
    "vnr_count",
    "algorithm",
    "revenue",
    "total_cost",
    "revenuetocostratio",
    "accepted",
    "rejected",
    "total_request",
    "embeddingratio",
    "pre_resource",
    "post_resource",
    "consumed",
    "avg_bw",
    "avg_crb",
    "avg_link",
    "No_of_Links_used",
    "avg_node",
    "No_of_Nodes_used",
    "avg_path",
    "avg_exec",
    "total_nodes",
    "total_links",
    "physical_networks",
    "nash_iterations"
]


def safe_excel_value(value):

    if isinstance(
        value,
        (dict, list, tuple, set)
    ):
        return str(value)

    return value


def append_rows(
    worksheet,
    rows
):

    if not rows:
        return

    headers = []

    for row in rows:

        for key in row.keys():

            if key not in headers:
                headers.append(key)

    worksheet.append(headers)

    for row in rows:

        worksheet.append([
            safe_excel_value(
                row.get(
                    header,
                    ""
                )
            )
            for header in headers
        ])


def format_sheet(worksheet):

    worksheet.freeze_panes = "A2"

    for cell in worksheet[1]:
        cell.font = cell.font.copy(
            bold=True
        )

    for column in worksheet.columns:

        max_length = 0

        for cell in column:

            value = cell.value

            if value is not None:

                max_length = max(
                    max_length,
                    len(str(value))
                )

        worksheet.column_dimensions[
            column[0].column_letter
        ].width = min(
            max_length + 2,
            40
        )


def write_results(
    filename,
    summary_rows,
    strategy_rows,
    accepted_rows,
    resource_rows,
    pricing_rows,
    log_lines=None
):

    workbook = Workbook()

    # =========================================================
    # SUMMARY
    # =========================================================

    ws = workbook.active
    ws.title = "Summary"

    ws.append(
        SUMMARY_HEADERS
    )

    for row in summary_rows:

        ws.append([
            safe_excel_value(
                row.get(
                    header,
                    ""
                )
            )
            for header in SUMMARY_HEADERS
        ])

    # =========================================================
    # EXPERIMENT SUMMARY (compact view)
    # =========================================================

    ws_exp = workbook.create_sheet(
        "Experiment_Summary"
    )

    experiment_headers = [
        "Experiment",
        "VNR_Count",
        "Accepted",
        "Rejected",
        "Total_Request",
        "Embedding_Ratio",
        "Revenue",
        "Total_Cost",
        "Revenue_to_Cost_Ratio",
        "CPU_Price",
        "BW_Price",
        "Nash_Iterations",
        "DE_Objective"
    ]

    ws_exp.append(experiment_headers)

    # Pricing rows are one row per experiment.
    pricing_by_experiment = {
        row.get("Experiment"): row
        for row in pricing_rows
    }

    for row in summary_rows:
        pricing = pricing_by_experiment.get(
            row.get("experiment"),
            {}
        )

        ws_exp.append([
            row.get("experiment", ""),
            row.get("vnr_count", ""),
            row.get("accepted", ""),
            row.get("rejected", ""),
            row.get("total_request", ""),
            row.get("embeddingratio", ""),
            row.get("revenue", ""),
            row.get("total_cost", ""),
            row.get("revenuetocostratio", ""),
            pricing.get("CPU_Price", ""),
            pricing.get("BW_Price", ""),
            row.get("nash_iterations", ""),
            pricing.get("Objective", "")
        ])

    # =========================================================
    # STRATEGIES
    # =========================================================

    ws2 = workbook.create_sheet(
        "VNR_Strategies"
    )

    append_rows(
        ws2,
        strategy_rows
    )

    # =========================================================
    # VNR RESULTS
    # =========================================================

    ws3 = workbook.create_sheet(
        "VNR_Results"
    )

    append_rows(
        ws3,
        accepted_rows
    )

    # =========================================================
    # RESOURCES
    # =========================================================

    ws4 = workbook.create_sheet(
        "Resources"
    )

    append_rows(
        ws4,
        resource_rows
    )

    # =========================================================
    # DE
    # =========================================================

    ws5 = workbook.create_sheet(
        "Upper_Level_DE"
    )

    append_rows(
        ws5,
        pricing_rows
    )

    # =========================================================
    # LOGS
    # =========================================================

    ws6 = workbook.create_sheet(
        "Logs"
    )

    ws6.append([
        "Line",
        "Log Message"
    ])

    for index, message in enumerate(
        log_lines or [],
        start=1
    ):

        ws6.append([
            index,
            safe_excel_value(message)
        ])

    # =========================================================
    # FORMAT
    # =========================================================

    for worksheet in workbook.worksheets:

        if worksheet.max_row > 0:
            format_sheet(
                worksheet
            )

    workbook.save(
        filename
    )