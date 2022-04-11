import numpy as np

from PymoNNto import Behaviour, def_dtype


# should be after or be
class ActivityBaseHomeostasis(Behaviour):
    def set_variables(self, n):
        self.max_activity = self.get_init_attr("max_activity", 50, n)
        self.min_activity = self.get_init_attr("min_activity", 10, n)
        self.window_size = self.get_init_attr("window_size", 100, n)
        self.updating_rate = self.get_init_attr("updating_rate", 0.001, n)

        # TODO: unsafe code need more time to digest the possibilities
        activity_rate = self.get_init_attr("activity_rate", 5, n)
        if isinstance(activity_rate, float) or isinstance(activity_rate, int):
            activity_rate = n.get_neuron_vec(mode="ones") * activity_rate

        self.activity_step = -self.window_size / activity_rate
        self.activities = n.get_neuron_vec(mode="zeros")
        self.exhaustion = n.get_neuron_vec()

    def new_iteration(self, n):
        self.activities += np.where(n.fired, 1, self.activity_step)

        if (n.iteration % self.window_size) == 0:
            greater = ((self.activities > self.max_activity) * -1).astype(def_dtype)
            smaller = ((self.activities < self.min_activity) * 1).astype(def_dtype)
            greater *= self.activities - self.max_activity
            smaller *= self.min_activity - self.activities

            change = (greater + smaller) * self.updating_rate
            self.exhaustion += change
            n.threshold -= self.exhaustion
