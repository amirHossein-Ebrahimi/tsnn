import numpy as np

from PymoNNto import Behaviour
from src.core.environement.dopamine import DopamineEnvironment
from src.core.environement.inferencer import PhaseDetectorEnvironment
from src.core.learning.stdp import bounds


class SynapsePairWiseSTDPWithoutDelay(Behaviour):
    def set_variables(self, synapse):

        configure = {
            "a_minus": -0.1,
            "a_plus": 0.2,
            "dt": 1.0,
            "stdp_factor": 1.0,
            "tau_minus": 3.0,
            "tau_plus": 3.0,
            "w_max": 10.0,
            "w_min": 0.0,
            "P": 1,
            "is_inhibitory": False,
            "weight_update_strategy": None,
        }

        for attr, value in configure.items():
            setattr(self, attr, self.get_init_attr(attr, value, synapse))

        synapse.J = self.get_init_attr("J", 10, synapse)
        synapse.W = synapse.get_synapse_mat("zeros")
        probable_connection_mask = np.random.random(synapse.W.shape) <= self.P
        normal_distribution = np.random.normal(
            loc=synapse.J / synapse.src.size,
            scale=1,
            size=synapse.W.shape,
        )
        synapse.W += normal_distribution * probable_connection_mask
        synapse.W = np.clip(synapse.W, self.w_min, self.w_max)

        if self.a_minus >= 0:
            raise AssertionError("a_minus should be negative")

        if self.weight_update_strategy not in (None, "soft-bound", "hard-bound"):
            raise AssertionError(
                "weight_update_strategy must be one of soft-bound|hard-bound|None"
            )

    def new_iteration(self, synapse):
        # For testing only, we won't update synapse weights in test mode!
        if not synapse.recording or PhaseDetectorEnvironment.is_phase("inference"):
            return

        ltd = synapse.src.fired * synapse.dst.trace[:, 0][:, np.newaxis]
        ltp = synapse.src.trace[:, 0] * synapse.dst.fired[:, np.newaxis]

        # soft bound for both delay and stdp separate
        dw = (
            DopamineEnvironment.get()  # from global environment
            * (self.a_plus * ltp + self.a_minus * ltd)  # stdp mechanism
            * bounds[self.weight_update_strategy or "none"](
                self.w_min, synapse.W, self.w_max
            )
            * self.stdp_factor  # stdp scale factor
            * synapse.enabled  # activation of synapse itself
            * self.dt
        )

        synapse.W[synapse.W > 0.01] -= 1e-5
        synapse.W = synapse.W + (1, -1)[self.is_inhibitory] * np.abs(dw)
        synapse.W = np.clip(synapse.W, self.w_min, self.w_max)
