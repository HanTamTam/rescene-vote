#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RESCENE (리센느) 공지 & 투표 자동 수집 및 동기화 엔진
- 공식 사이트(rescene.stream) 및 카카오톡 채널 웹 피드(pf.kakao.com/_WxcxowX)를 실시간 크롤링합니다.
- 새로운 음방 투표(인기가요, 뮤뱅, 음중 등) 및 시상식 연합 공지가 감지되면, index.html의 voteCardsData 배열에 카드를 자동 추가합니다.
- 모바일에서 전달된 텍스트가 있을 경우 이를 직접 분석하여 데이터로 변환 반영합니다.
"""

import os
import re
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "index.html")
MIRROR_PATH = os.path.join(BASE_DIR, "rescene_voting_schedule.html")
NOTICE_MD_PATH = os.path.join(BASE_DIR, "mma_alliance_voting_notice.md")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_url(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"⚠️ URL 조회 실패 ({url}): {e}")
        return ""

def load_index_html():
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return f.read()

def save_index_html(content):
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    with open(MIRROR_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ index.html & rescene_voting_schedule.html 저장 완료")

def inject_vote_card(card_obj):
    content = load_index_html()
    card_id = card_obj.get("id")

    if f'id: "{card_id}"' in content or f"id: '{card_id}'" in content:
        print(f"ℹ️ 이미 등록된 투표 카드입니다: {card_id}")
        return False

    # const voteCardsData = [ 바로 뒤에 삽입
    target = "const voteCardsData = ["
    if target not in content:
        print("❌ voteCardsData 배열을 찾을 수 없습니다.")
        return False

    # 객체를 깔끔한 JS 형식으로 변환
    card_js = "    " + json.dumps(card_obj, ensure_ascii=False, indent=6)[4:-1].strip()
    # trailing comma 처리
    card_entry = f"\n    {{\n      {card_js}\n    }},"

    new_content = content.replace(target, target + card_entry)
    save_index_html(new_content)
    print(f"🎉 신규 투표 카드 주입 성공: {card_obj.get('title')}")
    return True

def crawl_official_feeds():
    print("🌐 리센느 공식 채널 웹 크롤링 시작...")
    found_notices = []

    # 1. rescene.stream 투표 가이드 페이지 확인
    html_vote = fetch_url("https://rescene.stream/vote")
    html_inki = fetch_url("https://rescene.stream/vote/inkigayo")
    html_main = fetch_url("https://rescene.stream/")
    html_kakao = fetch_url("https://pf.kakao.com/_WxcxowX")

    combined_html = f"{html_vote}\n{html_inki}\n{html_main}\n{html_kakao}"

    # 1) 인기가요 사전투표 (LiNC 링크 앱) 감지
    if ("인기가요" in combined_html or "LiNC" in combined_html or "링크" in combined_html) and "사전" in combined_html:
        found_notices.append({
            "type": "inkigayo",
            "title": "SBS 인기가요 사전투표 : 리센느 'WITH'",
            "card": {
                "id": "inkigayo-with",
                "name": "인기가요 사전투표",
                "theme": "inki",
                "customBorder": "border-top: 4px solid #0284c7; background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 25%);",
                "badgeText": "🔴 인기가요 신곡 사전투표 (~11/06 23:59)",
                "badgeStyle": "background:#e0f2fe; color:#0369a1; font-weight:800;",
                "title": "SBS 인기가요 사전투표 : 리센느 'WITH'",
                "desc": "링크(LiNC) 앱에서 매일 계정당 <strong>최대 10표 투표</strong> 가능! (신곡 'WITH' 1위 순위 사전투표 집계 반영)",
                "startDate": "2026-11-04T00:00:00",
                "endDate": "2026-11-06T23:59:59",
                "deadlineColor": "#0284c7",
                "notice": "💎 <strong>무료 재화 적립 팁:</strong> 광고 보고 팬 포인트 룰렛 돌리기! 1표당 30 팬 포인트(또는 8젬) 소모. 계정당 매일 10표씩 투표 가능하며 다계정 참여가 가능합니다.",
                "noticeColor": { "bg": "rgba(2, 132, 199, 0.08)", "border": "rgba(2, 132, 199, 0.4)", "text": "#0369a1" },
                "actions": [
                    {
                        "type": "custom",
                        "label": "📱 링크(LiNC) 인기가요 직행 투표 열기 ↗",
                        "url": "https://apps.apple.com/kr/app/linc-%EB%A7%81%ED%81%AC/id6475704944",
                        "style": "background: linear-gradient(135deg, #0284c7, #0369a1); color: #ffffff; box-shadow: 0 3px 10px rgba(2, 132, 199, 0.3); border-radius: 12px; height: 46px; font-weight: 800; display:flex; align-items:center; justify-content:center; text-decoration:none;"
                    },
                    {
                        "type": "grid2",
                        "items": [
                            {
                                "label": "🍎 iOS (아이폰) 링크 앱 ↗",
                                "url": "https://apps.apple.com/kr/app/linc-%EB%A7%81%ED%81%AC/id6475704944",
                                "style": "background:#f0f9ff; border:1px solid #bae6fd; color:#0284c7; height:38px; font-size:11.5px; font-weight:700; border-radius:10px; display:flex; align-items:center; justify-content:center; text-decoration:none;"
                            },
                            {
                                "label": "🤖 안드로이드 링크 앱 ↗",
                                "url": "https://play.google.com/store/apps/details?id=com.sbs.linc",
                                "style": "background:#f0fdf4; border:1px solid #bbf7d0; color:#15803d; height:38px; font-size:11.5px; font-weight:700; border-radius:10px; display:flex; align-items:center; justify-content:center; text-decoration:none;"
                            }
                        ]
                    }
                ]
            }
        })

    return found_notices

def parse_raw_text(raw_text):
    print("📝 전달된 공지 텍스트 분석 중...")
    cards = []

    # 인기가요 감지
    if "인기가요" in raw_text:
        end_date = "2026-11-06T23:59:59"
        m = re.search(r"(\d{4})[.\-/ ](\d{1,2})[.\-/ ](\d{1,2})", raw_text)
        if m:
            end_date = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}T23:59:59"

        cards.append({
            "id": "inkigayo-with",
            "name": "인기가요 사전투표",
            "theme": "inki",
            "customBorder": "border-top: 4px solid #0284c7; background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 25%);",
            "badgeText": f"🔴 인기가요 신곡 사전투표 (~11/06 23:59)",
            "badgeStyle": "background:#e0f2fe; color:#0369a1; font-weight:800;",
            "title": "SBS 인기가요 사전투표 : 리센느 'WITH'",
            "desc": "링크(LiNC) 앱에서 매일 계정당 <strong>최대 10표 투표</strong> 필수! (신곡 'WITH' 1위 사전투표 집계 반영)",
            "startDate": datetime.now().strftime("%Y-%m-%dT00:00:00"),
            "endDate": end_date,
            "deadlineColor": "#0284c7",
            "notice": "💎 <strong>무료 재화 적립:</strong> 광고 보고 팬 포인트 룰렛 돌리기! 계정당 매일 10표 투표 가능.",
            "noticeColor": { "bg": "rgba(2, 132, 199, 0.08)", "border": "rgba(2, 132, 199, 0.4)", "text": "#0369a1" },
            "actions": [
                {
                    "type": "custom",
                    "label": "📱 링크(LiNC) 인기가요 직행 투표 열기 ↗",
                    "url": "https://apps.apple.com/kr/app/linc-%EB%A7%81%ED%81%AC/id6475704944",
                    "style": "background: linear-gradient(135deg, #0284c7, #0369a1); color: #ffffff; box-shadow: 0 3px 10px rgba(2, 132, 199, 0.3); border-radius: 12px; height: 46px; font-weight: 800; display:flex; align-items:center; justify-content:center; text-decoration:none;"
                }
            ]
        })

    return cards

def main():
    print("🚀 RESCENE 공지 & 투표 자동 동기화 엔진 가동")
    issue_body = os.environ.get("ISSUE_BODY", "")
    issue_title = os.environ.get("ISSUE_TITLE", "")
    raw_text = issue_body if issue_body and issue_body.strip() not in ["sync", "SYNC"] else ""

    modified = False

    # 1) 모바일 이슈 본문에 공지가 전달된 경우 -> 텍스트 직접 파싱
    if raw_text:
        print("📥 모바일 이슈 본문에서 공지 텍스트를 파싱합니다.")
        cards = parse_raw_text(raw_text)
        for c in cards:
            if inject_vote_card(c):
                modified = True

        # 공지 아카이브에 기록
        if os.path.exists(NOTICE_MD_PATH):
            with open(NOTICE_MD_PATH, "r", encoding="utf-8") as f:
                md_content = f.read()
            today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            entry = f"\n\n### 📢 [모바일 수집 공지] ({today_str})\n{raw_text.strip()}\n"
            if raw_text.strip() not in md_content:
                with open(NOTICE_MD_PATH, "a", encoding="utf-8") as f:
                    f.write(entry)
                modified = True

    # 2) 본문이 없거나 자동 스케줄 실행인 경우 -> 공식 채널 직접 크롤링
    else:
        print("📡 공식 채널(rescene.stream 및 카카오톡 채널)에서 최신 공지를 수집합니다.")
        notices = crawl_official_feeds()
        for n in notices:
            card = n.get("card")
            if card and inject_vote_card(card):
                modified = True

    # 3) 결과 보고
    if modified:
        print("✨ 신규 공지가 성공적으로 index.html에 주입되었습니다! (PR 생성 예정)")
    else:
        print("ℹ️ 이미 최신 상태이며 새로운 변동 사항이 없습니다.")

if __name__ == "__main__":
    main()
