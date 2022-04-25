import numpy as np

from PymoNNto import Behaviour
from src.core.environement.dopamine import DopamineEnvironment
from src.data.plotters import dw_plotter, w_plotter, words_stimulus_plotter


class SynapsePairWiseSTDP(Behaviour):
    __slots__ = [
        "tau_plus",
        "tau_minus",
        "a_plus",
        "a_minus",
        "dt",
        "weight_decay",
        "stdp_factor",
        "min_delay_threshold",
        "w_min",
        "w_max",
    ]

    def set_variables(self, synapse):
        synapse.W = synapse.get_synapse_mat("uniform")
        synapse.src.trace = synapse.src.get_neuron_vec()
        synapse.dst.trace = synapse.dst.get_neuron_vec()

        configure = {
            "tau_plus": 3.0,
            "tau_minus": 3.0,
            "a_plus": 0.1,
            "a_minus": -0.2,
            "dt": 1.0,
            "weight_decay": 0.0,
            "stdp_factor": 1.0,
            "delay_factor": 1.0,
            "min_delay_threshold": 0.15,
            "w_min": 0.0,
            "w_max": 10.0,
            "stimulus_scale_factor": 1,
            "noise_scale_factor": 1,
            "adaptive_noise_scale": 1,
        }

        for attr, value in configure.items():
            setattr(self, attr, self.get_init_attr(attr, value, synapse))
        # Scale W from [0,1) to [w_min, w_max)
        synapse.W *= (self.w_max - self.w_min) + self.w_min
        synapse.W = np.clip(synapse.W, self.w_min, self.w_max)

        self.weight_decay = 1 - self.weight_decay

        assert self.a_minus < 0, "a_minus should be negative"

    def new_iteration(self, synapse):
        # For testing only, we won't update synapse weights in test mode!
        if not synapse.recording:
            synapse.dst.I = synapse.W.dot(synapse.src.fired)
            return

        synapse.src.trace += (
            -synapse.src.trace / self.tau_plus + synapse.src.fired  # dx
        ) * self.dt

        synapse.dst.trace += (
            -synapse.dst.trace / self.tau_minus + synapse.dst.fired  # dy
        ) * self.dt

        dw_minus = (
            self.a_minus
            * synapse.src.fired[np.newaxis, :]
            * synapse.dst.trace[:, np.newaxis]
        )
        dw_plus = (
            self.a_plus
            * synapse.src.trace[np.newaxis, :]
            * synapse.dst.fired[:, np.newaxis]
        )

        dw = (
            DopamineEnvironment.get()  # from global environment
            * (dw_plus + dw_minus)  # stdp mechanism
            * synapse.weights_scale[:, :, 0]  # weight scale based on the synapse delay
            * self.stdp_factor  # stdp scale factor
            * synapse.enabled  # activation of synapse itself
            * self.dt
        )

        dw_plotter.add(np.max(dw))
        synapse.W = synapse.W * self.weight_decay + dw
        synapse.W = np.clip(synapse.W, self.w_min, self.w_max)
        w_plotter.add_image(synapse.W, vmin=self.w_min, vmax=self.w_max)
        """ stop condition for delay learning """
        use_shared_delay = dw.shape != synapse.delay.shape
        if use_shared_delay:
            dw = np.mean(dw, axis=0, keepdims=True)

        non_zero_dw = dw != 0
        if non_zero_dw.any():
            should_update = (
                np.min(synapse.delay[non_zero_dw]) > self.min_delay_threshold
            )
            if should_update:
                synapse.delay[non_zero_dw] -= dw[non_zero_dw] * self.delay_factor

        # shrink the noise scale factor at the beginning of each episode
        if synapse.iteration == 1:
            self.noise_scale_factor *= self.adaptive_noise_scale

        next_layer_stimulus = synapse.W.dot(synapse.src.fired)
        # TODO: need to investigate more for diagonal feature
        # TODO: check
        noise = (
            self.noise_scale_factor
            * (np.random.random(next_layer_stimulus.shape) - 0.5)
            * 2
        )
        synapse.dst.I = self.stimulus_scale_factor * next_layer_stimulus + noise

        words_stimulus_plotter.add(synapse.dst.I, should_copy=True)

    # NOTE: We might need the add clamping mechanism to the 'I' for the dst layer


# NOTE: clamping is better to be part of neurons itself
