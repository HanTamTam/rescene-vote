#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RESCENE 대시보드 일일 운영 점검 및 자동 감사 스크립트 (Daily Audit)
- 사용자가 "오늘 워크플로 확인해서 고쳐줘" / "오늘 머지된 거 점검해줘"라고 요청했을 때 실행하는 1차 진단 도구
- 1. git pull 로 원격(모바일에서 머지된 변경점) 동기화
- 2. 오늘 날짜로 머지된 커밋 및 PR 변경 이력 조회
- 3. test_dashboard.py 실행을 통한 4대 핵심 검증 (DOM, JS문법, 데이터 스키마/중복, 39개 링크 상태)
- 4. 발견된 이상 항목 요약 리포트 출력
"""

import os
import sys
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_RUNNER = os.path.join(BASE_DIR, "scripts", "test_dashboard.py")

def run_cmd(cmd, cwd=BASE_DIR):
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def main():
    print("=" * 60)
    print("🔍 [RESCENE 대시보드 일일 자동 감사 & 상태 진단]")
    print(f"⏰ 실행 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S KST')}")
    print("=" * 60)

    # 1. 원격 변경사항 pull
    print("\n1️⃣ [Git 최신 상태 동기화]")
    code, out, err = run_cmd("git pull origin main")
    if code == 0:
        print(f"   📥 Git Pull 완료: {out}")
    else:
        print(f"   ⚠️ Git Pull 경고/오류: {err or out}")

    # 2. 최근 커밋 및 머지 이력 확인 (오늘 기준)
    print("\n2️⃣ [최근 커밋 및 머지 내역 확인 (최근 5건)]")
    code, log_out, _ = run_cmd("git log -n 5 --pretty=format:'%h - %an (%ar): %s'")
    if code == 0 and log_out:
        for line in log_out.splitlines():
            print(f"   * {line}")
    else:
        print("   커밋 내역을 가져올 수 없습니다.")

    # 3. test_dashboard.py 무결성 및 링크 테스트 가동
    print("\n3️⃣ [종합 품질 검증(QA) 및 링크 유효성 진단]")
    code, test_out, test_err = run_cmd(f"python3 {TEST_RUNNER}")
    print(test_out)
    if test_err:
        print(f"[STDERR]: {test_err}")

    # 4. qa_report.md 결과 요약 확인
    report_file = os.path.join(BASE_DIR, "qa_report.md")
    print("\n4️⃣ [진단 결과 판정 요약]")
    if os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for l in lines[:10]:
            print(f"   {l.strip()}")
    else:
        print("   ⚠️ qa_report.md 파일이 생성되지 않았습니다.")

    print("\n" + "=" * 60)
    print("✅ 일일 감사 완료! 이상 항목이 있는 경우 관련 코드(HTML/Script)를 수정하고 커밋&푸시하세요.")
    print("=" * 60)

if __name__ == "__main__":
    main()
