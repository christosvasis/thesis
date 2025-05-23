from PyQt6.QtWidgets import QToolBar, QStatusBar, QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QCheckBox, QComboBox
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

class createUI:
    def __init__(self, main_window):
        self.main_window = main_window





    #  =======================================================================
    #  INITIALIZE STYLES
    #  =======================================================================
        main_window.setStyleSheet("""
            QMainWindow {
                background-color: lightgray;
            }
            QToolBar {
                background-color: gray;
                border-bottom: 1px solid #c0c0c0;
                spacing: 3px;
            }
            QStatusBar {
                background-color: #e9e9e9;
                color: #4a4a4a;
            }
            QGraphicsView {
                background-color: white;
                border: 1px solid #c0c0c0;
            }
        """)





    #  =======================================================================    
    #  INITIALIZE UI
    #  =======================================================================
    def setupUI(self):
        self.set_window_properties()
        self.create_main_toolbar()
        self.create_secondary_toolbar()
        self.create_status_bar()
        self.createGraphicsView()
        self.create_left_toolbar()



    #   Set window properties
    def set_window_properties(self):
        self.main_window.setWindowTitle("Form Creator")
        self.main_window.setGeometry(100, 100, 800, 600)



    #   Create main toolbar
    def create_main_toolbar(self):
        self.main_toolbar = self.main_window.menuBar()

        # Add actions to the main toolbar
        fileMenu = self.main_toolbar.addMenu("&File")
        editMenu = self.main_toolbar.addMenu("&Edit")
        aboutMenu = self.main_toolbar.addMenu("&About")



    #   Create grid toolbar
    def create_secondary_toolbar(self):
        self.secondary_toolbar = QToolBar("Secondary Toolbar")
        self.secondary_toolbar.setMovable(False)
        self.main_window.addToolBar(self.secondary_toolbar)


        # Secondary toolbar functionality
        gridCheckbox = QCheckBox("Show Grid")
        gridCheckbox.setChecked(True)
        gridCheckbox.stateChanged.connect(self.cut)
        self.secondary_toolbar.addWidget(gridCheckbox)

        gridDensityMenu = QComboBox()
        gridDensityMenu.addItem("Low Density")
        gridDensityMenu.addItem("Medium Density")
        gridDensityMenu.addItem("High Density")
        gridDensityMenu.setCurrentIndex(1)  # Set default to Medium Density
        gridDensityMenu.currentIndexChanged.connect(self.cut)
        self.secondary_toolbar.addWidget(gridDensityMenu)



    #   Create status bar
    def create_status_bar(self):
        self.statusBar = QStatusBar()
        self.main_window.setStatusBar(self.statusBar)



    #   Create graphics view
    def createGraphicsView(self):
        self.main_window.graphicView = QGraphicsView()
        self.main_window.scene = QGraphicsScene()
        self.main_window.scene.setSceneRect(0, 0, 600, 400)
        self.main_window.graphicView.setScene(self.main_window.scene)



    #   Create left toolbar
    def create_left_toolbar(self):
        self.left_toolbar = QToolBar("Left Toolbar")
        self.left_toolbar.setMovable(False)
        self.main_window.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.left_toolbar)
        # Add actions to the left toolbar
        self.left_toolbar.addAction("Add Shape")
        self.left_toolbar.addAction("Add Text")
        self.left_toolbar.addAction("Add Image")




    #   Create central widget
    def setupCentraWidget(self):
        centralWidget = QWidget()
        mainLayout = QVBoxLayout(centralWidget)

        mainLayout.addWidget(self.graphicView)
        self.main_window.setCentralWidget(centralWidget)


    #  =======================================================================    
    #  PROGRAM LOGIC
    #  =======================================================================
    def cut(self):
        cut_action = QAction("Cut")
        cut_action.setStatusTip("Cut selected content")
        cut_action.triggered.connect(self.cut)
        self.secondary_toolbar.addAction(cut_action)
        self.main_window.statusBar().showMessage("Cut to clipboard", 1000)