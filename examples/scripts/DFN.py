#
# Example showing how to load and solve the DFN
#

import pybamm
import numpy as np
import matplotlib.pyplot as plt

pybamm.set_logging_level("INFO")

# load model
model = pybamm.lithium_ion.DFN({"operating mode": "voltage"})

# create geometry
geometry = model.default_geometry

# load parameter values and process model and geometry
param = model.default_parameter_values
param["Voltage function [V]"] = 4.1
param.process_model(model)
param.process_geometry(geometry)

# set mesh
var = pybamm.standard_spatial_vars
var_pts = {var.x_n: 30, var.x_s: 30, var.x_p: 30, var.r_n: 10, var.r_p: 10}
mesh = pybamm.Mesh(geometry, model.default_submesh_types, var_pts)

# discretise model
disc = pybamm.Discretisation(mesh, model.default_spatial_methods)
disc.process_model(model)

# solve model
t_eval = np.linspace(0, 0.2, 100)
solver = model.default_solver
solver.rtol = 1e-3
solver.atol = 1e-6
solution = solver.solve(model, t_eval)

output_vars = pybamm.post_process_variables(
    model.variables, solution.t, solution.y, mesh
)
v = output_vars["Terminal voltage"]
ocv = output_vars["Measured open circuit voltage"]
eta = output_vars["Local overpotential sum"]
t = solution.t
plt.plot(t, v(t), "-", t, ocv(t) + eta(t), "o")
plt.show()

R_1 = output_vars["Local equivalent resistance"]
R_2 = output_vars["Local equivalent resistance by overpotential"]
plt.plot(t, R_1(t), "-", t, R_2(t), "o")
plt.show()

# plot
plot = pybamm.QuickPlot(solution)
plot.dynamic_plot()
