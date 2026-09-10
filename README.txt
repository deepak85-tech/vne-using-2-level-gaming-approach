TWO-LEVEL VNE PROJECT

This version automatically generates virtual-node to physical-node mappings.
You do not need to manually write mappings in candidate_strategies.py.

IMPORTANT FILES
- main.py: starts the experiment and sets CPU/BW prices.
- vnr_data.py: defines VNR input data.
- physical_network.py: defines physical nodes and physical links.
- candidate_strategies.py: automatically generates one-to-one mappings.
- game.py: checks CPU, uses Dijkstra for bandwidth-feasible paths, calculates cost and utility, and selects the best feasible mapping.
- dijkstra.py: shortest-path search with bandwidth feasibility.
- utility.py: revenue, cost, and utility calculations.
- differential_evolution.py: upper-level price search demonstration.
- excel_writer.py: creates Results.xlsx including a beginner-friendly Logs sheet.
- logger.py: writes the same explanation to Execution_Log.txt.

OUTPUTS
1. Results.xlsx
   - Summary
   - VNR_Strategies
   - VNR_Results
   - Resources
   - Upper_Level_DE
   - Logs

2. Execution_Log.txt
   A human-readable explanation of the run, including:
   - VNR processing order
   - number of generated mappings
   - selected virtual-to-physical mapping
   - Dijkstra physical paths
   - CPU/BW/total cost
   - utility
   - resource updates
   - rejection reasons

CURRENT WORKED INPUT
CPU price = 1.0
BW price = 0.7

The current VNR and physical network are the latest project example. VNR1 asks for a virtual link with BW 23, while the largest physical link currently has BW 20, so VNR1 is expected to be rejected under the current bandwidth-feasibility rule.

RUN
python main.py
