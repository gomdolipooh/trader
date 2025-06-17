import requests

class LoginService:
    def __init__(self):
        self.account = {
            'appkey': 'wif2exvXBK01R5780Sb4xt9DMjhEMNe9Kyqy90DcQrE',
            'secretkey': '-cF5H0QqOgbhAdz8HV_oSVEuhlpdIF-dAEorebEFpt8'
        }
        
    def get_access_token(self):
        """Access Token 발급"""
        url = "https://api.kiwoom.com/oauth2/token"
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
        }
        body = {
            'grant_type': 'client_credentials',
            'appkey': self.account['appkey'],
            'secretkey': self.account['secretkey'],
        }

        response = requests.post(url, headers=headers, json=body)
        if response.status_code == 200:
            return response.json().get('token')
        else:
            print('토큰 발급 실패:', response.text)
            return None