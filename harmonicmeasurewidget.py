from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QSpacerItem
from mytools.plotwidget import PlotWidget


class HarmonicMeasureWidget(QWidget):

    def __init__(self, parent=None, domain=None):
        super().__init__(parent)

        self._domain = domain

        self._plot = PlotWidget(parent=None, toolbar=True)

        self.btnMeasure = QPushButton('Измерить')

        self._hlay = QHBoxLayout()
        self._hlay.addWidget(self.btnMeasure)
        self._hlay.addStretch()

        self._layout = QVBoxLayout()
        self._layout.addItem(self._hlay)
        self._layout.addWidget(self._plot)
        self.setLayout(self._layout)

        self._init()

    def _init(self):
        self._plot.subplots_adjust(bottom=0.150)
        self._plot.set_title('Коэффициент преобразования для N-гармоники')
        self._plot.set_xscale('log')
        self._plot.set_xlabel('F, Гц', labelpad=-2)
        self._plot.set_ylabel('К-т пр., дБ', labelpad=-2)
        self._plot.grid(b=True, which='minor', color='0.7', linestyle='--')
        self._plot.grid(b=True, which='major', color='0.5', linestyle='-')

    def clear(self):
        self._plot.clear()
        self._init()

    def plotHarmonic(self):
        print('plotting harmonic')
        self._plot.plot(self._domain.singleMeasureXs, self._domain.singleMeasureYs, color='0.4')


