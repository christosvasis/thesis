from PyQt6.QtWidgets import QToolBar, QStatusBar, QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QCheckBox, QComboBox
from PyQt6.QtGui import QAction

class createUI:
    def __init__(self, main_window):
        self.main_window = main_window


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
        
    def setupUI(self):
        self.set_window_properties()
        self.create_main_toolbar()
        self.create_secondary_toolbar()
        self.create_status_bar()

    def set_window_properties(self):
        self.main_window.setWindowTitle("Stacked Toolbars Example")
        self.main_window.setGeometry(100, 100, 800, 600)

    def create_main_toolbar(self):
        self.main_toolbar = self.main_window.menuBar()

        # Add actions to the main toolbar
        fileMenu = self.main_toolbar.addMenu("&File")
        editMenu = self.main_toolbar.addMenu("&Edit")
        aboutMenu = self.main_toolbar.addMenu("&About")

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

    def create_status_bar(self):
        self.statusBar = QStatusBar()
        self.main_window.setStatusBar(self.statusBar)

    def cut(self):
        cut_action = QAction("Cut")
        cut_action.setStatusTip("Cut selected content")
        cut_action.triggered.connect(self.cut)
        self.secondary_toolbar.addAction(cut_action)

    def createGraphicsView(self):
        self.graphicView = QGraphicsView()
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 600, 400)
        self.graphicView.setScene(self.scene)

    def setupCentraWidget(self):
        centralWidget = QWidget()
        mainLayout = QVBoxLayout(centralWidget)

        mainLayout.addWidget(self.graphicView)
        self.setCentralWidget(centralWidget)

    def new_file(self):
        self.statusBar().showMessage("Creating new file...", 2000)
        
    def cut(self):
        self.statusBar().showMessage("Cut to clipboard", 2000)