import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from ui_class import createUI

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui_creator =  createUI(self)
        self.ui_creator.setupUI()

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