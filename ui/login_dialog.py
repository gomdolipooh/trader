from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from auth.login_service import LoginService

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.token = None
        self.login_service = LoginService()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("로그인")
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout()
        
        # 계좌 선택
        account_group = QGroupBox("계좌 선택")
        account_layout = QVBoxLayout()
        
        self.account1_radio = QRadioButton("계좌 1")
        self.account1_radio.setChecked(True)
        
        account_layout.addWidget(self.account1_radio)
        account_group.setLayout(account_layout)
        
        # 버튼
        button_layout = QHBoxLayout()
        
        self.login_btn = QPushButton("로그인")
        self.cancel_btn = QPushButton("취소")
        
        self.login_btn.clicked.connect(self.do_login)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addWidget(account_group)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def do_login(self):
        """로그인 실행"""
        self.login_btn.setText("로그인 중...")
        self.login_btn.setEnabled(False)
        
        # 백그라운드에서 로그인 처리
        self.login_worker = LoginWorker(self.login_service)
        self.login_worker.login_result.connect(self.on_login_result)
        self.login_worker.start()
        
    def on_login_result(self, success, token):
        """로그인 결과 처리"""
        self.login_btn.setText("로그인")
        self.login_btn.setEnabled(True)
        
        if success:
            self.token = token
            self.accept()
        else:
            QMessageBox.warning(self, "로그인 실패", "토큰 발급에 실패했습니다.")
            
    def get_token(self):
        return self.token

class LoginWorker(QThread):
    """로그인 작업 스레드"""
    login_result = pyqtSignal(bool, str)
    
    def __init__(self, login_service):
        super().__init__()
        self.login_service = login_service
        
    def run(self):
        try:
            token = self.login_service.get_access_token()
            if token:
                self.login_result.emit(True, token)
            else:
                self.login_result.emit(False, "")
        except Exception as e:
            self.login_result.emit(False, "")