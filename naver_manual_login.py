# -*- coding: utf-8 -*-
# naver_manual_login.py
# 네이버 창을 열고 사용자가 수동으로 로그인할 때까지 대기
# 로그인 후 블로그 화면까지 자동으로 이동

import os
import sys
import time

# 한글 출력을 위한 설정
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

BLOG_WRITE_URL = "https://blog.naver.com/GoBlogWrite.naver"
NAVER_LOGIN_URL = "https://nid.naver.com/nidlogin.login"
MODEL_WAIT = 15

def init_driver() -> webdriver.Chrome:
    """ChromeDriver 초기화 (브라우저 자동 종료 방지)"""
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
            '/opt/google/chrome/chrome'
        ]
        
        chrome_binary = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_binary = path
                print(f"✅ Chrome 바이너리 발견: {path}")
                break
        
        if chrome_binary:
            opts.binary_location = chrome_binary
        else:
            print("❌ Chrome 바이너리를 찾을 수 없습니다.")
            # 시스템에서 chrome 찾기 시도
            import subprocess
            try:
                result = subprocess.run(['which', 'google-chrome'], capture_output=True, text=True)
                if result.returncode == 0:
                    chrome_binary = result.stdout.strip()
                    opts.binary_location = chrome_binary
                    print(f"✅ which 명령으로 Chrome 발견: {chrome_binary}")
            except:
                pass
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

def wait_for_login(driver: webdriver.Chrome) -> bool:
    """사용자가 수동으로 로그인할 때까지 대기 (헤드리스 환경에서는 자동 로그인)"""
    print("🌐 네이버 로그인 페이지를 엽니다...")
    driver.get(NAVER_LOGIN_URL)
    
    # Render 환경에서 자동 로그인 시도
    if os.environ.get('RENDER') or os.environ.get('DISPLAY'):
        return auto_login(driver)
    
    # 로컬 환경에서는 수동 로그인
    return manual_login(driver)

def auto_login(driver: webdriver.Chrome) -> bool:
    """헤드리스 환경에서 자동 로그인"""
    naver_id = os.environ.get('NAVER_ID')
    naver_pw = os.environ.get('NAVER_PW')
    
    if not naver_id or not naver_pw:
        print("❌ 환경변수에 NAVER_ID 또는 NAVER_PW가 설정되지 않았습니다.")
        return False
    
    try:
        print("🤖 헤드리스 환경에서 자동 로그인을 시도합니다...")
        
        # ID 입력
        id_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "id"))
        )
        id_input.send_keys(naver_id)
        
        # 비밀번호 입력
        pw_input = driver.find_element(By.ID, "pw")
        pw_input.send_keys(naver_pw)
        
        # 로그인 버튼 클릭
        login_btn = driver.find_element(By.ID, "log.login")
        login_btn.click()
        
        # 로그인 완료 대기
        time.sleep(5)
        
        # 로그인 성공 확인
        if "nidlogin.login" not in driver.current_url:
            print("✅ 자동 로그인에 성공했습니다.")
            return True
        else:
            print("❌ 자동 로그인에 실패했습니다.")
            return False
            
    except Exception as e:
        print(f"❌ 자동 로그인 중 오류 발생: {str(e)}")
        return False

def manual_login(driver: webdriver.Chrome) -> bool:
    """로컬 환경에서 수동 로그인 대기"""
    # 자동 로그인 체크박스 해제
    try:
        time.sleep(2)  # 페이지 로딩 대기
        auto_login_checkbox = driver.find_element(By.ID, "keep")
        if auto_login_checkbox.is_selected():
            auto_login_checkbox.click()
            print("✅ 자동 로그인 체크박스를 해제했습니다.")
        else:
            print("📋 자동 로그인이 이미 해제되어 있습니다.")
    except Exception:
        print("📋 자동 로그인 체크박스를 찾을 수 없습니다.")
    
    print("👤 수동으로 로그인해 주세요...")
    print("⏳ 로그인 완료를 감지할 때까지 대기 중...")
    
    # 로그인 완료 감지 (최대 300초 = 5분 대기)
    max_wait_time = 300
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            # 로그인 완료 후 나타나는 요소들 체크
            # 1. 네이버 메인 페이지의 특정 요소
            # 2. 또는 현재 URL이 로그인 페이지가 아님
            current_url = driver.current_url
            
            if "nid.naver.com" not in current_url:
                print("✅ 로그인이 완료된 것 같습니다!")
                return True
            
            # 네이버 메인 페이지나 다른 페이지로 이동했는지 체크
            if "naver.com" in current_url and "nidlogin" not in current_url:
                print("✅ 네이버 페이지로 리다이렉트되었습니다!")
                return True
                
        except Exception as e:
            pass
            
        time.sleep(2)  # 2초마다 체크
        
        # 사용자에게 진행 상황 알림 (30초마다)
        elapsed = int(time.time() - start_time)
        if elapsed > 0 and elapsed % 30 == 0:
            remaining = max_wait_time - elapsed
            print(f"⏰ 대기 중... (남은 시간: {remaining}초)")
    
    print("❌ 로그인 대기 시간이 초과되었습니다.")
    return False

def navigate_to_blog(driver: webdriver.Chrome) -> bool:
    """블로그 글쓰기 페이지로 이동"""
    print("📝 블로그 글쓰기 페이지로 이동합니다...")
    
    try:
        driver.get(BLOG_WRITE_URL)
        wait = WebDriverWait(driver, MODEL_WAIT)
        
        # 임시저장 글 삭제 알림 처리
        try:
            time.sleep(2)  # 페이지 로딩 대기
            alert = driver.switch_to.alert
            print("📋 임시저장 글 삭제 알림을 확인했습니다.")
            alert.accept()  # 확인 버튼 클릭
            print("✅ 임시저장 글 삭제 알림을 처리했습니다.")
        except Exception:
            print("📋 임시저장 글 삭제 알림이 없습니다.")
        
        # 메인 프레임 전환 대기
        print("🔄 블로그 에디터 로딩 중...")
        wait.until(EC.frame_to_be_available_and_switch_to_it(
            (By.CSS_SELECTOR, "iframe#mainFrame")
        ))
        
        # 이어쓰기 팝업 처리
        try:
            cancel_btn = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".se-popup-button-cancel")
            ))
            cancel_btn.click()
            print("📋 이어쓰기 팝업을 닫았습니다.")
            wait.until(EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, ".se-popup-dim")
            ))
        except TimeoutException:
            print("📋 이어쓰기 팝업이 없습니다.")
        
        # 도움말 패널 닫기
        help_panel_closed = 0
        while True:
            try:
                help_close_btn = driver.find_element(
                    By.CSS_SELECTOR, ".se-help-panel-close-button"
                )
                help_close_btn.click()
                help_panel_closed += 1
                time.sleep(0.1)
            except WebDriverException:
                break
        
        if help_panel_closed > 0:
            print(f"❓ 도움말 패널 {help_panel_closed}개를 닫았습니다.")
        
        # 블로그 에디터가 정상적으로 로드되었는지 확인
        title_area = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".se-section-documentTitle")
        ))
        
        print("✅ 블로그 글쓰기 페이지 준비 완료!")
        print("📝 제목과 본문을 입력할 수 있습니다.")
        return True
        
    except Exception as e:
        print(f"❌ 블로그 페이지 이동 중 오류: {e}")
        return False

def keep_browser_alive(driver: webdriver.Chrome):
    """브라우저를 열어둔 상태로 유지"""
    print("\n🎉 모든 설정이 완료되었습니다!")
    print("💡 브라우저가 열린 상태로 유지됩니다.")
    print("📝 블로그 글쓰기를 자유롭게 사용하세요.")
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
    finally:
        try:
            driver.quit()
        except:
            pass

def main():
    """메인 실행 함수"""
    print("🚀 네이버 블로그 자동 로그인 프로그램 시작!")
    print("="*50)
    
    # 1. 브라우저 초기화
    driver = init_driver()
    
    try:
        # 2. 사용자 수동 로그인 대기
        if not wait_for_login(driver):
            print("❌ 로그인에 실패했습니다. 프로그램을 종료합니다.")
            return
        
        # 3. 블로그 페이지로 이동
        if not navigate_to_blog(driver):
            print("❌ 블로그 페이지 이동에 실패했습니다.")
            return
        
        # 4. 브라우저 유지
        keep_browser_alive(driver)
        
    except Exception as e:
        print(f"❌ 예상치 못한 오류가 발생했습니다: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()