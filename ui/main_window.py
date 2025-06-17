from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from ui.widgets.order_settings_widget import OrderSettingsWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.token = None
        self.debug_console = None  # 디버그 콘솔 추가
        self.setup_ui()
        
    def setup_ui(self):
        """메인 UI 구성"""
        self.setWindowTitle("AI 트레이딩 시스템")
        self.setGeometry(100, 100, 1200, 800)
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        
        # 상단 툴바
        top_layout = QHBoxLayout()
        
        # 로고/제목
        title_label = QLabel("🤖 AI 트레이딩 시스템")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        top_layout.addWidget(title_label)
        
        top_layout.addStretch()
        
        # 로그인/로그아웃 버튼
        self.login_btn = QPushButton("🔐 로그인")
        self.login_btn.clicked.connect(self.show_login_dialog)
        self.login_btn.setMinimumWidth(100)
        
        self.logout_btn = QPushButton("🚪 로그아웃") 
        self.logout_btn.clicked.connect(self.logout)
        self.logout_btn.setMinimumWidth(100)
        self.logout_btn.setVisible(False)  # 초기에는 숨김
        
        top_layout.addWidget(self.login_btn)
        top_layout.addWidget(self.logout_btn)
        
        # 디버그 콘솔 버튼 추가 (상단 툴바에)
        self.debug_btn = QPushButton("🐛 디버그 콘솔")
        self.debug_btn.clicked.connect(self.show_debug_console)
        self.debug_btn.setMaximumWidth(120)
        
        # 상단 레이아웃에 디버그 버튼 추가
        top_layout.addWidget(self.debug_btn)
        
        main_layout.addLayout(top_layout)
        
        # 상태 표시줄
        self.status_label = QLabel("시스템 준비 완료")
        self.status_label.setStyleSheet("color: #27ae60; padding: 5px;")
        main_layout.addWidget(self.status_label)
        
        # 탭 위젯
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        # 주문 설정 위젯 생성
        self.order_settings_widget = OrderSettingsWidget()
        
        # 탭 추가
        self.tabs.addTab(self.order_settings_widget, "주문 설정")
        self.tabs.addTab(QLabel("포트폴리오 관리 (준비중)"), "포트폴리오")
        self.tabs.addTab(QLabel("백테스팅 (준비중)"), "백테스팅")
        
        main_layout.addWidget(self.tabs)
        
        # 레이아웃 설정
        central_widget.setLayout(main_layout)
        
        # 상태바 설정
        self.statusBar().showMessage("준비 완료")
        
    def show_login_dialog(self):
        """로그인 대화상자 표시"""
        try:
            from ui.login_dialog import LoginDialog
            
            dialog = LoginDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.log_message("로그인 대화상자에서 승인됨 - 토큰 발급 시작")
                self.perform_login()
            else:
                self.log_message("로그인이 취소되었습니다")
                
        except ImportError as e:
            self.log_message(f"로그인 대화상자 로드 실패: {e}")
            # 로그인 대화상자가 없으면 직접 로그인 시도
            self.perform_login()
            
    def perform_login(self):
        """로그인 실행"""
        try:
            # 토큰 발급 시도
            from auth.login_service import LoginService
            
            self.log_message("🔐 키움 REST API 토큰 발급 중...")
            
            login_service = LoginService()
            token = login_service.get_access_token()
            
            if token:
                self.token = token
                self.log_message(f"✅ 토큰 발급 성공: {token[:20]}...")
                self.on_login_success()
            else:
                self.log_message("❌ 토큰 발급 실패")
                QMessageBox.warning(self, "로그인 실패", "토큰 발급에 실패했습니다.")
                
        except Exception as e:
            self.log_message(f"❌ 로그인 오류: {e}")
            QMessageBox.critical(self, "로그인 오류", f"로그인 처리 중 오류가 발생했습니다:\n{e}")
        
    def on_login_success(self):
        """로그인 성공 처리"""
        self.log_message("✅ 로그인 성공! UI 상태 업데이트 중...")
        
        # UI 상태 변경
        self.login_btn.setVisible(False)
        self.logout_btn.setVisible(True)
        self.status_label.setText("로그인 완료 - 서비스 이용 가능")
        self.status_label.setStyleSheet("color: #27ae60; padding: 5px;")
        self.statusBar().showMessage("로그인 완료")
        
        # 주문 설정 위젯에 토큰 전달
        if hasattr(self.order_settings_widget, 'set_token'):
            self.log_message("📤 주문 설정 위젯에 토큰 전달 중...")
            self.order_settings_widget.set_token(self.token)
        else:
            self.log_message("⚠️ 주문 설정 위젯에 set_token 메소드가 없습니다")
            
        self.log_message("🎉 로그인 완료 - 모든 기능 사용 가능")
        
    def logout(self):
        """로그아웃 처리"""
        self.log_message("🚪 로그아웃 처리 중...")
        
        # 토큰 제거
        self.token = None
        
        # UI 상태 변경
        self.login_btn.setVisible(True)
        self.logout_btn.setVisible(False)
        self.status_label.setText("로그아웃됨")
        self.status_label.setStyleSheet("color: #e74c3c; padding: 5px;")
        self.statusBar().showMessage("로그아웃됨")
        
        # 주문 설정 위젯 초기화
        if hasattr(self.order_settings_widget, 'clear_token'):
            self.order_settings_widget.clear_token()
            
        self.log_message("✅ 로그아웃 완료")
        
    def log_message(self, message):
        """로그 메시지 출력"""
        print(f"[MAIN] {message}")
        
        # 디버그 콘솔에도 로그 추가
        if self.debug_console:
            self.debug_console.add_log(f"[MAIN] {message}")
        
    def show_debug_console(self):
        """디버그 콘솔 표시"""
        if not self.debug_console:
            try:
                from ui.widgets.debug_console import DebugConsole
                self.debug_console = DebugConsole(self)
                
                # 기존 로그 메시지들을 디버그 콘솔에 추가
                self.debug_console.add_log("📱 메인 윈도우 디버그 콘솔 시작")
                
            except ImportError as e:
                print(f"디버그 콘솔 로드 실패: {e}")
                QMessageBox.warning(self, "모듈 오류", f"디버그 콘솔을 로드할 수 없습니다.\n오류: {e}")
                return
                
        self.debug_console.show()
        self.debug_console.raise_()
        self.debug_console.activateWindow()
        
    def closeEvent(self, event):
        """애플리케이션 종료 시 정리"""
        self.log_message("🔚 애플리케이션 종료 준비 중...")
        
        # 조건검색 서비스 정리
        if hasattr(self.order_settings_widget, 'cleanup'):
            self.order_settings_widget.cleanup()
            
        # 디버그 콘솔 정리
        if self.debug_console:
            self.debug_console.close()
            
        self.log_message("✅ 정리 완료 - 애플리케이션 종료")
        event.accept()