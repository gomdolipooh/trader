from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import datetime

class ConditionResultWindow(QMainWindow):
    def __init__(self, cnsl_idx, cnsl_nm, search_type, condition_service, parent=None):
        super().__init__(parent)
        self.cnsl_idx = cnsl_idx
        self.cnsl_nm = cnsl_nm
        self.search_type = search_type
        self.condition_service = condition_service
        self.stock_data = []  # 종목 데이터 저장
        
        # 창 설정
        search_type_name = "실시간" if search_type == '1' else "일반"
        self.setWindowTitle(f"[{search_type_name}] {cnsl_nm} - 조건검색 결과")
        self.setGeometry(200, 200, 800, 600)
        
        # 창 아이콘 설정
        self.setWindowIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        
        self.setup_ui()
        self.connect_signals()
        
        # 조건검색 시작
        self.start_condition_search()
        
    def setup_ui(self):
        """UI 구성"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # 상단 정보 패널
        info_panel = self.create_info_panel()
        layout.addWidget(info_panel)
        
        # 종목 리스트 테이블
        self.create_stock_table()
        layout.addWidget(self.stock_table)
        
        # 하단 버튼 패널
        button_panel = self.create_button_panel()
        layout.addWidget(button_panel)
        
        central_widget.setLayout(layout)
        
        # 상태바
        self.statusBar().showMessage("조건검색 준비 중...")
        
    def create_info_panel(self):
        """상단 정보 패널 생성"""
        group = QGroupBox("조건검색 정보")
        layout = QGridLayout()
        
        # 조건식명
        layout.addWidget(QLabel("조건식명:"), 0, 0)
        condition_label = QLabel(self.cnsl_nm)
        condition_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        layout.addWidget(condition_label, 0, 1)
        
        # 검색 타입
        layout.addWidget(QLabel("검색 타입:"), 0, 2)
        search_type_name = "실시간 조건검색" if self.search_type == '1' else "일반 조건검색"
        type_label = QLabel(search_type_name)
        if self.search_type == '1':
            type_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        else:
            type_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        layout.addWidget(type_label, 0, 3)
        
        # 상태 표시
        layout.addWidget(QLabel("상태:"), 1, 0)
        self.status_label = QLabel("조건검색 시작 중...")
        self.status_label.setStyleSheet("color: #3498db;")
        layout.addWidget(self.status_label, 1, 1)
        
        # 종목 수
        layout.addWidget(QLabel("종목 수:"), 1, 2)
        self.count_label = QLabel("0개")
        self.count_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.count_label, 1, 3)
        
        # 실시간 상태 (실시간 검색인 경우만)
        if self.search_type == '1':
            layout.addWidget(QLabel("실시간:"), 2, 0)
            self.real_status_label = QLabel("🔴 모니터링 중")
            self.real_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            layout.addWidget(self.real_status_label, 2, 1)
            
            # 마지막 업데이트 시간
            layout.addWidget(QLabel("마지막 업데이트:"), 2, 2)
            self.last_update_label = QLabel("-")
            layout.addWidget(self.last_update_label, 2, 3)
        
        group.setLayout(layout)
        return group
        
    def create_stock_table(self):
        """종목 테이블 생성"""
        self.stock_table = QTableWidget()
        
        if self.search_type == '1':
            # 실시간 조건검색 컬럼
            headers = ["상태", "종목코드", "종목명", "현재가", "등락률", "거래량", "시간", "비고"]
            self.stock_table.setColumnCount(len(headers))
            self.stock_table.setHorizontalHeaderLabels(headers)
            
            # 컬럼 너비 설정
            self.stock_table.setColumnWidth(0, 60)   # 상태
            self.stock_table.setColumnWidth(1, 80)   # 종목코드
            self.stock_table.setColumnWidth(2, 150)  # 종목명
            self.stock_table.setColumnWidth(3, 100)  # 현재가
            self.stock_table.setColumnWidth(4, 80)   # 등락률
            self.stock_table.setColumnWidth(5, 100)  # 거래량
            self.stock_table.setColumnWidth(6, 80)   # 시간
            self.stock_table.setColumnWidth(7, 100)  # 비고
        else:
            # 일반 조건검색 컬럼
            headers = ["순번", "종목코드", "종목명", "현재가", "등락률", "거래량", "시가총액"]
            self.stock_table.setColumnCount(len(headers))
            self.stock_table.setHorizontalHeaderLabels(headers)
            
            # 컬럼 너비 설정
            self.stock_table.setColumnWidth(0, 60)   # 순번
            self.stock_table.setColumnWidth(1, 80)   # 종목코드
            self.stock_table.setColumnWidth(2, 150)  # 종목명
            self.stock_table.setColumnWidth(3, 100)  # 현재가
            self.stock_table.setColumnWidth(4, 80)   # 등락률
            self.stock_table.setColumnWidth(5, 100)  # 거래량
            self.stock_table.setColumnWidth(6, 120)  # 시가총액
        
        # 테이블 설정
        self.stock_table.setAlternatingRowColors(True)
        self.stock_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.stock_table.setSortingEnabled(True)
        
        # 헤더 스타일
        self.stock_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
    def create_button_panel(self):
        """하단 버튼 패널 생성"""
        panel = QWidget()
        layout = QHBoxLayout()
        
        # 새로고침 버튼 (일반 조건검색만)
        if self.search_type == '0':
            self.refresh_btn = QPushButton("🔄 새로고침")
            self.refresh_btn.clicked.connect(self.refresh_search)
            layout.addWidget(self.refresh_btn)
        
        # 엑셀 내보내기 버튼
        self.export_btn = QPushButton("📊 엑셀 내보내기")
        self.export_btn.clicked.connect(self.export_to_excel)
        self.export_btn.setEnabled(False)  # 데이터가 있을 때만 활성화
        layout.addWidget(self.export_btn)
        
        layout.addStretch()
        
        # 실시간 정지/시작 버튼 (실시간 조건검색만)
        if self.search_type == '1':
            self.real_toggle_btn = QPushButton("⏸️ 실시간 정지")
            self.real_toggle_btn.clicked.connect(self.toggle_real_monitoring)
            layout.addWidget(self.real_toggle_btn)
        
        # 닫기 버튼
        self.close_btn = QPushButton("❌ 닫기")
        self.close_btn.clicked.connect(self.close)
        layout.addWidget(self.close_btn)
        
        panel.setLayout(layout)
        return panel
        
    def connect_signals(self):
        """시그널 연결"""
        if self.condition_service:
            self.condition_service.stock_data_received.connect(self.on_stock_data_received)
            self.condition_service.real_data_received.connect(self.on_real_data_received)
            self.condition_service.debug_message.connect(self.on_debug_message)
            
    def start_condition_search(self):
        """조건검색 시작"""
        if self.condition_service:
            self.status_label.setText("조건검색 요청 중...")
            self.status_label.setStyleSheet("color: #f39c12;")
            self.statusBar().showMessage("조건검색 요청 전송 중...")
            
            self.condition_service.request_condition_search(self.cnsl_idx, self.search_type)
        else:
            self.status_label.setText("❌ 서비스 오류")
            self.status_label.setStyleSheet("color: #e74c3c;")
            
    def on_stock_data_received(self, cnsl_idx, stock_list):
        """조건검색 결과 수신"""
        if cnsl_idx != self.cnsl_idx:
            return  # 다른 조건식 결과는 무시
            
        self.stock_data = stock_list
        self.update_stock_table()
        
        # 상태 업데이트
        stock_count = len(stock_list)
        self.count_label.setText(f"{stock_count}개")
        
        if stock_count == 0:
            self.status_label.setText("조건에 맞는 종목이 없습니다")
            self.status_label.setStyleSheet("color: #95a5a6;")
            self.statusBar().showMessage("조건검색 완료 - 결과 없음")
        elif stock_count > 100:
            self.status_label.setText(f"⚠️ 종목 수 초과 ({stock_count}개)")
            self.status_label.setStyleSheet("color: #e67e22;")
            self.statusBar().showMessage("종목 수가 100개를 초과합니다")
        else:
            if self.search_type == '1':
                self.status_label.setText("실시간 모니터링 중")
                self.status_label.setStyleSheet("color: #e74c3c;")
                self.statusBar().showMessage("실시간 조건검색 활성화")
            else:
                self.status_label.setText("조회 완료")
                self.status_label.setStyleSheet("color: #27ae60;")
                self.statusBar().showMessage("조건검색 완료")
                
        # 엑셀 내보내기 버튼 활성화
        self.export_btn.setEnabled(stock_count > 0)
        
    def update_stock_table(self):
        """종목 테이블 업데이트"""
        if not self.stock_data:
            self.stock_table.setRowCount(1)
            item = QTableWidgetItem("조건에 맞는 종목이 없습니다")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stock_table.setItem(0, 0, item)
            self.stock_table.setSpan(0, 0, 1, self.stock_table.columnCount())
            return
            
        self.stock_table.setRowCount(len(self.stock_data))
        
        for i, stock in enumerate(self.stock_data):
            if self.search_type == '1':
                # 실시간 조건검색 데이터 처리
                self.update_real_stock_row(i, stock)
            else:
                # 일반 조건검색 데이터 처리
                self.update_normal_stock_row(i, stock)
                
    def update_normal_stock_row(self, row, stock):
        """일반 조건검색 행 업데이트"""
        try:
            # 디버그: 실제 데이터 출력
            print(f"=== 종목 {row+1} 디버그 ===")
            print(f"전체 데이터: {stock}")
            print(f"필드 9001 (종목코드): '{stock.get('9001', '')}'")
            print(f"필드 302 (종목명): '{stock.get('302', '')}'")
            print(f"필드 10 (현재가): '{stock.get('10', '')}'")
            print(f"필드 12 (등락률): '{stock.get('12', '')}'")
            print(f"필드 25 (전일대비기호): '{stock.get('25', '')}'")
            print(f"필드 11 (전일대비): '{stock.get('11', '')}'")
            print(f"필드 13 (거래량): '{stock.get('13', '')}'")
            print("===========================")
            
            # 순번
            self.stock_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            
            # 종목코드 (필드 9001) - A 제거
            code_raw = stock.get("9001", "").strip()
            code = code_raw.replace("A", "") if code_raw.startswith("A") else code_raw
            self.stock_table.setItem(row, 1, QTableWidgetItem(code))
            
            # 종목명 (필드 302)
            name = stock.get("302", "").strip()
            if not name:
                name = f"종목{row+1}"
            self.stock_table.setItem(row, 2, QTableWidgetItem(name))
            
            # 현재가 (필드 10) - 숫자 변환 시도
            price_raw = stock.get("10", "0").strip()
            print(f"현재가 원본: '{price_raw}'")
            try:
                # 앞의 0 제거하고 숫자로 변환
                if price_raw and price_raw.replace('0', ''):
                    price = int(price_raw)
                    print(f"현재가 변환: {price}")
                else:
                    price = 0
                    
                price_item = QTableWidgetItem(f"{price:,}")
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.stock_table.setItem(row, 3, price_item)
            except Exception as e:
                print(f"현재가 변환 오류: {e}")
                self.stock_table.setItem(row, 3, QTableWidgetItem(price_raw))
            
            # 등락률 처리 - 실제 데이터 형태 확인
            rate_raw = stock.get("12", "0").strip()
            change_code = stock.get("25", "2").strip()
            
            print(f"등락률 원본: '{rate_raw}', 타입: {type(rate_raw)}")
            print(f"전일대비기호: '{change_code}'")
            
            try:
                # 여러 케이스 시도
                if rate_raw:
                    # 케이스 1: 이미 소수점이 포함된 경우 (예: "6.54")
                    if '.' in rate_raw:
                        rate_num = float(rate_raw)
                        print(f"케이스 1 - 소수점 포함: {rate_num}")
                    
                    # 케이스 2: 정수 형태지만 100을 나눠야 하는 경우 (예: "654" -> 6.54)
                    elif rate_raw.isdigit():
                        rate_int = int(rate_raw)
                        if rate_int > 1000:  # 큰 값이면 100으로 나누기
                            rate_num = rate_int / 100.0
                            print(f"케이스 2a - 큰 정수값: {rate_int} -> {rate_num}")
                        else:  # 작은 값이면 그대로
                            rate_num = rate_int / 100.0
                            print(f"케이스 2b - 작은 정수값: {rate_int} -> {rate_num}")
                    
                    # 케이스 3: 앞에 0이 많은 경우 (예: "000006540" -> 65.40)
                    else:
                        try:
                            rate_int = int(rate_raw.lstrip('0')) if rate_raw.lstrip('0') else 0
                            rate_num = rate_int / 100.0
                            print(f"케이스 3 - 앞에 0 제거: {rate_raw} -> {rate_int} -> {rate_num}")
                        except:
                            rate_num = 0.0
                            print(f"케이스 3 실패")
                else:
                    rate_num = 0.0
                    print(f"케이스 0 - 빈 값")
                
                # 전일대비기호에 따른 부호 결정
                if change_code in ["3", "5"]:  # 하락
                    rate_num = -abs(rate_num)
                    print(f"하락 적용: {rate_num}")
                elif change_code in ["1", "4"]:  # 상승
                    rate_num = abs(rate_num)
                    print(f"상승 적용: {rate_num}")
                
                rate_str = f"{rate_num:+.2f}%" if rate_num != 0 else "0.00%"
                print(f"최종 등락률: {rate_str}")
                
                rate_item = QTableWidgetItem(rate_str)
                rate_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                
                # 등락률에 따른 색상 설정
                if rate_num > 0:
                    rate_item.setForeground(QColor("#e74c3c"))  # 상승 - 빨강
                elif rate_num < 0:
                    rate_item.setForeground(QColor("#3498db"))  # 하락 - 파랑
                else:
                    rate_item.setForeground(QColor("#7f8c8d"))  # 보합 - 회색
                
                self.stock_table.setItem(row, 4, rate_item)
                
            except Exception as e:
                print(f"등락률 처리 오류: {e}")
                # 원본 데이터 그대로 표시 (디버그용)
                debug_str = f"원본:{rate_raw}"
                self.stock_table.setItem(row, 4, QTableWidgetItem(debug_str))
            
            # 거래량 (필드 13)
            volume_raw = stock.get("13", "0").strip()
            try:
                if volume_raw and volume_raw.replace('0', ''):
                    volume = int(volume_raw)
                else:
                    volume = 0
                volume_item = QTableWidgetItem(f"{volume:,}")
                volume_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                self.stock_table.setItem(row, 5, volume_item)
            except Exception as e:
                print(f"거래량 처리 오류: {e}")
                self.stock_table.setItem(row, 5, QTableWidgetItem(volume_raw))
            
            # 시가총액
            market_cap = "조회중"
            market_cap_item = QTableWidgetItem(market_cap)
            market_cap_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.stock_table.setItem(row, 6, market_cap_item)
            
        except Exception as e:
            print(f"일반 조건검색 행 업데이트 오류: {e}")
            print(f"문제 데이터: {stock}")
            # 오류 발생시 원본 데이터 표시
            for col in range(min(len(stock), self.stock_table.columnCount())):
                key = list(stock.keys())[col] if col < len(stock) else ""
                value = stock.get(key, "")
                self.stock_table.setItem(row, col, QTableWidgetItem(f"{key}:{value}"))
                
    def update_real_stock_row(self, row, stock):
        """실시간 조건검색 행 업데이트"""
        try:
            # 상태
            status_item = QTableWidgetItem("🟡")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stock_table.setItem(row, 0, status_item)
            
            # 종목코드 
            if isinstance(stock, dict) and "jmcode" in stock:
                # 실시간 데이터 형태
                code = stock.get("jmcode", "").strip()
                if code.startswith("A"):
                    code = code[1:]  # A 제거
            else:
                # 일반 데이터 형태
                code = str(stock).strip()
                
            self.stock_table.setItem(row, 1, QTableWidgetItem(code))
            
            # 종목명 (실시간에서는 기본적으로 없음)
            self.stock_table.setItem(row, 2, QTableWidgetItem("실시간 대기 중..."))
            
            # 현재가, 등락률, 거래량 (실시간 데이터 수신 후 업데이트)
            self.stock_table.setItem(row, 3, QTableWidgetItem("-"))
            self.stock_table.setItem(row, 4, QTableWidgetItem("-"))
            self.stock_table.setItem(row, 5, QTableWidgetItem("-"))
            
            # 시간
            now = datetime.datetime.now().strftime("%H:%M:%S")
            self.stock_table.setItem(row, 6, QTableWidgetItem(now))
            
            # 비고
            self.stock_table.setItem(row, 7, QTableWidgetItem("신규 진입"))
            
        except Exception as e:
            print(f"실시간 조건검색 행 업데이트 오류: {e}")
            
    def on_real_data_received(self, cnsl_idx, stock_code, values):
        """실시간 데이터 수신"""
        if self.search_type != '1':
            return  # 실시간이 아니면 무시
            
        try:
            # 해당 종목이 테이블에 있는지 찾기
            for row in range(self.stock_table.rowCount()):
                code_item = self.stock_table.item(row, 1)
                if code_item and stock_code.replace("A", "") in code_item.text():
                    # 실시간 데이터로 행 업데이트
                    self.update_real_data_row(row, stock_code, values)
                    break
                    
            # 마지막 업데이트 시간 갱신
            if hasattr(self, 'last_update_label'):
                now = datetime.datetime.now().strftime("%H:%M:%S")
                self.last_update_label.setText(now)
                
        except Exception as e:
            print(f"실시간 데이터 처리 오류: {e}")
            
    def update_real_data_row(self, row, stock_code, values):
        """실시간 데이터로 행 업데이트"""
        try:
            insert_delete = values.get("843", "I")  # I:삽입, D:삭제
            
            if insert_delete == "D":
                # 종목 삭제
                status_item = QTableWidgetItem("🔴")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.stock_table.setItem(row, 0, status_item)
                self.stock_table.setItem(row, 7, QTableWidgetItem("조건 이탈"))
            else:
                # 종목 업데이트
                status_item = QTableWidgetItem("🟢")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.stock_table.setItem(row, 0, status_item)
                
                # 시간 업데이트
                time_str = values.get("20", datetime.datetime.now().strftime("%H:%M:%S"))
                self.stock_table.setItem(row, 6, QTableWidgetItem(time_str))
                
                self.stock_table.setItem(row, 7, QTableWidgetItem("실시간 갱신"))
                
        except Exception as e:
            print(f"실시간 데이터 행 업데이트 오류: {e}")
            
    def on_debug_message(self, message):
        """디버그 메시지 처리"""
        # 이 창과 관련된 메시지만 처리
        if self.cnsl_idx in message or "조건검색" in message:
            print(f"[조건결과창] {message}")
            
    def refresh_search(self):
        """새로고침 (일반 조건검색만)"""
        if self.search_type == '0':
            self.start_condition_search()
            
    def toggle_real_monitoring(self):
        """실시간 모니터링 토글"""
        if self.search_type == '1':
            # 실제로는 실시간 정지/재시작 기능 구현
            current_text = self.real_toggle_btn.text()
            if "정지" in current_text:
                self.real_toggle_btn.setText("▶️ 실시간 시작")
                self.real_status_label.setText("⏸️ 일시정지")
            else:
                self.real_toggle_btn.setText("⏸️ 실시간 정지")
                self.real_status_label.setText("🔴 모니터링 중")
                
    def export_to_excel(self):
        """엑셀로 내보내기"""
        if not self.stock_data:
            QMessageBox.warning(self, "경고", "내보낼 데이터가 없습니다.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "엑셀 파일 저장", 
            f"{self.cnsl_nm}_조건검색결과.xlsx",
            "Excel Files (*.xlsx)"
        )
        
        if file_path:
            try:
                # 간단한 CSV 형태로 저장 (pandas 없이)
                import csv
                
                csv_path = file_path.replace('.xlsx', '.csv')
                with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # 헤더 작성
                    headers = []
                    for col in range(self.stock_table.columnCount()):
                        headers.append(self.stock_table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # 데이터 작성
                    for row in range(self.stock_table.rowCount()):
                        row_data = []
                        for col in range(self.stock_table.columnCount()):
                            item = self.stock_table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
                        
                QMessageBox.information(self, "완료", f"CSV 파일로 저장되었습니다:\n{csv_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "오류", f"파일 저장 중 오류가 발생했습니다:\n{e}")
                
    def closeEvent(self, event):
        """창 닫기 이벤트"""
        if self.search_type == '1' and self.condition_service:
            # 실시간 조건검색 해제
            self.condition_service.cancel_real_condition(self.cnsl_idx)
            
        event.accept()