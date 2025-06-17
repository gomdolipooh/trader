from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from datetime import datetime

class DebugConsole(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """디버그 콘솔 UI 구성"""
        self.setWindowTitle("조건검색 디버그 콘솔")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        # 상단 제어 영역
        control_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("로그 지우기")
        self.clear_btn.clicked.connect(self.clear_logs)
        
        self.save_btn = QPushButton("로그 저장")
        self.save_btn.clicked.connect(self.save_logs)
        
        self.auto_scroll_cb = QCheckBox("자동 스크롤")
        self.auto_scroll_cb.setChecked(True)
        
        control_layout.addWidget(self.clear_btn)
        control_layout.addWidget(self.save_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.auto_scroll_cb)
        
        layout.addLayout(control_layout)
        
        # 로그 표시 영역
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        
        # 다크 테마 스타일
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3e3e3e;
            }
        """)
        
        layout.addWidget(self.log_text)
        
        # 하단 상태 영역
        self.status_label = QLabel("디버그 콘솔 준비")
        self.status_label.setStyleSheet("color: #666666; font-size: 10px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
    def add_log(self, message):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # 메시지 타입에 따른 색상 지정
        color = self.get_message_color(message)
        
        formatted_message = f'<span style="color: #888888;">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        
        self.log_text.append(formatted_message)
        
        # 자동 스크롤
        if self.auto_scroll_cb.isChecked():
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.log_text.setTextCursor(cursor)
            
        # 상태 업데이트
        self.status_label.setText(f"마지막 로그: {timestamp}")
        
    def get_message_color(self, message):
        """메시지 내용에 따른 색상 반환"""
        if "❌" in message or "오류" in message or "실패" in message:
            return "#ff6b6b"  # 빨간색
        elif "✅" in message or "성공" in message or "완료" in message:
            return "#51cf66"  # 초록색
        elif "⚠️" in message or "경고" in message:
            return "#ffd43b"  # 노란색
    def get_message_color(self, message):
        """메시지 내용에 따른 색상 반환"""
        if "❌" in message or "오류" in message or "실패" in message:
            return "#ff6b6b"  # 빨간색
        elif "✅" in message or "성공" in message or "완료" in message:
            return "#51cf66"  # 초록색
        elif "⚠️" in message or "경고" in message:
            return "#ffd43b"  # 노란색
        elif "🔄" in message or "시도" in message or "중" in message:
            return "#74c0fc"  # 파란색
        elif "📤" in message or "📥" in message or "전송" in message or "수신" in message:
            return "#da77f2"  # 보라색
        else:
            return "#ffffff"  # 기본 흰색
            
    def clear_logs(self):
        """로그 지우기"""
        self.log_text.clear()
        self.status_label.setText("로그가 지워졌습니다")
        
    def save_logs(self):
        """로그 파일로 저장"""
        try:
            filename = f"condition_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath, _ = QFileDialog.getSaveFileName(
                self, 
                "디버그 로그 저장", 
                filename, 
                "텍스트 파일 (*.txt);;모든 파일 (*)"
            )
            
            if filepath:
                # HTML 태그 제거하고 순수 텍스트만 저장
                plain_text = self.log_text.toPlainText()
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(plain_text)
                    
                self.status_label.setText(f"로그 저장됨: {filepath}")
                QMessageBox.information(self, "저장 완료", f"로그가 저장되었습니다:\n{filepath}")
                
        except Exception as e:
            QMessageBox.warning(self, "저장 실패", f"로그 저장에 실패했습니다:\n{e}")
            
    def closeEvent(self, event):
        """창 닫기 이벤트"""
        # 창을 숨기기만 하고 완전히 닫지는 않음
        self.hide()
        event.ignore()