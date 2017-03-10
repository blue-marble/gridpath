<?xml version = "1.0" encoding="UTF-8" standalone="yes"?>
<CPLEXSolution version="1.2">
 <header
   problemName="/Users/ana/Dropbox/dev/gridpath/examples/test/logs/tmpc44vUq.pyomo.lp"
   objectiveValue="65494.4133333333"
   solutionTypeValue="1"
   solutionTypeString="basic"
   solutionStatusValue="1"
   solutionStatusString="optimal"
   solutionMethodString="dual"
   primalFeasible="1"
   dualFeasible="1"
   simplexIterations="13"
   writeLevel="1"/>
 <quality
   epRHS="1e-06"
   epOpt="1e-06"
   maxPrimalInfeas="0"
   maxDualInfeas="0"
   maxPrimalResidual="2.22044604925031e-16"
   maxDualResidual="7.58004770062826e-14"
   maxX="6"
   maxPi="40012.08"
   maxSlack="6"
   maxRedCost="999999999"
   kappa="26.6074074074074"/>
 <linearConstraints>
  <constraint name="c_u_Commit_Capacity_Constraint(Coal_1)_" index="0" status="BS" slack="6" dual="0"/>
  <constraint name="c_u_Commit_Capacity_Constraint(Coal_2)_" index="1" status="BS" slack="1" dual="0"/>
  <constraint name="c_u_Commit_Capacity_Constraint(Gas_CCGT_1)_" index="2" status="BS" slack="2" dual="0"/>
  <constraint name="c_u_Commit_Capacity_Constraint(Gas_CCGT_2)_" index="3" status="LL" slack="0" dual="-742.666666666667"/>
  <constraint name="c_u_Commit_Capacity_Constraint(Gas_CT_1)_" index="4" status="BS" slack="5.8" dual="0"/>
  <constraint name="c_u_Commit_Capacity_Constraint(Gas_CT_2)_" index="5" status="LL" slack="0" dual="-1582.33333333333"/>
  <constraint name="c_u_DispCapCommit_Max_Power_Constraint(Coal_1)_" index="6" status="LL" slack="0" dual="-1249.5"/>
  <constraint name="c_u_DispCapCommit_Max_Power_Constraint(Coal_2)_" index="7" status="LL" slack="0" dual="-1984.16666666667"/>
  <constraint name="c_u_DispCapCommit_Max_Power_Constraint(Gas_CCGT_1)_" index="8" status="LL" slack="0" dual="-1249.5"/>
  <constraint name="c_u_DispCapCommit_Max_Power_Constraint(Gas_CCGT_2)_" index="9" status="LL" slack="0" dual="-1993.16666666667"/>
  <constraint name="c_u_DispCapCommit_Max_Power_Constraint(Gas_CT_1)_" index="10" status="LL" slack="0" dual="-400.5"/>
  <constraint name="c_u_DispCapCommit_Max_Power_Constraint(Gas_CT_2)_" index="11" status="LL" slack="0" dual="-1983.16666666667"/>
  <constraint name="c_u_DispCapCommit_Min_Power_Constraint(Coal_1)_" index="12" status="LL" slack="0" dual="-848"/>
  <constraint name="c_u_DispCapCommit_Min_Power_Constraint(Coal_2)_" index="13" status="BS" slack="1" dual="0"/>
  <constraint name="c_l_DispCapCommit_Min_Power_Constraint(Gas_CCGT_1)_" index="14" status="LL" slack="0" dual="839"/>
  <constraint name="c_l_DispCapCommit_Min_Power_Constraint(Gas_CCGT_2)_" index="15" status="BS" slack="0" dual="-0"/>
  <constraint name="c_u_DispCapCommit_Min_Power_Constraint(Gas_CT_1)_" index="16" status="BS" slack="0.12" dual="0"/>
  <constraint name="c_u_DispCapCommit_Min_Power_Constraint(Gas_CT_2)_" index="17" status="BS" slack="3.6" dual="0"/>
  <constraint name="c_u_DispCapCommit_Startup_Constraint(Coal_1)_" index="18" status="BS" slack="5" dual="0"/>
  <constraint name="c_u_DispCapCommit_Startup_Constraint(Coal_2)_" index="19" status="LL" slack="0" dual="-0"/>
  <constraint name="c_u_DispCapCommit_Startup_Constraint(Gas_CCGT_1)_" index="20" status="BS" slack="2" dual="0"/>
  <constraint name="c_u_DispCapCommit_Startup_Constraint(Gas_CCGT_2)_" index="21" status="LL" slack="0" dual="-0"/>
  <constraint name="c_u_DispCapCommit_Startup_Constraint(Gas_CT_1)_" index="22" status="BS" slack="5.8" dual="0"/>
  <constraint name="c_u_DispCapCommit_Startup_Constraint(Gas_CT_2)_" index="23" status="LL" slack="0" dual="-0"/>
  <constraint name="c_u_DispCapCommit_Shutdown_Constraint(Coal_1)_" index="24" status="BS" slack="5" dual="0"/>
  <constraint name="c_u_DispCapCommit_Shutdown_Constraint(Coal_2)_" index="25" status="LL" slack="0" dual="-0"/>
  <constraint name="c_u_DispCapCommit_Shutdown_Constraint(Gas_CCGT_1)_" index="26" status="BS" slack="2" dual="0"/>
  <constraint name="c_u_DispCapCommit_Shutdown_Constraint(Gas_CCGT_2)_" index="27" status="LL" slack="0" dual="-0"/>
  <constraint name="c_u_DispCapCommit_Shutdown_Constraint(Gas_CT_1)_" index="28" status="BS" slack="5.8" dual="0"/>
  <constraint name="c_u_DispCapCommit_Shutdown_Constraint(Gas_CT_2)_" index="29" status="LL" slack="0" dual="-0"/>
  <constraint name="c_u_Variable_Max_Power_Constraint(Wind_1)_" index="30" status="LL" slack="0" dual="-442.5"/>
  <constraint name="c_u_Variable_Max_Power_Constraint(Wind_2)_" index="31" status="LL" slack="0" dual="-2025.16666666667"/>
  <constraint name="c_l_Variable_Min_Power_Constraint(Wind_1)_" index="32" status="BS" slack="-1.8" dual="-0"/>
  <constraint name="c_l_Variable_Min_Power_Constraint(Wind_2)_" index="33" status="BS" slack="-1" dual="-0"/>
  <constraint name="c_u_startup_cost_per_mw_Constraint(Coal_1)_" index="34" status="BS" slack="0.833333333333333" dual="0"/>
  <constraint name="c_u_startup_cost_per_mw_Constraint(Coal_2)_" index="35" status="LL" slack="0" dual="-1"/>
  <constraint name="c_u_startup_cost_per_mw_Constraint(Gas_CCGT_1)_" index="36" status="BS" slack="0.333333333333333" dual="0"/>
  <constraint name="c_u_startup_cost_per_mw_Constraint(Gas_CCGT_2)_" index="37" status="LL" slack="0" dual="-1"/>
  <constraint name="c_u_shutdown_cost_per_mw_Constraint(Gas_CCGT_1)_" index="38" status="LL" slack="0" dual="-1"/>
  <constraint name="c_u_shutdown_cost_per_mw_Constraint(Gas_CCGT_2)_" index="39" status="BS" slack="0.666666666666667" dual="0"/>
  <constraint name="c_u_shutdown_cost_per_mw_Constraint(Gas_CT_1)_" index="40" status="LL" slack="0" dual="-1"/>
  <constraint name="c_u_shutdown_cost_per_mw_Constraint(Gas_CT_2)_" index="41" status="BS" slack="0.966666666666667" dual="0"/>
  <constraint name="c_e_Meet_Load_Constraint(Zone1_1)_" index="42" status="LL" slack="0" dual="442.5"/>
  <constraint name="c_e_Meet_Load_Constraint(Zone1_2)_" index="43" status="LL" slack="0" dual="2025.16666666667"/>
  <constraint name="c_e_Meet_LF_Reserves_Up_Constraint(Zone1_1)_" index="44" status="LL" slack="0" dual="1249.5"/>
  <constraint name="c_e_Meet_LF_Reserves_Up_Constraint(Zone1_2)_" index="45" status="LL" slack="0" dual="1993.16666666667"/>
  <constraint name="c_e_Meet_Regulation_Up_Constraint(Zone1_1)_" index="46" status="LL" slack="0" dual="1249.5"/>
  <constraint name="c_e_Meet_Regulation_Up_Constraint(Zone1_2)_" index="47" status="LL" slack="0" dual="1984.16666666667"/>
  <constraint name="c_e_Meet_LF_Reserves_Down_Constraint(Zone1_1)_" index="48" status="LL" slack="0" dual="839"/>
  <constraint name="c_e_Meet_LF_Reserves_Down_Constraint(Zone1_2)_" index="49" status="LL" slack="0" dual="0"/>
  <constraint name="c_e_Meet_Regulation_Down_Constraint(Zone1_1)_" index="50" status="LL" slack="0" dual="839"/>
  <constraint name="c_e_Meet_Regulation_Down_Constraint(Zone1_2)_" index="51" status="LL" slack="0" dual="0"/>
  <constraint name="c_e_ONE_VAR_CONSTANT" index="52" status="LL" slack="0" dual="40012.08"/>
 </linearConstraints>
 <variables>
  <variable name="Commit_Capacity_MW(Coal_1)" index="0" status="LL" value="0" reducedCost="1073.53333333333"/>
  <variable name="Commit_Capacity_MW(Coal_2)" index="1" status="BS" value="5" reducedCost="0"/>
  <variable name="Commit_Capacity_MW(Gas_CCGT_1)" index="2" status="BS" value="4" reducedCost="0"/>
  <variable name="Commit_Capacity_MW(Gas_CCGT_2)" index="3" status="BS" value="6" reducedCost="0"/>
  <variable name="Commit_Capacity_MW(Gas_CT_1)" index="4" status="BS" value="0.2" reducedCost="0"/>
  <variable name="Commit_Capacity_MW(Gas_CT_2)" index="5" status="BS" value="6" reducedCost="0"/>
  <variable name="LF_Reserves_Down_Violation_MW(Zone1_1)" index="6" status="LL" value="0" reducedCost="999999160"/>
  <variable name="LF_Reserves_Down_Violation_MW(Zone1_2)" index="7" status="LL" value="0" reducedCost="999999999"/>
  <variable name="LF_Reserves_Up_Violation_MW(Zone1_1)" index="8" status="LL" value="0" reducedCost="999998749.5"/>
  <variable name="LF_Reserves_Up_Violation_MW(Zone1_2)" index="9" status="LL" value="0" reducedCost="999998005.833333"/>
  <variable name="Overgeneration_MW(Zone1_1)" index="10" status="LL" value="0" reducedCost="100000441.5"/>
  <variable name="Overgeneration_MW(Zone1_2)" index="11" status="LL" value="0" reducedCost="100002024.166667"/>
  <variable name="Provide_Power_DispCapacityCommit_MW(Coal_1)" index="12" status="BS" value="0" reducedCost="0"/>
  <variable name="Provide_Power_DispCapacityCommit_MW(Coal_2)" index="13" status="BS" value="3" reducedCost="0"/>
  <variable name="Provide_Power_DispCapacityCommit_MW(Gas_CCGT_1)" index="14" status="BS" value="2" reducedCost="0"/>
  <variable name="Provide_Power_DispCapacityCommit_MW(Gas_CCGT_2)" index="15" status="BS" value="4" reducedCost="0"/>
  <variable name="Provide_Power_DispCapacityCommit_MW(Gas_CT_1)" index="16" status="BS" value="0.2" reducedCost="0"/>
  <variable name="Provide_Power_DispCapacityCommit_MW(Gas_CT_2)" index="17" status="BS" value="6" reducedCost="0"/>
  <variable name="Regulation_Down_Violation_MW(Zone1_1)" index="18" status="LL" value="0" reducedCost="999999160"/>
  <variable name="Regulation_Down_Violation_MW(Zone1_2)" index="19" status="LL" value="0" reducedCost="999999999"/>
  <variable name="Regulation_Up_Violation_MW(Zone1_1)" index="20" status="LL" value="0" reducedCost="999998749.5"/>
  <variable name="Regulation_Up_Violation_MW(Zone1_2)" index="21" status="LL" value="0" reducedCost="999998014.833333"/>
  <variable name="shutdown_cost_per_mw(Gas_CCGT_1)" index="22" status="BS" value="0.666666666666667" reducedCost="0"/>
  <variable name="shutdown_cost_per_mw(Gas_CCGT_2)" index="23" status="LL" value="0" reducedCost="1"/>
  <variable name="shutdown_cost_per_mw(Gas_CT_1)" index="24" status="BS" value="0.966666666666667" reducedCost="0"/>
  <variable name="shutdown_cost_per_mw(Gas_CT_2)" index="25" status="LL" value="0" reducedCost="1"/>
  <variable name="startup_cost_per_mw(Coal_1)" index="26" status="LL" value="0" reducedCost="1"/>
  <variable name="startup_cost_per_mw(Coal_2)" index="27" status="BS" value="0.833333333333333" reducedCost="0"/>
  <variable name="startup_cost_per_mw(Gas_CCGT_1)" index="28" status="LL" value="0" reducedCost="1"/>
  <variable name="startup_cost_per_mw(Gas_CCGT_2)" index="29" status="BS" value="0.333333333333333" reducedCost="0"/>
  <variable name="Unserved_Energy_MW(Zone1_1)" index="30" status="LL" value="0" reducedCost="99999556.5"/>
  <variable name="Unserved_Energy_MW(Zone1_2)" index="31" status="LL" value="0" reducedCost="99997973.8333333"/>
  <variable name="ONE_VAR_CONSTANT" index="32" status="BS" value="1" reducedCost="0"/>
  <variable name="Provide_Regulation_Up_MW(Coal_1)" index="33" status="BS" value="0" reducedCost="0"/>
  <variable name="Provide_Regulation_Up_MW(Coal_2)" index="34" status="BS" value="2" reducedCost="0"/>
  <variable name="Provide_LF_Reserves_Up_MW(Gas_CCGT_1)" index="35" status="BS" value="1" reducedCost="0"/>
  <variable name="Provide_Regulation_Up_MW(Gas_CCGT_1)" index="36" status="BS" value="1" reducedCost="0"/>
  <variable name="Provide_LF_Reserves_Up_MW(Gas_CCGT_2)" index="37" status="BS" value="2" reducedCost="0"/>
  <variable name="Provide_Regulation_Up_MW(Gas_CCGT_2)" index="38" status="LL" value="0" reducedCost="9"/>
  <variable name="Provide_Regulation_Down_MW(Coal_1)" index="39" status="LL" value="0" reducedCost="9"/>
  <variable name="Provide_Regulation_Down_MW(Coal_2)" index="40" status="LL" value="0" reducedCost="0"/>
  <variable name="Provide_LF_Reserves_Down_MW(Gas_CCGT_1)" index="41" status="BS" value="1" reducedCost="0"/>
  <variable name="Provide_Regulation_Down_MW(Gas_CCGT_1)" index="42" status="BS" value="1" reducedCost="0"/>
  <variable name="Provide_LF_Reserves_Down_MW(Gas_CCGT_2)" index="43" status="BS" value="2" reducedCost="0"/>
  <variable name="Provide_Regulation_Down_MW(Gas_CCGT_2)" index="44" status="BS" value="2" reducedCost="0"/>
  <variable name="DispCapCommit_Startup_MW(Coal_1)" index="45" status="LL" value="0" reducedCost="0"/>
  <variable name="DispCapCommit_Startup_MW(Coal_2)" index="46" status="BS" value="5" reducedCost="0"/>
  <variable name="DispCapCommit_Startup_MW(Gas_CCGT_1)" index="47" status="LL" value="0" reducedCost="0"/>
  <variable name="DispCapCommit_Startup_MW(Gas_CCGT_2)" index="48" status="BS" value="2" reducedCost="0"/>
  <variable name="DispCapCommit_Startup_MW(Gas_CT_1)" index="49" status="LL" value="0" reducedCost="0"/>
  <variable name="DispCapCommit_Startup_MW(Gas_CT_2)" index="50" status="BS" value="5.8" reducedCost="0"/>
  <variable name="DispCapCommit_Shutdown_MW(Coal_1)" index="51" status="LL" value="0" reducedCost="0"/>
  <variable name="DispCapCommit_Shutdown_MW(Coal_2)" index="52" status="BS" value="5" reducedCost="0"/>
  <variable name="DispCapCommit_Shutdown_MW(Gas_CCGT_1)" index="53" status="LL" value="0" reducedCost="0"/>
  <variable name="DispCapCommit_Shutdown_MW(Gas_CCGT_2)" index="54" status="BS" value="2" reducedCost="0"/>
  <variable name="DispCapCommit_Shutdown_MW(Gas_CT_1)" index="55" status="LL" value="0" reducedCost="0"/>
  <variable name="DispCapCommit_Shutdown_MW(Gas_CT_2)" index="56" status="BS" value="5.8" reducedCost="0"/>
  <variable name="Provide_Variable_Power_MW(Wind_1)" index="57" status="BS" value="1.8" reducedCost="0"/>
  <variable name="Provide_Variable_Power_MW(Wind_2)" index="58" status="BS" value="1" reducedCost="0"/>
 </variables>
</CPLEXSolution>
