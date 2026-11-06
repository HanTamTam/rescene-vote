#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RESCENE (리센느) X(트위터) 음원총공팀 피드 전용 자동 동기화 & 갱신(Upsert) 엔진
- 오직 리센느 음원총공팀 공식 X 계정(@ResceneStream)의 피드만 모니터링합니다.
- @ResceneStream 피드에 새로운 음원 방송 투표, 스밍, 시상식 연합 공지가 올라오면 index.html의 voteCardsData에 자동 반영합니다.
- 이미 등록된 투표라도 마감일시 연장, 안내 문구/팁 변경 등 변동 사항이 감지되면 최신 정보로 덮어쓰는(Upsert) 기능을 지원합니다.
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
    print("✅ index.html & rescene_voting_schedule.html 동기화 저장 완료")

def find_card_span(content, card_id):
    """
    HTML 내 voteCardsData 배열에서 특정 card_id를 가진 객체의 시작('{')과 끝('},' 또는 '}') 인덱스를 탐색합니다.
    """
    # 따옴표 유무(JSON의 "id" 또는 JS 객체의 id)에 관계없이 정확히 카드를 찾습니다.
    pattern = re.compile(r'["\']?id["\']?\s*:\s*["\']' + re.escape(card_id) + r'["\']')
    match = pattern.search(content)
    if not match:
        return None
    idx = match.start()
    open_brace_idx = content.rfind('{', 0, idx)
    if open_brace_idx == -1:
        return None

    depth = 0
    in_string = False
    quote_char = ''
    i = open_brace_idx
    while i < len(content):
        ch = content[i]
        if in_string:
            if ch == '\\':
                i += 2
                continue
            elif ch == quote_char:
                in_string = False
        else:
            if ch in ('"', "'"):
                in_string = True
                quote_char = ch
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    if end_idx < len(content) and content[end_idx] == ',':
                        end_idx += 1
                    return (open_brace_idx, end_idx)
        i += 1
    return None

def upsert_vote_card(card_obj):
    """
    투표 카드를 신규 삽입하거나, 기존 카드가 변경되었으면 최신 데이터로 업데이트(Upsert)합니다.
    반환값: (성공여부: bool, 상태: 'inserted' | 'updated' | 'unchanged' | 'error')
    """
    content = load_index_html()
    card_id = card_obj.get("id")
    card_title = card_obj.get("title", card_id)

    target_array = "const voteCardsData = ["
    if target_array not in content:
        print("❌ voteCardsData 배열을 찾을 수 없습니다.")
        return False, "error"

    card_span = find_card_span(content, card_id)

    # 1. 기존 카드가 없는 경우 -> 신규 삽입 (Insert)
    if not card_span:
        card_js = "    " + json.dumps(card_obj, ensure_ascii=False, indent=6)[4:-1].strip()
        card_entry = f"\n    {{\n      {card_js}\n    }},"
        new_content = content.replace(target_array, target_array + card_entry)
        save_index_html(new_content)
        print(f"🎉 신규 투표 카드 등록 성공: {card_title} ({card_id})")
        return True, "inserted"

    # 2. 기존 카드가 존재하는 경우 -> 변동 사항 검사 후 갱신 (Update)
    start, end = card_span
    old_card_code = content[start:end]

    # 주요 변경 대상 필드 비교 (마감일, 배지문구, 안내팁, 설명)
    new_end_date = card_obj.get("endDate", "")
    new_badge = card_obj.get("badgeText", "")
    new_notice = card_obj.get("notice", "")
    new_desc = card_obj.get("desc", "")

    has_diff = False
    if new_end_date and f'endDate: "{new_end_date}"' not in old_card_code and f"endDate: '{new_end_date}'" not in old_card_code:
        has_diff = True
        print(f"⏰ [{card_id}] 마감일시 변동 감지 -> {new_end_date}")

    if new_badge and f'badgeText: "{new_badge}"' not in old_card_code and f"badgeText: '{new_badge}'" not in old_card_code:
        has_diff = True
        print(f"🏷️ [{card_id}] 배지 문구 변동 감지 -> {new_badge}")

    if new_notice and new_notice not in old_card_code:
        has_diff = True
        print(f"💡 [{card_id}] 투표 공지/팁 변동 감지")

    if new_desc and new_desc not in old_card_code:
        has_diff = True
        print(f"📝 [{card_id}] 설명 문구 변동 감지")

    if has_diff:
        card_js = "    " + json.dumps(card_obj, ensure_ascii=False, indent=6)[4:-1].strip()
        new_card_code = f"{{\n      {card_js}\n    }},"
        new_content = content[:start] + new_card_code + content[end:]
        save_index_html(new_content)
        print(f"🔄 [{card_id}] 기존 투표 카드 최신 정보로 갱신 완료!")
        return True, "updated"

    print(f"ℹ️ [{card_id}] 변동 사항 없음 (최신 상태 유지)")
    return False, "unchanged"

def get_x_feed_tweets():
    """
    @ResceneStream X(트위터) 피드에서 최신 트윗 목록을 추출합니다.
    클라우드 러너(GitHub Actions) 환경에서도 안정적으로 수집되도록 다중 소스를 순차 시도합니다:
    1) FxTwitter API v2 (오픈소스 X JSON API)
    2) FxTwitter RSS 피드 (fxtwitter.com/{user}/feed.xml)
    3) Twitter 공식 Syndication 위젯 엔드포인트
    4) Nitter 공개 미러 백업
    """
    print(f"🐦 @{TWITTER_USERNAME} X(트위터) 음총팀 피드 수집 중...")
    tweets = []

    # 1. FxTwitter API v2 (데이터센터 IP 차단 없는 고신뢰도 JSON 엔드포인트)
    try:
        fx_api_url = f"https://api.fxtwitter.com/2/profile/{TWITTER_USERNAME}/statuses"
        fx_json_str = fetch_url(fx_api_url, timeout=8)
        if fx_json_str and fx_json_str.strip().startswith("{"):
            fx_data = json.loads(fx_json_str)
            entries = fx_data.get("results") or fx_data.get("tweets") or fx_data.get("statuses") or []
            for item in entries:
                txt = item.get("text") or item.get("full_text") or ""
                created_at = item.get("created_at") or ""
                if txt:
                    tweets.append({"text": txt, "created_at": created_at, "source": "fxtwitter_api"})
            if tweets:
                print(f"✅ FxTwitter API에서 트윗 {len(tweets)}건 수집 완료")
                return tweets
    except Exception as ex:
        print(f"⚠️ FxTwitter API 조회 실패: {ex}")

    # 2. FxTwitter RSS 피드
    try:
        fx_rss_url = f"https://fxtwitter.com/{TWITTER_USERNAME}/feed.xml"
        rss_xml = fetch_url(fx_rss_url, timeout=8)
        if rss_xml and ("<rss" in rss_xml or "<feed" in rss_xml):
            root = ET.fromstring(rss_xml)
            for item in root.findall(".//item"):
                title = item.findtext("title") or ""
                desc = item.findtext("description") or ""
                full_txt = f"{title}\n{desc}"
                if full_txt.strip():
                    tweets.append({"text": full_txt, "source": "fxtwitter_rss"})
            if not tweets:
                for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
                    title = entry.findtext("{http://www.w3.org/2005/Atom}title") or ""
                    content = entry.findtext("{http://www.w3.org/2005/Atom}content") or ""
                    full_txt = f"{title}\n{content}"
                    if full_txt.strip():
                        tweets.append({"text": full_txt, "source": "fxtwitter_atom"})
            if tweets:
                print(f"✅ FxTwitter RSS에서 트윗 {len(tweets)}건 수집 완료")
                return tweets
    except Exception as ex:
        print(f"⚠️ FxTwitter RSS 조회 실패: {ex}")

    # 3. Twitter Syndication Timeline API (X 공식 위젯 엔드포인트)
    syn_url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{TWITTER_USERNAME}"
    html = fetch_url(syn_url, timeout=8)
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
                if tweets:
                    print(f"✅ X 공식 타임라인에서 트윗 {len(tweets)}건 수집 완료")
                    return tweets
            except Exception as ex:
                print(f"⚠️ Syndication JSON 파싱 오류: {ex}")

    # 4. Nitter RSS 미러 백업
    nitter_hosts = ["nitter.poast.org", "nitter.privacydev.net", "nitter.net"]
    for host in nitter_hosts:
        rss_url = f"https://{host}/{TWITTER_USERNAME}/rss"
        rss_xml = fetch_url(rss_url, timeout=5)
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

def parse_date_from_text(text, default_date_str="2026-11-06T23:59:59"):
    """
    트윗 본문에서 마감 날짜 및 시간을 정교하게 파싱합니다.
    예: 2026-11-07 23:59, 11/07 23:59, 11월 7일 24:00, ~11.08 등
    """
    now = datetime.now()
    year = now.year

    # 1) YYYY.MM.DD 또는 YYYY-MM-DD
    m_full = re.search(r"(\d{4})[.\-/ ](\d{1,2})[.\-/ ](\d{1,2})", text)
    if m_full:
        y, m, d = int(m_full.group(1)), int(m_full.group(2)), int(m_full.group(3))
        # 시간 검사
        m_time = re.search(r"(\d{1,2}):(\d{2})", text)
        h, mn = (int(m_time.group(1)), int(m_time.group(2))) if m_time else (23, 59)
        return f"{y:04d}-{m:02d}-{d:02d}T{h:02d}:{mn:02d}:59", f"~{m:02d}/{d:02d} {h:02d}:{mn:02d}"

    # 2) MM월 DD일 또는 MM/DD
    m_month = re.search(r"(\d{1,2})월\s*(\d{1,2})일", text) or re.search(r"(?:~|\s)(\d{1,2})[./](\d{1,2})", text)
    if m_month:
        m, d = int(m_month.group(1)), int(m_month.group(2))
        m_time = re.search(r"(\d{1,2}):(\d{2})", text)
        h, mn = (int(m_time.group(1)), int(m_time.group(2))) if m_time else (23, 59)
        return f"{year:04d}-{m:02d}-{d:02d}T{h:02d}:{mn:02d}:59", f"~{m:02d}/{d:02d} {h:02d}:{mn:02d}"

    return default_date_str, "~11/06 23:59"

def parse_x_tweet_for_actions(tweet_text):
    """
    트윗 본문을 분석하여 신규 또는 갱신할 투표 카드 객체를 생성합니다.
    """
    cards = []

    # 1) SBS 인기가요 사전투표 감지
    if "인기가요" in tweet_text and ("사전투표" in tweet_text or "사전 투표" in tweet_text or "LiNC" in tweet_text or "링크" in tweet_text or "사전" in tweet_text):
        end_date, badge_deadline = parse_date_from_text(tweet_text, "2026-11-06T23:59:59")

        # 연장 또는 특별 안내 문구 감지
        notice_tip = "💎 <strong>무료 재화 적립 팁:</strong> 광고 보고 팬 포인트 룰렛 돌리기! 1표당 30 팬 포인트(또는 8젬) 소모. 계정당 매일 10표씩 투표 가능하며 다계정 참여가 가능합니다."
        if "연장" in tweet_text:
            notice_tip += " (📢 <strong>총공팀 공지:</strong> 투표 기간이 연장되었습니다. 끝까지 총공 부탁드립니다!)"

        cards.append({
            "id": "inkigayo-with",
            "name": "인기가요 사전투표",
            "theme": "inki",
            "customBorder": "border-top: 4px solid #0284c7; background: linear-gradient(180deg, #f0f9ff 0%, #ffffff 25%);",
            "badgeText": f"🔴 인기가요 신곡 사전투표 ({badge_deadline})",
            "badgeStyle": "background:#e0f2fe; color:#0369a1; font-weight:800;",
            "title": "SBS 인기가요 사전투표 : 리센느 'WITH'",
            "desc": "링크(LiNC) 앱에서 매일 계정당 <strong>최대 10표 투표</strong> 필수! (신곡 'WITH' 1위 순위 사전투표 집계 반영)",
            "startDate": datetime.now().strftime("%Y-%m-%dT00:00:00"),
            "endDate": end_date,
            "deadlineColor": "#0284c7",
            "notice": notice_tip,
            "noticeColor": { "bg": "rgba(2, 132, 199, 0.08)", "border": "rgba(2, 132, 199, 0.4)", "text": "#0369a1" },
            "actions": [
                {
                    "type": "custom",
                    "label": "📱 링크(LiNC) 인기가요 직행 투표 열기 ↗",
                    "url": "https://app.linc.fan/31TL/UPBjE3DC",
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
    if "뮤직뱅크" in tweet_text and ("사전투표" in tweet_text or "쿠궁" in tweet_text or "fancast" in tweet_text or "뮤뱅" in tweet_text):
        end_date, badge_deadline = parse_date_from_text(tweet_text, "2026-11-10T11:00:00")
        cards.append({
            "id": "musicbank-vote",
            "name": "뮤직뱅크 사전투표",
            "theme": "kb",
            "customBorder": "border-top: 4px solid #3b82f6; background: linear-gradient(180deg, #eff6ff 0%, #ffffff 25%);",
            "badgeText": f"📢 뮤직뱅크 사전투표 ({badge_deadline})",
            "badgeStyle": "background:#dbeafe; color:#1d4ed8; font-weight:800;",
            "title": "KBS 뮤직뱅크 사전투표 : 리센느 'WITH'",
            "desc": "쿠궁(coogoong) 앱에서 리센느 'WITH' 투표 참여!",
            "startDate": datetime.now().strftime("%Y-%m-%dT00:00:00"),
            "endDate": end_date,
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
    if "음악중심" in tweet_text and ("사전투표" in tweet_text or "뮤빗" in tweet_text or "뮤니버스" in tweet_text or "음중" in tweet_text):
        end_date, badge_deadline = parse_date_from_text(tweet_text, "2026-11-12T11:00:00")
        cards.append({
            "id": "music-core-vote",
            "name": "음악중심 사전투표",
            "theme": "melon",
            "customBorder": "border-top: 4px solid #ec4899; background: linear-gradient(180deg, #fdf2f8 0%, #ffffff 25%);",
            "badgeText": f"📢 쇼! 음악중심 사전투표 ({badge_deadline})",
            "badgeStyle": "background:#fce7f3; color:#be185d; font-weight:800;",
            "title": "MBC 쇼! 음악중심 사전투표 : 리센느 'WITH'",
            "desc": "뮤빗(Mubeat) & 뮤니버스(Muniverse) 앱에서 음중 사전투표 진행!",
            "startDate": datetime.now().strftime("%Y-%m-%dT00:00:00"),
            "endDate": end_date,
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

def log_notice_archive(header_tag, text):
    if not os.path.exists(NOTICE_MD_PATH) or not text.strip():
        return False
    with open(NOTICE_MD_PATH, "r", encoding="utf-8") as f:
        md_content = f.read()

    first_line = text.strip().split("\n")[0][:40]
    if first_line not in md_content:
        today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n\n### 📢 [{header_tag}] ({today_str})\n{text.strip()}\n"
        with open(NOTICE_MD_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
        return True
    return False

def main():
    print(f"🚀 RESCENE X(@{TWITTER_USERNAME}) 음원총공팀 피드 전용 동기화 & 갱신(Upsert) 엔진 가동")
    issue_body = os.environ.get("ISSUE_BODY", "")
    raw_text = issue_body if issue_body and issue_body.strip() not in ["sync", "SYNC"] else ""

    modified = False

    # 1) 모바일 이슈 본문에 공지를 직접 붙여넣었을 경우
    if raw_text:
        print("📥 모바일에서 전달된 트윗/공지 텍스트를 분석합니다.")
        cards = parse_x_tweet_for_actions(raw_text)
        for c in cards:
            success, status = upsert_vote_card(c)
            if success:
                modified = True

        if log_notice_archive("모바일 수집 공지", raw_text):
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
                    success, status = upsert_vote_card(c)
                    if success:
                        modified = True

                # 마크다운 아카이브 갱신
                if log_notice_archive(f"X(@{TWITTER_USERNAME}) 트윗 피드", txt):
                    modified = True

    if modified:
        print("✨ X(@ResceneStream) 피드에서 변동/신규 공지를 감지하여 대시보드에 성공적으로 반영했습니다! (PR 생성 예정)")
    else:
        print("ℹ️ X(@ResceneStream) 피드 기준 이미 최신 상태이며 새로운 변동 사항이 없습니다.")

if __name__ == "__main__":
    main()
