/**
 * 📅 RESCENE Voting Schedule & Gantt Controller
 * - 요일별 투표 일정 & 오늘 할 일 렌더링
 * - 주간 음악방송 간트 표의 생방송 시간 표시 및 오늘 요일 동적 하이라이트
 */

const daySchedules = {
  0: [ // 일요일
    { title: "🚨 KGMA 베리즈 투표 (마감 D-2)", time: "~10/20 마감", desc: "베리즈 링크 매일 1표 행사!", urgent: "urgent-kgma", url: "https://link.berriz.in/ko/web/main/vote/2026kgma/" },
    { title: "MAMA 앱 90% + 트위터 RT 10%", time: "~10/22 마감", desc: "엠넷플러스 투표 및 트위터 #2026MAMAVOTE 글 RT!", urgent: "urgent-mama", url: "https://www.mnetplus.world/event/ko/2026-mama?deeplink=mnetplus%3A%2F%2Fvote%2Ftemplates%2Fmama-fans-choice-vote-r1%2F6ab09532c314bb17315adc4e" },
    { title: "카카오뱅크 모두의 스타상", time: "상시 (~10/30)", desc: "카뱅 원링크 1일 1회 (80% 반영)", urgent: "", url: "https://kakaobank.onelink.me/0qMi/p3ifhx4u" },
    { title: "멜론 MMA TOP10 투표", time: "상시 (~10/29)", desc: "유료 3표 / 무료 1표 행사", urgent: "", url: "https://m2.melon.com/mma/2026/vote/top10/" },
    { title: "SBS 인기가요 생방송 투표", time: "15:30 ~ 16:30", desc: "SuperStar X 앱 실시간 투표", urgent: "", url: "https://superstarx.io/" }
  ],
  1: [ // 월요일
    { title: "🚨 KGMA 베리즈 투표 (마감 D-1)", time: "~10/20 마감", desc: "베리즈 링크 매일 1표 행사!", urgent: "urgent-kgma", url: "https://link.berriz.in/ko/web/main/vote/2026kgma/" },
    { title: "MAMA 앱 90% + 트위터 RT 10%", time: "~10/22 마감", desc: "엠넷플러스 투표 및 트위터 RT!", urgent: "urgent-mama", url: "https://www.mnetplus.world/event/ko/2026-mama?deeplink=mnetplus%3A%2F%2Fvote%2Ftemplates%2Fmama-fans-choice-vote-r1%2F6ab09532c314bb17315adc4e" },
    { title: "카카오뱅크 모두의 스타상", time: "상시 (~10/30)", desc: "카뱅 원링크 1일 1회 (80% 반영)", urgent: "", url: "https://kakaobank.onelink.me/0qMi/p3ifhx4u" },
    { title: "멜론 MMA TOP10 투표", time: "상시 (~10/29)", desc: "유료 3표 / 무료 1표 행사", urgent: "", url: "https://m2.melon.com/mma/2026/vote/top10/" },
    { title: "엠카운트다운 사전투표 마감", time: "오전 10:00 마감", desc: "엠넷플러스 보유 표 전량 투표", urgent: "", url: "https://www.mnetplus.world/event/ko/2026-mama?deeplink=mnetplus%3A%2F%2Fvote%2Ftemplates%2Fmama-fans-choice-vote-r1%2F6ab09532c314bb17315adc4e" },
    { title: "더 쇼 & 쇼챔 사전투표 마감", time: "오후 14:00 마감", desc: "스타플래닛 & 아챔 마감 전 투표", urgent: "", url: "https://play.google.com/store/apps/details?id=com.nwz.ichampclient" }
  ],
  2: [ // 화요일
    { title: "🚨 KGMA 베리즈 투표 오늘 최종 마감!!", time: "오늘 23:59 마감", desc: "오늘 밤 마감됩니다! 베리즈 매일 1표 필수", urgent: "urgent-kgma", url: "https://link.berriz.in/ko/web/main/vote/2026kgma/" },
    { title: "MAMA 앱 90% + 트위터 RT 10%", time: "~10/22 마감", desc: "엠넷플러스 투표 및 트위터 RT!", urgent: "urgent-mama", url: "https://www.mnetplus.world/event/ko/2026-mama?deeplink=mnetplus%3A%2F%2Fvote%2Ftemplates%2Fmama-fans-choice-vote-r1%2F6ab09532c314bb17315adc4e" },
    { title: "카카오뱅크 모두의 스타상", time: "상시 (~10/30)", desc: "카뱅 원링크 1일 1회", urgent: "", url: "https://kakaobank.onelink.me/0qMi/p3ifhx4u" },
    { title: "더 쇼 생방송 실시간 투표", time: "18:05 ~ 19:00", desc: "스타플래닛 실시간 투표", urgent: "", url: "https://play.google.com/store/apps/details?id=inc.rowem.passicon" },
    { title: "음악중심 사전투표 오픈", time: "18:00 오픈", desc: "뮤빗 앱에서 음중 사전투표 시작", urgent: "", url: "https://mubeat.tv/" }
  ],
  3: [ // 수요일
    { title: "MAMA 앱 90% + 트위터 RT 10% (내일 마감)", time: "~10/22 마감", desc: "엠넷플러스 투표 및 트위터 RT!", urgent: "urgent-mama", url: "https://www.mnetplus.world/event/ko/2026-mama?deeplink=mnetplus%3A%2F%2Fvote%2Ftemplates%2Fmama-fans-choice-vote-r1%2F6ab09532c314bb17315adc4e" },
    { title: "카카오뱅크 모두의 스타상", time: "상시 (~10/30)", desc: "카뱅 원링크 1일 1회", urgent: "", url: "https://kakaobank.onelink.me/0qMi/p3ifhx4u" },
    { title: "쇼! 챔피언 생방송", time: "17:00 방송", desc: "MBC M 생방송 무대 응원", urgent: "", url: "https://play.google.com/store/apps/details?id=com.nwz.ichampclient" },
    { title: "뮤직뱅크 사전투표 마감", time: "오전 11:00 마감", desc: "올차트/뮤빗 마감 전 확인", urgent: "", url: "https://mubeat.tv/" }
  ],
  4: [ // 목요일
    { title: "🚨 MAMA 1차 투표 오늘 최종 마감!", time: "오늘 밤 23:59 마감", desc: "오늘 밤 11시 59분에 마감됩니다! 앱+트위터 모두 완료", urgent: "urgent-mama", url: "https://www.mnetplus.world/event/ko/2026-mama?deeplink=mnetplus%3A%2F%2Fvote%2Ftemplates%2Fmama-fans-choice-vote-r1%2F6ab09532c314bb17315adc4e" },
    { title: "카카오뱅크 모두의 스타상", time: "상시 (~10/30)", desc: "카뱅 원링크 1일 1회 투표", urgent: "", url: "https://kakaobank.onelink.me/0qMi/p3ifhx4u" },
    { title: "음악중심 사전투표 마감", time: "오전 11:00 마감", desc: "뮤빗 앱 음중 사전투표 마감", urgent: "", url: "https://mubeat.tv/" },
    { title: "엠카운트다운 생방 투표", time: "18:00 ~ 19:00", desc: "엠넷플러스 실시간 투표", urgent: "", url: "https://www.mnetplus.world/event/ko/2026-mama?deeplink=mnetplus%3A%2F%2Fvote%2Ftemplates%2Fmama-fans-choice-vote-r1%2F6ab09532c314bb17315adc4e" }
  ],
  5: [ // 금요일
    { title: "카카오뱅크 모두의 스타상 마감일!", time: "~10/30 최종마감", desc: "카뱅 원링크 1일 1회 투표", urgent: "", url: "https://kakaobank.onelink.me/0qMi/p3ifhx4u" },
    { title: "엠카 차주 사전투표 오픈", time: "14:00 오픈", desc: "엠넷플러스 다음 주 사전투표 시작", urgent: "", url: "https://www.mnetplus.world/event/ko/2026-mama?deeplink=mnetplus%3A%2F%2Fvote%2Ftemplates%2Fmama-fans-choice-vote-r1%2F6ab09532c314bb17315adc4e" },
    { title: "더 쇼 & 쇼챔 사전투표 동시 오픈", time: "20:00 오픈", desc: "스타플래닛 & 아챔 사전투표 오픈", urgent: "", url: "https://play.google.com/store/apps/details?id=com.nwz.ichampclient" }
  ],
  6: [ // 토요일
    { title: "🚨 KGMA 베리즈 투표 (마감 D-3)", time: "~10/20 마감", desc: "베리즈 링크 매일 1표 행사!", urgent: "urgent-kgma", url: "https://link.berriz.in/ko/web/main/vote/2026kgma/" },
    { title: "MAMA 1차 투표 (마감 D-5)", time: "~10/22 마감", desc: "엠넷플러스 앱 투표 90% + 트위터 RT 10%!", urgent: "urgent-mama", url: "https://www.mnetplus.world/event/ko/2026-mama?deeplink=mnetplus%3A%2F%2Fvote%2Ftemplates%2Fmama-fans-choice-vote-r1%2F6ab09532c314bb17315adc4e" },
    { title: "카카오뱅크 모두의 스타상", time: "상시 (~10/30)", desc: "카뱅 원링크 1일 1회 참여 (80% 반영)", urgent: "", url: "https://kakaobank.onelink.me/0qMi/p3ifhx4u" },
    { title: "멜론 MMA TOP10 투표", time: "상시 (~10/29)", desc: "유료 3표 / 무료 1표 행사", urgent: "", url: "https://m2.melon.com/mma/2026/vote/top10/" },
    { title: "쇼! 음악중심 생방 실시간", time: "15:15 ~ 16:15", desc: "뮤빗 앱 + 문자투표(#0505)", urgent: "", url: "https://mubeat.tv/" }
  ]
};

function renderDayTasks(dayIdx) {
  const container = document.getElementById("day-tasks-container");
  if (!container) return;
  const list = daySchedules[dayIdx] || [];
  let html = "";

  list.forEach(item => {
    html += `
      <div class="mini-task-item ${item.urgent || ''}">
        <div class="mini-task-header">
          <span class="mini-task-title">${item.title}</span>
          <span class="mini-task-time">${item.time}</span>
        </div>
        <p class="mini-task-desc">${item.desc}</p>
      </div>
    `;
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
