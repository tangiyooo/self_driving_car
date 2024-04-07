#-- coding: utf-8 --
from flask import request
import requests
import time
import wiringpi
import os


SERVER_URL = "http://172.17.60.65:5001/get_command"

#led = LED(4)  # LED가 GPIO 17에 연결되어 있다고 가정합니다.
#button = Button(5)  # 버튼이 GPIO 2에 연결되어 있다고 가정합니다.

#모터 상태
STOP  = 0
FORWARD  = 1
BACKWORD = 2
ERROR_MOTER=5
RIGHTSPEED=130
LEFTSPEED=RIGHTSPEED+ERROR_MOTER
TURN_RIGHTSPEED=130
TURN_LEFTSPEED=TURN_RIGHTSPEED+ERROR_MOTER

#모터 채널
CH1 = 0
CH2 = 1

#PIN 입출력 설정
OUTPUT = 1
INPUT = 0

#PIN 설정
HIGH = 1
LOW = 0

# wiringPi 핀 번호 설정 (실제 GPIO 핀 번호와 다를 수 있음)
shutdown_pin = 29 

#실제 핀 정의
#PWM PIN
ENA = 25
ENB = 30

#GPIO PIN
IN1 = 24
IN2 = 23
IN3 = 22
IN4 = 21

#핀 설정 함수
def setPinConfig(EN, INA, INB):
    wiringpi.pinMode(EN, OUTPUT)
    wiringpi.pinMode(INA, OUTPUT)
    wiringpi.pinMode(INB, OUTPUT)
    wiringpi.softPwmCreate(EN, 0, 255)

#모터 제어 함수
def setMotorContorl(PWM, INA, INB, speed, stat):
#모터 속도 제어 PWM
    wiringpi.softPwmWrite(PWM, speed)


    #앞으로
    if stat == FORWARD:
        wiringpi.digitalWrite(INA, HIGH)
        wiringpi.digitalWrite(INB, LOW)
    #뒤로
    elif stat == BACKWORD:
        wiringpi.digitalWrite(INA, LOW)
        wiringpi.digitalWrite(INB, HIGH)
    #정지
    elif stat == STOP:
        wiringpi.digitalWrite(INA, LOW)
        wiringpi.digitalWrite(INB, LOW)
#모터 제어함수 간단하게 사용하기 위해 한번더 래핑(감쌈)
def setMotor(ch, speed, stat):
    if ch == CH1:
        setMotorContorl(ENA, IN1, IN2, speed, stat)
    else:
        setMotorContorl(ENB, IN3, IN4, speed, stat)

def control_motor(command):
    if command == 'f':
        setMotor(CH1, 125, FORWARD)  # 두 바퀴 모두 앞으로
        setMotor(CH2, 125, FORWARD)
        wiringpi.delay(500)
        setMotor(CH1, 0, STOP)  # 두 바퀴 모두 정지
        setMotor(CH2, 0, STOP)
    elif command == 'b':
        setMotor(CH1, 125, BACKWORD)  # 두 바퀴 모두 뒤로
        setMotor(CH2, 125, BACKWORD)
        wiringpi.delay(500)
        setMotor(CH1, 0, STOP)  # 두 바퀴 모두 정지
        setMotor(CH2, 0, STOP)
    elif command == 'l':
        setMotor(CH1, 125, FORWARD)  # 왼쪽 바퀴는 앞으로, 오른쪽 바퀴는 뒤로 (좌회전)
        setMotor(CH2, 125, BACKWORD)
        wiringpi.delay(500)
        setMotor(CH1, 0, STOP)  # 두 바퀴 모두 정지
        setMotor(CH2, 0, STOP)
    elif command == 'r':
        setMotor(CH1, 125, BACKWORD)  # 왼쪽 바퀴는 뒤로, 오른쪽 바퀴는 앞으로 (우회전)
        setMotor(CH2, 125, FORWARD)
        wiringpi.delay(500)
        setMotor(CH1, 0, STOP)  # 두 바퀴 모두 정지
        setMotor(CH2, 0, STOP)
    elif command == 's':
        setMotor(CH1, 0, STOP)  # 두 바퀴 모두 정지
        setMotor(CH2, 0, STOP)
        wiringpi.delay(500)
    else:
        setMotor(CH1, 0, STOP)  # 두 바퀴 모두 정지
        setMotor(CH2, 0, STOP)
        wiringpi.delay(500)
        
def check_button():
    if wiringpi.digitalRead(shutdown_pin) == 0:  # 버튼이 눌렸는지 확인
        print("Button Pressed. Shutting down...")
        os.system('sudo shutdown now -h')  # 시스템 종료 명령 실행


#GPIO 라이브러리 설정
wiringpi.wiringPiSetup()  # wiringPi 초기화
wiringpi.pinMode(28, 1) # 28번 핀을 출력 모드로 설정 (1은 출력 모드를 의미)
wiringpi.pinMode(shutdown_pin, wiringpi.INPUT)  # 버튼 핀을 입력으로 설정
wiringpi.pullUpDnControl(shutdown_pin, wiringpi.PUD_UP)  # 내부 풀업 저항 활성화

#모터 핀 설정
setPinConfig(ENA, IN1, IN2)
setPinConfig(ENB, IN3, IN4)

while True:
    wiringpi.digitalWrite(28, 1) # 28번 핀에 HIGH 신호를 보내어 ON 상태로 만듦
    check_button()
    try:
        response = requests.get(SERVER_URL)
        if response.status_code == 200:
            command = response.json().get('command')
            if command:  # 서버로부터 명령어를 성공적으로 받았을 때
                control_motor(command)
    except Exception as e:
        time.sleep(1)  # 1초 대기 후 다시 시도
