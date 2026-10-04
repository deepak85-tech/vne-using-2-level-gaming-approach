# Two-Level VNE Project

**Efficient Resource Allocation for Online Virtual Network Requests Using a Two-Level Gaming Approach**

A game-theoretic Virtual Network Embedding (VNE) framework that maps Virtual Network Requests (VNRs) onto multiple Physical Networks (PNs).

- **Upper level:** Differential Evolution (DE) finds the best CPU and Bandwidth prices.
- **Lower level:** VNRs play a non-cooperative game to pick their embedding strategy.

---

## Architecture

```mermaid
flowchart TD
    A["ALIB / VNR Generation"] --> B["Physical Network Pool<br/>PN1 ... PNn"]
    B --> C["NORD-style Node Ranking"]
    C --> D["Candidate Strategy Generation"]

    subgraph UPPER["UPPER LEVEL"]
        E["Differential Evolution"] --> F["CPU Price + BW Price"]
    end

    subgraph LOWER["LOWER LEVEL"]
        G["Non-Cooperative VNR Game"] --> H["Node Mapping<br/>(CPU check)"]
        G --> I["Link Mapping<br/>(Dijkstra + BW check)"]
        H --> J["Utility = Revenue - Cost"]
        I --> J
    end

    D --> G
    F --> G
    J --> K{"Utility >= 0 ?"}
    K -- Yes --> L["ACCEPT VNR"]
    K -- No --> M["REJECT VNR"]
    L --> N["Results.xlsx + Logs"]
    M --> N
    N -. "objective feedback" .-> E
```

---

## Key Concepts

| Concept | Description |
|---|---|
| Physical Network (PN) | Nodes with CPU capacity, links with bandwidth capacity |
| VNR | Virtual nodes (CPU demand) and virtual links (BW demand) |
| NORD-style ranking | Ranks physical nodes by CPU, degree, betweenness, eigenvector centrality |
| Strategy | One complete virtual-to-physical node mapping (S1, S2, ...) |
| Dijkstra | Shortest path using only links with enough residual BW |
| Utility | `Revenue - Cost` (Cost = CPU cost + BW cost) |
| Acceptance | Accept if feasible and `Utility >= 0`, else reject |
| Pricing | DE searches `[CPU Price, BW Price]` |

> Note: Ranking is NORD-style, not the full Entropy + TOPSIS NORD algorithm.

---

## Constraints

```text
Available CPU >= Required CPU        (per virtual node)
Available BW  >= Required BW         (every link on the path)
```

A VNR is rejected when no feasible mapping/path exists or all strategies give negative utility.

---

## Project Files

| File | Purpose |
|---|---|
| `main.py` | Entry point: generates VNRs/PNs, runs DE + game, writes results |
| `vnr_data.py` | VNR definitions |
| `physical_network.py` | Physical network class and pool |
| `candidate_strategies.py` | Auto-generates node-mapping strategies |
| `nord_ranking.py` | Physical node ranking |
| `dijkstra.py` | Bandwidth-feasible shortest path |
| `game.py` | Lower-level non-cooperative game |
| `utility.py` | Revenue, cost, utility |
| `differential_evolution.py` | Upper-level price optimisation |
| `excel_writer.py` | Creates `Results.xlsx` |
| `logger.py` | Creates execution logs |
| `alib_converter.py` | ALIB substrate to PhysicalNetwork |
| `alib_vnr_converter.py` | ALIB requests to VNR format |

---

## Run

```bash
python main.py          # default run
python main.py 10       # process 10 VNRs
```

Measure runtime (PowerShell):

```powershell
Measure-Command { python main.py 10 }
```

Stop a run: `Ctrl + C`

---

## Outputs

| File | Contents |
|---|---|
| `Results.xlsx` | Summary, VNR_Strategies, VNR_Results, Resources, Upper_Level_DE, Logs |
| `Execution_Log.txt` | Detailed log of all runs (history kept) |
| `Current_Run_Log.txt` | Detailed log of latest run only |

Console output: best CPU/BW price, revenue, cost, revenue/cost ratio, accepted/rejected VNRs, acceptance ratio, Nash iterations.

---

## Requirements

- Python 3.x
- NetworkX, NumPy, Pandas, OpenPyXL
- ALIB package (for ALIB features)

---

