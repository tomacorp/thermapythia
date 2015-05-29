#!/Users/toma/python278i/bin/python
# -*- coding: utf-8 -*-
#

import MainWindow

import os
import platform
import sys

from PyQt4.QtGui import (QApplication, QIcon)

__version__ = "1.0.0"
    
def main():
  app = QApplication(sys.argv)
  app.setOrganizationName("tomacorp")
  app.setOrganizationDomain("tomacorp.com")  
  app.setWindowIcon(QIcon(":/icon.png"))
  w = MainWindow.Window()
  w.show()
  sys.exit(app.exec_())   
  
if __name__ == "__main__":
  main()  