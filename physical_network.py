class PhysicalNetwork:
    """Physical data-center network: node CPU and undirected link bandwidth."""

    def __init__(self, nodes, links):
        self.nodes = dict(nodes)
        self.links = {(min(u, v), max(u, v)): bw for (u, v), bw in links.items()}

    @staticmethod
    def from_default():
        nodes = {
            "A": 8, "B": 15, "C": 18,
            "D": 13, "E": 11, "F": 8,"G":10
        }
        links = {
            ("A", "B"): 10,
            ("A", "E"): 12,
            ("B", "C"): 16,
            ("C", "D"): 18,
            ("D", "G"): 15,
            ("G", "F"): 20,
            ("F", "E"): 13,
            
        }
        return PhysicalNetwork(nodes, links)

    def copy_resources(self):
        return {
            "cpu": dict(self.nodes),
            "bw": dict(self.links),
        }
