import requests
import json
import time
import threading
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from dataclasses import dataclass
from typing import Dict, List, Optional
import traceback

@dataclass
class TradingSettings:
    """매매 설정 데이터 클래스"""
    condition_idx: str
    condition_name: str
    is_market_order: bool
    price_offset: int
    buy_amount: int
    max_stocks: int = 10  # 최대 동시 보유 종목 수
    
@dataclass
class Position:
    """보유 종목 정보"""
    stock_code: str
    stock_name: str
    buy_price: int
    quantity: int
    buy_time: datetime
    order_no: str = ""

class TradingAPI:
    """키움 API 매매 요청 클래스"""
    
    def __init__(self, token: str, is_mock: bool = False):
        self.token = token
        self.host = 'https://mockapi.kiwoom.com' if is_mock else 'https://api.kiwoom.com'
        
    def buy_stock(self, stock_code: str, quantity: int, price: Optional[int] = None, 
                  trade_type: str = '3') -> Dict:
        """
        주식 매수 주문
        
        Args:
            stock_code: 종목코드 (A 제거된 상태)
            quantity: 주문수량
            price: 주문단가 (시장가일 경우 None)
            trade_type: 매매구분 ('3': 시장가, '0': 보통지정가)
        """
        try:
            # A 제거 확인
            if stock_code.startswith('A'):
                stock_code = stock_code[1:]
                
            url = f"{self.host}/api/dostk/ordr"
            
            headers = {
                'Content-Type': 'application/json;charset=UTF-8',
                'authorization': f'Bearer {self.token}',
                'cont-yn': 'N',
                'next-key': '',
                'api-id': 'kt10000',
            }
            
            data = {
                'dmst_stex_tp': 'KRX',
                'stk_cd': stock_code,
                'ord_qty': str(quantity),
                'ord_uv': str(price) if price else '',
                'trde_tp': trade_type,
                'cond_uv': ''
            }
            
            print(f"📤 매수 주문 요청: {stock_code}, 수량: {quantity}, 가격: {price}, 타입: {trade_type}")
            
            response = requests.post(url, headers=headers, json=data)
            
            print(f"📥 매수 응답 코드: {response.status_code}")
            response_data = response.json()
            print(f"📥 매수 응답 데이터: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': response_data,
                'order_no': response_data.get('ord_no', '') if response.status_code == 200 else ''
            }
            
        except Exception as e:
            print(f"❌ 매수 주문 오류: {e}")
            return {
                'success': False,
                'error': str(e),
                'order_no': ''
            }

class AutoTradingService(QObject):
    """자동매매 서비스"""
    
    # 시그널 정의
    position_added = pyqtSignal(dict)  # 신규 매수 완료
    trading_status_changed = pyqtSignal(str)  # 매매 상태 변경
    debug_message = pyqtSignal(str)  # 디버그 메시지
    error_occurred = pyqtSignal(str)  # 오류 발생
    
    def __init__(self, token: str, condition_service, is_mock: bool = False):
        super().__init__()
        self.token = token
        self.condition_service = condition_service
        self.trading_api = TradingAPI(token, is_mock)
        
        # 매매 상태
        self.is_active = False
        self.settings: Optional[TradingSettings] = None
        self.positions: Dict[str, Position] = {}  # 종목코드: 포지션
        self.pending_orders: Dict[str, datetime] = {}  # 주문 대기 중인 종목들
        self.blacklist: set = set()  # 매수 실패한 종목들 (일시적 제외)
        
        # 모니터링 설정
        self.check_interval = 2.0  # 2초마다 체크 (너무 빠르면 API 제한 걸림)
        self.order_timeout = 30  # 주문 타임아웃 (30초)
        self.blacklist_duration = 300  # 블랙리스트 유지 시간 (5분)
        
        # 타이머 설정
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_new_stocks)
        
        # 현재 조건검색에서 감지된 종목들
        self.current_stocks: set = set()
        
        # 조건검색 시그널 연결
        if self.condition_service:
            self.condition_service.real_data_received.connect(self.on_real_data_received)
            self.condition_service.stock_data_received.connect(self.on_stock_data_received)
            
    def start_auto_trading(self, settings: TradingSettings):
        """자동매매 시작"""
        try:
            self.settings = settings
            self.is_active = True
            
            self.debug_message.emit(f"🚀 자동매매 시작: {settings.condition_name}")
            self.debug_message.emit(f"📊 설정 - 매수금액: {settings.buy_amount:,}원, 최대종목: {settings.max_stocks}개")
            
            # 실시간 조건검색 시작
            if self.condition_service:
                self.debug_message.emit(f"🔍 실시간 조건검색 시작: {settings.condition_idx}")
                self.condition_service.request_condition_search(settings.condition_idx, '1')
                
            # 모니터링 타이머 시작
            self.monitor_timer.start(int(self.check_interval * 1000))
            
            self.trading_status_changed.emit("실행 중")
            self.debug_message.emit("✅ 자동매매 시스템 활성화 완료")
            
        except Exception as e:
            self.error_occurred.emit(f"자동매매 시작 실패: {e}")
            self.debug_message.emit(f"❌ 자동매매 시작 오류: {e}")
            
    def stop_auto_trading(self):
        """자동매매 중지"""
        try:
            self.is_active = False
            self.monitor_timer.stop()
            
            # 실시간 조건검색 중지
            if self.condition_service and self.settings:
                self.condition_service.cancel_real_condition(self.settings.condition_idx)
                
            self.trading_status_changed.emit("중지됨")
            self.debug_message.emit("⏹️ 자동매매 시스템 중지")
            
        except Exception as e:
            self.error_occurred.emit(f"자동매매 중지 실패: {e}")
            
    def on_stock_data_received(self, cnsl_idx: str, stock_list: List):
        """조건검색 초기 결과 수신"""
        if not self.is_active or not self.settings:
            return
            
        if cnsl_idx != self.settings.condition_idx:
            return
            
        try:
            # 초기 종목 목록 저장
            new_stocks = set()
            for stock in stock_list:
                if isinstance(stock, dict):
                    stock_code = stock.get("9001", "").replace("A", "")
                else:
                    stock_code = str(stock).replace("A", "")
                    
                if stock_code:
                    new_stocks.add(stock_code)
                    
            self.current_stocks = new_stocks
            self.debug_message.emit(f"📋 초기 조건검색 결과: {len(new_stocks)}개 종목")
            
            # 즉시 매수 검토
            self.check_and_buy_stocks(new_stocks)
            
        except Exception as e:
            self.debug_message.emit(f"❌ 초기 종목 데이터 처리 오류: {e}")
            
    def on_real_data_received(self, cnsl_idx: str, stock_code: str, values: Dict):
        """실시간 데이터 수신"""
        if not self.is_active or not self.settings:
            return
            
        try:
            # 종목 코드 정리
            clean_code = stock_code.replace("A", "")
            
            # 삽입/삭제 구분
            insert_delete = values.get("843", "I")
            
            if insert_delete == "I":
                # 신규 진입 종목
                if clean_code not in self.current_stocks:
                    self.current_stocks.add(clean_code)
                    self.debug_message.emit(f"🆕 신규 진입 종목: {clean_code}")
                    
                    # 즉시 매수 검토
                    self.check_and_buy_single_stock(clean_code)
                    
            elif insert_delete == "D":
                # 조건 이탈 종목
                if clean_code in self.current_stocks:
                    self.current_stocks.remove(clean_code)
                    self.debug_message.emit(f"🚫 조건 이탈 종목: {clean_code}")
                    
        except Exception as e:
            self.debug_message.emit(f"❌ 실시간 데이터 처리 오류: {e}")
            
    def check_new_stocks(self):
        """주기적으로 새로운 종목 체크 (타이머 콜백)"""
        if not self.is_active:
            return
            
        try:
            # 대기 중인 주문 타임아웃 체크
            self.cleanup_pending_orders()
            
            # 블랙리스트 정리
            self.cleanup_blacklist()
            
            # 현재 감지된 종목들 중 매수 가능한 종목 체크
            buyable_stocks = self.get_buyable_stocks()
            if buyable_stocks:
                self.check_and_buy_stocks(buyable_stocks)
                
        except Exception as e:
            self.debug_message.emit(f"❌ 주기적 체크 오류: {e}")
            
    def get_buyable_stocks(self) -> set:
        """매수 가능한 종목들 반환"""
        if not self.current_stocks:
            return set()
            
        # 이미 보유 중이거나 주문 대기 중이거나 블랙리스트에 있는 종목 제외
        excluded = (
            set(self.positions.keys()) |
            set(self.pending_orders.keys()) |
            self.blacklist
        )
        
        return self.current_stocks - excluded
        
    def check_and_buy_stocks(self, stock_codes: set):
        """여러 종목 매수 검토"""
        for stock_code in stock_codes:
            if len(self.positions) >= self.settings.max_stocks:
                self.debug_message.emit(f"⚠️ 최대 보유 종목 수 도달 ({self.settings.max_stocks}개)")
                break
                
            self.check_and_buy_single_stock(stock_code)
            
    def check_and_buy_single_stock(self, stock_code: str):
        """단일 종목 매수 검토 및 실행"""
        if not self.is_active or not self.settings:
            return
            
        try:
            # 이미 처리 중인 종목인지 확인
            if (stock_code in self.positions or 
                stock_code in self.pending_orders or 
                stock_code in self.blacklist):
                return
                
            # 최대 보유 종목 수 체크
            if len(self.positions) >= self.settings.max_stocks:
                return
                
            self.debug_message.emit(f"💰 매수 검토 시작: {stock_code}")
            
            # 매수 수량 계산
            quantity = self.calculate_quantity(stock_code)
            if quantity <= 0:
                self.debug_message.emit(f"⚠️ 매수 수량 계산 실패: {stock_code}")
                return
                
            # 매수 주문 대기 목록에 추가
            self.pending_orders[stock_code] = datetime.now()
            
            # 매수 주문 실행 (별도 스레드에서)
            threading.Thread(
                target=self.execute_buy_order,
                args=(stock_code, quantity),
                daemon=True
            ).start()
            
        except Exception as e:
            self.debug_message.emit(f"❌ 매수 검토 오류 ({stock_code}): {e}")
            
    def calculate_quantity(self, stock_code: str) -> int:
        """매수 수량 계산 (현재는 매수금액 기반으로 단순 계산)"""
        try:
            # 현재가 정보가 없으므로 임시로 매수금액을 평균 주가로 나눠서 계산
            # 실제로는 현재가 API를 호출해서 정확한 가격을 가져와야 함
            estimated_price = 50000  # 임시 평균 주가 (5만원)
            quantity = self.settings.buy_amount // estimated_price
            return max(1, quantity)  # 최소 1주
            
        except Exception as e:
            self.debug_message.emit(f"❌ 수량 계산 오류 ({stock_code}): {e}")
            return 0
            
    def execute_buy_order(self, stock_code: str, quantity: int):
        """매수 주문 실행"""
        try:
            self.debug_message.emit(f"📤 매수 주문 실행: {stock_code} {quantity}주")
            
            # 매매 타입 결정
            trade_type = '3' if self.settings.is_market_order else '0'
            price = None if self.settings.is_market_order else self.calculate_limit_price(stock_code)
            
            # API 호출
            result = self.trading_api.buy_stock(
                stock_code=stock_code,
                quantity=quantity,
                price=price,
                trade_type=trade_type
            )
            
            # 결과 처리
            if result['success']:
                self.on_buy_success(stock_code, quantity, price or 0, result.get('order_no', ''))
            else:
                self.on_buy_failure(stock_code, result.get('error', '주문 실패'))
                
        except Exception as e:
            self.debug_message.emit(f"❌ 매수 주문 실행 오류 ({stock_code}): {e}")
            self.on_buy_failure(stock_code, str(e))
        finally:
            # 대기 목록에서 제거
            if stock_code in self.pending_orders:
                del self.pending_orders[stock_code]
                
    def calculate_limit_price(self, stock_code: str) -> int:
        """지정가 계산 (호가 기반)"""
        # 실제로는 현재가 + 호가단위 계산이 필요
        # 여기서는 임시로 시장가와 동일하게 처리
        return 0
        
    def on_buy_success(self, stock_code: str, quantity: int, price: int, order_no: str):
        """매수 성공 처리"""
        try:
            # 포지션 추가
            position = Position(
                stock_code=stock_code,
                stock_name=f"종목{stock_code}",  # 실제로는 종목명 조회 필요
                buy_price=price,
                quantity=quantity,
                buy_time=datetime.now(),
                order_no=order_no
            )
            
            self.positions[stock_code] = position
            
            self.debug_message.emit(f"✅ 매수 완료: {stock_code} {quantity}주 (주문번호: {order_no})")
            
            # 시그널 발송
            position_dict = {
                'stock_code': stock_code,
                'stock_name': position.stock_name,
                'quantity': quantity,
                'buy_price': price,
                'buy_time': position.buy_time.strftime('%H:%M:%S'),
                'order_no': order_no
            }
            self.position_added.emit(position_dict)
            
        except Exception as e:
            self.debug_message.emit(f"❌ 매수 성공 처리 오류: {e}")
            
    def on_buy_failure(self, stock_code: str, error: str):
        """매수 실패 처리"""
        try:
            self.debug_message.emit(f"❌ 매수 실패: {stock_code} - {error}")
            
            # 블랙리스트에 추가 (일정 시간 동안 재시도 방지)
            self.blacklist.add(stock_code)
            
            # 5분 후 블랙리스트에서 제거하는 타이머 설정
            def remove_from_blacklist():
                if stock_code in self.blacklist:
                    self.blacklist.remove(stock_code)
                    self.debug_message.emit(f"🔄 블랙리스트 해제: {stock_code}")
                    
            timer = threading.Timer(self.blacklist_duration, remove_from_blacklist)
            timer.daemon = True
            timer.start()
            
        except Exception as e:
            self.debug_message.emit(f"❌ 매수 실패 처리 오류: {e}")
            
    def cleanup_pending_orders(self):
        """타임아웃된 대기 주문 정리"""
        try:
            current_time = datetime.now()
            timeout_orders = []
            
            for stock_code, order_time in self.pending_orders.items():
                if (current_time - order_time).seconds > self.order_timeout:
                    timeout_orders.append(stock_code)
                    
            for stock_code in timeout_orders:
                del self.pending_orders[stock_code]
                self.debug_message.emit(f"⏰ 주문 타임아웃: {stock_code}")
                
        except Exception as e:
            self.debug_message.emit(f"❌ 대기 주문 정리 오류: {e}")
            
    def cleanup_blacklist(self):
        """오래된 블랙리스트 항목 정리 (이미 타이머로 처리하므로 여기서는 체크만)"""
        pass
        
    def get_positions(self) -> Dict[str, Position]:
        """현재 보유 포지션 반환"""
        return self.positions.copy()
        
    def get_status(self) -> Dict:
        """현재 상태 정보 반환"""
        return {
            'is_active': self.is_active,
            'total_positions': len(self.positions),
            'pending_orders': len(self.pending_orders),
            'blacklist_count': len(self.blacklist),
            'monitoring_stocks': len(self.current_stocks),
            'settings': self.settings.__dict__ if self.settings else None
        }
        
    def cleanup(self):
        """정리 작업"""
        try:
            self.stop_auto_trading()
            self.positions.clear()
            self.pending_orders.clear()
            self.blacklist.clear()
            self.current_stocks.clear()
            self.debug_message.emit("🧹 자동매매 서비스 정리 완료")
            
        except Exception as e:
            self.debug_message.emit(f"❌ 자동매매 서비스 정리 오류: {e}")