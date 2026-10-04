import networkx as nx


class PhysicalNetwork:

    def __init__(self, nodes, links, name="PN"):

        if isinstance(nodes, dict):
            self.nodes = {
                node: float(cpu)
                for node, cpu in nodes.items()
            }
        else:
            self.nodes = {
                node: float(cpu)
                for node, cpu in nodes
            }

        self.links = {}

        if isinstance(links, dict):

            for key, bw in links.items():
                u, v = key
                self.links[
                    self.edge_key(u, v)
                ] = float(bw)

        else:

            for u, v, bw in links:
                self.links[
                    self.edge_key(u, v)
                ] = float(bw)

        self.name = name

        self.original_nodes = dict(self.nodes)
        self.original_links = dict(self.links)

    # =========================================================
    # EDGE KEY
    # =========================================================

    @staticmethod
    def edge_key(u, v):
        return tuple(sorted((u, v)))

    # =========================================================
    # CLONE
    # =========================================================

    def clone(self, name=None):

        return PhysicalNetwork(
            nodes=dict(self.nodes),
            links=[
                (u, v, bw)
                for (u, v), bw in self.links.items()
            ],
            name=name if name is not None else self.name
        )

    # =========================================================
    # COPY RESOURCES
    # =========================================================

    def copy_resources(self):

        return {
            "cpu": dict(self.nodes),
            "bw": dict(self.links)
        }

    # =========================================================
    # RESET
    # =========================================================

    def reset(self):

        self.nodes = dict(self.original_nodes)
        self.links = dict(self.original_links)

    # =========================================================
    # DEFAULT NETWORK
    # =========================================================

    @staticmethod
    def from_default():

        nodes = [
            ("A", 8),
            ("B", 15),
            ("C", 18),
            ("D", 13),
            ("E", 11),
            ("F", 8),
            ("G", 10)
        ]

        links = [
            ("A", "B", 10),
            ("A", "E", 12),
            ("B", "C", 16),
            ("C", "D", 18),
            ("D", "G", 15),
            ("G", "F", 20),
            ("F", "E", 13)
        ]

        return PhysicalNetwork(
            nodes,
            links,
            name="PN1"
        )

    # =========================================================
    # ALIB NETWORK
    # =========================================================

    @staticmethod
    def from_alib(
        pickle_file,
        alib_root,
        scenario_index=0,
        name="PN1"
    ):

        from alib_converter import convert_alib_substrate

        nodes, links = convert_alib_substrate(
            pickle_file,
            alib_root,
            scenario_index
        )

        return PhysicalNetwork(
            nodes,
            links,
            name=name
        )

    # =========================================================
    # NETWORKX
    # =========================================================

    def to_networkx(self):

        graph = nx.Graph()

        for node in self.nodes:
            graph.add_node(node)

        for (u, v), bandwidth in self.links.items():

            graph.add_edge(
                u,
                v,
                bandwidth=bandwidth
            )

        return graph

    # =========================================================
    # REMOVE EDGES SAFELY
    # =========================================================

    def remove_edges_safely(
        self,
        number_to_remove,
        offset=0
    ):

        if number_to_remove <= 0:
            return

        graph = self.to_networkx()

        edges = sorted(
            graph.edges(),
            key=lambda edge: (
                str(edge[0]),
                str(edge[1])
            )
        )

        if not edges:
            return

        offset %= len(edges)

        edges = (
            edges[offset:]
            + edges[:offset]
        )

        removed = 0

        for u, v in edges:

            if removed >= number_to_remove:
                break

            if not graph.has_edge(u, v):
                continue

            # Temporarily remove edge.
            graph.remove_edge(u, v)

            # Keep only connected variants.
            if nx.is_connected(graph):

                key = self.edge_key(u, v)

                if key in self.links:
                    del self.links[key]

                removed += 1

            else:

                # Restore edge.
                graph.add_edge(
                    u,
                    v,
                    bandwidth=self.original_links.get(
                        self.edge_key(u, v),
                        100.0
                    )
                )

    # =========================================================
    # CREATE NETWORK POOL
    # =========================================================

    @staticmethod
    def create_network_pool(
        base_network,
        number_of_networks=10
    ):

        if number_of_networks <= 0:
            raise ValueError(
                "number_of_networks must be greater than 0"
            )

        networks = []

        # PN1 = original substrate.
        networks.append(
            base_network.clone("PN1")
        )

        for i in range(
            2,
            number_of_networks + 1
        ):

            network = base_network.clone(
                f"PN{i}"
            )

            # Create different topology variants.
            remove_count = (
                1 + ((i - 2) % 3)
            )

            network.remove_edges_safely(
                number_to_remove=remove_count,
                offset=i - 2
            )

            networks.append(network)

        return networks

    # =========================================================
    # SUMMARY
    # =========================================================

    def summary(self):

        return {
            "name": self.name,
            "nodes": len(self.nodes),
            "links": len(self.links),
            "cpu": sum(self.nodes.values()),
            "bandwidth": sum(self.links.values())
        }

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(self):

        return (
            f"PhysicalNetwork("
            f"name={self.name}, "
            f"nodes={len(self.nodes)}, "
            f"links={len(self.links)})"
        )