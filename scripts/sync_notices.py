#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RESCENE (리센느) X(트위터) 음원총공팀 피드 전용 자동 동기화 엔진
- 오직 리센느 음원총공팀 공식 X 계정(@ResceneStream)의 피드만 모니터링합니다.
- @ResceneStream 피드에 새로운 음원 방송 투표, 스밍, 시상식 연합 공지가 올라오면 index.html의 voteCardsData에 자동 반영합니다.
"""

import os
import re
import sys
import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "index.html")
MIRROR_PATH = os.path.join(BASE_DIR, "rescene_voting_schedule.html")
NOTICE_MD_PATH = os.path.join(BASE_DIR, "mma_alliance_voting_notice.md")

TWITTER_USERNAME = "ResceneStream"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}

def fetch_url(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"⚠️ X 피드 조회 실패 ({url}): {e}")
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
        print(f"ℹ️ 이미 대시보드에 존재하는 투표 카드입니다: {card_id}")
        return False

    target = "const voteCardsData = ["
    if target not in content:
        print("❌ voteCardsData 배열을 찾을 수 없습니다.")
        return False

    card_js = "    " + json.dumps(card_obj, ensure_ascii=False, indent=6)[4:-1].strip()
    card_entry = f"\n    {{\n      {card_js}\n    }},"

    new_content = content.replace(target, target + card_entry)
    save_index_html(new_content)
    print(f"🎉 X 공지 기반 신규 투표 카드 생성 성공: {card_obj.get('title')}")
    return True

def get_x_feed_tweets():
    """
    @ResceneStream X(트위터) 피드에서 최신 트윗 목록을 추출합니다.
    1) Twitter 공식 Syndication 타임라인 API
    2) Nitter RSS 백업 미러
    """
    print(f"🐦 @{TWITTER_USERNAME} X(트위터) 음총팀 피드 수집 중...")
    tweets = []

    # 1. Twitter Syndication Timeline API (X 공식 위젯 엔드포인트)
    syn_url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{TWITTER_USERNAME}"
    html = fetch_url(syn_url)

    if html:
        next_data_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
        if next_data_match:
            try:
                data = json.loads(next_data_match.group(1))
                entries = data.get("props", {}).get("pageProps", {}).get("timeline", {}).get("entries", [])
                for e in entries:
                    tweet = e.get("content", {}).get("tweet", {})
                    if not tweet:
                        continue
                    text = tweet.get("full_text") or tweet.get("text", "")
                    created_at = tweet.get("created_at", "")
                    if text:
                        tweets.append({"text": text, "created_at": created_at, "source": "x_syndication"})
                print(f"✅ X 공식 타임라인에서 트윗 {len(tweets)}건 수집 완료")
            except Exception as ex:
                print(f"⚠️ Syndication JSON 파싱 오류: {ex}")

    # 2. Syndication 응답이 없을 경우 Nitter RSS 미러 백업 활용
    if not tweets:
        nitter_hosts = ["nitter.poast.org", "nitter.privacydev.net", "nitter.net"]
        for host in nitter_hosts:
            rss_url = f"https://{host}/{TWITTER_USERNAME}/rss"
            rss_xml = fetch_url(rss_url, timeout=6)
            if rss_xml and "<rss" in rss_xml:
                try:
                    root = ET.fromstring(rss_xml)
                    for item in root.findall(".//item"):
                        title = item.findtext("title") or ""
                        desc = item.findtext("description") or ""
                        full_txt = f"{title}\n{desc}"
                        tweets.append({"text": full_txt, "source": host})
                    if tweets:
                        print(f"✅ Nitter RSS({host})에서 트윗 {len(tweets)}건 수집 완료")
                        break
                except Exception as ex:
                    print(f"⚠️ RSS 파싱 실패 ({host}): {ex}")

    return tweets

def parse_x_tweet_for_actions(tweet_text):
    """
    트윗 본문을 분석하여 신규 투표 및 공지 카드를 생성합니다.
    """
    cards = []

    # 1) SBS 인기가요 사전투표 감지
    if "인기가요" in tweet_text and ("사전투표" in tweet_text or "사전 투표" in tweet_text or "LiNC" in tweet_text or "링크" in tweet_text):
        m = re.search(r"(\d{4})[.\-/ ](\d{1,2})[.\-/ ](\d{1,2})", tweet_text)
        end_date = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}T23:59:59" if m else "2026-11-06T23:59:59"

        cards.append({
            "id": "inkigayo-with",
            "name": "인기가요 사전투표",
            "theme": "inki",
            "customBorder": "border-top: 4px solid #0284c7; background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 25%);",
            "badgeText": "🔴 인기가요 신곡 사전투표 (~11/06 23:59)",
            "badgeStyle": "background:#e0f2fe; color:#0369a1; font-weight:800;",
            "title": "SBS 인기가요 사전투표 : 리센느 'WITH'",
            "desc": "링크(LiNC) 앱에서 매일 계정당 <strong>최대 10표 투표</strong> 필수! (신곡 'WITH' 1위 순위 사전투표 집계 반영)",
            "startDate": datetime.now().strftime("%Y-%m-%dT00:00:00"),
            "endDate": end_date,
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
        })

    # 2) KBS 뮤직뱅크 사전투표 (쿠궁 앱) 감지
    if "뮤직뱅크" in tweet_text and ("사전투표" in tweet_text or "쿠궁" in tweet_text or "fancast" in tweet_text):
        cards.append({
            "id": "musicbank-vote",
            "name": "뮤직뱅크 사전투표",
            "theme": "kb",
            "customBorder": "border-top: 4px solid #3b82f6; background: linear-gradient(180deg, #eff6ff 0%, #ffffff 25%);",
            "badgeText": "📢 뮤직뱅크 사전투표",
            "badgeStyle": "background:#dbeafe; color:#1d4ed8; font-weight:800;",
            "title": "KBS 뮤직뱅크 사전투표 : 리센느 'WITH'",
            "desc": "쿠궁(coogoong) 앱에서 리센느 'WITH' 투표 참여!",
            "startDate": datetime.now().strftime("%Y-%m-%dT00:00:00"),
            "endDate": "2026-11-10T11:00:00",
            "deadlineColor": "#1d4ed8",
            "actions": [
                {
                    "type": "primary",
                    "label": "📱 쿠궁(coogoong) 뮤뱅 투표 열기 ↗",
                    "url": "https://play.google.com/store/apps/details?id=com.contentsmadang.fancast"
                }
            ]
        })

    # 3) MBC 쇼! 음악중심 (뮤빗 & 뮤니버스) 감지
    if "음악중심" in tweet_text and ("사전투표" in tweet_text or "뮤빗" in tweet_text or "뮤니버스" in tweet_text):
        cards.append({
            "id": "music-core-vote",
            "name": "음악중심 사전투표",
            "theme": "melon",
            "customBorder": "border-top: 4px solid #ec4899; background: linear-gradient(180deg, #fdf2f8 0%, #ffffff 25%);",
            "badgeText": "📢 쇼! 음악중심 사전투표",
            "badgeStyle": "background:#fce7f3; color:#be185d; font-weight:800;",
            "title": "MBC 쇼! 음악중심 사전투표 : 리센느 'WITH'",
            "desc": "뮤빗(Mubeat) & 뮤니버스(Muniverse) 앱에서 음중 사전투표 진행!",
            "startDate": datetime.now().strftime("%Y-%m-%dT00:00:00"),
            "endDate": "2026-11-12T11:00:00",
            "deadlineColor": "#be185d",
            "actions": [
                {
                    "type": "primary",
                    "label": "📱 뮤빗(Mubeat) 음중 투표 열기 ↗",
                    "url": "https://mubeat.tv/"
                }
            ]
        })

    return cards

def main():
    print(f"🚀 RESCENE X(@{TWITTER_USERNAME}) 음원총공팀 피드 전용 동기화 엔진 가동")
    issue_body = os.environ.get("ISSUE_BODY", "")
    raw_text = issue_body if issue_body and issue_body.strip() not in ["sync", "SYNC"] else ""

    modified = False

    # 1) 모바일 이슈 본문에 공지를 직접 붙여넣었을 경우
    if raw_text:
        print("📥 모바일에서 전달된 트윗/공지 텍스트를 분석합니다.")
        cards = parse_x_tweet_for_actions(raw_text)
        for c in cards:
            if inject_vote_card(c):
                modified = True

        if os.path.exists(NOTICE_MD_PATH):
            with open(NOTICE_MD_PATH, "r", encoding="utf-8") as f:
                md_content = f.read()
            today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            entry = f"\n\n### 📢 [X 피드 수집 공지] ({today_str})\n{raw_text.strip()}\n"
            if raw_text.strip() not in md_content:
                with open(NOTICE_MD_PATH, "a", encoding="utf-8") as f:
                    f.write(entry)
                modified = True

    # 2) 자동 스케줄 실행 또는 빈칸 실행인 경우 -> 오직 @ResceneStream X 피드만 조회!
    else:
        print(f"📡 @{TWITTER_USERNAME} 공식 X 피드를 직접 크롤링합니다...")
        tweets = get_x_feed_tweets()

        if not tweets:
            print("ℹ️ 현재 X 피드에서 새로운 공개 트윗을 불러오지 못했거나 변동이 없습니다.")
        else:
            for tw in tweets:
                txt = tw.get("text", "")
                cards = parse_x_tweet_for_actions(txt)
                for c in cards:
                    if inject_vote_card(c):
                        modified = True

                # 마크다운 아카이브 갱신
                if os.path.exists(NOTICE_MD_PATH) and txt:
                    with open(NOTICE_MD_PATH, "r", encoding="utf-8") as f:
                        md_content = f.read()
                    first_line = txt.strip().split("\n")[0][:40]
                    if first_line not in md_content:
                        today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                        entry = f"\n\n### 📢 [X(@{TWITTER_USERNAME}) 트윗 피드] ({today_str})\n{txt.strip()}\n"
                        with open(NOTICE_MD_PATH, "a", encoding="utf-8") as f:
                            f.write(entry)
                        modified = True

    if modified:
        print("✨ X(@ResceneStream) 피드에서 새 공지를 감지하여 대시보드에 반영했습니다! (PR 생성 예정)")
    else:
        print("ℹ️ X(@ResceneStream) 피드 기준 이미 최신 상태이며 새로운 변동 사항이 없습니다.")

if __name__ == "__main__":
    main()
