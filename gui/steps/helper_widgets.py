import os

from PyQt5 import QtWidgets, QtWebEngineWidgets
from PyQt5.QtCore import QUrl
import plotly.graph_objects as go
import pkgutil


from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

class _ep_mpl_plot_area(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure(figsize=(200, 200), dpi=150)
        self.axes = fig.add_subplot(111)
        super(_ep_mpl_plot_area, self).__init__(fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        #self.plot()

    def plot_data(self, data):
        #self.figure = go.Figure()
        #self.axes.hold(True)
        for c, sweeps in data.sweeps.items():
            for s, sweep in sweeps.items():
        #        self.figure.add_trace(go.Scatter(x=sweep.x, y=sweep.y, name=f'Channel {c} Sweep {s}'))
                self.axes.plot(sweep.x, sweep.y)
        #self.figure.update_traces()
        
        self.draw()
        #self.setContent(self.figure.to_html())

class ep_quickplot_mpl(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ep_quickplot_mpl, self).__init__(parent)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.canvas = _ep_mpl_plot_area(self)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)
    
    def plot(self, data):
        self.canvas.plot_data(data)

class ep_quickplot(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, parent=None):
        super(ep_quickplot, self).__init__(parent)
        self.plotlyjs_path = os.path.join(os.path.dirname(pkgutil.get_loader("plotly").path), "package_data", "plotly.min.js").replace("\\", "/")
        self.figure = go.Figure()

    def plot(self, data):
        print(data.filename)
        #self.figure.data = []
        self.setPage(QtWebEngineWidgets.QWebEnginePage(self))
        figure = go.Figure()
        for c, sweeps in data.sweeps.items():
            for s, sweep in sweeps.items():
                figure.add_trace(go.Scatter(x=sweep.x, y=sweep.y, name=f'Channel {c} Sweep {s}'))
        
        figure.update_traces()
        raw_html = '<html><head><meta charset="utf-8" />'
        raw_html += f'<script src="file://{self.plotlyjs_path}"></script></head>'
        raw_html += '<body>'
        raw_html += figure.to_html(include_plotlyjs=False, full_html=False)
        raw_html += '</body></html>'

        QtWebEngineWidgets.QWebEngineProfile().clearHttpCache()
        self.setHtml(raw_html, QUrl('file://'))
        #self.reload()
        print(self.figure.data)
        pass