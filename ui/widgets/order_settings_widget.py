from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

class OrderSettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.condition_service = None
        self.condition_windows = []  # 열린 조건검색 창들 추적
        self.debug_console = None  # 디버그 콘솔
        self.token = None  # 토큰 저장
        
        # 자동매매 관련
        self.auto_trading_service = None
        self.auto_trading_active = False
        
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
        
        # 자동매매 상태 표시 패널
        status_group = self.create_status_group()
        main_layout.addWidget(status_group)
        
        # 매수 설정 그룹
        buy_group = self.create_buy_group()
        main_layout.addWidget(buy_group)
        
        # 매도 설정 그룹  
        sell_group = self.create_sell_group()
        main_layout.addWidget(sell_group)
        
        # 저장 및 제어 버튼
        control_layout = QHBoxLayout()
        control_layout.addStretch()
        
        self.save_btn = QPushButton("설정 저장")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setMinimumWidth(100)
        
        self.start_auto_btn = QPushButton("🚀 자동매매 시작")
        self.start_auto_btn.clicked.connect(self.start_auto_trading)
        self.start_auto_btn.setMinimumWidth(120)
        self.start_auto_btn.setEnabled(False)
        
        self.stop_auto_btn = QPushButton("⏹️ 자동매매 중지")
        self.stop_auto_btn.clicked.connect(self.stop_auto_trading)
        self.stop_auto_btn.setMinimumWidth(120)
        self.stop_auto_btn.setVisible(False)
        
        control_layout.addWidget(self.save_btn)
        control_layout.addWidget(self.start_auto_btn)
        control_layout.addWidget(self.stop_auto_btn)
        main_layout.addLayout(control_layout)
        
        # 여백 추가
        main_layout.addStretch()
        
        self.setLayout(main_layout)
        
    def create_status_group(self):
        """자동매매 상태 표시 그룹"""
        group = QGroupBox("자동매매 상태")
        layout = QGridLayout()
        
        # 상태 표시
        layout.addWidget(QLabel("상태:"), 0, 0)
        self.status_label = QLabel("대기 중")
        self.status_label.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        layout.addWidget(self.status_label, 0, 1)
        
        # 보유 종목 수
        layout.addWidget(QLabel("보유 종목:"), 0, 2)
        self.position_count_label = QLabel("0개")
        layout.addWidget(self.position_count_label, 0, 3)
        
        # 대기 주문
        layout.addWidget(QLabel("대기 주문:"), 1, 0)
        self.pending_orders_label = QLabel("0개")
        layout.addWidget(self.pending_orders_label, 1, 1)
        
        # 모니터링 종목
        layout.addWidget(QLabel("모니터링:"), 1, 2)
        self.monitoring_stocks_label = QLabel("0개")
        layout.addWidget(self.monitoring_stocks_label, 1, 3)
        
        group.setLayout(layout)
        return group
        
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
                
                # 자동매매 서비스 초기화
                self.init_auto_trading_service()
                
            except ImportError as e:
                print(f"❌ 조건검색 모듈 로드 실패: {e}")
                QMessageBox.warning(self, "모듈 오류", f"조건검색 기능을 사용할 수 없습니다.\n오류: {e}")
            except Exception as e:
                print(f"❌ 조건검색 서비스 초기화 실패: {e}")
                QMessageBox.warning(self, "초기화 오류", f"조건검색 서비스 초기화에 실패했습니다.\n오류: {e}")
        else:
            print("❌ 토큰이 없어서 조건검색 서비스를 초기화할 수 없습니다")
            
    def init_auto_trading_service(self):
        """자동매매 서비스 초기화"""
        try:
            from services.auto_trading_service import AutoTradingService
            
            if self.auto_trading_service:
                self.auto_trading_service.cleanup()
                
            self.auto_trading_service = AutoTradingService(
                token=self.token,
                condition_service=self.condition_service,
                is_mock=True  # 테스트용으로 모의투자 사용
            )
            
            # 시그널 연결
            self.auto_trading_service.position_added.connect(self.on_position_added)
            self.auto_trading_service.trading_status_changed.connect(self.on_trading_status_changed)
            self.auto_trading_service.debug_message.connect(self.on_debug_message)
            self.auto_trading_service.error_occurred.connect(self.on_trading_error)
            
            # 상태 업데이트 타이머
            self.status_timer = QTimer()
            self.status_timer.timeout.connect(self.update_trading_status)
            self.status_timer.start(5000)  # 5초마다 상태 업데이트
            
            print("✅ 자동매매 서비스 초기화 완료")
            
        except ImportError as e:
            print(f"❌ 자동매매 모듈 로드 실패: {e}")
        except Exception as e:
            print(f"❌ 자동매매 서비스 초기화 실패: {e}")
            
    def clear_token(self):
        """토큰 제거 및 서비스 정리"""
        self.token = None
        
        # 자동매매 중지
        if self.auto_trading_service:
            self.auto_trading_service.cleanup()
            self.auto_trading_service = None
            
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
            
        if self.condition_service:
            self.condition_service.stop_connection()
            self.condition_service = None
            
        # UI 상태 초기화
        self.condition_combo.clear()
        self.condition_combo.addItem("로그인이 필요합니다")
        self.condition_combo.setEnabled(False)
        self.condition_search_btn.setEnabled(False)
        self.condition_combo.setStyleSheet("")
        
        # 자동매매 버튼 상태 초기화
        self.start_auto_btn.setEnabled(False)
        self.stop_auto_btn.setVisible(False)
        self.start_auto_btn.setVisible(True)
        self.auto_trading_active = False
        
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
        
        # 최대 보유 종목 수 설정
        max_stocks_layout = QHBoxLayout()
        max_stocks_layout.addWidget(QLabel("최대 보유 종목:"))
        
        self.max_stocks_spin = QSpinBox()
        self.max_stocks_spin.setRange(1, 50)
        self.max_stocks_spin.setValue(10)  # 기본값 10개
        self.max_stocks_spin.setSuffix("개")
        
        max_stocks_layout.addWidget(self.max_stocks_spin)
        max_stocks_layout.addStretch()
        
        # 레이아웃 추가
        layout.addLayout(condition_layout)
        layout.addLayout(buy_type_layout)
        layout.addLayout(price_layout)
        layout.addLayout(amount_layout)
        layout.addLayout(max_stocks_layout)
        
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
            'amount': self.buy_amount_spin.value(),
            'max_stocks': self.max_stocks_spin.value()
        }
        
    def get_sell_settings(self):
        """매도 설정 값들 반환"""
        return {
            'condition': self.sell_condition_combo.currentText(),
            'is_market_order': self.market_sell_radio.isChecked(),
            'price_offset': self.sell_price_offset_spin.value() if self.limit_sell_radio.isChecked() else 0
        }
        
    def save_settings(self):
        """설정 저장 및 자동매매 준비"""
        buy_settings = self.get_buy_settings()
        sell_settings = self.get_sell_settings()
        
        # 설정 검증
        if not buy_settings['condition_idx']:
            QMessageBox.warning(self, "설정 오류", "조건식을 선택해주세요.")
            return
            
        if not self.token:
            QMessageBox.warning(self, "로그인 필요", "로그인 후 이용해주세요.")
            return
            
        # 설정 값들을 로그로 출력
        print("=== 주문 설정 저장 ===")
        print(f"매수 조건식: {buy_settings['condition']}")
        print(f"매수 방식: {'시장가' if buy_settings['is_market_order'] else '지정가'}")
        if not buy_settings['is_market_order']:
            print(f"매수 호가: {buy_settings['price_offset']}호가")
        print(f"매수 금액: {buy_settings['amount']:,}원")
        print(f"최대 보유 종목: {buy_settings['max_stocks']}개")
        
        print(f"매도 조건식: {sell_settings['condition']}")
        print(f"매도 방식: {'시장가' if sell_settings['is_market_order'] else '지정가'}")
        if not sell_settings['is_market_order']:
            print(f"매도 호가: {sell_settings['price_offset']}호가")
        print("=====================")
        
        # 자동매매 시작 버튼 활성화
        self.start_auto_btn.setEnabled(True)
        
        # 저장 완료 메시지
        QMessageBox.information(self, "저장 완료", 
                               "주문 설정이 저장되었습니다.\n"
                               "'자동매매 시작' 버튼을 눌러 자동매매를 시작할 수 있습니다.")
        
    def start_auto_trading(self):
        """자동매매 시작"""
        if not self.auto_trading_service:
            QMessageBox.warning(self, "서비스 오류", "자동매매 서비스가 초기화되지 않았습니다.")
            return
            
        try:
            from services.auto_trading_service import TradingSettings
            
            buy_settings = self.get_buy_settings()
            
            # 설정 객체 생성
            trading_settings = TradingSettings(
                condition_idx=buy_settings['condition_idx'],
                condition_name=buy_settings['condition'],
                is_market_order=buy_settings['is_market_order'],
                price_offset=buy_settings['price_offset'],
                buy_amount=buy_settings['amount'],
                max_stocks=buy_settings['max_stocks']
            )
            
            # 확인 대화상자
            reply = QMessageBox.question(
                self, 
                "자동매매 시작", 
                f"다음 설정으로 자동매매를 시작하시겠습니까?\n\n"
                f"조건식: {trading_settings.condition_name}\n"
                f"매수금액: {trading_settings.buy_amount:,}원\n"
                f"최대종목: {trading_settings.max_stocks}개\n"
                f"매수방식: {'시장가' if trading_settings.is_market_order else '지정가'}\n\n"
                f"⚠️ 실제 거래가 실행됩니다!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 자동매매 시작
                self.auto_trading_service.start_auto_trading(trading_settings)
                
                # UI 상태 변경
                self.start_auto_btn.setVisible(False)
                self.stop_auto_btn.setVisible(True)
                self.auto_trading_active = True
                
                # 설정 변경 방지
                self.save_btn.setEnabled(False)
                
                print("🚀 자동매매 시작됨")
                
        except Exception as e:
            QMessageBox.critical(self, "자동매매 시작 오류", f"자동매매 시작 중 오류가 발생했습니다:\n{e}")
            print(f"❌ 자동매매 시작 오류: {e}")
            
    def stop_auto_trading(self):
        """자동매매 중지"""
        if not self.auto_trading_service:
            return
            
        try:
            reply = QMessageBox.question(
                self, 
                "자동매매 중지", 
                "자동매매를 중지하시겠습니까?\n\n"
                "⚠️ 진행 중인 주문은 그대로 유지됩니다.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 자동매매 중지
                self.auto_trading_service.stop_auto_trading()
                
                # UI 상태 변경
                self.start_auto_btn.setVisible(True)
                self.stop_auto_btn.setVisible(False)
                self.auto_trading_active = False
                
                # 설정 변경 허용
                self.save_btn.setEnabled(True)
                
                print("⏹️ 자동매매 중지됨")
                
        except Exception as e:
            QMessageBox.critical(self, "자동매매 중지 오류", f"자동매매 중지 중 오류가 발생했습니다:\n{e}")
            print(f"❌ 자동매매 중지 오류: {e}")
            
    def on_position_added(self, position_data):
        """새로운 포지션 추가됨"""
        print(f"💰 새로운 매수: {position_data['stock_code']} {position_data['quantity']}주")
        
        # 알림 메시지 (옵션)
        if hasattr(self, 'show_trading_notifications') and self.show_trading_notifications:
            self.show_notification(f"매수 완료: {position_data['stock_code']}")
            
    def on_trading_status_changed(self, status):
        """자동매매 상태 변경"""
        self.status_label.setText(status)
        
        if status == "실행 중":
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        elif status == "중지됨":
            self.status_label.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: #3498db; font-weight: bold;")
            
    def on_trading_error(self, error):
        """자동매매 오류 발생"""
        print(f"❌ 자동매매 오류: {error}")
        QMessageBox.warning(self, "자동매매 오류", f"자동매매 중 오류가 발생했습니다:\n{error}")
        
    def update_trading_status(self):
        """자동매매 상태 업데이트"""
        if not self.auto_trading_service:
            return
            
        try:
            status = self.auto_trading_service.get_status()
            
            # 상태 정보 업데이트
            self.position_count_label.setText(f"{status['total_positions']}개")
            self.pending_orders_label.setText(f"{status['pending_orders']}개")
            self.monitoring_stocks_label.setText(f"{status['monitoring_stocks']}개")
            
        except Exception as e:
            print(f"❌ 상태 업데이트 오류: {e}")
        
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
            
    def show_notification(self, message):
        """시스템 알림 표시 (옵션)"""
        # 간단한 상태바 메시지로 대체
        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(message, 3000)
            
    def closeEvent(self, event):
        """위젯 닫기 이벤트"""
        if self.auto_trading_active:
            reply = QMessageBox.question(
                self, 
                "자동매매 실행 중", 
                "자동매매가 실행 중입니다.\n정말 종료하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
                
        self.cleanup()
        event.accept()