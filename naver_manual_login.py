# -*- coding: utf-8 -*-
# naver_manual_login.py
# 네이버 블로그 자동 작성: 제목 "1", 내용 "2" 작성 후 임시저장

import os
import sys
import time
import pyperclip

# 한글 출력을 위한 설정
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
    WebDriverException,
)
from webdriver_manager.chrome import ChromeDriverManager

# 환경변수에서 네이버 로그인 정보 가져오기
NAV_ID = os.getenv("NAVER_ID")
NAV_PW = os.getenv("NAVER_PW")
BLOG_WRITE_URL = "https://blog.naver.com/GoBlogWrite.naver"
MODEL_WAIT = 15

def init_driver() -> webdriver.Chrome:
    """ChromeDriver 초기화(브라우저 자동 종료 방지)"""
    opts = Options()
    
    # Render 환경 감지 및 헤드리스 설정
    if os.environ.get('RENDER') or os.environ.get('DISPLAY'):
        print("🐧 Render 환경에서 헤드리스 모드로 실행합니다...")
        opts.add_argument('--headless')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('--disable-gpu')
        opts.add_argument('--disable-extensions')
        opts.add_argument('--remote-debugging-port=9222')
        opts.add_argument('--disable-background-timer-throttling')
        opts.add_argument('--disable-backgrounding-occluded-windows')
        opts.add_argument('--disable-renderer-backgrounding')
        
        # Chrome 바이너리 경로 동적 찾기
        chrome_paths = [
            '/usr/bin/google-chrome-stable',
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/opt/google/chrome/chrome',
            '/snap/bin/chromium',
            '/usr/bin/chromium'
        ]
        
        chrome_binary = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_binary = path
                print(f"✅ Chrome 바이너리 발견: {path}")
                break
        
        if not chrome_binary:
            print("❌ Chrome 바이너리를 찾을 수 없습니다.")
            # 시스템에서 chrome 찾기 시도
            import subprocess
            commands_to_try = ['google-chrome', 'google-chrome-stable', 'chromium-browser', 'chromium']
            for cmd in commands_to_try:
                try:
                    result = subprocess.run(['which', cmd], capture_output=True, text=True)
                    if result.returncode == 0:
                        chrome_binary = result.stdout.strip()
                        print(f"✅ which 명령으로 {cmd} 발견: {chrome_binary}")
                        break
                except:
                    continue
        
        if chrome_binary:
            opts.binary_location = chrome_binary
        else:
            print("❌ 어떤 Chrome 바이너리도 찾을 수 없습니다.")
            print("🔄 ChromeDriverManager가 자동으로 처리하도록 시도합니다...")
    else:
        print("💻 로컬 환경에서 GUI 모드로 실행합니다...")
        opts.add_experimental_option("detach", True)
    
    # Chrome 콘솔 스팸 숨기기
    opts.add_experimental_option(
        "excludeSwitches", ["enable-logging", "enable-automation"]
    )
    opts.add_experimental_option("useAutomationExtension", False)
    
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=opts
        )
        driver.set_window_size(1600, 950)
        return driver
    except Exception as e:
        print(f"❌ Chrome 드라이버 초기화 실패: {str(e)}")
        raise

def naver_login(driver: webdriver.Chrome) -> WebDriverWait:
    """네이버 로그인 후 WebDriverWait 반환"""
    print("🌐 네이버 로그인 페이지로 이동합니다...")
    driver.get("https://nid.naver.com/nidlogin.login")
    time.sleep(0.5)   # 페이지 로딩 대기시간

    print("🔐 로그인 정보를 입력합니다...")
    
    # ID 입력
    driver.find_element(By.ID, "id").click()
    pyperclip.copy(NAV_ID)
    driver.find_element(By.ID, "id").send_keys(Keys.CONTROL, "v")
    time.sleep(0.1)

    # 비밀번호 입력
    driver.find_element(By.ID, "pw").click()
    pyperclip.copy(NAV_PW)
    driver.find_element(By.ID, "pw").send_keys(Keys.CONTROL, "v")
    pyperclip.copy("")  # 클립보드 비우기
    time.sleep(0.1)

    # 로그인 버튼 클릭
    driver.find_element(By.ID, "log.login").click()
    time.sleep(0.5)  # 로그인 완료 대기시간
    
    print("✅ 로그인 완료!")
    return WebDriverWait(driver, MODEL_WAIT)

def open_write_page(driver: webdriver.Chrome, wait: WebDriverWait):
    """블로그 글쓰기 페이지 접속 및 iframe 진입, 팝업/도움말 닫기"""
    print("📝 블로그 글쓰기 페이지로 이동합니다...")
    driver.get(BLOG_WRITE_URL)

    # 메인 프레임 전환
    print("🔄 메인 프레임으로 전환 중...")
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe#mainFrame")))

    # 이어쓰기 팝업 취소
    try:
        cancel_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-popup-button-cancel")))
        cancel_btn.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".se-popup-dim")))
        print("📋 이어쓰기 팝업을 닫았습니다.")
    except TimeoutException:
        print("📋 이어쓰기 팝업이 없습니다.")

    # 도움말 패널 닫기(존재할 때까지 반복)
    help_closed = 0
    while True:
        try:
            driver.find_element(By.CSS_SELECTOR, ".se-help-panel-close-button").click()
            help_closed += 1
            time.sleep(0.05)   # 루프 속도
        except WebDriverException:
            break
    
    if help_closed > 0:
        print(f"❓ 도움말 패널 {help_closed}개를 닫았습니다.")

def write_post(driver: webdriver.Chrome, wait: WebDriverWait, title: str, body: str):
    """제목과 본문 입력 후 저장"""
    print(f"✏️ 블로그 포스트를 작성합니다...")
    print(f"   제목: {title}")
    print(f"   내용: {body}")
    
    actions = ActionChains(driver)

    # 제목 입력
    print("📝 제목 입력 중...")
    title_area = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-section-documentTitle")))
    actions.move_to_element(title_area).click().perform()
    for ch in title:
        actions.send_keys(ch).pause(0.0001)
    actions.perform()
    actions.reset_actions()

    # 본문 입력
    print("📝 본문 입력 중...")
    body_area = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-section-text")))
    actions.move_to_element(body_area).click().perform()
    for line in body.splitlines():
        for ch in line:
            actions.send_keys(ch).pause(0.0001)
        actions.send_keys(Keys.ENTER).pause(0.0001)
    actions.perform()

    # 저장
    print("💾 임시저장 중...")
    save_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".save_btn__bzc5B")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", save_btn)
    time.sleep(0.05)    # 스크롤 안정화 시간
    try:
        save_btn.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", save_btn) 
    
    # '저장됨' 토스트 대기
    try:
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".toast_item__success, .se-toast-item__success")
            )
        )
        print("✅ 임시저장이 완료되었습니다!")
    except TimeoutException:
        print("⚠️ 저장 완료 메시지를 확인할 수 없지만 계속 진행합니다.")
    
    time.sleep(0.2) # 저장 대기시간

def main():
    """메인 실행 함수"""
    print("🚀 네이버 블로그 자동 작성 프로그램 시작!")
    print("📝 제목: '1', 내용: '2'를 자동으로 작성하고 임시저장합니다.")
    print("="*50)
    
    # 환경변수 확인
    if not NAV_ID or not NAV_PW:
        print("❌ 환경변수 NAVER_ID 또는 NAVER_PW가 설정되지 않았습니다.")
        return
    
    # 1. 브라우저 초기화
    driver = init_driver()
    
    try:
        # 2. 네이버 로그인
        wait = naver_login(driver)
        
        # 3. 블로그 글쓰기 페이지 열기
        open_write_page(driver, wait)
        
        # 4. 포스트 작성 (제목: "1", 내용: "2")
        write_post(driver, wait, "1", "2")
        
        print("🎉 블로그 포스트 작성이 완료되었습니다!")
        print("📄 제목: '1'")
        print("📄 내용: '2'")
        print("💾 임시저장 완료")
        
        # 5. 헤드리스 환경이 아닌 경우에만 브라우저 유지
        if not (os.environ.get('RENDER') or os.environ.get('DISPLAY')):
            print("💻 로컬 환경에서 브라우저를 유지합니다...")
            print("🔚 종료하려면 Ctrl+C를 누르거나 터미널을 닫아주세요.")
            try:
                while True:
                    time.sleep(10)
                    # 브라우저가 닫혔는지 체크
                    try:
                        driver.current_url
                    except:
                        print("🔚 브라우저가 닫혔습니다.")
                        break
            except KeyboardInterrupt:
                print("\n🔚 프로그램을 종료합니다.")
        else:
            print("🤖 헤드리스 환경에서 작업 완료. 브라우저를 종료합니다.")
            time.sleep(2)  # 결과 확인 시간
        
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {e}")
        raise e  # 서버 환경에서 오류 전파
    finally:
        try:
            if os.environ.get('RENDER') or os.environ.get('DISPLAY'):
                driver.quit()  # 헤드리스 환경에서는 명시적으로 종료
        except:
            pass

if __name__ == "__main__":
    main()