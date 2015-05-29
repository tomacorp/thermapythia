#!/Users/toma/python278i/bin/python
# -*- coding: utf-8 -*-
#
# Create the resources file with:
#   pyrcc4 -o qrc_resources.py resources.qrc
# This wraps the files in images/*.png and help/*.html in the file qrc_resources.py
#
# Preferences are stored in $HOME/Library/Preferences/com.tomacorp.python.plist

# TODO: Database connection should not be re-opened, this is throwing:
#    QSqlDatabasePrivate::addDatabase: duplicate connection name 'qt_sql_default_connection', old connection removed.
#

import os
import platform
import sys

import yaml

from PyQt4.QtCore import (PYQT_VERSION_STR, QFile, QFileInfo, QSettings,
                          QString, QT_VERSION_STR, QTimer, QVariant, Qt)
from PyQt4.QtCore import pyqtSignal as Signal
from PyQt4.QtGui import (QAction, QActionGroup, QApplication,
                         QDockWidget, QFileDialog, QFrame, QIcon, QImage, QImageReader,
                         QImageWriter, QInputDialog, QKeySequence, QLabel, QListWidget,
                         QMainWindow, QMessageBox, QPainter, QPixmap, QPrintDialog,
                         QPrinter, QSpinBox, QDialog, QTableView, QVBoxLayout)
from PyQt4.QtSql import (QSqlDatabase, QSqlQuery, QSqlTableModel, QSqlRelationalTableModel,
                         QSqlRelationalDelegate)
import HelpForm
import qrc_resources

import Matls
import Vias
import Layers
# import Zzz

__version__ = "1.0.0"

class MatlDelegate(QSqlRelationalDelegate):
  def __init__(self, parent=None):
    super(MatlDelegate, self).__init__(parent)

class MatlForm(QDialog):
  def __init__(self):
    super(MatlForm, self).__init__()
    
    
    
    if 1 == 0:
      self.matlModel= QSqlRelationalTableModel(self)
      self.matlModel.setTable('matl')
      self.matlModel.setHeaderData(0, Qt.Horizontal,QVariant('name'))
      self.matlModel.select()
      
      self.matlView= QTableView()
      self.matlView.setModel(self.matlModel)
      self.matlView.setItemDelegate(MatlDelegate(self))
      self.matlView.setSelectionMode(QTableView.SingleSelection)
      self.matlView.setSelectionBehavior(QTableView.SelectRows)
      self.matlView.resizeColumnsToContents()
      
      self.matlView.layout()
    
    matlViewLabel= QLabel("<font color=green size=72><b> Material Editor </b></font>")
    
    if 1 == 0:
      dataLayout= QVBoxLayout()
      dataLayout.addWidget(self.matlViewLabel)
      dataLayout.addWidget(self.matlView)
      self.setLayout(dataLayout)    
      self.matlPopup.show()
      self.matlPropsHere.show()
      self.show()    


class Window(QMainWindow):

  def __init__(self, parent=None):
    super(Window, self).__init__(parent)
    self.image = QImage()
    self.dirty = False
    self.filename = None
    self.dbFilename = None
    self.mirroredvertically = False
    self.mirroredhorizontally = False
    self.printer = None
    self.exampleForm= None
    self.matlPopup= None
    self.matlPropsHere= None
    self.create_widgets()
    self.create_actions()
    self.load_settings()
    self.setWindowTitle("Thermapythia")
    self.updateFileMenu()
    self.openStackupDB()
    QTimer.singleShot(0, self.loadInitialFile)


  def create_widgets(self):
    self.imageLabel = QLabel()
    self.imageLabel.setMinimumSize(200, 200)
    self.imageLabel.setAlignment(Qt.AlignCenter)
    self.imageLabel.setContextMenuPolicy(Qt.ActionsContextMenu)
    self.setCentralWidget(self.imageLabel)

    logDockWidget = QDockWidget("Log", self)
    logDockWidget.setObjectName("LogDockWidget")
    logDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea|
                                  Qt.RightDockWidgetArea)
    self.listWidget = QListWidget()
    logDockWidget.setWidget(self.listWidget)
    self.addDockWidget(Qt.RightDockWidgetArea, logDockWidget)

    self.sizeLabel = QLabel()
    self.sizeLabel.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
    status = self.statusBar()
    status.setSizeGripEnabled(False)
    status.addPermanentWidget(self.sizeLabel)
    status.showMessage("Ready", 5000)


  def create_actions(self):
    fileNewAction = self.createAction("&New...", self.fileNew,
                                      QKeySequence.New, "filenew", "Create an image file")
    fileOpenAction = self.createAction("&Open...", self.fileOpen,
                                       QKeySequence.Open, "fileopen",
                                       "Open an existing image file")
    fileSaveAction = self.createAction("&Save", self.fileSave,
                                       QKeySequence.Save, "filesave", "Save the image")
    fileSaveAsAction = self.createAction("Save &As...",
                                         self.fileSaveAs, icon="filesaveas",
                                         tip="Save the image using a new name")
    filePrintAction = self.createAction("&Print", self.filePrint,
                                        QKeySequence.Print, "fileprint", "Print the image")
    fileQuitAction = self.createAction("&Quit", self.close,
                                       "Ctrl+Q", "filequit", "Close the application")
    
    
    
    
    # createAction(String, slot, shortcut, icon, tip, checkable
    matlEditAction = self.createAction("&Materials", self.matlEdit, 
                                      None, "matls", "Edit materials")
    layerEditAction= self.createAction("&Layers", self.layerEdit, 
                                      None, "layers", "Edit layers") 
    viaEditAction= self.createAction("&Vias", self.viaEdit, 
                                      None, "vias", "Edit vias")  
    zzzEditAction= self.createAction("&Zzz", self.zzzEdit, 
                                     None, "zzz", "Edit zzz")     
    
    
    
    editInvertAction = self.createAction("&Invert", None, "Ctrl+I",
                                         "editinvert", "Invert the image's colors", True)
    editInvertAction.toggled.connect(self.editInvert)
    editSwapRedAndBlueAction = self.createAction("Sw&ap Red and Blue",
                                                 None, "Ctrl+A", "editswap",
                                                 "Swap the image's red and blue color components", True)
    editSwapRedAndBlueAction.toggled.connect(self.editSwapRedAndBlue)
    editZoomAction = self.createAction("&Zoom...", self.editZoom,
                                       "Alt+Z", "editzoom", "Zoom the image")
    mirrorGroup = QActionGroup(self)
    editUnMirrorAction = self.createAction("&Unmirror", None, "Ctrl+U",
                                           "editunmirror", "Unmirror the image", True)
    editUnMirrorAction.toggled.connect(self.editUnMirror)
    mirrorGroup.addAction(editUnMirrorAction)
    editMirrorHorizontalAction = self.createAction(
      "Mirror &Horizontally", None, "Ctrl+H", "editmirrorhoriz",
      "Horizontally mirror the image", True)
    editMirrorHorizontalAction.toggled.connect(
      self.editMirrorHorizontal)
    mirrorGroup.addAction(editMirrorHorizontalAction)
    editMirrorVerticalAction = self.createAction("Mirror &Vertically",
                                                 None, "Ctrl+V", "editmirrorvert",
                                                 "Vertically mirror the image", True)
    editMirrorVerticalAction.toggled.connect(self.editMirrorVertical)
    mirrorGroup.addAction(editMirrorVerticalAction)
    editUnMirrorAction.setChecked(True)
    helpAboutAction = self.createAction("&About Thermapythia",
                                        self.helpAbout)
    helpHelpAction = self.createAction("&Help", self.helpHelp,
                                       QKeySequence.HelpContents)

    self.fileMenu = self.menuBar().addMenu("&File")
    self.fileMenuActions = (fileNewAction, fileOpenAction,
                            fileSaveAction, fileSaveAsAction, None, filePrintAction,
                            fileQuitAction)
    self.fileMenu.aboutToShow.connect(self.updateFileMenu)
    
    stackupMenu = self.menuBar().addMenu("&Stackup")
    self.addActions(stackupMenu, (matlEditAction, layerEditAction, viaEditAction))
    
    
    editMenu = self.menuBar().addMenu("&Edit")
    self.addActions(editMenu, (editInvertAction,
                               editSwapRedAndBlueAction, editZoomAction))
    
    
    mirrorMenu = editMenu.addMenu(QIcon(":/editmirror.png"),
                                  "&Mirror")
    self.addActions(mirrorMenu, (editUnMirrorAction,
                                 editMirrorHorizontalAction, editMirrorVerticalAction))
    helpMenu = self.menuBar().addMenu("&Help")
    self.addActions(helpMenu, (helpAboutAction, helpHelpAction))

    fileToolbar = self.addToolBar("File")
    fileToolbar.setObjectName("FileToolBar")
    self.addActions(fileToolbar, (fileNewAction, fileOpenAction,
                                  fileSaveAsAction))
    
    stackupToolbar = self.addToolBar("Stackup")
    stackupToolbar.setObjectName("StackupToolBar")
    self.addActions(stackupToolbar, (matlEditAction, layerEditAction, viaEditAction))
    
    editToolbar = self.addToolBar("Edit")
    editToolbar.setObjectName("EditToolBar")
    self.addActions(editToolbar, (editInvertAction,
                                  editSwapRedAndBlueAction, editUnMirrorAction,
                                  editMirrorVerticalAction, editMirrorHorizontalAction))
    self.zoomSpinBox = QSpinBox()
    self.zoomSpinBox.setRange(1, 400)
    self.zoomSpinBox.setSuffix(" %")
    self.zoomSpinBox.setValue(100)
    self.zoomSpinBox.setToolTip("Zoom the image")
    self.zoomSpinBox.setStatusTip(self.zoomSpinBox.toolTip())
    self.zoomSpinBox.setFocusPolicy(Qt.NoFocus)
    self.zoomSpinBox.valueChanged.connect(self.showImage)
    editToolbar.addWidget(self.zoomSpinBox)

    self.addActions(self.imageLabel, (editInvertAction,
                                      editSwapRedAndBlueAction, editUnMirrorAction,
                                      editMirrorVerticalAction, editMirrorHorizontalAction))

    self.resetableActions = ((editInvertAction, False),
                             (editSwapRedAndBlueAction, False),
                             (editUnMirrorAction, True))


  def load_settings(self):
    settings = QSettings()
    self.recentFiles = settings.value("RecentFiles").toStringList()
    self.restoreGeometry(
      settings.value("MainWindow/Geometry").toByteArray())
    self.restoreState(settings.value("MainWindow/State").toByteArray())


  def createAction(self, text, slot=None, shortcut=None, icon=None,
                   tip=None, checkable=False):
    action = QAction(text, self)
    if icon is not None:
      action.setIcon(QIcon(":/{0}.png".format(icon)))
    if shortcut is not None:
      action.setShortcut(shortcut)
    if tip is not None:
      action.setToolTip(tip)
      action.setStatusTip(tip)
    if slot is not None:
      action.triggered.connect(slot)
    if checkable:
      action.setCheckable(True)
    return action


  def addActions(self, target, actions):
    for action in actions:
      if action is None:
        target.addSeparator()
      else:
        target.addAction(action)


  def closeEvent(self, event):
    if self.okToContinue():
      settings = QSettings()
      filename = (QVariant(QString(self.filename))
                  if self.filename is not None else QVariant())
      settings.setValue("LastFile", filename)
      recentFiles = (QVariant(self.recentFiles)
                     if self.recentFiles else QVariant())
      settings.setValue("RecentFiles", recentFiles)
      settings.setValue("MainWindow/Geometry", QVariant(
        self.saveGeometry()))
      settings.setValue("MainWindow/State", QVariant(
        self.saveState()))
    else:
      event.ignore()


  def okToContinue(self):
    if self.dirty:
      reply = QMessageBox.question(self,
                                   "Thermapythia - Unsaved Changes",
                                   "Save unsaved changes?",
                                   QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
      if reply == QMessageBox.Cancel:
        return False
      elif reply == QMessageBox.Yes:
        return self.fileSave()
    return True


  def loadInitialFile(self):
    settings = QSettings()
    fname = unicode(settings.value("LastFile").toString())
    if fname and QFile.exists(fname):
      self.loadFile(fname)


  def updateStatus(self, message):
    self.statusBar().showMessage(message, 5000)
    self.listWidget.addItem(message)
    if self.filename is not None:
      self.setWindowTitle("Thermapythia - {0}[*]".format(
        os.path.basename(self.filename)))
    elif not self.image.isNull():
      self.setWindowTitle("Thermapythia - Unnamed[*]")
    else:
      self.setWindowTitle("Thermapythia[*]")
    self.setWindowModified(self.dirty)

  def updateFileMenu(self):
    self.fileMenu.clear()
    self.addActions(self.fileMenu, self.fileMenuActions[:-1])
    current = (QString(self.filename)
               if self.filename is not None else None)
    recentFiles = []
    for fname in self.recentFiles:
      if fname != current and QFile.exists(fname):
        recentFiles.append(fname)
    if recentFiles:
      self.fileMenu.addSeparator()
      for i, fname in enumerate(recentFiles):
        action = QAction(QIcon(":/icon.png"),
                         "&{0} {1}".format(i + 1, QFileInfo(
                           fname).fileName()), self)
        action.setData(QVariant(fname))
        action.triggered.connect(self.loadFile)
        self.fileMenu.addAction(action)
    self.fileMenu.addSeparator()
    self.fileMenu.addAction(self.fileMenuActions[-1])

  def fileNew(self):
    if not self.okToContinue():
      return
    dialog = newimagedlg.NewImageDlg(self)
    if dialog.exec_():
      self.addRecentFile(self.filename)
      self.image = QImage()
      for action, check in self.resetableActions:
        action.setChecked(check)
      self.image = dialog.image()
      self.filename = None
      self.dirty = True
      self.showImage()
      self.sizeLabel.setText("{0} x {1}".format(self.image.width(),
                                                self.image.height()))
      self.updateStatus("Created new image")


  def fileOpen(self):
    if not self.okToContinue():
      return
    dir = (os.path.dirname(self.filename)
           if self.filename is not None else ".")
    formats = (["*.{0}".format(unicode(format).lower())
                for format in QImageReader.supportedImageFormats()])
    fname = unicode(QFileDialog.getOpenFileName(self,
                                                "Thermapythia - Choose Image", dir,
                                                "Image files ({0})".format(" ".join(formats))))
    if fname:
      self.loadFile(fname)


  def loadFile(self, fname=None):
    if fname is None:
      action = self.sender()
      if isinstance(action, QAction):
        fname = unicode(action.data().toString())
        if not self.okToContinue():
          return
      else:
        return
    if fname:
      self.filename = None
      image = QImage(fname)
      if image.isNull():
        message = "Failed to read {0}".format(fname)
      else:
        self.addRecentFile(fname)
        self.image = QImage()
        for action, check in self.resetableActions:
          action.setChecked(check)
        self.image = image
        self.filename = fname
        self.showImage()
        self.dirty = False
        self.sizeLabel.setText("{0} x {1}".format(
          image.width(), image.height()))
        message = "Loaded {0}".format(os.path.basename(fname))
      self.updateStatus(message)


  def addRecentFile(self, fname):
    if fname is None:
      return
    if not self.recentFiles.contains(fname):
      self.recentFiles.prepend(QString(fname))
      while self.recentFiles.count() > 9:
        self.recentFiles.takeLast()


  def fileSave(self):
    if self.image.isNull():
      return True
    if self.filename is None:
      return self.fileSaveAs()
    else:
      if self.image.save(self.filename, None):
        self.updateStatus("Saved as {0}".format(self.filename))
        self.dirty = False
        return True
      else:
        self.updateStatus("Failed to save {0}".format(
          self.filename))
        return False


  def fileSaveAs(self):
    if self.image.isNull():
      return True
    fname = self.filename if self.filename is not None else "."
    formats = (["*.{0}".format(unicode(format).lower())
                for format in QImageWriter.supportedImageFormats()])
    fname = unicode(QFileDialog.getSaveFileName(self,
                                                "Thermapythia - Save Image", fname,
                                                "Image files ({0})".format(" ".join(formats))))
    if fname:
      if "." not in fname:
        fname += ".png"
      self.addRecentFile(fname)
      self.filename = fname
      return self.fileSave()
    return False


  def filePrint(self):
    if self.image.isNull():
      return
    if self.printer is None:
      self.printer = QPrinter(QPrinter.HighResolution)
      self.printer.setPageSize(QPrinter.Letter)
    form = QPrintDialog(self.printer, self)
    if form.exec_():
      painter = QPainter(self.printer)
      rect = painter.viewport()
      size = self.image.size()
      size.scale(rect.size(), Qt.KeepAspectRatio)
      painter.setViewport(rect.x(), rect.y(), size.width(),
                          size.height())
      painter.drawImage(0, 0, self.image)
  
  
  
  #
  def openStackupDB(self):
  
    if self.dbFilename != None:
      return
    self.dbFilename = os.path.join(os.path.dirname(__file__), "stackup.db")
    create = not QFile.exists(self.dbFilename)
  
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(self.dbFilename)
    if not db.open():
      QMessageBox.warning(None, "Can't open stackup database",
                          QString("Database Error: %1").arg(db.lastError().text()))
      sys.exit(1)  
    if create == False:
      self.updateStatus("Found stackup database file: " + str(self.dbFilename))
      
    self.createDatabaseTables()
      
    with open('test2.js', "r") as jsonHandle:
      jsonContents= jsonHandle.read()    
    config= yaml.load(jsonContents)    
      
    matlCount= self.countDatabaseTableRows("matl")
    if matlCount == 0:
      self.updateStatus("material editor call goes here.")
      #
      # TODO: Put the guess-what-I'm thinking Qt table editor thing here.
      #
      # self.loadDefaultMatls()
      matls = Matls.Matls(config['matl_config'])
      self.loadDefaultData('matl', matls)      
      
    viaCount= self.countDatabaseTableRows("via")
    if viaCount == 0:  
      vias = Vias.Vias(config['via_config'])
      self.loadDefaultData('via', vias)
      
    layerCount= self.countDatabaseTableRows("layer")
    if layerCount == 0:  
      layers = Layers.Layers(config['layer_config'])
      self.loadDefaultData('layer', layers)
      
    # initialize zzz new content here, perhaps
  
  def createDatabaseTables(self):
    query = QSqlQuery()
    self.updateStatus("Creating database tables")
          # "id" INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
    statusMatl = query.exec_("""CREATE TABLE IF NOT EXISTS "matl" (
                  "name" TEXT,
                  "type" TEXT,
                  "density" real,
                  "color" TEXT,
                  "specific_heat" real,
                  "conductivity" real,
                  "conductivityXX" real,
                  "conductivityYY" real,
                  "conductivityZZ" real,
                  "reflection_coeff" real,
                  "emissivity" real,
                  "max_height" real,
                  "thickness" real
                  );""")
    if statusMatl == False:
      self.updateStatus("Could not create material property database table 'matl'")
      self.updateStatus("Database error message: " + query.lastError().text())
    
    statusPhylayer = query.exec_("""CREATE TABLE IF NOT EXISTS "layer" (
                  "id" INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                  "name" TEXT,
                  "matl" TEXT,
                  "type" TEXT,
                  "thickness" real,
                  "displaces" TEXT,
                  "coverage" real,
                  "z_bottom" real,
                  "z_top" real,
                  "adheres_to" TEXT);""")
    if statusPhylayer == False:
      self.updateStatus("Could not create material property database table 'layer'")
      self.updateStatus("Database error message: " + query.lastError().text())  
    
    statusVia = query.exec_("""CREATE TABLE IF NOT EXISTS "via" (
                  "id" INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                  "name" TEXT,
                  "matl" TEXT,
                  "to" TEXT,
                  "from" TEXT);""")
    if statusVia == False:
      self.updateStatus("Could not create material property database table 'via'")
      self.updateStatus("Database error message: " + query.lastError().text())      
    
  def countDatabaseTableRows(self, tablename):
    query = QSqlQuery()
    self.updateStatus("Loading database tables")    
    query.prepare("select count(*) from " + tablename + ";")
    status = query.exec_()
    if status == False:
      self.updateStatus("Could not count entries in table '" + tablename + "'")
      self.updateStatus("Database error message: " + query.lastError().text())
    query.first()
    count, ok = query.value(0).toInt()
    # self.updateStatus("There are " + str(count) + " rows in the " + tablename + " table")
    return count

  def loadDefaultData(self, table, data):
    query = QSqlQuery()
    insertList= "', '".join(data.tableCols)
    insertList= "'" + insertList + "'"    
    colCount= len(data.tableCols)
    quest= ""
    for i in range(0, colCount):
      quest = quest + "?,"
    quest= quest[:-1]
    
    sql= "INSERT INTO " + table + "(" + insertList + ") VALUES (" + quest + ");"
    # self.updateStatus(sql)
    status= query.prepare(sql)
    if status == False:
      self.updateStatus("Could not prepare material property database table " + table)
      self.updateStatus("Database error message: " + query.lastError().text())    
    
    for row in data.propDict:
      for prop in data.tableCols:
        propval= data.propDict[row][prop]
        if data.tableColSQLTypes[prop] == 'TEXT':
          query.addBindValue(QVariant(QString(propval)))
          # self.updateStatus("Setting TEXT property " + prop + " to value " + str(propval) + " in row " + str(row))
        elif data.tableColSQLTypes[prop] == 'real':
          if (propval == '-'):
            propreal= -999.9
          else:
            propreal= float(propval)
          query.addBindValue(QVariant(propreal))
          # self.updateStatus("Setting real property " + prop + " to value " + str(propreal) + " in row " + str(row))
      status= query.exec_()
      if status == False:
        self.updateStatus("Could not load property database table " + table + " with " + str(row))
        self.updateStatus("Database error message: " + query.lastError().text())
 
 
 
  def matlEdit(self):
    self.dirty= True
    self.updateStatus("Call edit material code here")
    # This ends up in a little child window
    
    
    self.matlPopup= QLabel("<font color=green size=72><b> Material Editor </b></font>")
    # self.matlPopup.setWindowFlags(Qt.SplashScreen)
    self.matlPopup.setWindowTitle("Material edit popup")
    
    self.matlPropsHere= QLabel("<font color=red size=24><b> Data goes here </b></font>")
    # self.matlPopup.setWindowFlags(Qt.SplashScreen) 
    
    if 1 == 0:
      dataLayout= QVBoxLayout()
      dataLayout.addWidget(self.matlPopup)
      dataLayout.addWidget(self.matlPropsHere)
      self.setLayout(dataLayout)    
    
    self.matlPopup.show()
    self.matlPropsHere.show()
    
#    self.exampleForm= MatlForm()
    # First need a layout manager, and add the widget to that. 
    # Then attach the layout manager to a window.
    # addWidget(self.exampleForm)
#    self.exampleForm.show()
    
    QTimer.singleShot(5000, self.update)
    
    self.updateStatus("Created stackup db")
    
  def layerEdit(self):
    self.dirty= True
    self.updateStatus("Call edit layer code here") 
    
    # This way of doing it is modal - window doesn't go away and covers up other windows until it is dismissed.
    form= MatlForm()
    form.exec_()
    

  def viaEdit(self):
    self.dirty= True
    self.updateStatus("Call edit via code here")

  def zzzEdit(self):
    self.dirty= True
    self.updateStatus("Call code to be triggered by zzz button here")         

  def editInvert(self, on):
    if self.image.isNull():
      return
    self.image.invertPixels()
    self.showImage()
    self.dirty = True
    self.updateStatus("Inverted" if on else "Uninverted")
       

  def editSwapRedAndBlue(self, on):
    if self.image.isNull():
      return
    self.image = self.image.rgbSwapped()
    self.showImage()
    self.dirty = True
    self.updateStatus(("Swapped Red and Blue"
                       if on else "Unswapped Red and Blue"))


  def editUnMirror(self, on):
    if self.image.isNull():
      return
    if self.mirroredhorizontally:
      self.editMirrorHorizontal(False)
    if self.mirroredvertically:
      self.editMirrorVertical(False)


  def editMirrorHorizontal(self, on):
    if self.image.isNull():
      return
    self.image = self.image.mirrored(True, False)
    self.showImage()
    self.mirroredhorizontally = not self.mirroredhorizontally
    self.dirty = True
    self.updateStatus(("Mirrored Horizontally"
                       if on else "Unmirrored Horizontally"))


  def editMirrorVertical(self, on):
    if self.image.isNull():
      return
    self.image = self.image.mirrored(False, True)
    self.showImage()
    self.mirroredvertically = not self.mirroredvertically
    self.dirty = True
    self.updateStatus(("Mirrored Vertically"
                       if on else "Unmirrored Vertically"))


  def editZoom(self):
    if self.image.isNull():
      return
    percent, ok = QInputDialog.getInteger(self,
                                          "Thermapythia - Zoom", "Percent:",
                                          self.zoomSpinBox.value(), 1, 400)
    if ok:
      self.zoomSpinBox.setValue(percent)


  def showImage(self, percent=None):
    if self.image.isNull():
      return
    if percent is None:
      percent = self.zoomSpinBox.value()
    factor = percent / 100.0
    width = self.image.width() * factor
    height = self.image.height() * factor
    image = self.image.scaled(width, height, Qt.KeepAspectRatio)
    self.imageLabel.setPixmap(QPixmap.fromImage(image))


  def helpAbout(self):
    QMessageBox.about(self, "About Thermapythia",
                      """<b>Thermapythia</b> v {0}
                <p>Thermal Analyzer in Python predicts circuit board temperature
                <p>Python {1} - Qt {2} - PyQt {3} on {4}""".format(
                                                             __version__, platform.python_version(),
                                                             QT_VERSION_STR, PYQT_VERSION_STR,
                                                             platform.system()))


  def helpHelp(self):
    form = HelpForm.HelpForm("index.html", self)
    form.show()
