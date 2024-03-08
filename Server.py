#             Project
# Name - Nisarg Jaswal
# Student i - 116088220
import mysql.connector
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import jwt
from cryptography.fernet import Fernet

class RequestHandler(BaseHTTPRequestHandler):
    secret_key = 'ee8c52a0187b3a35a2d8d8c7bc99c3bf6a7d5ee765a478f888d8e47b6a708340'
    fernet_key = Fernet.generate_key()
    cipher = Fernet(fernet_key)

    def _set_response(self, status_code=200, content_type='text/html'):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/protected':
            token = self.headers.get('Authorization')
            if token:
                try:
                    decrypted_token = self.cipher.decrypt(token.encode('utf-8')).decode('utf-8')
                    decoded_token = jwt.decode(decrypted_token, self.secret_key)
                    self._set_response()
                    self.wfile.write(json.dumps({'message': f'Welcome, {decoded_token["user"]}!'}).encode('utf-8'))
                except jwt.ExpiredSignatureError:
                    self._set_response(401)
                    self.wfile.write(json.dumps({'message': 'Token has expired'}).encode('utf-8'))
                except jwt.InvalidTokenError:
                    self._set_response(401)
                    self.wfile.write(json.dumps({'message': 'Invalid token'}).encode('utf-8'))
            else:
                self._set_response(401)
                self.wfile.write(json.dumps({'message': 'Token is missing!'}).encode('utf-8'))
        elif parsed_path.path == '/login':
            self._set_response()
            self.wfile.write(b'''
                <html>
                <body>
                <form method="post" action="/login">
                    Username: <input type="text" name="username"><br>
                    Password: <input type="password" name="password"><br>
                    <input type="submit" value="Login">
                </form>
    
                </body>
                </html>
            ''')
        else:
            self._set_response(200)
            self.wfile.write(b'Visit /login to access the login page.')

    def do_POST(self):
        if self.path == '/login':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = parse_qs(post_data.decode('utf-8'))

            if 'username' in params and 'password' in params:
                try:
                    db_connection = mysql.connector.connect(
                        host="localhost",
                        user="root",
                        password="nj@mysql1",
                        database="database1"
                    )
                    cursor = db_connection.cursor()
                    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (params['username'][0], params['password'][0]))
                    user = cursor.fetchone()
                    cursor.close()
                    db_connection.close()
                    if user:
                        token = jwt.encode({'user': params['username'][0]}, self.secret_key)
                        encrypted_token = self.cipher.encrypt(token).decode('utf-8')
                        self._set_response()
                        self.wfile.write(json.dumps({'user': params['username'][0]}).encode('utf-8'))
                    else:
                        self._set_response(401)
                        self.wfile.write(json.dumps({'message': 'Could not verify!'}).encode('utf-8'))
                except mysql.connector.Error as err:
                    print("MySQL Error:", err)
                    self._set_response(500)
                    self.wfile.write(json.dumps({'message': 'Internal Server Error'}).encode('utf-8'))
            else:
                self._set_response(400)
                self.wfile.write(json.dumps({'message': 'Bad request!'}).encode('utf-8'))
        else:
            self._set_response(404)
            self.wfile.write(json.dumps({'message': 'Not found'}).encode('utf-8'))

def run_server():
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, RequestHandler)
    print('Server running on port 8000...')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
