from src.core.visualizer.history_recoreder_1d import HistoryRecorder1D
from src.core.visualizer.history_recoreder_2d import HistoryRecorder2D

dopamine_plotter = HistoryRecorder1D(title="dopamine", window_size=25, enabled=False)
dw_plotter = HistoryRecorder1D(title="dw", window_size=25, enabled=False)
w_plotter = HistoryRecorder2D(title="w", window_size=25)
delay_plotter = HistoryRecorder2D(title="delay", window_size=25, enabled=False)
threshold_plotter = HistoryRecorder1D(title="threshold", enabled=False)
