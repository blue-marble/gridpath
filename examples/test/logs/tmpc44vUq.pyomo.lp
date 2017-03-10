\* Source Pyomo model name=unknown *\

min 
Total_Cost:
+1984 Commit_Capacity_MW(Coal_1)
+1984 Commit_Capacity_MW(Coal_2)
+1250 Commit_Capacity_MW(Gas_CCGT_1)
+1250 Commit_Capacity_MW(Gas_CCGT_2)
+400.66666666666663 Commit_Capacity_MW(Gas_CT_1)
+400.66666666666663 Commit_Capacity_MW(Gas_CT_2)
+999999999 LF_Reserves_Down_Violation_MW(Zone1_1)
+999999999 LF_Reserves_Down_Violation_MW(Zone1_2)
+999999999 LF_Reserves_Up_Violation_MW(Zone1_1)
+999999999 LF_Reserves_Up_Violation_MW(Zone1_2)
+99999999 Overgeneration_MW(Zone1_1)
+99999999 Overgeneration_MW(Zone1_2)
+41 Provide_Power_DispCapacityCommit_MW(Coal_1)
+41 Provide_Power_DispCapacityCommit_MW(Coal_2)
+32 Provide_Power_DispCapacityCommit_MW(Gas_CCGT_1)
+32 Provide_Power_DispCapacityCommit_MW(Gas_CCGT_2)
+42 Provide_Power_DispCapacityCommit_MW(Gas_CT_1)
+42 Provide_Power_DispCapacityCommit_MW(Gas_CT_2)
+999999999 Regulation_Down_Violation_MW(Zone1_1)
+999999999 Regulation_Down_Violation_MW(Zone1_2)
+999999999 Regulation_Up_Violation_MW(Zone1_1)
+999999999 Regulation_Up_Violation_MW(Zone1_2)
+1 shutdown_cost_per_mw(Gas_CCGT_1)
+1 shutdown_cost_per_mw(Gas_CCGT_2)
+1 shutdown_cost_per_mw(Gas_CT_1)
+1 shutdown_cost_per_mw(Gas_CT_2)
+1 startup_cost_per_mw(Coal_1)
+1 startup_cost_per_mw(Coal_2)
+1 startup_cost_per_mw(Gas_CCGT_1)
+1 startup_cost_per_mw(Gas_CCGT_2)
+99999999 Unserved_Energy_MW(Zone1_1)
+99999999 Unserved_Energy_MW(Zone1_2)
+40012.080000000002 ONE_VAR_CONSTANT

s.t.

c_u_Commit_Capacity_Constraint(Coal_1)_:
+1 Commit_Capacity_MW(Coal_1)
<= 6

c_u_Commit_Capacity_Constraint(Coal_2)_:
+1 Commit_Capacity_MW(Coal_2)
<= 6

c_u_Commit_Capacity_Constraint(Gas_CCGT_1)_:
+1 Commit_Capacity_MW(Gas_CCGT_1)
<= 6

c_u_Commit_Capacity_Constraint(Gas_CCGT_2)_:
+1 Commit_Capacity_MW(Gas_CCGT_2)
<= 6

c_u_Commit_Capacity_Constraint(Gas_CT_1)_:
+1 Commit_Capacity_MW(Gas_CT_1)
<= 6

c_u_Commit_Capacity_Constraint(Gas_CT_2)_:
+1 Commit_Capacity_MW(Gas_CT_2)
<= 6

c_u_DispCapCommit_Max_Power_Constraint(Coal_1)_:
-1 Commit_Capacity_MW(Coal_1)
+1 Provide_Power_DispCapacityCommit_MW(Coal_1)
+1 Provide_Regulation_Up_MW(Coal_1)
<= 0

c_u_DispCapCommit_Max_Power_Constraint(Coal_2)_:
-1 Commit_Capacity_MW(Coal_2)
+1 Provide_Power_DispCapacityCommit_MW(Coal_2)
+1 Provide_Regulation_Up_MW(Coal_2)
<= 0

c_u_DispCapCommit_Max_Power_Constraint(Gas_CCGT_1)_:
-1 Commit_Capacity_MW(Gas_CCGT_1)
+1 Provide_LF_Reserves_Up_MW(Gas_CCGT_1)
+1 Provide_Power_DispCapacityCommit_MW(Gas_CCGT_1)
+1 Provide_Regulation_Up_MW(Gas_CCGT_1)
<= 0

c_u_DispCapCommit_Max_Power_Constraint(Gas_CCGT_2)_:
-1 Commit_Capacity_MW(Gas_CCGT_2)
+1 Provide_LF_Reserves_Up_MW(Gas_CCGT_2)
+1 Provide_Power_DispCapacityCommit_MW(Gas_CCGT_2)
+1 Provide_Regulation_Up_MW(Gas_CCGT_2)
<= 0

c_u_DispCapCommit_Max_Power_Constraint(Gas_CT_1)_:
-1 Commit_Capacity_MW(Gas_CT_1)
+1 Provide_Power_DispCapacityCommit_MW(Gas_CT_1)
<= 0

c_u_DispCapCommit_Max_Power_Constraint(Gas_CT_2)_:
-1 Commit_Capacity_MW(Gas_CT_2)
+1 Provide_Power_DispCapacityCommit_MW(Gas_CT_2)
<= 0

c_u_DispCapCommit_Min_Power_Constraint(Coal_1)_:
+0.40000000000000002 Commit_Capacity_MW(Coal_1)
-1 Provide_Power_DispCapacityCommit_MW(Coal_1)
+1 Provide_Regulation_Down_MW(Coal_1)
<= 0

c_u_DispCapCommit_Min_Power_Constraint(Coal_2)_:
+0.40000000000000002 Commit_Capacity_MW(Coal_2)
-1 Provide_Power_DispCapacityCommit_MW(Coal_2)
+1 Provide_Regulation_Down_MW(Coal_2)
<= 0

c_l_DispCapCommit_Min_Power_Constraint(Gas_CCGT_1)_:
-1 Provide_LF_Reserves_Down_MW(Gas_CCGT_1)
+1 Provide_Power_DispCapacityCommit_MW(Gas_CCGT_1)
-1 Provide_Regulation_Down_MW(Gas_CCGT_1)
>= 0

c_l_DispCapCommit_Min_Power_Constraint(Gas_CCGT_2)_:
-1 Provide_LF_Reserves_Down_MW(Gas_CCGT_2)
+1 Provide_Power_DispCapacityCommit_MW(Gas_CCGT_2)
-1 Provide_Regulation_Down_MW(Gas_CCGT_2)
>= 0

c_u_DispCapCommit_Min_Power_Constraint(Gas_CT_1)_:
+0.40000000000000002 Commit_Capacity_MW(Gas_CT_1)
-1 Provide_Power_DispCapacityCommit_MW(Gas_CT_1)
<= 0

c_u_DispCapCommit_Min_Power_Constraint(Gas_CT_2)_:
+0.40000000000000002 Commit_Capacity_MW(Gas_CT_2)
-1 Provide_Power_DispCapacityCommit_MW(Gas_CT_2)
<= 0

c_u_DispCapCommit_Startup_Constraint(Coal_1)_:
+1 Commit_Capacity_MW(Coal_1)
-1 Commit_Capacity_MW(Coal_2)
-1 DispCapCommit_Startup_MW(Coal_1)
<= 0

c_u_DispCapCommit_Startup_Constraint(Coal_2)_:
-1 Commit_Capacity_MW(Coal_1)
+1 Commit_Capacity_MW(Coal_2)
-1 DispCapCommit_Startup_MW(Coal_2)
<= 0

c_u_DispCapCommit_Startup_Constraint(Gas_CCGT_1)_:
+1 Commit_Capacity_MW(Gas_CCGT_1)
-1 Commit_Capacity_MW(Gas_CCGT_2)
-1 DispCapCommit_Startup_MW(Gas_CCGT_1)
<= 0

c_u_DispCapCommit_Startup_Constraint(Gas_CCGT_2)_:
-1 Commit_Capacity_MW(Gas_CCGT_1)
+1 Commit_Capacity_MW(Gas_CCGT_2)
-1 DispCapCommit_Startup_MW(Gas_CCGT_2)
<= 0

c_u_DispCapCommit_Startup_Constraint(Gas_CT_1)_:
+1 Commit_Capacity_MW(Gas_CT_1)
-1 Commit_Capacity_MW(Gas_CT_2)
-1 DispCapCommit_Startup_MW(Gas_CT_1)
<= 0

c_u_DispCapCommit_Startup_Constraint(Gas_CT_2)_:
-1 Commit_Capacity_MW(Gas_CT_1)
+1 Commit_Capacity_MW(Gas_CT_2)
-1 DispCapCommit_Startup_MW(Gas_CT_2)
<= 0

c_u_DispCapCommit_Shutdown_Constraint(Coal_1)_:
+1 Commit_Capacity_MW(Coal_1)
-1 Commit_Capacity_MW(Coal_2)
-1 DispCapCommit_Shutdown_MW(Coal_1)
<= 0

c_u_DispCapCommit_Shutdown_Constraint(Coal_2)_:
-1 Commit_Capacity_MW(Coal_1)
+1 Commit_Capacity_MW(Coal_2)
-1 DispCapCommit_Shutdown_MW(Coal_2)
<= 0

c_u_DispCapCommit_Shutdown_Constraint(Gas_CCGT_1)_:
+1 Commit_Capacity_MW(Gas_CCGT_1)
-1 Commit_Capacity_MW(Gas_CCGT_2)
-1 DispCapCommit_Shutdown_MW(Gas_CCGT_1)
<= 0

c_u_DispCapCommit_Shutdown_Constraint(Gas_CCGT_2)_:
-1 Commit_Capacity_MW(Gas_CCGT_1)
+1 Commit_Capacity_MW(Gas_CCGT_2)
-1 DispCapCommit_Shutdown_MW(Gas_CCGT_2)
<= 0

c_u_DispCapCommit_Shutdown_Constraint(Gas_CT_1)_:
+1 Commit_Capacity_MW(Gas_CT_1)
-1 Commit_Capacity_MW(Gas_CT_2)
-1 DispCapCommit_Shutdown_MW(Gas_CT_1)
<= 0

c_u_DispCapCommit_Shutdown_Constraint(Gas_CT_2)_:
-1 Commit_Capacity_MW(Gas_CT_1)
+1 Commit_Capacity_MW(Gas_CT_2)
-1 DispCapCommit_Shutdown_MW(Gas_CT_2)
<= 0

c_u_Variable_Max_Power_Constraint(Wind_1)_:
+1 Provide_Variable_Power_MW(Wind_1)
<= 1.8

c_u_Variable_Max_Power_Constraint(Wind_2)_:
+1 Provide_Variable_Power_MW(Wind_2)
<= 1

c_l_Variable_Min_Power_Constraint(Wind_1)_:
+1 Provide_Variable_Power_MW(Wind_1)
>= 0

c_l_Variable_Min_Power_Constraint(Wind_2)_:
+1 Provide_Variable_Power_MW(Wind_2)
>= 0

c_u_startup_cost_per_mw_Constraint(Coal_1)_:
+0.16666666666666666 Commit_Capacity_MW(Coal_1)
-0.16666666666666666 Commit_Capacity_MW(Coal_2)
-1 startup_cost_per_mw(Coal_1)
<= 0

c_u_startup_cost_per_mw_Constraint(Coal_2)_:
-0.16666666666666666 Commit_Capacity_MW(Coal_1)
+0.16666666666666666 Commit_Capacity_MW(Coal_2)
-1 startup_cost_per_mw(Coal_2)
<= 0

c_u_startup_cost_per_mw_Constraint(Gas_CCGT_1)_:
+0.16666666666666666 Commit_Capacity_MW(Gas_CCGT_1)
-0.16666666666666666 Commit_Capacity_MW(Gas_CCGT_2)
-1 startup_cost_per_mw(Gas_CCGT_1)
<= 0

c_u_startup_cost_per_mw_Constraint(Gas_CCGT_2)_:
-0.16666666666666666 Commit_Capacity_MW(Gas_CCGT_1)
+0.16666666666666666 Commit_Capacity_MW(Gas_CCGT_2)
-1 startup_cost_per_mw(Gas_CCGT_2)
<= 0

c_u_shutdown_cost_per_mw_Constraint(Gas_CCGT_1)_:
-0.33333333333333331 Commit_Capacity_MW(Gas_CCGT_1)
+0.33333333333333331 Commit_Capacity_MW(Gas_CCGT_2)
-1 shutdown_cost_per_mw(Gas_CCGT_1)
<= 0

c_u_shutdown_cost_per_mw_Constraint(Gas_CCGT_2)_:
+0.33333333333333331 Commit_Capacity_MW(Gas_CCGT_1)
-0.33333333333333331 Commit_Capacity_MW(Gas_CCGT_2)
-1 shutdown_cost_per_mw(Gas_CCGT_2)
<= 0

c_u_shutdown_cost_per_mw_Constraint(Gas_CT_1)_:
-0.16666666666666666 Commit_Capacity_MW(Gas_CT_1)
+0.16666666666666666 Commit_Capacity_MW(Gas_CT_2)
-1 shutdown_cost_per_mw(Gas_CT_1)
<= 0

c_u_shutdown_cost_per_mw_Constraint(Gas_CT_2)_:
+0.16666666666666666 Commit_Capacity_MW(Gas_CT_1)
-0.16666666666666666 Commit_Capacity_MW(Gas_CT_2)
-1 shutdown_cost_per_mw(Gas_CT_2)
<= 0

c_e_Meet_Load_Constraint(Zone1_1)_:
-1 Overgeneration_MW(Zone1_1)
+1 Provide_Power_DispCapacityCommit_MW(Coal_1)
+1 Provide_Power_DispCapacityCommit_MW(Gas_CCGT_1)
+1 Provide_Power_DispCapacityCommit_MW(Gas_CT_1)
+1 Provide_Variable_Power_MW(Wind_1)
+1 Unserved_Energy_MW(Zone1_1)
= 4

c_e_Meet_Load_Constraint(Zone1_2)_:
-1 Overgeneration_MW(Zone1_2)
+1 Provide_Power_DispCapacityCommit_MW(Coal_2)
+1 Provide_Power_DispCapacityCommit_MW(Gas_CCGT_2)
+1 Provide_Power_DispCapacityCommit_MW(Gas_CT_2)
+1 Provide_Variable_Power_MW(Wind_2)
+1 Unserved_Energy_MW(Zone1_2)
= 14

c_e_Meet_LF_Reserves_Up_Constraint(Zone1_1)_:
+1 LF_Reserves_Up_Violation_MW(Zone1_1)
+1 Provide_LF_Reserves_Up_MW(Gas_CCGT_1)
= 1

c_e_Meet_LF_Reserves_Up_Constraint(Zone1_2)_:
+1 LF_Reserves_Up_Violation_MW(Zone1_2)
+1 Provide_LF_Reserves_Up_MW(Gas_CCGT_2)
= 2

c_e_Meet_Regulation_Up_Constraint(Zone1_1)_:
+1 Provide_Regulation_Up_MW(Coal_1)
+1 Provide_Regulation_Up_MW(Gas_CCGT_1)
+1 Regulation_Up_Violation_MW(Zone1_1)
= 1

c_e_Meet_Regulation_Up_Constraint(Zone1_2)_:
+1 Provide_Regulation_Up_MW(Coal_2)
+1 Provide_Regulation_Up_MW(Gas_CCGT_2)
+1 Regulation_Up_Violation_MW(Zone1_2)
= 2

c_e_Meet_LF_Reserves_Down_Constraint(Zone1_1)_:
+1 LF_Reserves_Down_Violation_MW(Zone1_1)
+1 Provide_LF_Reserves_Down_MW(Gas_CCGT_1)
= 1

c_e_Meet_LF_Reserves_Down_Constraint(Zone1_2)_:
+1 LF_Reserves_Down_Violation_MW(Zone1_2)
+1 Provide_LF_Reserves_Down_MW(Gas_CCGT_2)
= 2

c_e_Meet_Regulation_Down_Constraint(Zone1_1)_:
+1 Provide_Regulation_Down_MW(Coal_1)
+1 Provide_Regulation_Down_MW(Gas_CCGT_1)
+1 Regulation_Down_Violation_MW(Zone1_1)
= 1

c_e_Meet_Regulation_Down_Constraint(Zone1_2)_:
+1 Provide_Regulation_Down_MW(Coal_2)
+1 Provide_Regulation_Down_MW(Gas_CCGT_2)
+1 Regulation_Down_Violation_MW(Zone1_2)
= 2

c_e_ONE_VAR_CONSTANT: 
ONE_VAR_CONSTANT = 1.0

bounds
   0 <= Provide_LF_Reserves_Up_MW(Gas_CCGT_1) <= +inf
   0 <= Provide_LF_Reserves_Up_MW(Gas_CCGT_2) <= +inf
   0 <= Provide_LF_Reserves_Down_MW(Gas_CCGT_1) <= +inf
   0 <= Provide_LF_Reserves_Down_MW(Gas_CCGT_2) <= +inf
   0 <= Provide_Regulation_Up_MW(Coal_1) <= +inf
   0 <= Provide_Regulation_Up_MW(Coal_2) <= +inf
   0 <= Provide_Regulation_Up_MW(Gas_CCGT_1) <= +inf
   0 <= Provide_Regulation_Up_MW(Gas_CCGT_2) <= +inf
   0 <= Provide_Regulation_Down_MW(Coal_1) <= +inf
   0 <= Provide_Regulation_Down_MW(Coal_2) <= +inf
   0 <= Provide_Regulation_Down_MW(Gas_CCGT_1) <= +inf
   0 <= Provide_Regulation_Down_MW(Gas_CCGT_2) <= +inf
   0 <= Provide_Power_DispCapacityCommit_MW(Coal_1) <= +inf
   0 <= Provide_Power_DispCapacityCommit_MW(Coal_2) <= +inf
   0 <= Provide_Power_DispCapacityCommit_MW(Gas_CCGT_1) <= +inf
   0 <= Provide_Power_DispCapacityCommit_MW(Gas_CCGT_2) <= +inf
   0 <= Provide_Power_DispCapacityCommit_MW(Gas_CT_1) <= +inf
   0 <= Provide_Power_DispCapacityCommit_MW(Gas_CT_2) <= +inf
   0 <= Commit_Capacity_MW(Coal_1) <= +inf
   0 <= Commit_Capacity_MW(Coal_2) <= +inf
   0 <= Commit_Capacity_MW(Gas_CCGT_1) <= +inf
   0 <= Commit_Capacity_MW(Gas_CCGT_2) <= +inf
   0 <= Commit_Capacity_MW(Gas_CT_1) <= +inf
   0 <= Commit_Capacity_MW(Gas_CT_2) <= +inf
   0 <= DispCapCommit_Startup_MW(Coal_1) <= +inf
   0 <= DispCapCommit_Startup_MW(Coal_2) <= +inf
   0 <= DispCapCommit_Startup_MW(Gas_CCGT_1) <= +inf
   0 <= DispCapCommit_Startup_MW(Gas_CCGT_2) <= +inf
   0 <= DispCapCommit_Startup_MW(Gas_CT_1) <= +inf
   0 <= DispCapCommit_Startup_MW(Gas_CT_2) <= +inf
   0 <= DispCapCommit_Shutdown_MW(Coal_1) <= +inf
   0 <= DispCapCommit_Shutdown_MW(Coal_2) <= +inf
   0 <= DispCapCommit_Shutdown_MW(Gas_CCGT_1) <= +inf
   0 <= DispCapCommit_Shutdown_MW(Gas_CCGT_2) <= +inf
   0 <= DispCapCommit_Shutdown_MW(Gas_CT_1) <= +inf
   0 <= DispCapCommit_Shutdown_MW(Gas_CT_2) <= +inf
   0 <= Provide_Variable_Power_MW(Wind_1) <= +inf
   0 <= Provide_Variable_Power_MW(Wind_2) <= +inf
   0 <= startup_cost_per_mw(Coal_1) <= +inf
   0 <= startup_cost_per_mw(Coal_2) <= +inf
   0 <= startup_cost_per_mw(Gas_CCGT_1) <= +inf
   0 <= startup_cost_per_mw(Gas_CCGT_2) <= +inf
   0 <= shutdown_cost_per_mw(Gas_CCGT_1) <= +inf
   0 <= shutdown_cost_per_mw(Gas_CCGT_2) <= +inf
   0 <= shutdown_cost_per_mw(Gas_CT_1) <= +inf
   0 <= shutdown_cost_per_mw(Gas_CT_2) <= +inf
   0 <= Overgeneration_MW(Zone1_1) <= +inf
   0 <= Overgeneration_MW(Zone1_2) <= +inf
   0 <= Unserved_Energy_MW(Zone1_1) <= +inf
   0 <= Unserved_Energy_MW(Zone1_2) <= +inf
   0 <= LF_Reserves_Up_Violation_MW(Zone1_1) <= +inf
   0 <= LF_Reserves_Up_Violation_MW(Zone1_2) <= +inf
   0 <= Regulation_Up_Violation_MW(Zone1_1) <= +inf
   0 <= Regulation_Up_Violation_MW(Zone1_2) <= +inf
   0 <= LF_Reserves_Down_Violation_MW(Zone1_1) <= +inf
   0 <= LF_Reserves_Down_Violation_MW(Zone1_2) <= +inf
   0 <= Regulation_Down_Violation_MW(Zone1_1) <= +inf
   0 <= Regulation_Down_Violation_MW(Zone1_2) <= +inf
end
