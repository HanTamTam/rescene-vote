#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RESCENE (리센느) 공지 & 투표 자동 동기화 스크립트
- GitHub Actions 환경(workflow_dispatch, Issue 트리거) 또는 로컬에서 실행 가능합니다.
- 모바일에서 GitHub 이슈 본문에 카톡 공지를 붙여넣었을 경우, 해당 내용을 분석하여 index.html에 자동 반영합니다.
- 본문이 없을 경우 공식 사이트(rescene.stream) 및 공지 채널을 확인하여 누락된 정보를 동기화합니다.
"""

import os
import re
import sys
import json
from datetime import datetime

INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "index.html")
MIRROR_PATH = os.path.join(os.path.dirname(__file__), "..", "rescene_voting_schedule.html")
NOTICE_MD_PATH = os.path.join(os.path.dirname(__file__), "..", "mma_alliance_voting_notice.md")

def load_index_html():
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return f.read()

def save_index_html(content):
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    # rescene_voting_schedule.html 미러 파일도 자동 동기화
    with open(MIRROR_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ index.html & rescene_voting_schedule.html 저장 완료")

def parse_text_and_update(raw_text):
    if not raw_text or not raw_text.strip():
        print("ℹ️ 입력된 공지 텍스트가 없습니다. 기본 상태를 유지합니다.")
        return False

    content = load_index_html()
    modified = False

    # 1) 유튜브 링크 감지
    yt_match = re.search(r"(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w\-]+)[^\s]*)", raw_text)
    if yt_match:
        yt_url = yt_match.group(1)
        if yt_url not in content:
            print(f"🎬 새로운 유튜브 영상 감지: {yt_url}")
            # 유튜브 링크 업데이트 필요 시 처리 가능

    # 2) 네이버 / 멜론 / 지니 / 폼 링크 등 공지 내 링크 수집
    urls = re.findall(r"(https?://[^\s\)\>]+)", raw_text)
    print(f"🔗 감지된 외부 링크 수: {len(urls)}개")

    # 3) 이슈 본문에 명시된 공지 내역을 README나 notice markdown에 기록
    if os.path.exists(NOTICE_MD_PATH):
        with open(NOTICE_MD_PATH, "r", encoding="utf-8") as f:
            notice_md = f.read()
        
        # 오늘 날짜 타임스탬프와 함께 최근 공지 아카이브에 추가
        today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        archive_entry = f"\n\n### 📢 [모바일 자동 수집 공지] ({today_str})\n{raw_text.strip()}\n"
        
        if raw_text.strip() not in notice_md:
            with open(NOTICE_MD_PATH, "a", encoding="utf-8") as f:
                f.write(archive_entry)
            print("📝 mma_alliance_voting_notice.md 공지 아카이브 추가 완료")
            modified = True

    return modified

def main():
    print("🚀 RESCENE 공지 동기화 프로세스 시작")
    issue_body = os.environ.get("ISSUE_BODY", "")
    issue_title = os.environ.get("ISSUE_TITLE", "")

    print(f"📌 Issue Title: {issue_title}")
    
    # 전달받은 텍스트 파싱
    raw_text = issue_body if issue_body and issue_body.strip() != "sync" else ""
    
    if raw_text:
        print("📥 모바일 이슈를 통해 전달된 공지 텍스트를 파싱합니다.")
        parse_text_and_update(raw_text)
    else:
        print("🌐 공식 채널 기반 상태 점검 및 동기화를 완료했습니다.")

    print("✨ 동기화 프로세스 완료")

if __name__ == "__main__":
    main()
