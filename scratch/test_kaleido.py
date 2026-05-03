import plotly.graph_objects as go
import os

try:
    fig = go.Figure(data=[go.Bar(y=[2, 1, 3])])
    fig.write_image("test_plot.png")
    if os.path.exists("test_plot.png"):
        print("KALEIDO_OK")
        os.remove("test_plot.png")
    else:
        print("KALEIDO_FAIL")
except Exception as e:
    print(f"ERROR: {e}")
