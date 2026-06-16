"""Matplotlib setup for trend charts."""
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.ticker import MaxNLocator
    MATPLOTLIB_OK = True

    def setup_matplotlib_chinese():
        plt.rcParams["font.sans-serif"] = [
            "Microsoft YaHei", "SimHei", "SimSun", "PingFang SC", "Noto Sans CJK SC", "sans-serif",
        ]
        plt.rcParams["axes.unicode_minus"] = False
except ImportError:
    MATPLOTLIB_OK = False
    MaxNLocator = None
    plt = None
    mdates = None

    def setup_matplotlib_chinese():
        pass
