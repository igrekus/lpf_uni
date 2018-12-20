import errno
import os
import subprocess
import xlsxwriter

from PyQt5 import uic
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import Qt, pyqtSlot, QRegularExpression

from domain import Domain
from harmonicmeasurewidget import HarmonicMeasureWidget
from singlemeasurewidget import SingleMeasureWidget
from statplotwidget import StatPlotWidget


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WA_QuitOnClose)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # create instance variables
        self._ui = uic.loadUi("mainwindow.ui", self)

        self._domain = Domain(parent=self)

        self._ui.singleMeasure = SingleMeasureWidget(parent=self, domain=self._domain)
        self._ui.layHarmonic.addLayout(self._ui.layCode)
        self._ui.layHarmonic.addWidget(self._ui.singleMeasure)

        self._ui.statPlot = StatPlotWidget(parent=self, domain=self._domain)
        self._ui.tabwidgetCharts.insertTab(0, self._ui.statPlot, 'Измерения')

        self._ui.harmonicMeasure = HarmonicMeasureWidget(parent=self, domain=self._domain)
        self._ui.tabwidgetCharts.insertTab(1, self._ui.harmonicMeasure, 'Гармоники')

        self._init()

    def _init(self):
        self._ui.editAnalyzerAddr.setValidator(QRegularExpressionValidator(QRegularExpression(
            '^TCPIP::(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}'
            '([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])::INSTR$')))

        self._setupSignals()
        self._setupControls()
        self._refreshView()

    def _setupSignals(self):
        self._ui.harmonicMeasure.btnMeasure.clicked.connect(self.on_btnMeasureHarmonic_clicked)
        self._domain.statsReady.connect(self.on_statsReady)
        self._domain.codeMeasured.connect(self.on_codeMeasured)
        self._domain.harmonicMeasured.connect(self.on_harmonicMeasured)
        self._domain.singleMeasured.connect(self.on_singleMeasured)

    def _setupControls(self):
        pass
        # self._ui.tabwidgetCharts.setCurrentIndex(0)

    def _refreshView(self):
        pass

    def _modeFindInstr(self):
        self._ui.btnMeasure.setEnabled(False)
        self._ui.btnMeasureSingle.setEnabled(False)
        self._ui.spinCutoffMagnitude.setEnabled(True)
        self._ui.harmonicMeasure.btnMeasure.setEnabled(False)

    def _modeMeasureReady(self):
        self._ui.btnMeasure.setEnabled(True)
        self._ui.btnMeasureSingle.setEnabled(True)
        self._ui.spinCutoffMagnitude.setEnabled(True)
        self._ui.harmonicMeasure.btnMeasure.setEnabled(False)

    def _modeMeasureRunning(self):
        self._ui.btnMeasure.setEnabled(False)
        self._ui.btnMeasureSingle.setEnabled(False)
        self._ui.spinCutoffMagnitude.setEnabled(False)
        self._ui.harmonicMeasure.btnMeasure.setEnabled(False)

    def _modeMeasureFinished(self):
        self._ui.btnMeasure.setEnabled(True)
        self._ui.btnMeasureSingle.setEnabled(True)
        self._ui.spinCutoffMagnitude.setEnabled(True)
        self._ui.harmonicMeasure.btnMeasure.setEnabled(True)

    # event handlers
    def resizeEvent(self, event):
        self._refreshView()

    def on_statsReady(self):
        self._modeMeasureFinished()
        self._ui.statPlot.plotStats()

    def on_codeMeasured(self):
        self._ui.statPlot.plotCode()

    def on_harmonicMeasured(self):
        self._ui.harmonicMeasure.btnMeasure.setEnabled(True)
        try:
            self._ui.harmonicMeasure.plot()
        except Exception as ex:
            print(ex)

    def on_singleMeasured(self):
        self._ui.singleMeasure.plot()

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
            self._ui.statPlot.clear()
            self._modeMeasureRunning()
            self._domain.measure()

    @pyqtSlot()
    def on_btnMeasureSingle_clicked(self):
        self._domain.measureSingle()

    @pyqtSlot()
    def on_btnMeasureHarmonic_clicked(self):
        if not self._domain.amps:
            QMessageBox.information(self, 'Внимание',
                                    'Сперва необходимо провести стандартное измерение.')
            return

        self._ui.harmonicMeasure.clear()
        self._domain.measureHarmonics()
        self._ui.harmonicMeasure.btnMeasure.setEnabled(False)

    @pyqtSlot(int)
    def on_spinCode_valueChanged(self, value):
        self._domain.code = value

    @pyqtSlot(int)
    def on_spinHarmonic_valueChanged(self, value):
        self._domain.harmonicN = value

    @pyqtSlot()
    def on_btnExportPng_clicked(self):
        print('saving images')
        path = ".\\image\\"
        self._ui.statPlot.save(path)
        subprocess.call(f'explorer {path}', shell=True)
        print('done')

    @pyqtSlot()
    def on_btnExportExcel_clicked(self):
        print('export to excel')
        to_export = [('частота_среза.xlsx', 'Код', 'Частота среза', self._domain.cutoffXs, self._domain.cutoffYs),
                     ('дельта_частоты.xlsx', 'Код', 'Дельта', self._domain.deltaXs, self._domain.deltaYs),
                     ('затухание_x2.xlsx', 'Код', 'Затухание при x2 частоте', self._domain.lossDoubleXs, self._domain.lossDoubleYs),
                     ('затухание_x3.xlsx', 'Код', 'Затухание при x3 частоте', self._domain.lossTripleXs, self._domain.lossTripleYs)]

        try:
            for ex in to_export:
                self.export_to_excel(ex)

            self.export_to_excel_double_data(
                ('подавление_гармоник.xlsx', 'Код', 'Подавление x2', 'Подавление х3', self._domain.codes, self._domain.harm_deltas[2], self._domain.harm_deltas[3])
            )

        except Exception as ex:
            print(ex)
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

    def export_to_excel_double_data(self, data):
        fname, xname, yname1, yname2, xdata, ydata1, ydata2 = data

        excel_path = ".\\excel\\"
        try:
            os.makedirs(excel_path)
        except OSError as ex:
            if ex.errno != errno.EEXIST:
                raise

        wb = xlsxwriter.Workbook(excel_path + fname)
        ws = wb.add_worksheet("Sheet1")

        ws.write("A1", xname)
        ws.write("B1", yname1)
        ws.write("C1", yname2)

        start_row = 0
        row = 0
        for x, y1, y2 in zip(xdata, ydata1, ydata2):
            row += 1
            ws.write(start_row + row, 0, x)
            ws.write(start_row + row, 1, y1)
            ws.write(start_row + row, 2, y2)

        chart = wb.add_chart({
            "type": "scatter",
            "subtype": "smooth"
        })
        chart.add_series({
            "name": "Sheet1!$B$1",
            "categories": "=Sheet1!$A$2:$A$" + str(row + 1),
            "values": "=Sheet1!$B$2:$B$" + str(row + 1)
        })
        chart.add_series({
            "name": "Sheet1!$C$1",
            "categories": "=Sheet1!$A$2:$A$" + str(row + 1),
            "values": "=Sheet1!$C$2:$C$" + str(row + 1)
        })
        chart.set_x_axis({"name": xname})
        chart.set_y_axis({"name": 'Подавление гармоник'})
        ws.insert_chart("F3", chart)

        wb.close()

