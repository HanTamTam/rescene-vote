/**
 * 📅 RESCENE Voting Schedule & Gantt Controller
 * - 요일별 투표 일정 & 오늘 할 일 렌더링
 * - 주간 음악방송 간트 표의 생방송 시간 표시 및 오늘 요일 동적 하이라이트
 */

const daySchedules = {
  0: [ // 일요일
    { title: "✨ [연합] AAA 이세계아이돌 투표 & 아챔 루비 룰렛", time: "상시 (~11/04)", desc: "아챔샵 룰렛 10회 + 6시간 간격 분할 투표로 룰렛 페이백 극대화!", urgent: "urgent-aaa", url: "https://rescene.stream/go/aaa" },
    { title: "멜론 MMA TOP10 투표", time: "상시 (~10/29)", desc: "스밍권 보유 3표 / 미보유 1표 행사", urgent: "", url: "https://kko.to/RFUMpSDfsk" },
    { title: "카카오뱅크 모두의 스타상", time: "상시 (~10/30)", desc: "카뱅 원링크 1일 1회 (혜택 ➔ 아래로 스크롤)", urgent: "", url: "https://kakaobank.onelink.me/0qMi/p3ifhx4u" },
    { title: "SBS 인기가요 생방송", time: "15:30 방송", desc: "SuperStar X 앱 실시간 투표 & 공식 온에어 시청", urgent: "", url: "https://superstarx.io/" }
  ],
  1: [ // 월요일
    { title: "✨ [연합] AAA 이세계아이돌 투표 & 아챔 루비 룰렛", time: "상시 (~11/04)", desc: "아챔샵 룰렛 10회 + 6시간 간격 분할 투표로 룰렛 페이백 극대화!", urgent: "urgent-aaa", url: "https://rescene.stream/go/aaa" },
    { title: "멜론 MMA TOP10 투표", time: "상시 (~10/29)", desc: "스밍권 보유 3표 / 미보유 1표 행사", urgent: "", url: "https://kko.to/RFUMpSDfsk" },
    { title: "카카오뱅크 모두의 스타상", time: "상시 (~10/30)", desc: "카뱅 원링크 1일 1회 (80% 반영)", urgent: "", url: "https://kakaobank.onelink.me/0qMi/p3ifhx4u" },
    { title: "엠카운트다운 사전투표 마감", time: "오전 10:00 마감", desc: "엠넷플러스 보유 표 전량 투표", urgent: "", url: "https://www.mnetplus.world/" },
    { title: "더 쇼 & 쇼챔 사전투표 마감", time: "오후 14:00 마감", desc: "스타플래닛 & 아챔 마감 전 투표", urgent: "", url: "https://play.google.com/store/apps/details?id=com.nwz.ichampclient" }
  ],
  2: [ // 화요일
    { title: "✨ [연합] AAA 이세계아이돌 투표 & 아챔 루비 룰렛", time: "상시 (~11/04)", desc: "아챔샵 룰렛 10회 + 6시간 간격 분할 투표로 룰렛 페이백 극대화!", urgent: "urgent-aaa", url: "https://rescene.stream/go/aaa" },
    { title: "멜론 MMA TOP10 투표", time: "상시 (~10/29)", desc: "스밍권 보유 3표 / 미보유 1표 행사", urgent: "", url: "https://kko.to/RFUMpSDfsk" },
    { title: "카카오뱅크 모두의 스타상", time: "상시 (~10/30)", desc: "카뱅 원링크 1일 1회 참여", urgent: "", url: "https://kakaobank.onelink.me/0qMi/p3ifhx4u" },
    { title: "더 쇼 생방송 실시간 투표", time: "18:05 ~ 19:00", desc: "스타플래닛 실시간 투표 & 유튜브 THE K-POP 시청", urgent: "", url: "https://play.google.com/store/apps/details?id=inc.rowem.passicon" },
    { title: "음악중심 사전투표 오픈", time: "18:00 오픈", desc: "뮤빗 앱에서 음중 사전투표 시작", urgent: "", url: "https://mubeat.tv/" }
  ],
  3: [ // 수요일 (오늘 10/21)
    { title: "🚨 MAMA 1차 투표 (내일 마감!)", time: "~10/22 23:59 마감", desc: "엠넷플러스 앱 1일 1계정 투표 + 𝕏 트윗 필수!", urgent: "urgent-mama", url: "https://mnetplus.world/event/2026-mama?deeplink=mnetplus%3A%2F%2Fvote%2Ftemplates%2Fmama-fans-choice-vote-r2-v2%2F6acecda6f3778e1b06f5170b%3Furl_fallback_type%3Dupdate&missionType=MAMA_2026_FANS_CHOICE_VOTE_2ND_SHARE&refererCode=" },
    { title: "✨ [연합] AAA 이세계아이돌 투표 & 아챔 루비 룰렛", time: "상시 (~11/04)", desc: "아챔샵 룰렛 10회 + 6시간 간격 분할 투표로 룰렛 페이백 극대화!", urgent: "urgent-aaa", url: "https://rescene.stream/go/aaa" },
    { title: "멜론 MMA TOP10 투표", time: "상시 (~10/29)", desc: "스밍권 3표 / 미보유 1표 행사", urgent: "", url: "https://kko.to/RFUMpSDfsk" },
    { title: "카카오뱅크 모두의 스타상", time: "상시 (~10/30)", desc: "카뱅 원링크 1일 1회 (혜택 ➔ 아래로 스크롤)", urgent: "", url: "https://kakaobank.onelink.me/0qMi/p3ifhx4u" },
    { title: "쇼! 챔피언 생방송", time: "17:00 방송", desc: "MBC M 생방송 응원 & 유튜브 ALL THE K-POP 시청", urgent: "", url: "https://play.google.com/store/apps/details?id=com.nwz.ichampclient" },
    { title: "뮤직뱅크 사전투표 마감", time: "오전 11:00 마감", desc: "올차트 앱 K-차트 사전투표 마감 전 투표", urgent: "", url: "https://play.google.com/store/apps/details?id=com.smtn.allstarsolutions" }
  ],
  4: [ // 목요일 (내일 10/22 마감일!)
    { title: "🚨 MAMA 1차 투표 오늘 밤 최종 마감!!", time: "오늘 밤 23:59 마감", desc: "오늘 밤 11시 59분에 마감됩니다! 앱+트위터 전량 완료", urgent: "urgent-mama", url: "https://mnetplus.world/event/2026-mama?deeplink=mnetplus%3A%2F%2Fvote%2Ftemplates%2Fmama-fans-choice-vote-r2-v2%2F6acecda6f3778e1b06f5170b%3Furl_fallback_type%3Dupdate&missionType=MAMA_2026_FANS_CHOICE_VOTE_2ND_SHARE&refererCode=" },
    { title: "✨ [연합] AAA 이세계아이돌 투표 & 아챔 루비 룰렛", time: "상시 (~11/04)", desc: "아챔샵 룰렛 10회 + 6시간 간격 분할 투표로 룰렛 페이백 극대화!", urgent: "urgent-aaa", url: "https://rescene.stream/go/aaa" },
    { title: "멜론 MMA TOP10 투표", time: "상시 (~10/29)", desc: "스밍권 3표 / 미보유 1표 행사", urgent: "", url: "https://kko.to/RFUMpSDfsk" },
    { title: "카카오뱅크 모두의 스타상", time: "상시 (~10/30)", desc: "카뱅 원링크 1일 1회 투표", urgent: "", url: "https://kakaobank.onelink.me/0qMi/p3ifhx4u" },
    { title: "음악중심 사전투표 마감", time: "오전 11:00 마감", desc: "뮤빗 앱 음중 사전투표 마감", urgent: "", url: "https://mubeat.tv/" },
    { title: "엠카운트다운 생방 투표", time: "18:00 ~ 19:00", desc: "엠넷플러스 실시간 투표 & 티빙 온에어 시청", urgent: "", url: "https://www.mnetplus.world/" }
  ],
  5: [ // 금요일
    { title: "✨ [연합] AAA 이세계아이돌 투표 & 아챔 루비 룰렛", time: "상시 (~11/04)", desc: "아챔샵 룰렛 10회 + 6시간 간격 분할 투표로 룰렛 페이백 극대화!", urgent: "urgent-aaa", url: "https://rescene.stream/go/aaa" },
    { title: "멜론 MMA TOP10 투표", time: "상시 (~10/29)", desc: "스밍권 3표 / 미보유 1표 행사", urgent: "", url: "https://kko.to/RFUMpSDfsk" },
    { title: "카카오뱅크 모두의 스타상", time: "상시 (~10/30)", desc: "카뱅 원링크 1일 1회 투표", urgent: "", url: "https://kakaobank.onelink.me/0qMi/p3ifhx4u" },
    { title: "뮤직뱅크 생방송", time: "17:05 방송", desc: "KBS2 본방송 & 공식 온에어 시청(시청률 반영)", urgent: "", url: "https://onair.kbs.co.kr/index.html?sname=onair&stype=live&ch_code=12" },
    { title: "엠카 차주 사전투표 오픈", time: "14:00 오픈", desc: "엠넷플러스 다음 주 사전투표 시작", urgent: "", url: "https://www.mnetplus.world/" },
    { title: "더 쇼 & 쇼챔 사전투표 동시 오픈", time: "20:00 오픈", desc: "스타플래닛 & 아챔 사전투표 오픈", urgent: "", url: "https://play.google.com/store/apps/details?id=com.nwz.ichampclient" }
  ],
  6: [ // 토요일
    { title: "✨ [연합] AAA 이세계아이돌 투표 & 아챔 루비 룰렛", time: "상시 (~11/04)", desc: "아챔샵 룰렛 10회 + 6시간 간격 분할 투표로 룰렛 페이백 극대화!", urgent: "urgent-aaa", url: "https://rescene.stream/go/aaa" },
    { title: "멜론 MMA TOP10 투표", time: "상시 (~10/29)", desc: "스밍권 3표 / 미보유 1표 행사", urgent: "", url: "https://kko.to/RFUMpSDfsk" },
    { title: "카카오뱅크 모두의 스타상", time: "상시 (~10/30)", desc: "카뱅 원링크 1일 1회 참여 (80% 반영)", urgent: "", url: "https://kakaobank.onelink.me/0qMi/p3ifhx4u" },
    { title: "쇼! 음악중심 생방 실시간", time: "15:15 ~ 16:15", desc: "뮤빗 앱 + 문자투표(#0505) & MBC 온에어 시청", urgent: "", url: "https://mubeat.tv/" }
  ]
};

function renderDayTasks(dayIdx) {
  const container = document.getElementById("day-tasks-container");
  if (!container) return;
  const list = daySchedules[dayIdx] || [];
  let html = "";

  list.forEach(item => {
    if (item.cancelled) {
      html += `
        <div class="mini-task-item" style="opacity: 0.7; background: #f1f5f9; border-left: 3px solid #94a3b8;">
          <div class="mini-task-header">
            <span class="mini-task-title" style="color: #64748b; text-decoration: line-through;">${item.title}</span>
            <span class="mini-task-time" style="color: #ef4444; font-weight: 700; background: #fee2e2; padding: 2px 6px; border-radius: 4px;">결방</span>
          </div>
          <p class="mini-task-desc" style="color: #64748b;">${item.desc}</p>
        </div>
      `;
    } else {
      html += `
        <div class="mini-task-item ${item.urgent || ''}">
          <div class="mini-task-header">
            <span class="mini-task-title">${item.title}</span>
            <span class="mini-task-time">${item.time}</span>
          </div>
          <p class="mini-task-desc">${item.desc}</p>
        </div>
      `;
    }
  });

  container.innerHTML = html;
}

function setDay(dayIdx) {
  const buttons = document.querySelectorAll(".day-pill-btn");
  buttons.forEach((btn, idx) => {
    const bDay = [1, 2, 3, 4, 5, 6, 0][idx];
    if (bDay === dayIdx) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  renderDayTasks(dayIdx);
}
