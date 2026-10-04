def calculate_revenue(vnr):
    """
    VNR revenue based on requested CPU and bandwidth.
    """

    cpu_revenue = sum(
        vnr["nodes"].values()
    )

    bw_revenue = sum(
        vnr["links"].values()
    )

    return cpu_revenue + bw_revenue


def calculate_cost(
    vnr,
    paths,
    cpu_price,
    bw_price
):

    cpu_demand = sum(
        vnr["nodes"].values()
    )

    cpu_cost = (
        cpu_demand
        * cpu_price
    )

    bw_cost = 0.0

    for (
        virtual_link,
        required_bw
    ) in vnr["links"].items():

        path = paths.get(
            virtual_link
        )

        if path is None:

            return (
                float("inf"),
                float("inf"),
                float("inf")
            )

        hop_count = len(path) - 1

        bw_cost += (
            required_bw
            * hop_count
            * bw_price
        )

    total_cost = (
        cpu_cost
        + bw_cost
    )

    return (
        total_cost,
        cpu_cost,
        bw_cost
    )


def calculate_utility(
    revenue,
    total_cost
):

    if total_cost == float("inf"):
        return float("-inf")

    return revenue - total_cost