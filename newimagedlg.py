
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future_builtins import *

from PyQt4.QtCore import (QVariant, Qt)
from PyQt4.QtCore import pyqtSignal as Signal
from PyQt4.QtGui import (QApplication, QBrush, QColorDialog, QDialog,
                         QPainter, QPixmap)

class NewImageDlg(QDialog, ui_newimagedlg.Ui_NewImageDlg):

  def __init__(self, parent=None):
    super(NewImageDlg, self).__init__(parent)
    self.setupUi(self)

    self.color = Qt.red
    for value, text in (
      (Qt.SolidPattern, "Solid"),
      (Qt.Dense1Pattern, "Dense #1"),
      (Qt.Dense2Pattern, "Dense #2"),
      (Qt.Dense3Pattern, "Dense #3"),
      (Qt.Dense4Pattern, "Dense #4"),
      (Qt.Dense5Pattern, "Dense #5"),
      (Qt.Dense6Pattern, "Dense #6"),
      (Qt.Dense7Pattern, "Dense #7"),
      (Qt.HorPattern, "Horizontal"),
      (Qt.VerPattern, "Vertical"),
      (Qt.CrossPattern, "Cross"),
      (Qt.BDiagPattern, "Backward Diagonal"),
      (Qt.FDiagPattern, "Forward Diagonal"),
      (Qt.DiagCrossPattern, "Diagonal Cross")):
      self.brushComboBox.addItem(text, QVariant(value))

    self.colorButton.clicked.connect(self.getColor)
    self.brushComboBox.activated.connect(self.setColor)
    self.setColor()
    self.widthSpinBox.setFocus()


  def getColor(self):
    color = QColorDialog.getColor(Qt.black, self)
    if color.isValid():
      self.color = color
      self.setColor()


  def setColor(self):
    pixmap = self._makePixmap(60, 30)
    self.colorLabel.setPixmap(pixmap)


  def image(self):
    pixmap = self._makePixmap(self.widthSpinBox.value(),
                              self.heightSpinBox.value())
    return QPixmap.toImage(pixmap)


  def _makePixmap(self, width, height):
    pixmap = QPixmap(width, height)
    style = self.brushComboBox.itemData(
      self.brushComboBox.currentIndex()).toInt()[0]
    brush = QBrush(self.color, Qt.BrushStyle(style))
    painter = QPainter(pixmap)
    painter.fillRect(pixmap.rect(), Qt.white)
    painter.fillRect(pixmap.rect(), brush)
    return pixmap


if __name__ == "__main__":
  import sys

  app = QApplication(sys.argv)
  form = NewImageDlg()
  form.show()
  app.exec_()

