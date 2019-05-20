#
# Lead-acid Composite model
#
import pybamm


class Composite(pybamm.LeadAcidBaseModel):
    """Composite model for lead-acid, from [1]_.
    Uses leading-order model from :class:`pybamm.lead_acid.LOQS`

    References
    ----------
    .. [1] V Sulzer, SJ Chapman, CP Please, DA Howey, and CW Monroe. Faster Lead-Acid
           Battery Simulations from Porous-Electrode Theory: II. Asymptotic Analysis.
           arXiv preprint arXiv:1902.01774, 2019.

    **Extends:** :class:`pybamm.LeadAcidBaseModel`
    """

    def __init__(self):
        # Update own model with submodels
        super().__init__()
        self.name = "Composite model"

        "-----------------------------------------------------------------------------"
        "Parameters"
        param = pybamm.standard_parameters_lead_acid

        "-----------------------------------------------------------------------------"
        "Model Variables"

        c_e = pybamm.standard_variables.c_e
        eps = pybamm.standard_variables.eps

        "-----------------------------------------------------------------------------"
        "Submodels"
        # Leading order model and variables
        leading_order_model = pybamm.lead_acid.LOQS()
        c_e_0 = leading_order_model.variables["Average electrolyte concentration"]
        eps_0 = leading_order_model.variables["Porosity"]
        j_n_0 = leading_order_model.variables[
            "Negative electrode interfacial current density"
        ]
        j_p_0 = leading_order_model.variables[
            "Positive electrode interfacial current density"
        ]
        # Porosity
        porosity_model = pybamm.porosity.Standard(param)
        porosity_model.set_differential_system(eps, j_n_0, j_p_0)
        self.update(porosity_model)

        # Electrolyte concentration
        reactions = {
            "main": {
                "neg": {"s_plus": param.s_n, "aj": j_n_0},
                "pos": {"s_plus": param.s_p, "aj": j_p_0},
                "porosity change": porosity_model.variables["Porosity change"],
            }
        }
        electrolyte_conc_model = pybamm.electrolyte_diffusion.StefanMaxwell(param)
        electrolyte_conc_model.set_differential_system(c_e, reactions, epsilon=eps_0)

        self.update(leading_order_model, electrolyte_conc_model)

        "-----------------------------------------------------------------------------"
        "Post-Processing"
        # Interfacial current density

        # Exchange-current density
        int_curr_model = pybamm.interface.LeadAcidReaction(param)
        neg = ["negative electrode"]
        pos = ["positive electrode"]
        c_e_n, _, c_e_p = c_e.orphans
        j0_n = int_curr_model.get_exchange_current_densities(c_e_n, neg)
        j0_p = int_curr_model.get_exchange_current_densities(c_e_p, pos)
        j_vars = int_curr_model.get_derived_interfacial_currents(
            j_n_0, j_p_0, j0_n, j0_p
        )
        self.variables.update(j_vars)

        # Potentials
        ocp_n = param.U_n(c_e_n)
        ocp_p = param.U_p(c_e_p)
        eta_r_n = int_curr_model.get_inverse_butler_volmer(j_n_0, j0_n, neg)
        eta_r_p = int_curr_model.get_inverse_butler_volmer(j_p_0, j0_p, pos)
        pot_model = pybamm.potential.Potential(param)
        ocp_vars = pot_model.get_derived_open_circuit_potentials(ocp_n, ocp_p)
        eta_r_vars = pot_model.get_derived_reaction_overpotentials(eta_r_n, eta_r_p)
        self.variables.update({**ocp_vars, **eta_r_vars})

        # Load electrolyte and electrode potentials
        electrode_model = pybamm.electrode.Ohm(param)
        electrolyte_current_model = pybamm.electrolyte_current.MacInnesStefanMaxwell(
            param
        )

        # Negative electrode potential
        phi_s_n = electrode_model.get_neg_pot_explicit_combined(eps_0)

        # Electrolyte potential
        electrolyte_vars = electrolyte_current_model.get_explicit_combined(
            ocp_n, eta_r_n, c_e, phi_s_n, eps_0, c_e_0
        )
        self.variables.update(electrolyte_vars)
        phi_e = electrolyte_vars["Electrolyte potential"]

        # Electrode
        electrode_vars = electrode_model.get_explicit_combined(
            phi_s_n, phi_e, ocp_p, eta_r_p, eps_0
        )
        self.variables.update(electrode_vars)
