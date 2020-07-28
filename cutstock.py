#https://www.dcc.fc.up.pt/~jpp/mpa/cutstock.py
#https://www.researchgate.net/publication/228419999_Extended_Haessler_Heuristic_Algorithm_for_Cutting_Stock_Problem_a_Case_Study_in_Film_Industry

import gurobipy as GRB

LOG = True
EPS = 1.e-6

def solve_cutting_stock(width_quantity_assignment, bin_capacity):

  valid_cut_patterns = []
  for position, unique_width in enumerate(width_quantity_assignment):
    cut_patttern = [0] * len(width_quantity_assignment)
    cut_patttern[position] = int(bin_capacity / unique_width)
    valid_cut_patterns.append(cut_patttern)

  if LOG:
    print ("sizes of orders=", list(width_quantity_assignment.keys()))
    print ("quantities of orders=", list(width_quantity_assignment.values()))
    print ("roll size=", bin_capacity)
    print ("initial patterns", valid_cut_patterns)

  master_problem = GRB.Model("LP")
  pattern_choice = {}
  for i in range(len(width_quantity_assignment)):
    pattern_choice[i] = master_problem.addVar(obj = 1, vtype = "I", name = "x[%d]" %i)
  master_problem.update()

  orders = {}
  for iterator, width in enumerate(width_quantity_assignment):
    coef = valid_cut_patterns[iterator][iterator]
    decision_var = pattern_choice[iterator]
    orders[iterator] = master_problem.addConstr(GRB.LinExpr(coef, decision_var), ">", width_quantity_assignment[width], name = "Order[%d]" %iterator)

  master_problem.update()
  master_problem.Params.OutputFlag = 0

  def solve_knapsack_sub_problem():
    while (True):
      relax = master_problem.relax()
      relax.optimize()
      dual_values = [c.Pi for c in relax.getConstrs()]
  
      knapsack_sub_problem = GRB.Model("KP")
      knapsack_sub_problem.ModelSense = -1 # maximize
      
      dual_variables = {}
      for iterator, width in enumerate(width_quantity_assignment):
        dual_variables[iterator] = knapsack_sub_problem.addVar(obj = dual_values[iterator], ub = width_quantity_assignment[width], vtype="I", name="y[%d]"%iterator)
      knapsack_sub_problem.update()
  
      pattern_length = GRB.LinExpr(list(width_quantity_assignment.keys()), [dual_variables[i] for i in range(len(width_quantity_assignment))])
      knapsack_sub_problem.addConstr(pattern_length, "<", bin_capacity, name = "width")
      knapsack_sub_problem.update()
      knapsack_sub_problem.Params.OutputFlag = 0
      knapsack_sub_problem.optimize()
  
      if LOG:
        print ("objective of knapsack_sub_problem problem:", knapsack_sub_problem.ObjVal)
      if knapsack_sub_problem.ObjVal < 1 + EPS:
         break
  
      new_pattern = [int(dual_variables[i].X + 0.5) for i in dual_variables]
      valid_cut_patterns.append(new_pattern)
      if LOG:
        print ("shadow prices and new pattern:")
        for i, dual_value in enumerate(dual_values):
          print ("\t%5d%12g%7d" % (i, dual_value, new_pattern[i]))
        print()
  
      def add_new_col_to_master():
        col = GRB.Column()
        for i in range(len(width_quantity_assignment)):
          if valid_cut_patterns[-1][i] > 0:
            col.addTerms(valid_cut_patterns[-1][i], orders[i])
        pattern_choice[len(valid_cut_patterns) - 1] = master_problem.addVar(obj = 1, vtype = "I", name = "x[%d]" %(len(valid_cut_patterns) - 1), column = col)
        master_problem.update()

      add_new_col_to_master()

  solve_knapsack_sub_problem()

  if LOG:
    master_problem.Params.OutputFlag = 1
  master_problem.optimize()

  if LOG:
    print ()
    print ("final solution (integer master problem):  objective =", master_problem.ObjVal)
    print ("patterns:")
    for k in pattern_choice:
      if pattern_choice[k].X > EPS:
        print ("pattern", k,)
        print ("\tsizes:", )
        print ([list(width_quantity_assignment.keys())[i] for i in range(len(width_quantity_assignment)) if valid_cut_patterns[k][i]>0 for j in range(valid_cut_patterns[k][i]) ],)
        print ("--> %d rolls" % int(pattern_choice[k].X+.5))

  rolls = []
  for k in pattern_choice:
    for j in range(int(pattern_choice[k].X + .5)):
      rolls.append(sorted([list(width_quantity_assignment.keys())[i] for i in range(len(width_quantity_assignment)) if valid_cut_patterns[k][i]>0 for j in range(valid_cut_patterns[k][i])]))
  rolls.sort()
  return rolls

def get_example_values_1():
  bin_size = 110
  requested_width = [20, 45, 50, 55, 75]
  quantity_of_width_request = [48, 35, 24, 10, 8]
  width_quantity_assignment = dict(zip(requested_width, quantity_of_width_request))
  return width_quantity_assignment, bin_size

def get_example_values_2():
  bin_size = 9
  requested_width = [2, 3, 4, 5, 6, 7, 8]
  quantity_of_width_request = [4, 2, 6, 6, 2, 2, 2]
  width_quantity_assignment = dict(zip(requested_width, quantity_of_width_request))
  return width_quantity_assignment, bin_size

if __name__ == "__main__":
  
  width_quantity_assignment, bin_size = get_example_values_2()

  print ("\n\n\nCutting stock problem:")
  rolls = solve_cutting_stock(width_quantity_assignment, bin_size)
  print (len(rolls), "rolls:")
  print (rolls)
