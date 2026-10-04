from alib_vnr_converter import convert_alib_requests


pickle_file = (
    r"D:\minwith log\input\senario_RedBestel.pickle"
)

alib_root = (
    r"D:\mini project resources\P3_ALIB_MASTER\P3_ALIB_MASTER"
)


vnrs = convert_alib_requests(
    pickle_file,
    alib_root,
    scenario_index=0
)


print("Number of VNRs:", len(vnrs))

for vnr in vnrs:

    print("\n-------------------------")
    print("VNR:", vnr["id"])

    print(
        "Virtual nodes:",
        len(vnr["nodes"])
    )

    print(
        "Virtual links:",
        len(vnr["links"])
    )

    print(
        "CPU demand:",
        sum(vnr["nodes"].values())
    )

    print(
        "BW demand:",
        sum(vnr["links"].values())
    )

    print(
        "Nodes:",
        vnr["nodes"]
    )

    print(
        "First links:",
        list(vnr["links"].items())[:5]
    )