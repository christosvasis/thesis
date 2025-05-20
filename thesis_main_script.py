import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QToolBar, QStatusBar, QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QCheckBox, QComboBox
from PyQt6.QtGui import QAction, QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Stacked Toolbars Example")
        self.setGeometry(100, 100, 800, 600)

        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)

        mainLayout = QVBoxLayout(centralWidget)





        # =======================================================================
        #
        #               PROGRAM STYLESHEET CODE
        #
        # =======================================================================
        self.setStyleSheet("""
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
            QLabel, QPushButton, QLineEdit {
                color: #333333;
            }
            QGraphicsView {
                background-color: white;
                border: 1px solid #c0c0c0;
            }
        """)





        # =======================================================================
        #
        #               TOOLBARS CODE
        #
        # =======================================================================
        # Create status bar
        self.setStatusBar(QStatusBar(self))
        
        # Create the MAIN toolbar
        self.main_toolbar = self.menuBar()
        self.main_toolbar.setStyleSheet("background-color: gray;")

        # DON'T USE THIS IF YOU WANT TO KEEP THE MENUBAR
        #self.main_toolbar.setMovable(False)
        #self.addToolBar(self.main_toolbar)
        #newFile = QAction("File", self)
        #newFile.setStatusTip("File menu")
        #newFile.triggered.connect(self.new_file)
        #self.main_toolbar.addAction(newFile)


        # ANOTHER WAY TO CREATE A TOOLBAR LIKE THE CLASSIC MENUBAR
        #main_toolbar = QToolBar("Main Toolbar")
        #self.addToolBar(main_toolbar)
        #main_toolbar.setMovable(False)
        #menu_button = QToolButton()
        #menu_button.setText("Menu")
        #menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        #dropdown_menu = QMenu()
        #dropdown_menu.addAction("Option 1")
        #dropdown_menu.addAction("Option 2")
        #menu_button.setMenu(dropdown_menu)
        #main_toolbar.addWidget(menu_button)
        
        # Add a toolbar break to force the next toolbar to start on a new line
        self.addToolBarBreak()
        
        # Create the second toolbar that will be placed below the first one
        self.secondary_toolbar = QToolBar("Secondary Toolbar", self)
        self.secondary_toolbar.setMovable(False)
        self.addToolBar(self.secondary_toolbar)
        
        # Add actions to the main toolbar
        fileMenu = self.main_toolbar.addMenu("&File")
        editMenu = self.main_toolbar.addMenu("&Edit")
        aboutMenu = self.main_toolbar.addMenu("&About")


        
        self.main_toolbar.addSeparator()





        # =======================================================================
        #
        #               TOOLBARS INTERACTION CODE
        #
        # =======================================================================

        # ===============   ADD CHECKBOX TO TOGGLE GRID LINES   ===============
        gridCheckbox = QCheckBox("Show Grid")
        gridCheckbox.setChecked(True)
        gridCheckbox.stateChanged.connect(self.cut)
        self.secondary_toolbar.addWidget(gridCheckbox)

        # ===============   ADD A DROPDOWN MENU TO CHANGE GRID DENSITY   ===============
        gridDensityMenu = QComboBox()
        gridDensityMenu.addItem("Low Density")
        gridDensityMenu.addItem("Medium Density")
        gridDensityMenu.addItem("High Density")
        gridDensityMenu.setCurrentIndex(1)  # Set default to Medium Density
        gridDensityMenu.currentIndexChanged.connect(self.cut)
        self.secondary_toolbar.addWidget(gridDensityMenu)


        cut_action = QAction("Cut", self)
        cut_action.setStatusTip("Cut selected content")
        cut_action.triggered.connect(self.cut)
        self.secondary_toolbar.addAction(cut_action)





        # =======================================================================
        #
        #               CANVAS CODE
        #
        # =======================================================================
        self.graphicView = QGraphicsView()
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 600, 400)
        self.graphicView.setScene(self.scene)





        # =======================================================================
        #
        #               WINDOW LAYOUT CODE
        #
        # =======================================================================
        mainLayout.addWidget(self.graphicView)
        
        # Probably obsolete, but keeping for reference
        # mainLayout.addLayout(self.main_toolbar.layout())
        # mainLayout.addLayout(self.secondary_toolbar.layout())
        
    def new_file(self):
        self.statusBar().showMessage("Creating new file...", 2000)
        
    def cut(self):
        self.statusBar().showMessage("Cut to clipboard", 2000)





# =======================================================================
#
#               MAIN APP CODE, NOT TO BE MODIFIED
#
# =======================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())