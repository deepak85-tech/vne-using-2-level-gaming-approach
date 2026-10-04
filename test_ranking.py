from physical_network import PhysicalNetwork
from nord_ranking import rank_physical_nodes


network = PhysicalNetwork.from_default()

ranked_nodes = rank_physical_nodes(network)

print("\nNORD-style physical node ranking:")
print("=" * 50)

for i, node in enumerate(ranked_nodes, start=1):
    print(i, node)