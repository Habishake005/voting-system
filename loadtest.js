import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 50 },
    { duration: '2m',  target: 200 },
    { duration: '30s', target: 0 },
  ],
};

export default function () {
  const params = {
    headers: { 'Content-Type': 'application/json' },
  };
  
  // Hit auth service login repeatedly to spike CPU
  http.post('http://127.0.0.1:51306/api/auth/login',
    JSON.stringify({ username: 'testuser', password: 'wrongpassword' }),
    params
  );
  
  sleep(0.1);
}