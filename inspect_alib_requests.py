from alib_converter import load_alib_pickle, get_scenario

pickle_file = r"D:\minwith log\input\senario_RedBestel.pickle"
alib_root = r"D:\mini project resources\P3_ALIB_MASTER\P3_ALIB_MASTER"

data = load_alib_pickle(pickle_file, alib_root)

print("Data type:", type(data))

scenario = get_scenario(data, 0)

print("\nScenario type:", type(scenario))
print("Scenario attributes:")
print(vars(scenario).keys())

print("\nRequests:")
requests = getattr(scenario, "requests", None)

print("Requests type:", type(requests))

if requests is not None:
    print("Number of requests:", len(requests))

    for i, request in enumerate(requests[:3]):
        print("\n--- REQUEST", i, "---")
        print("Type:", type(request))

        if hasattr(request, "__dict__"):
            print(vars(request))

        else:
            print(request)