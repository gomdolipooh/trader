from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class ConditionResultWindow(QWidget):
    def __init__(self, cnsl_idx, cnsl_nm, search_type, condition_service, parent=None):
        super().__init__(parent)
        self.cnsl_idx = cnsl_idx
        self.cnsl_nm = cnsl_nm
        self.search_type = search_type
        self.condition_service = condition_service
        self.setup_ui()
        self.connect_signals()
        
        # 조건검색 요청
        self.condition_service.request_condition_search(cnsl_idx, search_type)
        
    def setup_ui(self):
        """UI 구성"""
        search_type_name = "실시간" if self.search_type == '1' else "일반"
        self.setWindowTitle(f"[{search_type_name}] {self.cnsl_nm} - 조건검색 결과")
        self.setGeometry(200, 200, 800, 600)
        
        layout = QVBoxLayout()
        
        # 상태 표시
        status_frame = QFrame()
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("종목 데이터를 불러오는 중...")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        
        if self.search_type == '1':
            real_status = QLabel("🔴 실시간 모니터링 중")
            real_status.setStyleSheet("color: red; font-weight: bold;")
            status_layout.addWidget(real_status)
            
        status_layout.addStretch()
        status_frame.setLayout(status_layout)
        layout.addWidget(status_frame)
        
        # 종목 테이블
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(5)
        self.stock_table.setHorizontalHeaderLabels(["상태", "종목명", "종목코드", "현재가", "등락률"])
        
        # 테이블 설정
        header = self.stock_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        self.stock_table.setColumnWidth(0, 50)   # 상태
        self.stock_table.setColumnWidth(2, 80)   # 종목코드
        self.stock_table.setColumnWidth(3, 100)  # 현재가
        self.stock_table.setColumnWidth(4, 80)   # 등락률
        
        self.stock_table.setAlternatingRowColors(True)
        self.stock_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.stock_table)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        if self.search_type == '1':
            self.stop_btn = QPushButton("실시간 중지")
            self.stop_btn.clicked.connect(self.stop_real_monitoring)
            button_layout.addWidget(self.stop_btn)
            
        self.close_btn = QPushButton("닫기")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def connect_signals(self):
        """시그널 연결"""
        self.condition_service.stock_data_received.connect(self.on_stock_data_received)
        self.condition_service.real_data_received.connect(self.on_real_data_received)
        
    def on_stock_data_received(self, cnsl_idx, stock_list):
        """종목 데이터 수신 처리"""
        if cnsl_idx != self.cnsl_idx:
            return
            
        if len(stock_list) > 100:
            self.status_label.setText(f"⚠️ 종목이 {len(stock_list)}개로 100개를 초과합니다. 조건식을 더 구체적으로 설정해주세요.")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            return
            
        self.update_stock_table(stock_list)
        
        if self.search_type == '1':
            self.status_label.setText(f"실시간 조건검색 시작: {len(stock_list)}개 종목 등록")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.status_label.setText(f"조회 완료: {len(stock_list)}개 종목")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
    def update_stock_table(self, stock_list):
        """종목 테이블 업데이트"""
        self.stock_table.setRowCount(len(stock_list))
        
        if not stock_list:
            self.stock_table.setRowCount(1)
            self.stock_table.setItem(0, 1, QTableWidgetItem("조건에 맞는 종목이 없습니다"))
            return
            
        for i, stock in enumerate(stock_list):
            try:
                if self.search_type == '1':
                    # 실시간 조건검색 - 종목코드만 있음
                    code = stock.get("jmcode", "").strip()
                    clean_code = code.replace("A", "") if code.startswith("A") else code
                    
                    self.stock_table.setItem(i, 0, QTableWidgetItem("🟡"))
                    self.stock_table.setItem(i, 1, QTableWidgetItem("실시간 데이터 대기 중..."))
                    self.stock_table.setItem(i, 2, QTableWidgetItem(clean_code))
                    self.stock_table.setItem(i, 3, QTableWidgetItem("-"))
                    self.stock_table.setItem(i, 4, QTableWidgetItem("-"))
                    
                else:
                    # 일반 조건검색
                    name = stock.get("302", "").strip() or f"종목{i+1}"
                    
                    # 현재가
                    price_raw = stock.get("10", "0").strip()
                    try:
                        price = int(price_raw) if price_raw.isdigit() else 0
                        price_str = f"{price:,}원"
                    except:
                        price_str = "0원"
                    
                    # 등락률
                    rate_raw = stock.get("12", "0").strip()
                    try:
                        rate_num = int(rate_raw) / 100 if rate_raw.isdigit() else 0
                        rate_str = f"{rate_num:.2f}%"
                    except:
                        rate_str = "0.00%"
                    
                    # 전일대비구분으로 상태 표시
                    change_code = stock.get("25", "2").strip()
                    if change_code == "1" or change_code == "4":  # 상승
                        status_symbol = "🔴"
                    elif change_code == "3" or change_code == "5":  # 하락
                        status_symbol = "🔵"
                    else:  # 보합
                        status_symbol = "⚪"
                    
                    # 종목코드
                    code = stock.get("9001", "").strip()
                    
                    self.stock_table.setItem(i, 0, QTableWidgetItem(status_symbol))
                    self.stock_table.setItem(i, 1, QTableWidgetItem(name))
                    self.stock_table.setItem(i, 2, QTableWidgetItem(code))
                    self.stock_table.setItem(i, 3, QTableWidgetItem(price_str))
                    self.stock_table.setItem(i, 4, QTableWidgetItem(rate_str))
                    
            except Exception as e:
                print(f"종목 {i} 처리 오류: {e}")
                self.stock_table.setItem(i, 1, QTableWidgetItem("데이터 처리 오류"))
                
    def on_real_data_received(self, cnsl_idx, stock_code, values):
        """실시간 데이터 수신 처리"""
        if self.search_type != '1':
            return
            
        # 종목코드에서 A 제거
        clean_code = stock_code.replace("A", "") if stock_code.startswith("A") else stock_code
        
        # 테이블에서 해당 종목 찾기
        for i in range(self.stock_table.rowCount()):
            code_item = self.stock_table.item(i, 2)
            if code_item and clean_code in code_item.text():
                insert_delete = values.get("843", "I")
                
                if insert_delete == "D":
                    # 삭제 - 테이블에서 제거
                    self.stock_table.removeRow(i)
                    break
                else:
                    # 업데이트
                    self.stock_table.setItem(i, 0, QTableWidgetItem("🔴"))
                    self.stock_table.setItem(i, 1, QTableWidgetItem("실시간 업데이트됨"))
                    
                    # 시간 정보가 있으면 표시
                    time_info = values.get('20', '')
                    if time_info:
                        self.stock_table.setItem(i, 4, QTableWidgetItem(f"시간: {time_info}"))
                break
        else:
            # 새로운 종목 추가
            if values.get("843", "I") == "I":
                row = self.stock_table.rowCount()
                self.stock_table.insertRow(row)
                self.stock_table.setItem(row, 0, QTableWidgetItem("🟢"))
                self.stock_table.setItem(row, 1, QTableWidgetItem("신규 진입"))
                self.stock_table.setItem(row, 2, QTableWidgetItem(clean_code))
                self.stock_table.setItem(row, 3, QTableWidgetItem("-"))
                
                time_info = values.get('20', '')
                self.stock_table.setItem(row, 4, QTableWidgetItem(f"시간: {time_info}" if time_info else "-"))
        
        # 상태 업데이트
        from datetime import datetime
        now = datetime.now().strftime("%H:%M:%S")
        self.status_label.setText(f"🔴 실시간 업데이트: {now}")
        
    def stop_real_monitoring(self):
        """실시간 모니터링 중지"""
        self.condition_service.cancel_real_condition(self.cnsl_idx)
        self.status_label.setText("실시간 모니터링 중지됨")
        self.status_label.setStyleSheet("color: gray; font-weight: bold;")
        self.stop_btn.setEnabled(False)
        
    def closeEvent(self, event):
        """창 닫기 이벤트"""
        if self.search_type == '1':
            self.condition_service.cancel_real_condition(self.cnsl_idx)
        event.accept()