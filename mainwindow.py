import errno
import os
import subprocess
import xlsxwriter

from PyQt5 import uic
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import Qt, pyqtSlot, QRegularExpression

from domain import Domain
from harmonicplotwidget import HarmonicPlotWidget
from statplotwidget import StatPlotWidget


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WA_QuitOnClose)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # create instance variables
        self._ui = uic.loadUi("mainwindow.ui", self)

        self._domain = Domain(parent=self)
        self._statPlot = StatPlotWidget(parent=self, domain=self._domain)

        self._harmonicPlot = HarmonicPlotWidget(parent=self, domain=self._domain)
        self._ui.layHarmonic.addLayout(self._ui.codeWidget)
        self._ui.layHarmonic.addWidget(self._harmonicPlot)

        # TODO add harmonic plot widget

        self._ui.tabCharts.insertTab(0, self._statPlot, 'Измерения')
        # self._ui.tabCharts.setCurrentIndex(0)

        self._init()

    def _init(self):
        self._ui.editAnalyzerAddr.setValidator(QRegularExpressionValidator(QRegularExpression(
            '^TCPIP::(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}'
            '([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])::INSTR$')))

        self._setupSignals()
        self._setupControls()
        self._refreshView()

    def _setupSignals(self):
        self._domain.statsReady.connect(self.on_statsReady)
        self._domain.codeMeasured.connect(self.on_codeMeasured)
        self._domain.harmonicMeasured.connect(self.on_harmonicMeasured)

    def _setupControls(self):
        pass

    def _refreshView(self):
        pass

    def _modeFindInstr(self):
        self._ui.btnMeasure.setEnabled(False)
        self._ui.btnMeasureHarmonic.setEnabled(False)
        self._ui.spinCutoffMagnitude.setEnabled(True)

    def _modeMeasureReady(self):
        self._ui.btnMeasure.setEnabled(True)
        self._ui.btnMeasureHarmonic.setEnabled(True)
        self._ui.spinCutoffMagnitude.setEnabled(True)

    def _modeMeasureRunning(self):
        self._ui.btnMeasure.setEnabled(False)
        self._ui.btnMeasureHarmonic.setEnabled(False)
        self._ui.spinCutoffMagnitude.setEnabled(False)

    def _modeMeasureFinished(self):
        self._ui.btnMeasure.setEnabled(True)
        self._ui.btnMeasureHarmonic.setEnabled(True)
        self._ui.spinCutoffMagnitude.setEnabled(True)

    # event handlers
    def resizeEvent(self, event):
        self._refreshView()

    def on_statsReady(self):
        self._modeMeasureFinished()
        self._statPlot.plotStats()

    def on_codeMeasured(self):
        self._statPlot.plotCode()

    def on_harmonicMeasured(self):
        self._harmonicPlot.plotHarmonic()

    @pyqtSlot(str)
    def on_editAnalyzerAddr_textChanged(self, text):
        self._domain.analyzerAddress = text

    @pyqtSlot(float)
    def on_spinCutoffMagnitude_valueChanged(self, value):
        self._domain.cutoffMag = value

    @pyqtSlot()
    def on_btnFindInstr_clicked(self):
        if not self._domain.findInstruments():
            QMessageBox.information(self, 'Ошибка', 'Инструменты не найдены, проверьте подключение.')
            return

        self._ui.editArduino.setText(self._domain.programmerName)
        self._ui.editAnalyzer.setText(self._domain.analyzerName)
        self._modeMeasureReady()

    @pyqtSlot()
    def on_btnMeasure_clicked(self):
        if self._domain.canMeasure:
            self._statPlot.clear()
            self._modeMeasureRunning()
            self._domain.measure()

    @pyqtSlot()
    def on_btnMeasureHarmonic_clicked(self):
        self._domain.measureHarmonic()

    @pyqtSlot(int)
    def on_spinCode_valueChanged(self, value):
        self._domain.code = value

    @pyqtSlot(int)
    def on_spinHarmonic_valueChanged(self, value):
        self._domain.harmonic = value

    @pyqtSlot()
    def on_btnExportPng_clicked(self):
        print('saving images')
        path = ".\\image\\"
        self._statPlot.save(path)
        subprocess.call(f'explorer {path}', shell=True)
        print('done')

    @pyqtSlot()
    def on_btnExportExcel_clicked(self):
        print('export to excel')
        to_export = [('cutoff_freq.xlsx', 'Код', 'Частота среза', self._domain.cutoffXs, self._domain.cutoffYs),
                     ('cutoff_delta.xlsx', 'Код', 'Дельта', self._domain.deltaXs, self._domain.deltaYs)]

        for ex in to_export:
            self.export_to_excel(ex)

        subprocess.call('explorer ' + '.\\excel\\', shell=True)

    def export_to_excel(self, data):
        fname, xname, yname, xdata, ydata = data

        excel_path = ".\\excel\\"
        try:
            os.makedirs(excel_path)
        except OSError as ex:
            if ex.errno != errno.EEXIST:
                raise

        wb = xlsxwriter.Workbook(excel_path + fname)
        ws = wb.add_worksheet("Sheet1")

        ws.write("A1", xname)
        ws.write("B1", yname)

        start_row = 0
        row = 0
        for x, y in zip(xdata, ydata):
            row += 1
            ws.write(start_row + row, 0, x)
            ws.write(start_row + row, 1, y)

        chart = wb.add_chart({"type": "scatter",
                              "subtype": "smooth"})
        chart.add_series({"name": "Sheet1!$B$1",
                          "categories": "=Sheet1!$A$2:$A$" + str(row + 1),
                          "values": "=Sheet1!$B$2:$B$" + str(row + 1)})
        chart.set_x_axis({"name": xname})
        chart.set_y_axis({"name": yname})
        ws.insert_chart("D3", chart)

        wb.close()



