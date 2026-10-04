from alib_vnr_converter import convert_alib_requests
from physical_network import PhysicalNetwork
from candidate_strategies import get_candidate_strategies


pickle_file = (
    r"D:\minwith log\input\senario_RedBestel.pickle"
)

alib_root = (
    r"D:\mini project resources\P3_ALIB_MASTER\P3_ALIB_MASTER"
)


network = PhysicalNetwork.from_alib(
    pickle_file,
    alib_root,
    scenario_index=0
)

vnrs = convert_alib_requests(
    pickle_file,
    alib_root,
    scenario_index=0
)


for vnr in vnrs:

    strategies = get_candidate_strategies(
    vnr,
    network,
    max_physical_nodes=10
    )

    print(
        vnr["id"],
        "->",
        len(strategies),
        "candidate mappings"
    )