from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

class OrderSettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.condition_service = None
        self.condition_windows = []  # 열린 조건검색 창들 추적
        self.debug_console = None  # 디버그 콘솔
        self.token = None  # 토큰 저장
        self.setup_ui()
        
    def setup_ui(self):
        """주문 설정 UI 구성"""
        main_layout = QVBoxLayout()
        
        # 상단 디버그 버튼
        debug_layout = QHBoxLayout()
        debug_layout.addStretch()
        
        self.debug_btn = QPushButton("🐛 디버그 콘솔")
        self.debug_btn.clicked.connect(self.show_debug_console)
        self.debug_btn.setMaximumWidth(120)
        debug_layout.addWidget(self.debug_btn)
        
        main_layout.addLayout(debug_layout)
        
        # 매수 설정 그룹
        buy_group = self.create_buy_group()
        main_layout.addWidget(buy_group)
        
        # 매도 설정 그룹  
        sell_group = self.create_sell_group()
        main_layout.addWidget(sell_group)
        
        # 저장 버튼
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        self.save_btn = QPushButton("설정 저장")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setMinimumWidth(100)
        
        save_layout.addWidget(self.save_btn)
        main_layout.addLayout(save_layout)
        
        # 여백 추가
        main_layout.addStretch()
        
        self.setLayout(main_layout)
        
    def show_debug_console(self):
        """디버그 콘솔 표시"""
        if not self.debug_console:
            try:
                from ui.widgets.debug_console import DebugConsole
                self.debug_console = DebugConsole(self)
            except ImportError as e:
                print(f"디버그 콘솔 로드 실패: {e}")
                QMessageBox.warning(self, "모듈 오류", "디버그 콘솔을 로드할 수 없습니다.")
                return
                
        self.debug_console.show()
        self.debug_console.raise_()
        self.debug_console.activateWindow()
        
    def set_token(self, token):
        """토큰 설정 및 조건검색 서비스 초기화"""
        self.token = token
        if token:
            try:
                from services.condition_service import ConditionService
                
                print(f"🔧 조건검색 서비스 초기화 시작 - 토큰: {token[:20]}...")
                
                # 기존 서비스가 있으면 정리
                if self.condition_service:
                    self.condition_service.stop_connection()
                
                self.condition_service = ConditionService(token)
                self.condition_service.condition_list_received.connect(self.update_condition_list)
                self.condition_service.connection_status_changed.connect(self.on_connection_status_changed)
                self.condition_service.debug_message.connect(self.on_debug_message)
                
                # UI 상태 초기화
                self.condition_combo.clear()
                self.condition_combo.addItem("🔄 서버 연결 중...")
                self.condition_combo.setEnabled(False)
                self.condition_search_btn.setEnabled(False)
                
                self.condition_service.start_connection()
                print("✅ 조건검색 서비스 초기화 완료")
                
            except ImportError as e:
                print(f"❌ 조건검색 모듈 로드 실패: {e}")
                QMessageBox.warning(self, "모듈 오류", f"조건검색 기능을 사용할 수 없습니다.\n오류: {e}")
            except Exception as e:
                print(f"❌ 조건검색 서비스 초기화 실패: {e}")
                QMessageBox.warning(self, "초기화 오류", f"조건검색 서비스 초기화에 실패했습니다.\n오류: {e}")
        else:
            print("❌ 토큰이 없어서 조건검색 서비스를 초기화할 수 없습니다")
            
    def clear_token(self):
        """토큰 제거 및 서비스 정리"""
        self.token = None
        if self.condition_service:
            self.condition_service.stop_connection()
            self.condition_service = None
            
        # UI 상태 초기화
        self.condition_combo.clear()
        self.condition_combo.addItem("로그인이 필요합니다")
        self.condition_combo.setEnabled(False)
        self.condition_search_btn.setEnabled(False)
        self.condition_combo.setStyleSheet("")
        
        print("🧹 조건검색 서비스 정리 완료")
        
    def cleanup(self):
        """정리 작업"""
        self.clear_token()
        
        # 열린 조건검색 창들 닫기
        for window in self.condition_windows[:]:  # 리스트 복사본 사용
            if window and not window.isHidden():
                window.close()
        self.condition_windows.clear()
        
        # 디버그 콘솔 닫기
        if self.debug_console:
            self.debug_console.close()
        
    def on_connection_status_changed(self, connected):
        """연결 상태 변경 처리"""
        if connected:
            print("✅ 조건검색 서버 연결됨")
            self.condition_combo.setStyleSheet("")  # 기본 스타일로 복원
        else:
            print("❌ 조건검색 서버 연결 해제됨")
            self.condition_combo.setStyleSheet("color: red;")
            
    def on_debug_message(self, message):
        """디버그 메시지 처리"""
        print(f"[조건검색 디버그] {message}")
        
        # 디버그 콘솔에 로그 추가
        if self.debug_console:
            self.debug_console.add_log(message)
        
        # UI에 상태 메시지 반영 (더 구체적으로)
        if "WebSocket 연결 성공" in message:
            self.condition_combo.clear()
            self.condition_combo.addItem("🔐 로그인 중...")
        elif "로그인 성공" in message:
            self.condition_combo.clear()
            self.condition_combo.addItem("📋 조건검색 목록 불러오는 중...")
        elif "조건검색 목록 수신" in message:
            # 목록이 수신되면 곧 업데이트될 예정이므로 대기 메시지 표시
            pass
        elif "연결 타임아웃" in message or "연결 오류" in message or "로그인 실패" in message:
            self.condition_combo.clear()
            self.condition_combo.addItem("❌ 연결 실패")
            self.condition_combo.setStyleSheet("color: red;")
            self.condition_search_btn.setEnabled(False)
            
    def create_buy_group(self):
        """매수 설정 그룹 생성"""
        group = QGroupBox("매수 설정")
        layout = QVBoxLayout()
        
        # 조건식 목록
        condition_layout = QHBoxLayout()
        condition_layout.addWidget(QLabel("조건식:"))
        
        self.condition_combo = QComboBox()
        self.condition_combo.setMaxVisibleItems(15)  # 최대 15개까지 보이도록
        self.condition_combo.addItem("로그인이 필요합니다")
        self.condition_combo.setEnabled(False)
        
        condition_layout.addWidget(self.condition_combo)
        
        # 조건검색 버튼
        self.condition_search_btn = QPushButton("조건검색 실행")
        self.condition_search_btn.clicked.connect(self.show_condition_search_dialog)
        self.condition_search_btn.setEnabled(False)
        condition_layout.addWidget(self.condition_search_btn)
        
        condition_layout.addStretch()
        
        # 매수 방식 선택
        buy_type_layout = QVBoxLayout()
        buy_type_layout.addWidget(QLabel("매수 방식:"))
        
        self.market_buy_radio = QRadioButton("시장가 매수")
        self.market_buy_radio.setChecked(True)
        
        self.limit_buy_radio = QRadioButton("현재가 대비 호가 지정가 주문")
        
        buy_type_layout.addWidget(self.market_buy_radio)
        buy_type_layout.addWidget(self.limit_buy_radio)
        
        # 호가 설정 (지정가 선택시에만 활성화)
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("호가 설정:"))
        
        self.price_offset_spin = QSpinBox()
        self.price_offset_spin.setRange(-10, 10)
        self.price_offset_spin.setValue(0)
        self.price_offset_spin.setSuffix("호가")
        self.price_offset_spin.setEnabled(False)  # 초기에는 비활성화
        
        price_layout.addWidget(self.price_offset_spin)
        price_layout.addStretch()
        
        # 매수 금액 설정
        amount_layout = QHBoxLayout()
        amount_layout.addWidget(QLabel("매수 금액:"))
        
        self.buy_amount_spin = QSpinBox()
        self.buy_amount_spin.setRange(10000, 100000000)  # 1만원 ~ 1억원
        self.buy_amount_spin.setValue(100000)  # 기본값 10만원
        self.buy_amount_spin.setSuffix("원")
        self.buy_amount_spin.setSingleStep(10000)  # 1만원 단위
        
        amount_layout.addWidget(self.buy_amount_spin)
        amount_layout.addStretch()
        
        # 레이아웃 추가
        layout.addLayout(condition_layout)
        layout.addLayout(buy_type_layout)
        layout.addLayout(price_layout)
        layout.addLayout(amount_layout)
        
        group.setLayout(layout)
        
        # 라디오 버튼 연결
        self.market_buy_radio.toggled.connect(self.on_buy_type_changed)
        self.limit_buy_radio.toggled.connect(self.on_buy_type_changed)
        
        return group
        
    def create_sell_group(self):
        """매도 설정 그룹 생성"""
        group = QGroupBox("매도 설정")
        layout = QVBoxLayout()
        
        # 매도 조건식 목록
        sell_condition_layout = QHBoxLayout()
        sell_condition_layout.addWidget(QLabel("매도 조건식:"))
        
        self.sell_condition_combo = QComboBox()
        self.sell_condition_combo.setMaxVisibleItems(15)  # 최대 15개까지 보이도록
        
        # 매도 조건식 목록 추가
        sell_conditions = [
            "수익률 달성 매도",
            "손절선 도달 매도", 
            "RSI 과매수 매도",
            "볼린저밴드 상단 터치 매도",
            "이동평균선 하향돌파 매도",
            "MACD 하향돌파 매도",
            "스토캐스틱 고점권 매도",
            "데드크로스 매도",
            "거래량 급감 매도",
            "상승 추세선 이탈 매도",
            "일목균형표 구름대 하향돌파",
            "삼선전환도 음전환 매도",
            "CCI 과매수 매도",
            "모멘텀 하향돌파 매도",
            "피보나치 되돌림 저항 매도"
        ]
        
        for condition in sell_conditions:
            self.sell_condition_combo.addItem(condition)
            
        sell_condition_layout.addWidget(self.sell_condition_combo)
        sell_condition_layout.addStretch()
        
        # 매도 방식 선택
        sell_type_layout = QVBoxLayout()
        sell_type_layout.addWidget(QLabel("매도 방식:"))
        
        self.market_sell_radio = QRadioButton("시장가 매도")
        self.market_sell_radio.setChecked(True)
        
        self.limit_sell_radio = QRadioButton("현재가 대비 호가 지정가 주문")
        
        sell_type_layout.addWidget(self.market_sell_radio)
        sell_type_layout.addWidget(self.limit_sell_radio)
        
        # 매도 호가 설정 (지정가 선택시에만 활성화)
        sell_price_layout = QHBoxLayout()
        sell_price_layout.addWidget(QLabel("호가 설정:"))
        
        self.sell_price_offset_spin = QSpinBox()
        self.sell_price_offset_spin.setRange(-10, 10)
        self.sell_price_offset_spin.setValue(0)
        self.sell_price_offset_spin.setSuffix("호가")
        self.sell_price_offset_spin.setEnabled(False)  # 초기에는 비활성화
        
        sell_price_layout.addWidget(self.sell_price_offset_spin)
        sell_price_layout.addStretch()
        
        # 레이아웃 추가
        layout.addLayout(sell_condition_layout)
        layout.addLayout(sell_type_layout)
        layout.addLayout(sell_price_layout)
        
        group.setLayout(layout)
        
        # 라디오 버튼 연결
        self.market_sell_radio.toggled.connect(self.on_sell_type_changed)
        self.limit_sell_radio.toggled.connect(self.on_sell_type_changed)
        
        return group
        
    def on_buy_type_changed(self):
        """매수 방식 변경시 호가 설정 활성화/비활성화"""
        self.price_offset_spin.setEnabled(self.limit_buy_radio.isChecked())
        
    def on_sell_type_changed(self):
        """매도 방식 변경시 호가 설정 활성화/비활성화"""
        self.sell_price_offset_spin.setEnabled(self.limit_sell_radio.isChecked())
        
    def get_buy_settings(self):
        """매수 설정 값들 반환"""
        return {
            'condition': self.condition_combo.currentText(),
            'condition_idx': self.condition_combo.currentData(),
            'is_market_order': self.market_buy_radio.isChecked(),
            'price_offset': self.price_offset_spin.value() if self.limit_buy_radio.isChecked() else 0,
            'amount': self.buy_amount_spin.value()
        }
        
    def get_sell_settings(self):
        """매도 설정 값들 반환"""
        return {
            'condition': self.sell_condition_combo.currentText(),
            'is_market_order': self.market_sell_radio.isChecked(),
            'price_offset': self.sell_price_offset_spin.value() if self.limit_sell_radio.isChecked() else 0
        }
        
    def save_settings(self):
        """설정 저장"""
        buy_settings = self.get_buy_settings()
        sell_settings = self.get_sell_settings()
        
        # 설정 값들을 로그로 출력 (나중에 파일 저장 등으로 변경 가능)
        print("=== 주문 설정 저장 ===")
        print(f"매수 조건식: {buy_settings['condition']}")
        print(f"매수 방식: {'시장가' if buy_settings['is_market_order'] else '지정가'}")
        if not buy_settings['is_market_order']:
            print(f"매수 호가: {buy_settings['price_offset']}호가")
        print(f"매수 금액: {buy_settings['amount']:,}원")
        
        print(f"매도 조건식: {sell_settings['condition']}")
        print(f"매도 방식: {'시장가' if sell_settings['is_market_order'] else '지정가'}")
        if not sell_settings['is_market_order']:
            print(f"매도 호가: {sell_settings['price_offset']}호가")
        print("=====================")
        
        # 저장 완료 메시지
        QMessageBox.information(self, "저장 완료", "주문 설정이 저장되었습니다.")
        
    def update_condition_list(self, condition_list):
        """조건검색 목록 업데이트"""
        self.condition_combo.clear()
        self.condition_combo.setEnabled(True)
        self.condition_search_btn.setEnabled(True)
        self.condition_combo.setStyleSheet("")  # 스타일 초기화
        
        if not condition_list:
            self.condition_combo.addItem("조건검색식이 없습니다")
            self.condition_search_btn.setEnabled(False)
            return
            
        for condition in condition_list:
            cnsl_idx = condition["cnsl_idx"]
            cnsl_nm = condition["cnsl_nm"]
            self.condition_combo.addItem(f"{cnsl_nm}", cnsl_idx)
            
        print(f"✅ 조건검색 목록 업데이트 완료: {len(condition_list)}개")
            
    def show_condition_search_dialog(self):
        """조건검색 타입 선택 다이얼로그 표시"""
        if self.condition_combo.currentData() is None:
            QMessageBox.warning(self, "경고", "선택된 조건식이 없습니다.")
            return
            
        cnsl_idx = self.condition_combo.currentData()
        cnsl_nm = self.condition_combo.currentText()
        
        # 조건검색 타입 선택 다이얼로그
        dialog = QDialog(self)
        dialog.setWindowTitle(f"조건검색 타입 선택 - {cnsl_nm}")
        dialog.setFixedSize(350, 200)
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        # 제목
        title_label = QLabel(f"조건식: {cnsl_nm}")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 설명
        desc_label = QLabel("검색 타입을 선택하세요:")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        normal_btn = QPushButton("일반 조건검색")
        normal_btn.setToolTip("한 번만 조건에 맞는 종목을 검색합니다")
        normal_btn.clicked.connect(lambda: self.execute_condition_search(dialog, cnsl_idx, cnsl_nm, '0'))
        
        real_btn = QPushButton("실시간 조건검색")
        real_btn.setToolTip("실시간으로 조건에 맞는 종목을 모니터링합니다")
        real_btn.clicked.connect(lambda: self.execute_condition_search(dialog, cnsl_idx, cnsl_nm, '1'))
        
        button_layout.addWidget(normal_btn)
        button_layout.addWidget(real_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec()
        
    def execute_condition_search(self, dialog, cnsl_idx, cnsl_nm, search_type):
        """조건검색 실행"""
        dialog.accept()
        
        if not self.condition_service:
            QMessageBox.warning(self, "오류", "조건검색 서비스가 초기화되지 않았습니다.")
            return
            
        try:
            from ui.widgets.condition_result_window import ConditionResultWindow
            
            # 조건검색 결과 창 열기
            result_window = ConditionResultWindow(
                cnsl_idx, cnsl_nm, search_type, self.condition_service, self
            )
            result_window.show()
            self.condition_windows.append(result_window)
            
            # 창이 닫힐 때 목록에서 제거
            def remove_window():
                if result_window in self.condition_windows:
                    self.condition_windows.remove(result_window)
                    
            result_window.destroyed.connect(remove_window)
            
            print(f"📊 조건검색 창 열기: {cnsl_nm} ({search_type})")
            
        except ImportError as e:
            print(f"조건검색 결과 창 로드 실패: {e}")
            QMessageBox.warning(self, "모듈 오류", "조건검색 결과 창을 열 수 없습니다.")
            
    def closeEvent(self, event):
        """위젯 닫기 이벤트"""
        self.cleanup()
        event.accept()