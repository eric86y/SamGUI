DARK_STYLE = """

            QWidget#MainWindow {
                background-color: #171d25;
                color: #ffffff;
                border-radius: 20px;
            }
            
            QWidget#AppView {
                background-color: #08081f;
            }
            
            QWidget#DebugView {
                background-color: #24272c;
            }
            
            
            QWidget#CanvasPanel {
                background-color: #24272c;
                border: 2px solid #343942;
                padding: 6px;
            }
            
            QWidget#ItemList {
                border: none;
                QListView::item {
                    border: none;
                }

                QListView::item::hover {
                    background-color: #2C2C2C;
                }
                QListView::item::selected {
                    background-color: #1c222a;
                }
            }

            QWidget#HierarchyEntry {
                background-color: #24272c;
            }

            QFrame#Header {
                background-color: qlineargradient(x1:0 y1:0, x2:0 y2:1, stop:0 #2c323b, stop:1 #171d25);
                border: 2px solid #343942;
                border-radius: 8px;
                text-align: center;
            }
            
            QFrame#HierarchyHeader {
                padding: 6px;
            }


            QFrame#ToolBox {
                background-color: #24272c;
                border-style: outset;
            }
            
            QFrame#ToolLabel {
               width: 100px;
               padding-top: 16px;
               font-weight: bold;
               color: #CCCCCC;
            }

            QFrame#SideBox {
                background-color: #24272c;
                border: 2px solid #343942;
                border-radius: 8px;
                text-align: center;
            }
              
            QFrame#CanvasHierarchy {
                background-color: #24272c;
                border: 2px solid #343942;
                border-radius: 8px;
                text-align: center;
            }

            QFrame#ToolBox#Qlabel {
                width: 100px;
                padding-top: 4px;
                font-weight: bold;
                color: #CCCCCC;
                border-top: 1px solid #32363e;
            }

            QLabel {
                color: #ffffff;
                font-weight: bold;
            }

            QPushButton {
                color: #ffffff;
                background-color: #4d4d4d;
                border-radius: 5px;

            }
            QPushButton#MenuButton {
                background-color: #2c2f37;
            }
            
            QPushButton#DialogButton {
                color: #000000;
                font: bold 12px; 
                width: 240px;
                height: 32px;
                background-color: #ffad00;
                border: 2px solid #ffad00;
                border-radius: 4px;

                QPushButton::hover {
                    color: #ff0000;
                }
            }
        
            QLineEdit#DebugFilterLabel {
                color: #ffffff;
                background-color: #474747;
                border: 2px solid #343942;
                border-radius: 8px;
                padding: 6px;
                text-align: left;
            }
            
            QLineEdit#DialogLineEdit {
                color: #ffffff;
                background-color: #474747;
                border: 2px solid #343942;
                border-radius: 8px;
                padding: 6px;
                text-align: left;
            }
        
            QPushButton#listButton {
                background-color: #2a2950;
            }
            
            QPushButton:hover {
                background-color: #999999;
            }

            QGraphicsView#GraphicsView {
                background-color: #24272c;
                padding: 4px;
            }
            
            QTableWidget {
                background-color: #474747;
            }
            
            QListWidget#WidgetList {
                background-color: #24272c;
                border: 0px;
                
                
            }

            QListWidget#HierarchyEntry {
                width: 400px;
                height: 120px;
                background-color: #24272c;
            }

            QMessageBox {
                width: 400px;
                padding: 5px;
                color: #FFFFFF;
                background-color: #24272c;
            }
            QDialog{
                background-color: black;
            }

            QDialog#ImportDialog {
                background-color: #24272c;
            
                QLabel {
                    color: #ffffff;
                }
            }

            QInputDialog {
                width: 400px;
                padding: 5px;
                color: #FFFFFF;
                background-color: #24272c;
            }
            
            QInputDialog::QLineEdit {
                background-color: #41444b;
            }
                
            InputDialog {
                color: #ffffff;
                background-color: red;
            }
            
            QTableWidget#DebugDataTable {
                color: #ffffff;
            }
            
            QDialog#SamDialog {
                background-color: #24272c;

                QProgressBar {
                    background-color: #24272c;
                    border-radius: 5px;
                    border-width: 2px;
                }
    
                QProgressBar::chunk
                {
                    background-color: #003d66;
                    border-radius: 5px;
                    margin: 3px 3px 3px 3px;
                }
            }
            
            QDialog#ImportProjectDialog#QLabel 
            {
                width: 100px;
                padding-top: 4px;
                font-weight: bold;
                color: #CCCCCC;
                border-top: 1px solid #32363e;
            }
            
            QMessageBox#NotificationWindow {
                background-color: #24272c;
                color: #ffffff; 
            }
            
            QScrollbar#VerticalScrollBar {
                
            }
    """