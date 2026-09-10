def get_vnrs():
    """Exactly the two VNRs used in the project example."""
    return [
        {
            "id": "VNR2",
            "nodes": {"VN2(1)": 8, "VN2(2)": 9, "VN2(3)": 10,"VN2(4)":12,"VN2(5)":11},
            "links": {
                ("VN2(1)", "VN2(2)"): 10,
                ("VN2(1)", "VN2(4)"): 9,
                ("VN2(2)", "VN2(3)"): 11,
                ("VN2(3)", "VN2(5)"): 12,
                ("VN2(5)", "VN2(4)"): 4,
            },
        },
        {
            "id": "VNR1",
            "nodes": {"VN1": 11, "VN2": 18},
            "links": {
                ("VN1", "VN2"): 23,
            },
        },
    ]
