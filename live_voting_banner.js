/**
 * 🔴 RESCENE Live Voting Smart Banner Controller
 * - 방송 1시간 전: 비활성화(Disabled) 예고 배너 + 시작 카운트다운 노출
 * - 방송 진행 중: 빨간색 네온 펄스 애니메이션 + 활성화된 다이렉트 투표 버튼 노출
 * - 방송 종료 후: 배너 자동 제거(숨김)
 */

const liveVoteSchedules = [
  {
    day: 2, // 화요일
    name: "SBS M 더 쇼 (THE SHOW)",
    app: "스타플래닛 (Star Planet)",
    url: "https://play.google.com/store/apps/details?id=inc.rowem.passicon",
    previewStart: 17 * 60 + 5, // 17:05
    liveStart: 18 * 60 + 5,    // 18:05
    liveEnd: 19 * 60,          // 19:00
    tip: "1위 후보 진입 시 스타플래닛 앱에서 실시간 투표에 참여해 주세요!"
  },
  {
    day: 3, // 수요일
    name: "MBC M 쇼! 챔피언",
    app: "아이돌챔프",
    url: "https://m.idolchamp.com/",
    previewStart: 16 * 60,     // 16:00
    liveStart: 17 * 60,        // 17:00
    liveEnd: 18 * 60,          // 18:00
    tip: "사전투표 점수가 반영된 생방송 1위 발표 및 실시간 무대 응원!"
  },
  {
    day: 4, // 목요일
    name: "Mnet 엠카운트다운",
    app: "엠넷플러스 (Mnet Plus)",
    url: "https://www.mnetplus.world/",
    previewStart: 17 * 60,     // 17:00
    liveStart: 18 * 60,        // 18:00
    liveEnd: 19 * 60,          // 19:00
    tip: "1위 후보 진입 시 엠넷플러스 앱에서 1인 1회 실시간 투표 오픈!"
  },
  {
    day: 6, // 토요일
    name: "MBC 쇼! 음악중심",
    app: "뮤빗 (Mubeat) & 문자투표",
    url: "https://mubeat.tv/",
    previewStart: 14 * 60 + 15, // 14:15
    liveStart: 15 * 60 + 15,    // 15:15
    liveEnd: 16 * 60 + 15,      // 16:15
    tip: "1위 후보 진입 시 뮤빗 앱 실시간 투표 + 문자투표(#0505) 동시 참여!"
  },
  {
    day: 0, // 일요일
    name: "SBS 인기가요",
    app: "SuperStar X",
    url: "https://superstarx.io/",
    previewStart: 14 * 60 + 30, // 14:30
    liveStart: 15 * 60 + 30,    // 15:30
    liveEnd: 16 * 60 + 30,      // 16:30
    tip: "1위 후보 진입 시 SuperStar X 앱 실시간 투표 참여!",
    isCancelled: true,
    cancelReason: "야구 포스트시즌 중계로 인한 결방 (10/18)"
  }
];

function checkLiveBroadcastBanner() {
  const bannerContainer = document.getElementById("live-broadcast-banner");
  if (!bannerContainer) return;

  const now = new Date();
  const currentDayOfWeek = now.getDay();
  const currentMinutes = now.getHours() * 60 + now.getMinutes();
  const currentSeconds = now.getSeconds();

  const show = liveVoteSchedules.find(s => s.day === currentDayOfWeek);

  if (!show) {
    bannerContainer.innerHTML = "";
    return;
  }

  // 0) 방송 결방(Cancelled) 상태인 경우 -> 비활성화(Disabled) 결방 배너 안내
  if (show.isCancelled) {
    if (currentMinutes >= show.previewStart && currentMinutes < (show.liveEnd + 60)) {
      bannerContainer.innerHTML = `
        <div class="live-banner-card" style="background: #f1f5f9; border: 2px dashed #94a3b8; color: #475569;">
          <div class="live-header-row">
            <span class="live-badge" style="background: #e2e8f0; color: #475569; font-weight: 800;">🚫 방송 결방 안내</span>
            <span class="live-timer" style="color: #64748b; font-weight: 700;">10/18(일) 생방송 없음</span>
          </div>
          <div>
            <h3 class="live-title" style="color: #334155; font-size: 17px; font-weight: 800;">📺 ${show.name} 결방 (${show.cancelReason || '중계 편성'})</h3>
            <p class="live-desc" style="color: #64748b; font-size: 13px;">오늘(10/18) SBS 인기가요는 프로야구 포스트시즌 중계로 인해 결방되어 실시간 생방송 투표가 진행되지 않습니다.</p>
          </div>
          <button class="btn-live-action disabled" style="background: #e2e8f0; color: #94a3b8; cursor: not-allowed; border: none; font-weight: 800; pointer-events: none;">
            ⛔ 오늘 생방송 투표 미진행 (결방)
          </button>
        </div>
      `;
      return;
    } else {
      bannerContainer.innerHTML = "";
      return;
    }
  }

  // 1) 방송 1시간 전 예고 상태 (Disabled)
  if (currentMinutes >= show.previewStart && currentMinutes < show.liveStart) {
    const remainingSec = (show.liveStart * 60) - (currentMinutes * 60 + currentSeconds);
    const mins = Math.floor(remainingSec / 60);
    const secs = remainingSec % 60;
    const timeStr = `${mins}분 ${secs < 10 ? '0' : ''}${secs}초`;

    bannerContainer.innerHTML = `
      <div class="live-banner-card live-preview-mode">
        <div class="live-header-row">
          <span class="live-badge preview">⏳ 생방 1시간 전 예고</span>
          <span class="live-timer">시작까지 ${timeStr}</span>
        </div>
        <div>
          <h3 class="live-title">${show.name} 실시간 투표 대기 중</h3>
          <p class="live-desc">투표 앱: ${show.app} · ${show.tip}</p>
        </div>
        <button class="btn-live-action disabled">
          🔒 생방송 시작 시 활성화됩니다 (${Math.floor(show.liveStart/60)}:${show.liveStart%60 < 10 ? '0': ''}${show.liveStart%60} 오픈)
        </button>
      </div>
    `;
  }
  // 2) 생방송 진행 중 상태 (Active)
  else if (currentMinutes >= show.liveStart && currentMinutes < show.liveEnd) {
    const remainingSec = (show.liveEnd * 60) - (currentMinutes * 60 + currentSeconds);
    const mins = Math.floor(remainingSec / 60);
    const secs = remainingSec % 60;
    const timeStr = `${mins}분 ${secs < 10 ? '0' : ''}${secs}초`;

    bannerContainer.innerHTML = `
      <div class="live-banner-card live-active-mode">
        <div class="live-header-row">
          <span class="live-badge active"><span class="dot"></span> LIVE 투표 진행 중!</span>
          <span class="live-timer">마감까지 ${timeStr}</span>
        </div>
        <div>
          <h3 class="live-title">🔥 ${show.name} 1위 후보 실시간 투표 오픈!</h3>
          <p class="live-desc">지금 바로 투표에 참여해 리센느에게 힘을 보태주세요! (${show.tip})</p>
        </div>
        <a href="${show.url}" target="_blank" class="btn-live-action enabled">
          지금 바로 실시간 투표하기 ↗
        </a>
      </div>
    `;
  }
  // 3) 그 외 시간대 (방송 전 또는 종료 후): 자동 숨김
  else {
    bannerContainer.innerHTML = "";
  }
}

// 1초 간격 실시간 모니터링 시작
setInterval(checkLiveBroadcastBanner, 1000);
document.addEventListener("DOMContentLoaded", checkLiveBroadcastBanner);
