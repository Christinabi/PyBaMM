import numpy as np
import pybamm

pybamm.set_logging_level("INFO")

# load models
models = [
    pybamm.lead_acid.LOQS(),
    pybamm.lead_acid.Composite(),
    pybamm.lead_acid.NewmanTiedemann(),
]

# create geometry
geometry = models[-1].default_geometry

# load parameter values and process models and geometry
param = models[0].default_parameter_values
param.update({"Typical current [A]": 20})
for model in models:
    param.process_model(model)
param.process_geometry(geometry)

# set mesh
var = pybamm.standard_spatial_vars
var_pts = {var.x_n: 30, var.x_s: 30, var.x_p: 30}
mesh = pybamm.Mesh(geometry, models[-1].default_submesh_types, var_pts)

# discretise models
for model in models:
    disc = pybamm.Discretisation(mesh, model.default_spatial_methods)
    disc.process_model(model)

# solve model
solvers = [None] * len(models)
t_eval = np.linspace(0, 1, 100)
for i, model in enumerate(models):
    solver = model.default_solver
    solver.solve(model, t_eval)
    solvers[i] = solver

# plot
output_variables = [
    "Interfacial current density [A.m-2]",
    "Electrolyte concentration [mol.m-3]",
    "Current [A]",
    "Porosity",
    "Electrolyte potential [V]",
    "Terminal voltage [V]",
]
plot = pybamm.QuickPlot(models, mesh, solvers, output_variables)
plot.dynamic_plot()
