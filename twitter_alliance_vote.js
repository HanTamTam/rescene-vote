/**
 * 𝕏 (Twitter) MAMA Vote & Alliance Certification Handler
 * - 리센느 투표 해시태그 + 연합팀 5개 해시태그 원클릭 트윗 작성 및 복사
 */

const MAMA_ALLIANCE_TAGS = [
  '#2026MAMAVOTE',
  '#rescene',
  '#리마인X앨리즈',
  '#리마인X앤클로',
  '#리마인과함께_븨아피',
  '#REMINEXS2U',
  '#리마인X몬스티즈'
];

function getTwitterIntentUrl() {
  const text = MAMA_ALLIANCE_TAGS.join('\n');
  return `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`;
}

function openTwitterAllianceVote() {
  window.open(getTwitterIntentUrl(), '_blank');
}

function copyAllAllianceTags() {
  const text = MAMA_ALLIANCE_TAGS.join('\n');
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      alert('연합 해시태그 6종이 복사되었습니다! 트위터에 붙여넣어 인증하세요.');
    });
  } else {
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    alert('연합 해시태그 6종이 복사되었습니다! 트위터에 붙여넣어 인증하세요.');
  }
}
