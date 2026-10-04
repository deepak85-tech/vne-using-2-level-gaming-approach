from candidate_strategies import get_candidate_strategies
from dijkstra import shortest_feasible_path
from utility import (
    calculate_revenue,
    calculate_cost,
    calculate_utility
)


class LowerLevelGame:

    def __init__(
        self,
        physical_networks,
        cpu_price=1.0,
        bw_price=0.7,
        max_iterations=20,
        max_strategies=200
    ):
        """
        physical_networks:
            List of PhysicalNetwork objects.

        Example:
            [PN1, PN2, ..., PN10]
        """

        # ------------------------------------------------------
        # Backward compatibility
        # ------------------------------------------------------

        if not isinstance(
            physical_networks,
            list
        ):
            physical_networks = [
                physical_networks
            ]

        self.networks = physical_networks

        self.cpu_price = cpu_price
        self.bw_price = bw_price

        self.max_iterations = max_iterations
        self.max_strategies = max_strategies

        # VNR allocation state
        #
        # {
        #     vnr_id: {
        #         "network_index": 0,
        #         "allocation": {...}
        #     }
        # }
        self.allocations = {}

    # ==========================================================
    # VNR NORMALIZATION
    # ==========================================================

    @staticmethod
    def normalize_vnr(vnr):

        # ------------------------------------------------------
        # Nodes
        # ------------------------------------------------------

        if isinstance(
            vnr.get("nodes"),
            dict
        ):
            nodes = dict(
                vnr["nodes"]
            )

        else:
            nodes = {
                node_id: cpu
                for node_id, cpu
                in vnr.get("nodes", [])
            }

        # ------------------------------------------------------
        # Links
        # ------------------------------------------------------

        links = {}

        raw_links = vnr.get(
            "links",
            {}
        )

        if isinstance(
            raw_links,
            dict
        ):

            for key, bandwidth in raw_links.items():

                u, v = key

                links[
                    tuple(
                        sorted(
                            (u, v)
                        )
                    )
                ] = bandwidth

        else:

            for link in raw_links:

                if len(link) < 3:
                    continue

                u = link[0]
                v = link[1]
                bandwidth = link[2]

                links[
                    tuple(
                        sorted(
                            (u, v)
                        )
                    )
                ] = bandwidth

        result = {
            "id": vnr.get(
                "id",
                "VNR"
            ),
            "nodes": nodes,
            "links": links
        }

        if "allowed_nodes" in vnr:
            result[
                "allowed_nodes"
            ] = vnr[
                "allowed_nodes"
            ]

        return result

    # ==========================================================
    # EDGE KEY
    # ==========================================================

    @staticmethod
    def edge_key(u, v):

        return tuple(
            sorted(
                (u, v)
            )
        )

    # ==========================================================
    # APPLY ALLOCATION
    # ==========================================================

    def _apply_allocation(
        self,
        network,
        allocation
    ):
        """
        Permanently consume resources on one selected
        physical network.
        """

        if allocation is None:
            return False

        # ------------------------------------------------------
        # CPU
        # ------------------------------------------------------

        cpu_used = allocation.get(
            "cpu_used",
            {}
        )

        for physical_node, demand in cpu_used.items():

            if physical_node not in network.nodes:
                return False

            if network.nodes[
                physical_node
            ] < demand:

                return False

        # ------------------------------------------------------
        # BW
        # ------------------------------------------------------

        link_demands = allocation.get(
            "link_demands",
            {}
        )

        for physical_link, demand in link_demands.items():

            key = self.edge_key(
                physical_link[0],
                physical_link[1]
            )

            if key not in network.links:
                return False

            if network.links[key] < demand:
                return False

        # ------------------------------------------------------
        # Actually consume
        # ------------------------------------------------------

        for physical_node, demand in cpu_used.items():

            network.nodes[
                physical_node
            ] -= demand

        for physical_link, demand in link_demands.items():

            key = self.edge_key(
                physical_link[0],
                physical_link[1]
            )

            network.links[
                key
            ] -= demand

        return True

    # ==========================================================
    # RELEASE ALLOCATION
    # ==========================================================

    def _release_allocation(
        self,
        network,
        allocation
    ):
        """
        Return resources previously consumed by a VNR.
        """

        if allocation is None:
            return

        # CPU
        for physical_node, demand in allocation.get(
            "cpu_used",
            {}
        ).items():

            network.nodes[
                physical_node
            ] += demand

            original = network.original_nodes.get(
                physical_node
            )

            if original is not None:
                network.nodes[
                    physical_node
                ] = min(
                    network.nodes[
                        physical_node
                    ],
                    original
                )

        # BW
        for physical_link, demand in allocation.get(
            "link_demands",
            {}
        ).items():

            key = self.edge_key(
                physical_link[0],
                physical_link[1]
            )

            if key not in network.links:
                continue

            network.links[
                key
            ] += demand

            original = network.original_links.get(
                key
            )

            if original is not None:
                network.links[
                    key
                ] = min(
                    network.links[
                        key
                    ],
                    original
                )

    # ==========================================================
    # EVALUATE ONE STRATEGY
    # ==========================================================

    def check_and_evaluate(
        self,
        vnr,
        network,
        strategy
    ):
        """
        Check one VNE embedding strategy.

        Important:
        This function does NOT permanently consume resources.

        It returns an allocation object that can later be
        committed using _apply_allocation().
        """

        vnr = self.normalize_vnr(
            vnr
        )

        mapping = strategy.get(
            "mapping",
            {}
        )

        # ------------------------------------------------------
        # Check all virtual nodes mapped
        # ------------------------------------------------------

        if set(mapping.keys()) != set(
            vnr["nodes"].keys()
        ):
            return {
                "accepted": False,
                "reason": "Incomplete node mapping"
            }

        # ------------------------------------------------------
        # CPU feasibility
        # ------------------------------------------------------

        cpu_used = {}

        for virtual_node, demand in vnr[
            "nodes"
        ].items():

            physical_node = mapping.get(
                virtual_node
            )

            if physical_node not in network.nodes:

                return {
                    "accepted": False,
                    "reason": (
                        f"Physical node "
                        f"{physical_node} "
                        f"does not exist"
                    )
                }

            # ALIB allowed-node restriction
            allowed_nodes = vnr.get(
                "allowed_nodes",
                {}
            )

            if allowed_nodes:

                allowed = allowed_nodes.get(
                    virtual_node,
                    []
                )

                allowed = {
                    str(x)
                    for x in allowed
                }

                if str(
                    physical_node
                ) not in allowed:

                    return {
                        "accepted": False,
                        "reason": (
                            f"Node {physical_node} "
                            f"not allowed for "
                            f"VNR node "
                            f"{virtual_node}"
                        )
                    }

            if network.nodes[
                physical_node
            ] < demand:

                return {
                    "accepted": False,
                    "reason": (
                        f"Insufficient CPU "
                        f"on {physical_node}"
                    )
                }

            cpu_used[
                physical_node
            ] = (
                cpu_used.get(
                    physical_node,
                    0
                )
                + demand
            )

        # ------------------------------------------------------
        # Check aggregated CPU
        # ------------------------------------------------------

        for physical_node, demand in cpu_used.items():

            if network.nodes[
                physical_node
            ] < demand:

                return {
                    "accepted": False,
                    "reason": (
                        f"Aggregated CPU "
                        f"capacity exceeded "
                        f"on {physical_node}"
                    )
                }

        # ------------------------------------------------------
        # Virtual link embedding
        # ------------------------------------------------------

        temp_bw = dict(
            network.links
        )

        paths = {}
        link_demands = {}

        # Sort high-bandwidth links first
        virtual_links = sorted(
            vnr["links"].items(),
            key=lambda item: item[1],
            reverse=True
        )

        for (
            virtual_link,
            required_bw
        ) in virtual_links:

            virtual_u, virtual_v = (
                virtual_link
            )

            physical_u = mapping[
                virtual_u
            ]

            physical_v = mapping[
                virtual_v
            ]

            path = shortest_feasible_path(
                temp_bw,
                physical_u,
                physical_v,
                required_bw
            )

            if path is None:

                return {
                    "accepted": False,
                    "reason": (
                        f"No feasible path "
                        f"for virtual link "
                        f"{virtual_u}-"
                        f"{virtual_v}"
                    )
                }

            paths[
                virtual_link
            ] = path

            # Consume bandwidth temporarily
            for a, b in zip(
                path,
                path[1:]
            ):

                key = self.edge_key(
                    a,
                    b
                )

                if key not in temp_bw:
                    return {
                        "accepted": False,
                        "reason": (
                            f"Physical link "
                            f"{key} missing"
                        )
                    }

                temp_bw[
                    key
                ] -= required_bw

                if temp_bw[
                    key
                ] < 0:

                    return {
                        "accepted": False,
                        "reason": (
                            f"Bandwidth exceeded "
                            f"on {key}"
                        )
                    }

                link_demands[
                    key
                ] = (
                    link_demands.get(
                        key,
                        0
                    )
                    + required_bw
                )

        # ------------------------------------------------------
        # Revenue
        # ------------------------------------------------------

        revenue = calculate_revenue(
            vnr
        )

        # ------------------------------------------------------
        # Cost
        # ------------------------------------------------------

        cost, cpu_cost, bw_cost = (
            calculate_cost(
                vnr,
                paths,
                self.cpu_price,
                self.bw_price
            )
        )

        if cost == float("inf"):

            return {
                "accepted": False,
                "reason": "Cost calculation failed"
            }

        # ------------------------------------------------------
        # Utility
        # ------------------------------------------------------

        utility = calculate_utility(
            revenue,
            cost
        )

        # ------------------------------------------------------
        # Allocation object
        # ------------------------------------------------------

        allocation = {
            "cpu_used": dict(
                cpu_used
            ),
            "paths": dict(
                paths
            ),
            "link_demands": dict(
                link_demands
            )
        }

        return {

            "accepted": True,

            "revenue": revenue,

            "cost": cost,

            "cpu_cost": cpu_cost,

            "bw_cost": bw_cost,

            "utility": utility,

            "mapping": dict(
                mapping
            ),

            "paths": dict(
                paths
            ),

            "link_demands": dict(
                link_demands
            ),

            "allocation": allocation,

            "strategy": strategy.get(
                "name",
                "UNKNOWN"
            )
        }

    # ==========================================================
    # FIND BEST RESPONSE ACROSS ALL NETWORKS
    # ==========================================================

    def find_best_response(
        self,
        vnr
    ):
        """
        Test this VNR on EVERY physical network.

        No network is permanently modified here.

        Returns the best feasible result.
        """

        vnr = self.normalize_vnr(
            vnr
        )

        all_results = []

        # ------------------------------------------------------
        # Try PN1 ... PN10
        # ------------------------------------------------------

        for network_index, network in enumerate(
            self.networks
        ):

            strategies = get_candidate_strategies(
                vnr,
                network,
                max_physical_nodes=10,
                max_strategies=self.max_strategies
            )

            network_best = None

            for strategy in strategies:

                evaluation = (
                    self.check_and_evaluate(
                        vnr,
                        network,
                        strategy
                    )
                )

                if not evaluation[
                    "accepted"
                ]:
                    continue

                if (
                    network_best is None
                    or
                    evaluation[
                        "utility"
                    ]
                    >
                    network_best[
                        "utility"
                    ]
                ):
                    network_best = evaluation

            if network_best is not None:

                network_best[
                    "network_index"
                ] = network_index

                network_best[
                    "network_name"
                ] = network.name

                all_results.append(
                    network_best
                )

        # ------------------------------------------------------
        # No feasible network
        # ------------------------------------------------------

        if not all_results:

            return {
                "accepted": False,
                "reason": (
                    "No feasible embedding "
                    "on any physical network"
                ),
                "network_results": []
            }

        # ------------------------------------------------------
        # Select maximum utility
        # ------------------------------------------------------

        best = max(
            all_results,
            key=lambda x: x[
                "utility"
            ]
        )

        best[
            "network_results"
        ] = all_results

        return best

    # ==========================================================
    # COMMIT RESULT
    # ==========================================================

    def commit_result(
        self,
        vnr,
        result
    ):
        """
        Permanently allocate the selected VNR on its selected PN.
        """

        if not result.get(
            "accepted",
            False
        ):
            return False

        network_index = result[
            "network_index"
        ]

        network = self.networks[
            network_index
        ]

        success = self._apply_allocation(
            network,
            result[
                "allocation"
            ]
        )

        if not success:
            return False

        vnr_id = vnr[
            "id"
        ]

        self.allocations[
            vnr_id
        ] = {

            "network_index":
                network_index,

            "network_name":
                network.name,

            "allocation":
                result[
                    "allocation"
                ],

            "result":
                result
        }

        return True

    # ==========================================================
    # RELEASE CURRENT VNR
    # ==========================================================

    def release_vnr(
        self,
        vnr
    ):
        """
        Release current allocation of one VNR.
        """

        vnr_id = vnr[
            "id"
        ]

        current = self.allocations.get(
            vnr_id
        )

        if current is None:
            return

        network_index = current[
            "network_index"
        ]

        network = self.networks[
            network_index
        ]

        self._release_allocation(
            network,
            current[
                "allocation"
            ]
        )

        del self.allocations[
            vnr_id
        ]

    # ==========================================================
    # RESOURCE SNAPSHOT HELPERS FOR DETAILED LOGGING
    # ==========================================================

    @staticmethod
    def _snapshot_selected_resources(network, allocation):
        """
        Snapshot only the physical resources touched by one VNR.

        CPU contains the physical nodes used by the VNR.
        BW contains the physical links used by its virtual-link paths.
        """
        allocation = allocation or {}

        cpu_nodes = set(
            allocation.get("cpu_used", {}).keys()
        )

        bw_links = set()

        for link in allocation.get(
            "link_demands",
            {}
        ).keys():
            bw_links.add(
                tuple(sorted((link[0], link[1])))
            )

        return {
            "CPU": {
                node: float(network.nodes[node])
                for node in sorted(
                    cpu_nodes,
                    key=str
                )
                if node in network.nodes
            },
            "BW": {
                link: float(network.links[link])
                for link in sorted(
                    bw_links,
                    key=lambda x: (
                        str(x[0]),
                        str(x[1])
                    )
                )
                if link in network.links
            }
        }

    def _build_detailed_resource_history(
        self,
        ordered_vnrs
    ):
        """
        Reconstruct the final Nash allocation in processing order and
        capture physical resources immediately before and after each VNR.

        This avoids using the last global snapshot as a substitute for
        per-VNR before/after resources.
        """

        # Start from the original physical resources.
        for network in self.networks:
            network.reset()

        history = []

        for order, vnr in enumerate(
            ordered_vnrs,
            start=1
        ):
            vnr_id = vnr["id"]
            current = self.allocations.get(vnr_id)

            display_vnr = f"VNR{order}"

            cpu_demand = sum(
                vnr["nodes"].values()
            )

            bw_demand = sum(
                vnr["links"].values()
            )

            base_record = {
                "Display_VNR": display_vnr,
                "Original_ID": vnr_id,
                "Processing_Order": order,
                "CPU_Demand": float(cpu_demand),
                "BW_Demand": float(bw_demand),
                "Virtual_Nodes": dict(
                    vnr["nodes"]
                ),
                "Virtual_Links": dict(
                    vnr["links"]
                ),
                "Network": "NONE",
                "Strategy": "",
                "Utility": 0.0,
                "Revenue": 0.0,
                "Cost": 0.0,
                "CPU_Cost": 0.0,
                "BW_Cost": 0.0,
                "Mapping": {},
                "Paths": {},
                "CPU_Before": {},
                "BW_Before": {},
                "CPU_After": {},
                "BW_After": {},
                "CPU_Consumed": 0.0,
                "BW_Consumed": 0.0,
                "Status": "REJECTED",
                "Reason": "No feasible physical network"
            }

            if current is None:
                history.append(base_record)
                continue

            network_index = current["network_index"]
            network = self.networks[network_index]
            result = current["result"]
            allocation = current["allocation"]

            before = self._snapshot_selected_resources(
                network,
                allocation
            )

            # Apply this final allocation so the next VNR sees the
            # resources left by this VNR.
            applied = self._apply_allocation(
                network,
                allocation
            )

            if not applied:
                base_record["Reason"] = (
                    "Final allocation could not be reconstructed"
                )
                history.append(base_record)
                continue

            after = self._snapshot_selected_resources(
                network,
                allocation
            )

            # Convert tuple-key dictionaries into readable string-key
            # dictionaries for TXT/Excel logging.
            mapping = dict(
                result.get("mapping", {})
            )

            paths = dict(
                result.get("paths", {})
            )

            virtual_links = {}

            for (
                virtual_link,
                required_bw
            ) in vnr["links"].items():
                u, v = virtual_link
                virtual_links[
                    f"{u}->{v}"
                ] = float(required_bw)

            readable_paths = {}

            for (
                virtual_link,
                path
            ) in paths.items():
                u, v = virtual_link
                readable_paths[
                    f"{u}->{v}"
                ] = list(path)

            base_record.update({
                "Network": network.name,
                "Strategy": result.get(
                    "strategy",
                    ""
                ),
                "Utility": float(
                    result.get(
                        "utility",
                        0
                    )
                ),
                "Revenue": float(
                    result.get(
                        "revenue",
                        0
                    )
                ),
                "Cost": float(
                    result.get(
                        "cost",
                        0
                    )
                ),
                "CPU_Cost": float(
                    result.get(
                        "cpu_cost",
                        0
                    )
                ),
                "BW_Cost": float(
                    result.get(
                        "bw_cost",
                        0
                    )
                ),
                "Mapping": mapping,
                "Paths": readable_paths,
                "Virtual_Links": virtual_links,
                "CPU_Before": before["CPU"],
                "BW_Before": {
                    f"{u}->{v}": value
                    for (
                        u, v
                    ), value in before["BW"].items()
                },
                "CPU_After": after["CPU"],
                "BW_After": {
                    f"{u}->{v}": value
                    for (
                        u, v
                    ), value in after["BW"].items()
                },
                "CPU_Consumed": sum(
                    allocation.get(
                        "cpu_used",
                        {}
                    ).values()
                ),
                "BW_Consumed": sum(
                    allocation.get(
                        "link_demands",
                        {}
                    ).values()
                ),
                "Status": "ACCEPTED",
                "Reason": "Embedding successfully allocated"
            })

            history.append(base_record)

        # Restore the exact final state expected by the returned result.
        for network in self.networks:
            network.reset()

        for order, vnr in enumerate(
            ordered_vnrs,
            start=1
        ):
            current = self.allocations.get(
                vnr["id"]
            )

            if current is not None:
                self._apply_allocation(
                    self.networks[
                        current["network_index"]
                    ],
                    current["allocation"]
                )

        return history


    # ==========================================================
    # PLAY NASH GAME
    # ==========================================================

    def play(
        self,
        vnrs
    ):
        """
        Multi-network lower-level Nash game.

        For every VNR:

            PN1
            PN2
            ...
            PN10

        are tested.

        The VNR selects the feasible embedding with the
        highest utility.

        Resources are committed ONLY on the selected network.

        Then the process repeats until no VNR changes.
        """

        # ------------------------------------------------------
        # Normalize VNRs
        # ------------------------------------------------------

        vnrs = [
            self.normalize_vnr(vnr)
            for vnr in vnrs
        ]

        # ------------------------------------------------------
        # Processing order
        # ------------------------------------------------------

        ordered_vnrs = sorted(
            vnrs,
            key=lambda v: len(
                v["nodes"]
            ),
            reverse=True
        )

        # Stable display names for logs/results. The original ALIB/VNR
        # identifier is preserved separately as "id".
        for order, vnr in enumerate(
            ordered_vnrs,
            start=1
        ):
            vnr["display_id"] = f"VNR{order}"

        # ------------------------------------------------------
        # Reset all networks
        # ------------------------------------------------------

        for network in self.networks:
            network.reset()

        self.allocations = {}

        logs = []

        resource_history = []

        # ======================================================
        # NASH ITERATIONS
        # ======================================================

        for iteration in range(
            self.max_iterations
        ):

            changed = False

            for vnr in ordered_vnrs:

                vnr_id = vnr[
                    "id"
                ]

                old = self.allocations.get(
                    vnr_id
                )

                # --------------------------------------------------
                # Temporarily release current allocation
                # --------------------------------------------------

                old_network_index = None

                old_result = None

                if old is not None:

                    old_network_index = old[
                        "network_index"
                    ]

                    old_result = old[
                        "result"
                    ]

                    self._release_allocation(
                        self.networks[
                            old_network_index
                        ],
                        old[
                            "allocation"
                        ]
                    )

                    del self.allocations[
                        vnr_id
                    ]

                # --------------------------------------------------
                # Find best network + mapping
                # --------------------------------------------------

                best = self.find_best_response(
                    vnr
                )

                # --------------------------------------------------
                # No feasible mapping
                # --------------------------------------------------

                if not best.get(
                    "accepted",
                    False
                ):

                    # Restore previous allocation
                    if old is not None:

                        self._apply_allocation(
                            self.networks[
                                old_network_index
                            ],
                            old[
                                "allocation"
                            ]
                        )

                        self.allocations[
                            vnr_id
                        ] = old

                    logs.append({
                        "Iteration":
                            iteration + 1,

                        "VNR":
                            vnr_id,

                        "Network":
                            "NONE",

                        "Decision":
                            "REJECTED",

                        "Reason":
                            best.get(
                                "reason",
                                "No feasible network"
                            )
                    })

                    continue

                # --------------------------------------------------
                # Decide whether to change
                # --------------------------------------------------

                new_utility = best[
                    "utility"
                ]

                old_utility = (
                    old_result[
                        "utility"
                    ]
                    if old_result
                    is not None
                    else None
                )

                should_change = False

                # First allocation
                if old is None:
                    should_change = True

                # Strict utility improvement
                elif new_utility > (
                    old_utility + 1e-9
                ):
                    should_change = True

                # Same utility but no old allocation
                elif old is None:
                    should_change = True

                # --------------------------------------------------
                # Apply selected allocation
                # --------------------------------------------------

                if should_change:

                    success = self.commit_result(
                        vnr,
                        best
                    )

                    if success:

                        changed = True

                        logs.append({

                            "Iteration":
                                iteration + 1,

                            "VNR":
                                vnr_id,

                            "Network":
                                best[
                                    "network_name"
                                ],

                            "Decision":
                                "UPDATED",

                            "Utility":
                                round(
                                    new_utility,
                                    4
                                ),

                            "Cost":
                                round(
                                    best[
                                        "cost"
                                    ],
                                    4
                                )
                        })

                    else:

                        # Restore old allocation
                        if old is not None:

                            self._apply_allocation(
                                self.networks[
                                    old_network_index
                                ],
                                old[
                                    "allocation"
                                ]
                            )

                            self.allocations[
                                vnr_id
                            ] = old

                else:

                    # Restore old allocation
                    if old is not None:

                        self._apply_allocation(
                            self.networks[
                                old_network_index
                            ],
                            old[
                                "allocation"
                            ]
                        )

                        self.allocations[
                            vnr_id
                        ] = old

                    logs.append({

                        "Iteration":
                            iteration + 1,

                        "VNR":
                            vnr_id,

                        "Network":
                            (
                                old[
                                    "network_name"
                                ]
                                if old
                                else "NONE"
                            ),

                        "Decision":
                            "NO_CHANGE",

                        "Utility":
                            (
                                round(
                                    old_utility,
                                    4
                                )
                                if old_utility
                                is not None
                                else 0
                            )
                    })

            # ------------------------------------------------------
            # Nash stopping condition
            # ------------------------------------------------------

            if not changed:
                break

        # ======================================================
        # FINAL RESULTS
        # ======================================================

        accepted = []
        strategies = []

        # ------------------------------------------------------
        # VNR result rows
        # ------------------------------------------------------

        for vnr in ordered_vnrs:

            vnr_id = vnr[
                "id"
            ]

            current = self.allocations.get(
                vnr_id
            )

            if current is None:

                accepted.append({

                    "VNR":
                        vnr["display_id"],

                    "Original_ID":
                        vnr_id,

                    "Accepted":
                        "NO",

                    "Network":
                        "NONE",

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

                    "Reason":
                        "No feasible physical network"
                })

                continue

            result = current[
                "result"
            ]

            mapping_text = " | ".join(
                f"{v}->{p}"
                for v, p
                in result[
                    "mapping"
                ].items()
            )

            path_text = " | ".join(

                f"{u}-{v}:"
                + "->".join(
                    path
                )

                for (
                    u, v
                ), path

                in result[
                    "paths"
                ].items()
            )

            accepted.append({

                "VNR":
                    vnr["display_id"],

                "Original_ID":
                    vnr_id,

                "Accepted":
                    "YES",

                "Network":
                    result[
                        "network_name"
                    ],

                "Revenue":
                    round(
                        result[
                            "revenue"
                        ],
                        4
                    ),

                "Cost":
                    round(
                        result[
                            "cost"
                        ],
                        4
                    ),

                "Utility":
                    round(
                        result[
                            "utility"
                        ],
                        4
                    ),

                "Mapping":
                    mapping_text,

                "Paths":
                    path_text,

                "Strategy":
                    result.get(
                        "strategy",
                        ""
                    )
            })

            strategies.append({

                "VNR":
                    vnr["display_id"],

                "Original_ID":
                    vnr_id,

                "Network":
                    result[
                        "network_name"
                    ],

                "Strategy":
                    result.get(
                        "strategy",
                        ""
                    ),

                "Mapping":
                    mapping_text,

                "Paths":
                    path_text,

                "Utility":
                    round(
                        result[
                            "utility"
                        ],
                        4
                    ),

                "Revenue":
                    round(
                        result[
                            "revenue"
                        ],
                        4
                    ),

                "Cost":
                    round(
                        result[
                            "cost"
                        ],
                        4
                    )
            })

        # ======================================================
        # DETAILED PER-VNR RESOURCE HISTORY
        # ======================================================

        resource_history = (
            self._build_detailed_resource_history(
                ordered_vnrs
            )
        )

        # Keep the final physical-network resource snapshot as a
        # separate result so existing callers can still inspect the
        # final state of every physical network.
        final_resource_snapshot = []

        for network in self.networks:

            final_resource_snapshot.append({

                "Network":
                    network.name,

                "CPU":
                    dict(
                        network.nodes
                    ),

                "BW":
                    dict(
                        network.links
                    )
            })

        # ======================================================
        # RETURN
        # ======================================================

        return {

            "ordered_vnrs":
                ordered_vnrs,

            "strategies":
                strategies,

            "accepted":
                accepted,

            "resources":
                self._combined_resources(),

            "resource_history":
                resource_history,

            "final_resource_snapshot":
                final_resource_snapshot,

            "logs":
                logs,

            "iterations":
                iteration + 1
        }

    # ==========================================================
    # COMBINED RESOURCES
    # ==========================================================

    def _combined_resources(self):

        cpu = {}
        bw = {}

        for network in self.networks:

            for node, value in network.nodes.items():

                cpu[
                    f"{network.name}:{node}"
                ] = value

            for link, value in network.links.items():

                bw[
                    (
                        network.name,
                        link
                    )
                ] = value

        return {
            "cpu": cpu,
            "bw": bw
        }