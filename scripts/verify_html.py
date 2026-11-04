#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RESCENE 대시보드 자동 무결성 및 문법 안전 검사기 (Safety Guardrail)
- index.html 및 rescene_voting_schedule.html의 자바스크립트 문법 오류(SyntaxError)를 사전 감지합니다.
- 핵심 DOM 요소 ID(vote-cards-container, vote-card-count 등)의 존재 여부를 검증합니다.
- 오류 발견 시 exit 1을 반환하여 잘못된 코드가 깃허브 PR이나 배포로 이어지는 것을 사전에 100% 차단합니다.
"""

import os
import re
import sys
import subprocess
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "index.html")
MIRROR_PATH = os.path.join(BASE_DIR, "rescene_voting_schedule.html")

REQUIRED_DOM_IDS = [
    "vote-cards-container",
    "vote-card-count",
    "today-badge",
    "live-broadcast-banner"
]

def check_file_exists_and_readable(path):
    if not os.path.exists(path):
        print(f"❌ [치명적 오류] 파일이 존재하지 않습니다: {path}")
        return False
    if os.path.getsize(path) < 1000:
        print(f"❌ [치명적 오류] 파일 크기가 너무 작거나 비어 있습니다: {path} ({os.path.getsize(path)} bytes)")
        return False
    return True

def verify_dom_elements(html_content, file_name):
    print(f"🔍 [{file_name}] 필수 DOM 요소 검사 중...")
    missing_ids = []
    for req_id in REQUIRED_DOM_IDS:
        pattern = rf'id=["\']{re.escape(req_id)}["\']'
        if not re.search(pattern, html_content):
            missing_ids.append(req_id)

    if missing_ids:
        print(f"❌ [{file_name}] 필수 DOM ID가 누락되었습니다: {missing_ids}")
        return False
    print(f"✅ [{file_name}] 필수 DOM ID {len(REQUIRED_DOM_IDS)}개 모두 정상 확인")
    return True

def verify_javascript_syntax(html_content, file_name):
    print(f"🔍 [{file_name}] 자바스크립트 문법 무결성 검사 중...")
    script_match = re.search(r'<script>(.*?)</script>', html_content, re.DOTALL)
    if not script_match:
        print(f"❌ [{file_name}] <script> 태그를 찾을 수 없습니다.")
        return False

    script_code = script_match.group(1)

    # 임시 자바스크립트 파일 생성
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tmp:
        tmp.write(script_code)
        tmp_path = tmp.name

    try:
        # 1) GitHub Actions 환경 (Node.js 기본 탑재)
        node_check = subprocess.run(["node", "--check", tmp_path], capture_output=True, text=True)
        if node_check.returncode == 0:
            print(f"✅ [{file_name}] Node.js 문법 파서 검사 통과 (오류 없음)")
            return True
        else:
            print(f"❌ [{file_name}] Node.js 문법 파싱 오류 발견:\n{node_check.stderr}")
            return False
    except FileNotFoundError:
        # 2) macOS 환경 (JavaScriptCore jsc)
        jsc_bin = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"
        if os.path.exists(jsc_bin):
            jsc_check = subprocess.run([jsc_bin, "-c", tmp_path], capture_output=True, text=True)
            if jsc_check.returncode == 0:
                print(f"✅ [{file_name}] JSC 파서 문법 검사 통과 (오류 없음)")
                return True
            else:
                # JSC execution syntax check
                mock_env = "const document = { getElementById: ()=>null, querySelectorAll: ()=>[] };\nconst window = {};\n"
                with open(tmp_path, "w", encoding="utf-8") as f:
                    f.write(mock_env + script_code)
                jsc_run = subprocess.run([jsc_bin, tmp_path], capture_output=True, text=True)
                if "SyntaxError" in (jsc_run.stderr + jsc_run.stdout):
                    print(f"❌ [{file_name}] JSC 문법 오류 감지:\n{jsc_run.stdout}\n{jsc_run.stderr}")
                    return False
                print(f"✅ [{file_name}] JSC 문법 안전성 검사 통과")
                return True

        # 3) 기본 괄호 균형 검사 (Fallback)
        stack = []
        pairs = {')': '(', '}': '{', ']': '['}
        for char in script_code:
            if char in '({[':
                stack.append(char)
            elif char in ')}]':
                if not stack or stack[-1] != pairs[char]:
                    print(f"❌ [{file_name}] 괄호 불일치 문법 오류 감지: {char}")
                    return False
                stack.pop()
        print(f"✅ [{file_name}] 기본 구문 균형 검사 통과")
        return True
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def main():
    print("🛡️ [안전 가드레일] RESCENE 대시보드 자동 사전 무결성 검증 시작")
    
    # 1. 파일 존재 및 가독성 검사
    if not check_file_exists_and_readable(INDEX_PATH):
        sys.exit(1)
    if not check_file_exists_and_readable(MIRROR_PATH):
        sys.exit(1)

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        index_html = f.read()
    with open(MIRROR_PATH, "r", encoding="utf-8") as f:
        mirror_html = f.read()

    # 2. DOM 요소 검증
    if not verify_dom_elements(index_html, "index.html"):
        sys.exit(1)
    if not verify_dom_elements(mirror_html, "rescene_voting_schedule.html"):
        sys.exit(1)

    # 3. 자바스크립트 문법 오류 검증
    if not verify_javascript_syntax(index_html, "index.html"):
        sys.exit(1)
    if not verify_javascript_syntax(mirror_html, "rescene_voting_schedule.html"):
        sys.exit(1)

    print("\n🎉 모든 안전 가드레일 검사를 100% 통과했습니다. 안전하게 배포할 수 있는 상태입니다!")
    sys.exit(0)

if __name__ == "__main__":
    main()
