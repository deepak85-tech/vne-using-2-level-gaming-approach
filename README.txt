TWO-LEVEL VNE GAME PROJECT
==========================

Files
-----
main.py
    Main program. Runs the fixed-price worked example, runs the upper-level
    Differential Evolution demonstration, and writes Results.xlsx.

physical_network.py
    Contains the single physical network input:
    A=10, B=23, C=19, D=16, E=33, F=12 CPU.
    Links:
    A-B=15, A-D=8, B-C=9, B-E=18, B-F=12,
    C-F=8, E-F=30, D-E=19 BW.

vnr_data.py
    Contains exactly VNR2 and VNR1.

candidate_strategies.py
    Contains three demonstration strategies per VNR:
    selected, rejected, and feasible-but-lower-utility.

dijkstra.py
    Shortest feasible path using unit hop count. Bandwidth is checked as
    a constraint.

utility.py
    Revenue, price-based resource cost, and utility.

game.py
    Lower-level non-cooperative VNR game. Each VNR evaluates its candidate
    strategies and selects the feasible strategy with highest utility.
    Accepted resources are then reserved before the next VNR acts.

differential_evolution.py
    Dependency-free Differential Evolution implementation.

excel_writer.py
    Writes the results into Results.xlsx.

How to run
-----------
1. Put all .py files in one folder.
2. Open terminal/PowerShell in that folder.
3. Run:
       python main.py

No scipy is required.

Fixed prices
------------
CPU price = 0.50
BW price  = 0.20 per BW per physical hop

Important
---------
This is a first-phase implementation matching the agreed worked example.
The candidate strategies are explicitly listed so that the output visibly
contains:
- a selected strategy,
- an infeasible/rejected strategy,
- a feasible but lower-utility strategy.

For a later full implementation, candidate_strategies.py can be replaced
with a general embedding-strategy generator.
