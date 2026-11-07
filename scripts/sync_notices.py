#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RESCENE (리센느) X(트위터) 음원총공팀 피드 전용 3계층 하이브리드 지능형 동기화 & 갱신(Upsert) 엔진
- 1계층 (Rule-based Fast Path): 인기가요(LiNC 딥링크), 뮤직뱅크(쿠궁), 쇼! 음악중심(뮤빗/뮤니버스) 등 표준 투표 초고속 처리
- 2계층 (AI-Powered Card Synthesizer & Multimodal Vision): 
    - 텍스트뿐만 아니라 첨부된 포스터/카드뉴스/시간표 이미지(OCR)를 Gemini 1.5 Flash 비전으로 동시 분석
    - 본문이 짧거나 글씨가 없어도 이미지 속 세부 일정, 마감일, 투표/스밍 방법을 정확히 추출하여 카드로 자동 조립
- 3계층 (Universal Fail-safe Fallback): AI 부재/오류 시에도 해시태그 복사(copy), 링크/포스터 직행 기반 만능 카드로 100% 안전 발행
"""

import os
import re
import sys
import json
import base64
import hashlib
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "index.html")
MIRROR_PATH = os.path.join(BASE_DIR, "rescene_voting_schedule.html")
NOTICE_MD_PATH = os.path.join(BASE_DIR, "mma_alliance_voting_notice.md")

TWITTER_USERNAME = "ResceneStream"
LINC_DIRECT_URL = "https://app.linc.fan/31TL/UPBjE3DC"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}

def fetch_url(url, timeout=12, custom_headers=None):
    try:
        h = custom_headers if custom_headers else HEADERS
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"⚠️ URL 조회 실패 ({url[:60]}...): {e}")
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
    따옴표 유무(JSON의 "id" 또는 JS 객체의 id)에 관계없이 정확히 카드를 찾습니다.
    """
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
    @ResceneStream X(트위터) 피드에서 최신 트윗 목록 및 첨부 이미지 URL을 추출합니다.
    1) FxTwitter API v2 (텍스트 + media.photos)
    2) FxTwitter RSS 피드 (텍스트 + <img> 태그 파싱)
    3) Twitter Syndication 위젯 엔드포인트 (텍스트 + entities.media)
    """
    print(f"🐦 @{TWITTER_USERNAME} X(트위터) 음총팀 피드 수집 중...")
    tweets = []

    # 1. FxTwitter API v2
    try:
        fx_api_url = f"https://api.fxtwitter.com/2/profile/{TWITTER_USERNAME}/statuses"
        fx_json_str = fetch_url(fx_api_url, timeout=8)
        if fx_json_str and fx_json_str.strip().startswith("{"):
            fx_data = json.loads(fx_json_str)
            entries = fx_data.get("results") or fx_data.get("tweets") or fx_data.get("statuses") or []
            for item in entries:
                txt = item.get("text") or item.get("full_text") or ""
                created_at = item.get("created_at") or ""
                image_urls = []

                # 이미지 미디어 추출 (FxTwitter v2 규격)
                media = item.get("media") or {}
                photos = media.get("photos", []) if isinstance(media, dict) else (media if isinstance(media, list) else [])
                if not photos and isinstance(item.get("photos"), list):
                    photos = item.get("photos")

                for p in photos:
                    if isinstance(p, dict) and p.get("url"):
                        image_urls.append(p.get("url"))
                    elif isinstance(p, str) and p.startswith("http"):
                        image_urls.append(p)

                if txt or image_urls:
                    tweets.append({
                        "text": txt,
                        "created_at": created_at,
                        "image_urls": image_urls,
                        "source": "fxtwitter_api"
                    })
            if tweets:
                print(f"✅ FxTwitter API에서 트윗 {len(tweets)}건(이미지 포함) 수집 완료")
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
                image_urls = re.findall(r'<img[^>]+src=["\'](https?://pbs\.twimg\.com/media/[^"\']+)["\']', desc)
                if not image_urls:
                    image_urls = re.findall(r'<img[^>]+src=["\'](https?://[^"\']+)["\']', desc)

                if full_txt.strip() or image_urls:
                    tweets.append({
                        "text": full_txt,
                        "image_urls": image_urls,
                        "source": "fxtwitter_rss"
                    })
            if tweets:
                print(f"✅ FxTwitter RSS에서 트윗 {len(tweets)}건 수집 완료")
                return tweets
    except Exception as ex:
        print(f"⚠️ FxTwitter RSS 조회 실패: {ex}")

    # 3. Twitter Syndication Timeline API
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
                    media_list = tweet.get("entities", {}).get("media", []) or tweet.get("photos", [])
                    image_urls = [m.get("media_url_https") or m.get("url") for m in media_list if m.get("media_url_https") or m.get("url")]

                    if text or image_urls:
                        tweets.append({
                            "text": text,
                            "created_at": created_at,
                            "image_urls": image_urls,
                            "source": "x_syndication"
                        })
                if tweets:
                    print(f"✅ X 공식 타임라인에서 트윗 {len(tweets)}건 수집 완료")
                    return tweets
            except Exception as ex:
                print(f"⚠️ Syndication JSON 파싱 오류: {ex}")

    return tweets

def parse_date_from_text(text, default_date_str=None):
    now = datetime.now()
    year = now.year

    # 1. 명시적 날짜 (YYYY-MM-DD 또는 M월 D일 / M.D)
    m_full = re.search(r"(\d{4})[.\-/ ](\d{1,2})[.\-/ ](\d{1,2})", text)
    if m_full:
        y, m, d = int(m_full.group(1)), int(m_full.group(2)), int(m_full.group(3))
        m_time = re.search(r"(\d{1,2}):(\d{2})", text)
        h, mn = (int(m_time.group(1)), int(m_time.group(2))) if m_time else (23, 59)
        return f"{y:04d}-{m:02d}-{d:02d}T{h:02d}:{mn:02d}:59", f"~{m:02d}/{d:02d} {h:02d}:{mn:02d}"

    m_month = re.search(r"(\d{1,2})월\s*(\d{1,2})일", text) or re.search(r"(?:~|\s)(\d{1,2})[./](\d{1,2})", text)
    if m_month:
        m, d = int(m_month.group(1)), int(m_month.group(2))
        m_time = re.search(r"(\d{1,2}):(\d{2})", text)
        h, mn = (int(m_time.group(1)), int(m_time.group(2))) if m_time else (23, 59)
        return f"{year:04d}-{m:02d}-{d:02d}T{h:02d}:{mn:02d}:59", f"~{m:02d}/{d:02d} {h:02d}:{mn:02d}"

    # 2. 번개 공지 시간 명시 (예: "3시간 동안", "2시간 달립니다", "~10시까지")
    m_hours = re.search(r"(\d{1,2})\s*시간\s*(?:동안|달립|집중)", text)
    if m_hours:
        duration_hrs = int(m_hours.group(1))
        exp = now + timedelta(hours=duration_hrs)
        return exp.strftime("%Y-%m-%dT%H:%M:%S"), f"~{exp.strftime('%H:%M')} ({duration_hrs}시간 번개)"

    m_until_hr = re.search(r"~(\d{1,2})시(?:\s*까지)?", text)
    if m_until_hr:
        target_hr = int(m_until_hr.group(1))
        exp = now.replace(hour=target_hr, minute=0, second=0)
        if exp < now:
            exp += timedelta(days=1)
        return exp.strftime("%Y-%m-%dT%H:%M:%S"), f"~{target_hr:02d}:00까지"

    # 3. 초단기 번개 공지 키워드 (스밍 리셋, 참여 대기 등 -> 기본 2시간 수명)
    flash_kws = ["리셋", "대기", "정각", "게릴라", "잠시 후", "지금부터"]
    if any(k in text for k in flash_kws):
        exp = now + timedelta(hours=2)
        return exp.strftime("%Y-%m-%dT%H:%M:%S"), f"~{exp.strftime('%H:%M')} (번개)"

    # 4. 컴백 활동기 상시 참여 공지 키워드 (라디오 신청, 멜론 댓글/선물 등 -> 11/20 상시)
    campaign_kws = ["라디오", "댓글", "팬톡", "음원 선물", "선물 총공", "라디오 신청"]
    if any(k in text for k in campaign_kws):
        return "2026-11-20T23:59:59", "~11/20 (활동기 상시)"

    # 5. 일반 데일리 공지 기본값: 당일 자정(23:59:59)
    if default_date_str:
        return default_date_str, "~" + default_date_str[5:10].replace("-", "/") + " " + default_date_str[11:16]
    return now.strftime("%Y-%m-%dT23:59:59"), f"~오늘 23:59"

# =====================================================================
# 1계층: 정규식 고속 패스 (Rule-based Fast Path)
# =====================================================================
def parse_rule_based_actions(tweet_text):
    cards = []

    # 1) SBS 인기가요 사전투표
    if "인기가요" in tweet_text and ("사전투표" in tweet_text or "사전 투표" in tweet_text or "LiNC" in tweet_text or "링크" in tweet_text or "사전" in tweet_text):
        end_date, badge_deadline = parse_date_from_text(tweet_text, "2026-11-06T23:59:59")
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
                    "url": LINC_DIRECT_URL,
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

    # 2) KBS 뮤직뱅크 사전투표 (쿠궁 앱)
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

    # 3) MBC 쇼! 음악중심 (뮤빗 & 뮤니버스)
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

# =====================================================================
# 2계층: AI 스마트 조립기 & 멀티모달 비전 (Gemini 1.5 Flash Vision)
# =====================================================================
def synthesize_card_with_ai(tweet_text, image_urls=None):
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None

    # 트윗 텍스트도 없고 이미지도 없으면 스킵
    if not tweet_text.strip() and not image_urls:
        return None

    # 이미지 다운로드 및 Base64 인코딩 (최대 2장까지 멀티모달 분석)
    image_parts = []
    if image_urls:
        for img_u in image_urls[:2]:
            try:
                img_req = urllib.request.Request(img_u, headers=HEADERS)
                with urllib.request.urlopen(img_req, timeout=8) as img_resp:
                    img_bytes = img_resp.read()
                    b64 = base64.b64encode(img_bytes).decode("utf-8")
                    mime = "image/png" if ".png" in img_u.lower() else "image/jpeg"
                    image_parts.append({
                        "inlineData": {
                            "mimeType": mime,
                            "data": b64
                        }
                    })
                    print(f"🖼️ [AI 멀티모달] 트윗 이미지({img_u[:45]}...) 비전 분석 대기")
            except Exception as img_err:
                print(f"⚠️ 이미지 다운로드 실패 ({img_u[:40]}...): {img_err}")

    prompt = f"""
당신은 걸그룹 RESCENE(리센느) 음원총공팀 공식 트윗을 분석하여 대시보드 카드 JSON 객체로 변환하는 전문 AI 엔진입니다.
제공된 트윗 본문 텍스트와 함께 첨부된 이미지(포스터, 카드뉴스, 시간표, 총공 안내문, 캡처 등)의 글씨(OCR) 및 시각 정보를 종합 분석하세요.

[🚫 엄격한 제외 원칙 - 아래 항목은 무조건 "null"만 반환하세요]:
1. 모금, 후원, 계좌번호, 입금 요청 공지 (대시보드 신뢰도 원칙상 절대 생성 금지)
2. 총공팀 내부 헬퍼 구인, 일손 부족, 아이디 회수/제출 등 내부 운영 공지
3. 단순 감정적 호소글, 단순 투표 독려글 (대시보드 상단 1~3순위 투표 카드로 이미 대체됨)
4. 이미 상단 배너에 있는 중복 가이드 (지니 음악나누기, FLO 응원하기, 카카오뮤직 등)
5. 단순 멤버 친목 사진이나 팬덤 참여 액션이 필요 없는 일반 글

[✅ 카드 생성 대상 및 수명(endDate) 산정 기준]:
- 팬들이 직접 무료로 참여할 수 있는 실질적인 새 미션(멜론 댓글 총공, 방송사 라디오 신청 등)만 카드로 조립합니다.
- 수명(endDate):
  • 초단기 번개 공지(스밍 리셋, 참여 대기 등): 본문에 명시된 시간 또는 발행 2시간 뒤 만료
  • 활동기 상시 참여 공지(라디오 신청, 멜론 댓글 등): 2026-11-20T23:59:59
  • 일반 데일리 이벤트: 당일 23:59:59

[JSON 스키마 규격]:
{{
  "id": "영문-하이픈-고유ID",
  "name": "간이 명칭 (예: 총공 공지, 음원 공구, 라디오 신청 등)",
  "theme": "inki|mama|melon|kb|kgma 중 택1 또는 빈문자열",
  "badgeText": "📢 배지 문구 (~마감일시)",
  "title": "카드 제목 (간결하고 명확하게)",
  "desc": "설명 및 참여 방법 (HTML <strong>, <br> 태그 허용)",
  "startDate": "YYYY-MM-DDTHH:mm:ss",
  "endDate": "YYYY-MM-DDTHH:mm:ss",
  "notice": "유의사항 또는 팁 문구",
  "actions": [
    // 아래 액션 타입 중 문맥에 맞게 1~2개 구성:
    // 1) 링크 버튼: {{"type": "primary", "label": "버튼 라벨 ↗", "url": "URL"}}
    // 2) 원본 포스터 보기: {{"type": "custom", "label": "🖼️ 공지 안내 이미지 보기 ↗", "url": "이미지URL"}}
    // 3) 해시태그/계좌 복사: {{"type": "copy", "label": "📋 필수 복사", "copyText": "#해시태그", "toast": "복사되었습니다!"}}
    // 4) 생방송 문자투표: {{"type": "sms", "label": "✉️ 문자투표", "number": "#0011", "body": "리센느"}}
  ]
}}

[분석할 트윗 본문]:
{tweet_text}

반드시 마크다운 코드블록(```json ... ```) 또는 순수 JSON 문자열로만 응답하세요.
"""

    parts = [{"text": prompt}] + image_parts

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024}
    }

    try:
        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            candidate = res_data.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text", "")
            clean_json = candidate.strip()
            if clean_json.startswith("```"):
                clean_json = re.sub(r"^```(?:json)?", "", clean_json)
                clean_json = re.sub(r"```$", "", clean_json).strip()

            if clean_json == "null" or not clean_json.startswith("{"):
                return None

            card_obj = json.loads(clean_json)
            if card_obj.get("id") and card_obj.get("title") and card_obj.get("actions"):
                print(f"✨ [AI 2계층 멀티모달] 공지 카드 자율 조립 성공: {card_obj.get('title')}")
                return card_obj
    except Exception as ex:
        print(f"⚠️ [AI 2계층 멀티모달] Gemini 호출 실패 (3계층으로 폴백): {ex}")

    return None

# =====================================================================
# 3계층: 만능 범용 레고 블록 (Universal Fail-safe Fallback)
# =====================================================================
def generate_fallback_card(tweet_text, image_urls=None):
    # 🚫 수집 제외(블랙리스트) 필터링
    # 1) 모금/계좌/기부, 2) 총공팀 내부 헬퍼 구인, 3) 단순 감정적 호소/독려글
    blacklist = ["모금", "계좌", "후원", "기부", "입금", "헬퍼", "일손", "아이디 회수", "회수하셔서", "절실합니다", "도와주세요"]
    if any(b in tweet_text for b in blacklist):
        print(f"🚫 [필터링 제외] 모금/헬퍼/운영 관련 공지 제외: {tweet_text[:30]}...")
        return None
    action_keywords = ["총공", "투표", "스밍", "다운", "해시태그", "모금", "인증", "신청", "1위", "생방", "공구", "가이드", "편성표"]
    has_action_kw = any(k in tweet_text for k in action_keywords)
    has_images = bool(image_urls)

    # 텍스트에 키워드가 없더라도 이미지가 첨부되어 있으면 공지로 간주하여 보존
    if not has_action_kw and not has_images:
        return None

    # 트윗 텍스트 해시로 고유 ID 생성
    seed_str = (tweet_text + ("_" + image_urls[0] if image_urls else "")).encode('utf-8')
    hash_id = hashlib.md5(seed_str).hexdigest()[:8]
    card_id = f"notice-{hash_id}"

    lines = [l.strip() for l in tweet_text.strip().split("\n") if l.strip()]
    first_line = lines[0][:35] if lines else ("리센느 총공팀 공지 안내" if has_images else "리센느 총공 공지")

    end_date, badge_deadline = parse_date_from_text(tweet_text, (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT23:59:59"))

    # 트윗 내 URL 및 해시태그 추출
    urls = re.findall(r'https?://[^\s]+', tweet_text)
    hashtags = re.findall(r'#[\w가-힣]+', tweet_text)

    actions = []
    if urls:
        for idx, u in enumerate(urls[:2]):
            actions.append({
                "type": "custom",
                "label": f"📱 관련 링크 열기 #{idx+1} ↗",
                "url": u,
                "style": "background: linear-gradient(135deg, #475569, #334155); color: #ffffff; border-radius: 12px; height: 44px; font-weight: 700; display:flex; align-items:center; justify-content:center; text-decoration:none;"
            })

    # 첨부 이미지가 있는 경우 원본 이미지 직행 버튼 추가
    if image_urls:
        actions.append({
            "type": "custom",
            "label": "🖼️ 총공팀 원본 포스터/안내문 보기 ↗",
            "url": image_urls[0],
            "style": "background: linear-gradient(135deg, #6366f1, #4f46e5); color: #ffffff; border-radius: 12px; height: 44px; font-weight: 700; display:flex; align-items:center; justify-content:center; text-decoration:none; box-shadow:0 2px 8px rgba(99,102,241,0.3);"
        })

    if hashtags:
        tag_str = " ".join(hashtags)
        actions.append({
            "type": "copy",
            "label": "📋 필수 해시태그 원클릭 복사",
            "copyText": tag_str,
            "toast": "해시태그가 복사되었습니다!"
        })

    if not actions:
        actions.append({
            "type": "custom",
            "label": "🐦 X(@ResceneStream) 공식 트윗 보기 ↗",
            "url": f"https://x.com/{TWITTER_USERNAME}",
            "style": "background: #0f172a; color: #ffffff; border-radius: 12px; height: 44px; font-weight: 700; display:flex; align-items:center; justify-content:center; text-decoration:none;"
        })

    desc_text = tweet_text.replace("\n", "<br>") if tweet_text.strip() else "총공팀 트윗에 안내 이미지가 첨부되어 있습니다. 아래 [원본 포스터/안내문 보기] 버튼을 눌러 확인해 주세요!"

    card = {
        "id": card_id,
        "name": "총공 공지",
        "theme": "kb",
        "customBorder": "border-top: 4px solid #6366f1; background: linear-gradient(180deg, #eef2ff 0%, #ffffff 25%);",
        "badgeText": f"📢 총공팀 실시간 공지 ({badge_deadline})",
        "badgeStyle": "background:#e0e7ff; color:#4338ca; font-weight:800;",
        "title": f"📢 {first_line}",
        "desc": desc_text,
        "startDate": datetime.now().strftime("%Y-%m-%dT00:00:00"),
        "endDate": end_date,
        "deadlineColor": "#4338ca",
        "notice": "💡 리센느 음원총공팀 피드에서 실시간으로 감지된 최신 공지입니다.",
        "actions": actions
    }
    print(f"🛡️ [범용 3계층] 레고 블록 기반 Fallback 카드 자동 생성: {card.get('title')}")
    return card

# =====================================================================
# 통합 파서 (1계층 -> 2계층(멀티모달) -> 3계층 하이브리드 파이프라인)
# =====================================================================
def parse_x_tweet_for_actions(tweet_text, image_urls=None):
    # 1계층: 정규식 고속 매칭 시도
    rule_cards = parse_rule_based_actions(tweet_text)
    if rule_cards:
        return rule_cards

    # 2계층: Gemini AI 기반 텍스트 + 이미지 멀티모달 카드 조립 시도
    ai_card = synthesize_card_with_ai(tweet_text, image_urls=image_urls)
    if ai_card:
        return [ai_card]

    # 3계층: 만능 범용 레고 블록(Fallback) 카드 생성
    fallback_card = generate_fallback_card(tweet_text, image_urls=image_urls)
    if fallback_card:
        return [fallback_card]

    return []

def log_notice_archive(header_tag, text, image_urls=None):
    if not os.path.exists(NOTICE_MD_PATH) or (not text.strip() and not image_urls):
        return False
    with open(NOTICE_MD_PATH, "r", encoding="utf-8") as f:
        md_content = f.read()

    first_line = text.strip().split("\n")[0][:40] if text.strip() else (image_urls[0] if image_urls else "")
    if first_line and first_line not in md_content:
        today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        img_section = ""
        if image_urls:
            img_section = "\n" + "\n".join(f'<p><a href="{u}"><img src="{u}" alt="공지 이미지" style="max-width:100%;" /></a></p>' for u in image_urls)

        entry = f"\n\n### 📢 [{header_tag}] ({today_str})\n{text.strip()}{img_section}\n"
        with open(NOTICE_MD_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
        return True
    return False

def main():
    print(f"🚀 RESCENE X(@{TWITTER_USERNAME}) 3계층 하이브리드 지능형 동기화 엔진 가동 (멀티모달 비전 탑재)")
    issue_body = os.environ.get("ISSUE_BODY", "")
    raw_text = issue_body if issue_body and issue_body.strip() not in ["sync", "SYNC"] else ""

    modified = False

    # 1) 모바일 이슈 본문에 공지를 직접 붙여넣었을 경우
    if raw_text:
        print("📥 모바일에서 전달된 트윗/공지 텍스트를 분석합니다.")
        # 텍스트 내 포함된 이미지 URL 추출
        extracted_imgs = re.findall(r'https?://[^\s]+\.(?:jpg|jpeg|png|webp)', raw_text, re.IGNORECASE)
        cards = parse_x_tweet_for_actions(raw_text, image_urls=extracted_imgs)
        for c in cards:
            success, status = upsert_vote_card(c)
            if success:
                modified = True

        if log_notice_archive("모바일 수집 공지", raw_text, image_urls=extracted_imgs):
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
                imgs = tw.get("image_urls", [])
                cards = parse_x_tweet_for_actions(txt, image_urls=imgs)
                for c in cards:
                    success, status = upsert_vote_card(c)
                    if success:
                        modified = True

                # 마크다운 아카이브 갱신
                if log_notice_archive(f"X(@{TWITTER_USERNAME}) 트윗 피드", txt, image_urls=imgs):
                    modified = True

    if modified:
        print("✨ X(@ResceneStream) 피드에서 변동/신규 공지를 감지하여 대시보드에 성공적으로 반영했습니다! (PR 생성 예정)")
    else:
        print("ℹ️ X(@ResceneStream) 피드 기준 이미 최신 상태이며 새로운 변동 사항이 없습니다.")

if __name__ == "__main__":
    main()
