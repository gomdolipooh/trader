import asyncio
import websockets
import json
import uuid
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import traceback

SOCKET_URL = 'wss://api.kiwoom.com:10000/api/dostk/websocket'

class ConditionService(QObject):
    # 시그널 정의
    condition_list_received = pyqtSignal(list)  # 조건식 목록 수신
    connection_status_changed = pyqtSignal(bool)  # 연결 상태 변경
    stock_data_received = pyqtSignal(str, list)  # 종목 데이터 수신 (조건식 idx, 종목 리스트)
    real_data_received = pyqtSignal(str, str, dict)  # 실시간 데이터 (조건식 idx, 종목코드, 데이터)
    debug_message = pyqtSignal(str)  # 디버그 메시지
    
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.websocket = None
        self.connected = False
        self.keep_running = True
        self.condition_responses = {}
        self.worker_thread = None
        
    def start_connection(self):
        """WebSocket 연결 시작"""
        self.debug_message.emit(f"🔄 조건검색 서비스 시작 - 토큰: {self.token[:20]}..." if self.token else "❌ 토큰이 없습니다")
        
        if not self.token:
            self.debug_message.emit("❌ 토큰이 없어서 조건검색 서비스를 시작할 수 없습니다")
            self.connection_status_changed.emit(False)
            return
            
        if self.worker_thread and self.worker_thread.isRunning():
            self.debug_message.emit("⚠️ 이미 조건검색 서비스가 실행 중입니다")
            return
            
        self.worker_thread = ConditionWorkerThread(self.token)
        
        # 시그널 연결
        self.worker_thread.condition_list_received.connect(self.condition_list_received.emit)
        self.worker_thread.connection_status_changed.connect(self.connection_status_changed.emit)
        self.worker_thread.stock_data_received.connect(self.stock_data_received.emit)
        self.worker_thread.real_data_received.connect(self.real_data_received.emit)
        self.worker_thread.debug_message.connect(self.debug_message.emit)
        
        self.worker_thread.start()
        self.debug_message.emit("🚀 조건검색 워커 스레드 시작됨")
        
    def stop_connection(self):
        """WebSocket 연결 중지"""
        self.debug_message.emit("🛑 조건검색 서비스 중지 요청")
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.wait(5000)  # 5초 대기
            if self.worker_thread.isRunning():
                self.debug_message.emit("⚠️ 워커 스레드가 정상적으로 종료되지 않았습니다")
            else:
                self.debug_message.emit("✅ 워커 스레드 정상 종료됨")
            
    def request_condition_search(self, cnsl_idx, search_type):
        """조건검색 요청"""
        if self.worker_thread:
            self.debug_message.emit(f"📝 조건검색 요청: {cnsl_idx} (타입: {search_type})")
            self.worker_thread.request_condition_search(cnsl_idx, search_type)
        else:
            self.debug_message.emit("❌ 워커 스레드가 없어서 조건검색 요청 실패")
            
    def cancel_real_condition(self, cnsl_idx):
        """실시간 조건검색 해제"""
        if self.worker_thread:
            self.debug_message.emit(f"🚫 실시간 조건검색 해제: {cnsl_idx}")
            self.worker_thread.cancel_real_condition(cnsl_idx)

class ConditionWorkerThread(QThread):
    # 워커 스레드용 시그널
    condition_list_received = pyqtSignal(list)
    connection_status_changed = pyqtSignal(bool)
    stock_data_received = pyqtSignal(str, list)
    real_data_received = pyqtSignal(str, str, dict)
    debug_message = pyqtSignal(str)
    
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.websocket = None
        self.connected = False
        self.keep_running = True
        self.condition_responses = {}
        self.loop = None
        
    def run(self):
        """스레드 실행"""
        try:
            self.debug_message.emit("🔧 새로운 이벤트 루프 생성 중...")
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.debug_message.emit("✅ 이벤트 루프 생성 완료")
            
            self.debug_message.emit("🌐 WebSocket 핸들러 시작...")
            self.loop.run_until_complete(self.websocket_handler())
            
        except Exception as e:
            self.debug_message.emit(f"❌ 워커 스레드 실행 중 오류: {e}")
            self.debug_message.emit(f"📋 스택 트레이스: {traceback.format_exc()}")
        finally:
            self.debug_message.emit("🏁 워커 스레드 종료")
        
    def stop(self):
        """스레드 중지"""
        self.debug_message.emit("🛑 워커 스레드 중지 요청 받음")
        self.keep_running = False
        if self.loop:
            try:
                asyncio.run_coroutine_threadsafe(self.disconnect(), self.loop)
            except Exception as e:
                self.debug_message.emit(f"⚠️ 연결 해제 중 오류: {e}")
            
    async def websocket_handler(self):
        """WebSocket 핸들러"""
        try:
            self.debug_message.emit("🔗 WebSocket 연결 시도 중...")
            await self.connect()
            
            if self.connected:
                self.debug_message.emit("📨 메시지 수신 루프 시작...")
                await self.receive_messages()
            else:
                self.debug_message.emit("❌ 연결 실패로 메시지 수신 루프 시작 안됨")
                
        except Exception as e:
            self.debug_message.emit(f"❌ WebSocket 핸들러 오류: {e}")
            self.debug_message.emit(f"📋 상세 오류: {traceback.format_exc()}")
            
    async def connect(self):
        """WebSocket 연결"""
        try:
            self.debug_message.emit(f"🌐 WebSocket 연결 시도: {SOCKET_URL}")
            
            # 연결 타임아웃 설정 (10초)
            self.websocket = await asyncio.wait_for(
                websockets.connect(SOCKET_URL), 
                timeout=10.0
            )
            
            self.connected = True
            self.connection_status_changed.emit(True)
            self.debug_message.emit("✅ WebSocket 연결 성공!")
            
            # 로그인 패킷 전송
            login_param = {
                'trnm': 'LOGIN',
                'token': self.token
            }
            self.debug_message.emit("🔐 로그인 패킷 전송 중...")
            await self.send_message(login_param)
            
        except asyncio.TimeoutError:
            self.debug_message.emit("❌ WebSocket 연결 타임아웃 (10초)")
            self.connected = False
            self.connection_status_changed.emit(False)
        except websockets.exceptions.InvalidURI:
            self.debug_message.emit(f"❌ 잘못된 WebSocket URI: {SOCKET_URL}")
            self.connected = False
            self.connection_status_changed.emit(False)
        except Exception as e:
            self.debug_message.emit(f"❌ WebSocket 연결 오류: {e}")
            self.debug_message.emit(f"📋 연결 오류 상세: {traceback.format_exc()}")
            self.connected = False
            self.connection_status_changed.emit(False)
            
    async def send_message(self, message):
        """메시지 전송"""
        if not self.connected or not self.websocket:
            self.debug_message.emit("⚠️ 연결이 끊어져 있어 메시지 전송 불가")
            return
            
        try:
            if not isinstance(message, str):
                message_str = json.dumps(message)
            else:
                message_str = message
            
            await self.websocket.send(message_str)
            self.debug_message.emit(f"📤 메시지 전송: {message_str}")
            
        except Exception as e:
            self.debug_message.emit(f"❌ 메시지 전송 실패: {e}")
            self.connected = False
            self.connection_status_changed.emit(False)
            
    async def receive_messages(self):
        """메시지 수신"""
        while self.keep_running:
            try:
                if not self.websocket:
                    self.debug_message.emit("❌ WebSocket이 없어서 수신 루프 종료")
                    break
                    
                # 메시지 수신 (타임아웃 설정)
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)
                    response = json.loads(message)
                except asyncio.TimeoutError:
                    self.debug_message.emit("⏰ 메시지 수신 타임아웃 (30초) - 연결 확인 중...")
                    # PING 메시지 보내서 연결 확인
                    await self.send_message({"trnm": "PING"})
                    continue
                    
                trnm = response.get('trnm')
                
                if trnm == 'LOGIN':
                    await self.handle_login_response(response)
                elif trnm == 'PING':
                    # PING 응답 (에코백)
                    await self.send_message(response)
                elif trnm == 'CNSRLST':
                    await self.handle_condition_list_response(response)
                elif trnm == 'CNSRREQ':
                    await self.handle_condition_search_response(response)
                elif trnm == 'REAL':
                    await self.handle_real_data_response(response)
                    
                # PING이 아닌 메시지만 로그 출력
                if trnm != 'PING':
                    self.debug_message.emit(f"📥 메시지 수신: {trnm} - {response.get('return_code', 'N/A')}")
                    
            except websockets.ConnectionClosed:
                self.debug_message.emit("🔌 WebSocket 연결이 서버에 의해 닫혔습니다")
                self.connected = False
                self.connection_status_changed.emit(False)
                break
            except json.JSONDecodeError as e:
                self.debug_message.emit(f"❌ JSON 파싱 오류: {e}")
            except Exception as e:
                self.debug_message.emit(f"❌ 메시지 수신 오류: {e}")
                break
                
    async def handle_login_response(self, response):
        """로그인 응답 처리"""
        return_code = response.get('return_code')
        return_msg = response.get('return_msg', '')
        
        if return_code != 0:
            self.debug_message.emit(f"❌ 로그인 실패: 코드={return_code}, 메시지={return_msg}")
            await self.disconnect()
        else:
            self.debug_message.emit("✅ 로그인 성공!")
            self.debug_message.emit("📋 조건검색 목록 요청 중...")
            
            # 조건검색식 목록 요청
            await asyncio.sleep(0.5)
            cnsrlst_param = {'trnm': 'CNSRLST'}
            await self.send_message(cnsrlst_param)
            
    async def handle_condition_list_response(self, response):
        """조건검색 목록 응답 처리"""
        data = response.get("data", [])
        self.debug_message.emit(f"📋 조건검색 목록 수신: {len(data)}개")
        
        condition_list = [
            {"cnsl_idx": item[0], "cnsl_nm": item[1]} 
            for item in data
        ]
        
        for condition in condition_list:
            self.debug_message.emit(f"  - {condition['cnsl_idx']}: {condition['cnsl_nm']}")
            
        self.condition_list_received.emit(condition_list)
        
    async def handle_condition_search_response(self, response):
        """조건검색 응답 처리"""
        seq = str(response.get("seq", "")).strip()
        original_seq = response.get("seq")
        
        # seq 매칭
        matched_seq = None
        if seq in self.condition_responses:
            matched_seq = seq
        elif original_seq in self.condition_responses:
            matched_seq = original_seq
        else:
            for key in self.condition_responses.keys():
                if str(key).strip() == seq or str(key) == str(original_seq):
                    matched_seq = key
                    break
                    
        if matched_seq:
            self.debug_message.emit(f"✅ 조건검색 응답 매칭: '{original_seq}' -> '{matched_seq}'")
            await self.condition_responses[matched_seq].put(response)
        else:
            self.debug_message.emit(f"⚠️ 매칭되지 않은 seq: '{original_seq}', 대기 중인 키들: {list(self.condition_responses.keys())}")
            
    async def handle_real_data_response(self, response):
        """실시간 데이터 응답 처리"""
        try:
            data_list = response.get("data", [])
            self.debug_message.emit(f"📊 실시간 데이터 수신: {len(data_list)}개")
            
            for data in data_list:
                name = data.get("name", "")  # 종목코드
                values = data.get("values", {})
                
                # 조건식 idx 찾기 (실제로는 더 복잡한 로직 필요)
                self.real_data_received.emit("", name, values)
                
        except Exception as e:
            self.debug_message.emit(f"❌ 실시간 데이터 처리 오류: {e}")
            
    def request_condition_search(self, cnsl_idx, search_type):
        """조건검색 요청 (메인 스레드에서 호출)"""
        if self.loop:
            self.debug_message.emit(f"📝 조건검색 요청 시작: {cnsl_idx} (타입: {search_type})")
            asyncio.run_coroutine_threadsafe(
                self._send_condition_request(cnsl_idx, search_type), 
                self.loop
            )
        else:
            self.debug_message.emit("❌ 이벤트 루프가 없어서 조건검색 요청 실패")
            
    async def _send_condition_request(self, cnsl_idx, search_type):
        """조건검색 요청 실제 처리"""
        req_id = str(uuid.uuid4())[:8]
        
        try:
            self.debug_message.emit(f"[{req_id}] 🔧 조건검색 요청 파라미터 구성 중...")
            
            # 응답 큐 준비
            self.condition_responses[cnsl_idx] = asyncio.Queue()
            self.debug_message.emit(f"[{req_id}] 📦 응답 큐 등록: {cnsl_idx}")
            
            # 요청 파라미터 구성
            req_param = {
                'trnm': 'CNSRREQ',
                'seq': cnsl_idx,
                'search_type': search_type,
                'stex_tp': 'K'
            }
            
            # 일반 조건검색인 경우에만 연속조회 파라미터 추가
            if search_type == '0':
                req_param.update({
                    'cont_yn': 'N',
                    'next_key': ''
                })
                self.debug_message.emit(f"[{req_id}] 📋 일반 조건검색 파라미터 추가")
            else:
                self.debug_message.emit(f"[{req_id}] 📋 실시간 조건검색 파라미터 설정")
                
            await self.send_message(req_param)
            self.debug_message.emit(f"[{req_id}] ✅ 조건검색 요청 전송 완료")
            
            # 응답 대기
            try:
                self.debug_message.emit(f"[{req_id}] ⏳ 조건검색 응답 대기 중... (15초 타임아웃)")
                response = await asyncio.wait_for(
                    self.condition_responses[cnsl_idx].get(), 
                    timeout=15.0
                )
                
                stock_list = response.get("data", [])
                self.debug_message.emit(f"[{req_id}] 📊 조건검색 결과 수신: {len(stock_list)}개 종목")
                
                # 100개 초과 체크
                if len(stock_list) > 100:
                    self.debug_message.emit(f"[{req_id}] ⚠️ 종목 수가 100개를 초과합니다: {len(stock_list)}개")
                    
                self.stock_data_received.emit(cnsl_idx, stock_list)
                
            except asyncio.TimeoutError:
                self.debug_message.emit(f"[{req_id}] ❌ 조건검색 응답 타임아웃 (15초)")
                self.stock_data_received.emit(cnsl_idx, [])
                
        except Exception as e:
            self.debug_message.emit(f"[{req_id}] ❌ 조건검색 요청 처리 오류: {e}")
            self.debug_message.emit(f"[{req_id}] 📋 오류 상세: {traceback.format_exc()}")
            self.stock_data_received.emit(cnsl_idx, [])
        finally:
            # 응답 큐 정리
            if cnsl_idx in self.condition_responses:
                del self.condition_responses[cnsl_idx]
                self.debug_message.emit(f"[{req_id}] 🗑️ 응답 큐 정리: {cnsl_idx}")
            
    def cancel_real_condition(self, cnsl_idx):
        """실시간 조건검색 해제 (메인 스레드에서 호출)"""
        if self.loop:
            self.debug_message.emit(f"🚫 실시간 조건검색 해제 요청: {cnsl_idx}")
            asyncio.run_coroutine_threadsafe(
                self._send_real_cancel(cnsl_idx), 
                self.loop
            )
        else:
            self.debug_message.emit("❌ 이벤트 루프가 없어서 실시간 해제 실패")
            
    async def _send_real_cancel(self, cnsl_idx):
        """실시간 해제 요청"""
        try:
            cancel_param = {
                "trnm": "CNSRCLR",
                "seq": cnsl_idx
            }
            await self.send_message(cancel_param)
            self.debug_message.emit(f"✅ 실시간 해제 요청 전송 완료: {cnsl_idx}")
            
        except Exception as e:
            self.debug_message.emit(f"❌ 실시간 해제 요청 실패: {e}")
            
    async def disconnect(self):
        """연결 해제"""
        self.debug_message.emit("🔌 WebSocket 연결 해제 시작...")
        self.keep_running = False
        
        if self.connected and self.websocket:
            try:
                await self.websocket.close()
                self.connected = False
                self.connection_status_changed.emit(False)
                self.debug_message.emit("✅ WebSocket 연결 해제 완료")
            except Exception as e:
                self.debug_message.emit(f"⚠️ 연결 해제 중 오류: {e}")
        else:
            self.debug_message.emit("ℹ️ 이미 연결이 해제되어 있음")