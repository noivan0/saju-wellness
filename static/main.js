const API = '';  // 같은 도메인

// ═══════════════════════════════════════════════════════════
// 사주담 인라인 데이터 (pillar_data.js 인라인 포함)
// ═══════════════════════════════════════════════════════════

// ─────────────────────────────────────────────────────────
// 일주별 해석 데이터 (22개 주요 일주)
// ─────────────────────────────────────────────────────────
const PILLAR_INTERPRETATIONS = {
  '갑자': {
    element: '木水',
    personality: '독립적이고 창의적인 기질. 새로운 것을 시작하는 힘이 강하며, 맑고 직선적인 성정을 지닙니다.',
    strengths: ['강한 추진력과 리더십', '창의적 사고와 기획력', '직관적 판단력'],
    challenges: ['고집이 강해 타협이 어려울 수 있음', '시작은 잘 하지만 마무리에 주의 필요'],
    today_advice: '새로운 아이디어를 실행에 옮기기 좋은 날입니다. 결단이 필요한 일을 시작하세요.',
    compatible: ['병오', '무오', '임오'],
    career: '기획, 창업, 리더십이 필요한 분야, 예술, 교육'
  },
  '을축': {
    element: '木土',
    personality: '온화하고 꾸준한 기질. 안정적인 환경에서 능력을 발휘하며 사람들의 신뢰를 얻습니다.',
    strengths: ['꾸준하고 성실한 노력', '타인을 배려하는 따뜻함', '현실적이고 실용적인 판단'],
    challenges: ['변화에 적응이 느릴 수 있음', '자기 주장을 드러내는 것을 어려워함'],
    today_advice: '차분하게 기초를 다지는 날입니다. 중요한 계획을 꼼꼼히 점검하세요.',
    compatible: ['기사', '신사', '계사'],
    career: '농업, 요리, 부동산, 의료, 행정, 교육'
  },
  '병인': {
    element: '火木',
    personality: '열정적이고 진취적인 기질. 사람을 끌어당기는 카리스마와 따뜻한 에너지를 가집니다.',
    strengths: ['강렬한 열정과 행동력', '넓은 인맥과 사교성', '솔직하고 명쾌한 표현력'],
    challenges: ['감정 기복이 있을 수 있음', '너무 앞서 나가다 주변과 마찰'],
    today_advice: '사람들과 교류하고 아이디어를 나누기 좋은 날입니다. 협업 제안에 열린 자세를 취하세요.',
    compatible: ['갑자', '임자', '경자'],
    career: '마케팅, 방송, 엔터테인먼트, 리더십, 스포츠'
  },
  '정묘': {
    element: '火木',
    personality: '섬세하고 감성적인 기질. 예술적 감각이 뛰어나며 내면의 직관이 강합니다.',
    strengths: ['예민한 감성과 예술성', '배려심이 깊고 공감능력 탁월', '창의적 표현력'],
    challenges: ['과민 반응으로 감정 소모가 큼', '결정이 느려질 때가 있음'],
    today_advice: '감성적인 작업이나 예술적 표현에 집중하기 좋습니다. 내면의 소리에 귀 기울이세요.',
    compatible: ['갑자', '을해', '계해'],
    career: '예술, 디자인, 상담, 음악, 글쓰기'
  },
  '무진': {
    element: '土土',
    personality: '든든하고 포용력 있는 기질. 중심을 잡아주는 안정적인 성격으로 신뢰받습니다.',
    strengths: ['강한 책임감과 지구력', '포용력과 리더십', '큰 그림을 보는 시야'],
    challenges: ['고집이 세고 변화를 거부하는 경향', '자기 희생으로 번아웃 주의'],
    today_advice: '오늘은 중요한 결정을 위한 기반을 다지기 좋습니다. 장기 목표를 재점검하세요.',
    compatible: ['갑자', '갑오', '임자'],
    career: '경영, 부동산, 건설, 행정, 종교, 교육 관리직'
  },
  '기사': {
    element: '土火',
    personality: '세심하고 분석적인 기질. 꼼꼼한 계획력과 실행력으로 목표를 달성합니다.',
    strengths: ['섬세한 분석력과 계획성', '성실하고 책임감 강함', '인내심이 뛰어남'],
    challenges: ['완벽주의로 인한 스트레스', '타인의 평가에 예민함'],
    today_advice: '세부 사항을 점검하고 계획을 정리하기 좋은 날입니다. 한 가지에 집중하세요.',
    compatible: ['갑자', '갑인', '임자'],
    career: '회계, 법률, 의료, 연구, 편집, 행정'
  },
  '경오': {
    element: '金火',
    personality: '결단력 있고 화려한 기질. 강인한 의지와 명확한 목적의식으로 성공을 추구합니다.',
    strengths: ['강한 의지력과 결단력', '명확한 목표 설정', '카리스마와 자신감'],
    challenges: ['독선적으로 보일 수 있음', '유연성이 부족할 때가 있음'],
    today_advice: '중요한 결정이나 협상에 자신감 있게 임하세요. 직진하는 에너지가 강합니다.',
    compatible: ['을해', '계해', '정해'],
    career: '군인, 경찰, 법률, 금융, 스포츠, 경영'
  },
  '신미': {
    element: '金土',
    personality: '우아하고 섬세한 기질. 미적 감각과 완성도에 대한 높은 기준을 가집니다.',
    strengths: ['세련된 미적 감각', '섬세한 소통 능력', '온화하고 외교적'],
    challenges: ['완벽주의가 과해 스트레스 유발', '결단이 느릴 수 있음'],
    today_advice: '아름다운 것에 집중하고 세련된 마무리를 추구하세요. 디테일이 빛나는 날입니다.',
    compatible: ['병오', '무오', '갑오'],
    career: '패션, 미용, 예술, 외교, 비서, 의료미용'
  },
  '임신': {
    element: '水金',
    personality: '지혜롭고 분석적인 기질. 깊이 생각하고 전략적으로 움직이는 능력이 탁월합니다.',
    strengths: ['뛰어난 분석력과 전략적 사고', '유연한 적응력', '다방면에 걸친 지식욕'],
    challenges: ['생각이 너무 많아 결단이 늦음', '감정 표현이 서투를 수 있음'],
    today_advice: '깊이 생각하고 전략을 세우기 좋은 날입니다. 데이터와 정보를 분석하세요.',
    compatible: ['경자', '무자', '갑자'],
    career: 'IT, 연구, 전략기획, 금융, 컨설팅'
  },
  '계유': {
    element: '水金',
    personality: '조용하고 깊은 기질. 내면의 통찰력과 날카로운 직관으로 핵심을 꿰뚫습니다.',
    strengths: ['날카로운 관찰력과 직관', '독립적으로 깊이 파고드는 집중력', '신중하고 정확함'],
    challenges: ['고독을 즐기나 고립될 수 있음', '지나친 신중함으로 기회를 놓칠 수 있음'],
    today_advice: '혼자만의 시간에 집중하고 중요한 통찰을 얻기 좋습니다. 직관을 신뢰하세요.',
    compatible: ['무오', '병오', '임오'],
    career: '연구, 분석, 철학, 의료, 상담, IT 보안'
  },
  '갑오': {
    element: '木火',
    personality: '활기차고 도전적인 기질. 빠른 행동력과 리더십으로 앞장서는 것을 좋아합니다.',
    strengths: ['뛰어난 행동력과 추진력', '열정과 독립심', '창의적이고 즉흥적'],
    challenges: ['충동적인 결정을 내릴 때가 있음', '지속성이 부족할 수 있음'],
    today_advice: '행동이 필요한 날! 생각을 줄이고 실행에 집중하세요. 빠른 결단이 결실을 맺습니다.',
    compatible: ['기해', '계해', '신해'],
    career: '스포츠, 군인, 경찰, 벤처창업, 리더십 직군'
  },
  '을사': {
    element: '木火',
    personality: '재치 있고 영리한 기질. 빠른 두뇌 회전과 언어 능력으로 설득력이 뛰어납니다.',
    strengths: ['뛰어난 언어 능력과 설득력', '재치 있고 유머 감각', '적응력과 임기응변'],
    challenges: ['약삭빠르게 보일 수 있음', '깊이보다 넓이를 추구해 산만해질 수 있음'],
    today_advice: '소통과 설득이 필요한 일을 처리하기 좋습니다. 말의 힘이 발휘되는 날입니다.',
    compatible: ['무자', '경자', '임자'],
    career: '언론, 법률, 영업, 외교, 강사, 작가'
  },
  '병자': {
    element: '火水',
    personality: '역동적이고 감성적인 기질. 강한 열정 아래 섬세한 감성이 흐릅니다.',
    strengths: ['강렬한 열정과 감수성', '인간미와 따뜻함', '어떤 상황에서도 에너지를 발산'],
    challenges: ['감정 기복이 클 수 있음', '열정이 과해 소진될 수 있음'],
    today_advice: '감정 에너지를 창의적인 방향으로 쏟기 좋습니다. 열정이 넘치는 날입니다.',
    compatible: ['신축', '기축', '계축'],
    career: '예술, 상담, 의료, 소방, 사회복지'
  },
  '정해': {
    element: '火水',
    personality: '따뜻하고 철학적인 기질. 내면의 깊이와 따뜻한 감성이 조화를 이룹니다.',
    strengths: ['깊은 공감능력과 배려심', '철학적 사고와 내면의 깊이', '부드럽지만 강한 의지'],
    challenges: ['이상과 현실 사이에서 갈등', '타인의 감정에 너무 영향 받음'],
    today_advice: '직관과 감성에 집중하는 날입니다. 중요한 사람들과의 진심 어린 대화를 나누세요.',
    compatible: ['갑자', '무자', '임자'],
    career: '상담, 의료, 사회복지, 교육, 예술, 종교'
  },
  '무인': {
    element: '土木',
    personality: '든든하고 진취적인 기질. 안정적인 기반 위에서 도전을 즐기는 성격입니다.',
    strengths: ['책임감과 실행력의 조화', '신뢰받는 리더십', '끈기 있는 추진력'],
    challenges: ['다소 고집스럽고 융통성 부족', '큰 그림보다 세부 실행에 집중 경향'],
    today_advice: '믿음직한 행동으로 신뢰를 쌓기 좋습니다. 중요한 약속을 지키는 날로 삼으세요.',
    compatible: ['갑자', '갑오', '병자'],
    career: '건설, 군인, 경영, 행정, 농업, 체육 지도'
  },
  '기묘': {
    element: '土木',
    personality: '온화하고 섬세한 기질. 부드러운 외양 아래 강한 내면이 자리합니다.',
    strengths: ['섬세하고 예민한 감수성', '배려심 깊은 성격', '실용적이고 알뜰함'],
    challenges: ['걱정이 많고 결단이 느릴 수 있음', '자기 주장이 약할 수 있음'],
    today_advice: '세밀한 작업과 꼼꼼한 계획을 세우기 좋습니다. 주변을 정리하고 환경을 가꾸세요.',
    compatible: ['갑자', '병자', '임자'],
    career: '교육, 보육, 요리, 의료, 상담, 원예'
  },
  '경신': {
    element: '金金',
    personality: '명확하고 강인한 기질. 정확함과 결단력이 뛰어나며 원칙을 중시합니다.',
    strengths: ['정확하고 논리적인 사고', '강한 결단력과 의지력', '원칙과 규칙을 잘 지킴'],
    challenges: ['유연성이 부족하고 경직될 수 있음', '완벽주의로 인한 과도한 스트레스'],
    today_advice: '정확한 판단과 원칙적인 행동이 빛납니다. 중요한 결정을 내리기 최적의 날입니다.',
    compatible: ['임자', '계해', '을해'],
    career: '법률, 군인, 경찰, 의료, 공학, 금융'
  },
  '신유': {
    element: '金金',
    personality: '세련되고 명석한 기질. 예리한 판단력과 미적 감각이 조화를 이룹니다.',
    strengths: ['예리한 분석력과 판단력', '고급스러운 미적 감각', '정확하고 꼼꼼함'],
    challenges: ['비판적 성향으로 관계에 마찰', '완벽주의가 지나쳐 효율성 저하'],
    today_advice: '정밀한 작업과 분석에 집중하기 좋습니다. 품질을 높이는 일에 에너지를 쏟으세요.',
    compatible: ['무자', '갑자', '임자'],
    career: '의료, 법률, 패션, 예술 비평, 금융 분석'
  },
  '임자': {
    element: '水水',
    personality: '지혜롭고 유연한 기질. 깊은 통찰력과 뛰어난 직관으로 흐름을 읽습니다.',
    strengths: ['깊은 지혜와 통찰력', '뛰어난 적응력과 유연함', '지식욕과 탐구 정신'],
    challenges: ['의지가 약해 흔들릴 수 있음', '감정 기복과 우유부단함'],
    today_advice: '직관과 창의성이 최고조에 달하는 날입니다. 오래 고민하던 문제의 해답을 찾으세요.',
    compatible: ['경오', '무오', '병오'],
    career: 'IT, 철학, 연구, 문학, 예술, 상담'
  },
  '계해': {
    element: '水水',
    personality: '신비롭고 내성적인 기질. 깊은 내면의 세계와 날카로운 직관을 가집니다.',
    strengths: ['뛰어난 직관력과 감수성', '깊이 있는 사고력', '조용하지만 강한 내면'],
    challenges: ['내성적이어서 고립되기 쉬움', '감정을 숨기다 폭발할 수 있음'],
    today_advice: '내면의 소리에 귀 기울이고 영감을 얻기 좋은 날입니다. 혼자만의 시간을 가지세요.',
    compatible: ['병오', '무오', '갑오'],
    career: '철학, 연구, 심리학, 음악, 예술, 상담'
  },
  '갑인': {
    element: '木木',
    personality: '강하고 직선적인 기질. 독립심이 강하고 자신의 길을 개척하는 힘이 있습니다.',
    strengths: ['강인한 독립심과 자존심', '뚜렷한 목표 의식', '진취적이고 도전적'],
    challenges: ['독선적으로 보일 수 있음', '타인의 도움 받기를 꺼림'],
    today_advice: '자신감을 가지고 새로운 시작을 추진하세요. 독립적인 결정이 빛나는 날입니다.',
    compatible: ['정해', '기해', '계해'],
    career: '창업, 리더십, 법률, 의료, 교육, 스포츠'
  },
  '을묘': {
    element: '木木',
    personality: '유연하고 창의적인 기질. 부드럽게 어울리면서도 강인한 생명력이 있습니다.',
    strengths: ['뛰어난 적응력과 창의성', '사람들과 잘 어울리는 친화력', '섬세하고 예민한 감각'],
    challenges: ['뚜렷한 결단이 어려울 수 있음', '줏대가 없어 보일 수 있음'],
    today_advice: '유연하게 협력하고 창의적인 아이디어를 펼치기 좋습니다. 네트워킹에 집중하세요.',
    compatible: ['경신', '무신', '임신'],
    career: '예술, 교육, 원예, 음식, 상담, 디자인'
  }
};

// ─────────────────────────────────────────────────────────
// 오행별 기질 분석 (5오행 전체)
// ─────────────────────────────────────────────────────────
const ELEMENT_PERSONALITIES = {
  '목': {
    title: '목(木) 기질 — 성장과 창조',
    emoji: '🌱',
    description: '나무처럼 위로 뻗어나가려는 성장의 에너지를 지닙니다. 새로운 것을 시작하고 성장시키는 힘이 탁월합니다.',
    trait: '인자하고 직선적이며 진취적',
    career: '교육, 의료, 창업, 예술, 기획, 법률',
    relationship: '솔직하고 따뜻하나 고집이 있음. 신뢰를 소중히 여김',
    today: '활동적인 계획을 세우고 실행하세요. 성장에 집중하면 좋습니다',
    color: 'var(--wood)',
    cssClass: 'el-wood'
  },
  '화': {
    title: '화(火) 기질 — 열정과 표현',
    emoji: '🔥',
    description: '불처럼 타오르는 열정과 표현력이 가장 큰 무기입니다. 사람들을 밝게 하고 활력을 줍니다.',
    trait: '열정적이고 표현력 강하며 카리스마 있음',
    career: '마케팅, 연예, 리더십, 디자인, 강사, 방송',
    relationship: '열정적이고 따뜻하지만 감정 기복에 주의. 상대를 빛나게 함',
    today: '사람들과 소통하고 아이디어를 나누세요. 열정이 전달되는 날입니다',
    color: 'var(--fire)',
    cssClass: 'el-fire'
  },
  '토': {
    title: '토(土) 기질 — 안정과 신뢰',
    emoji: '🏔️',
    description: '대지처럼 든든하고 포용력 있는 에너지입니다. 사람들에게 안정감을 주고 신뢰를 쌓습니다.',
    trait: '신뢰감 있고 포용력 있으며 현실적',
    career: '경영, 행정, 부동산, 요리, 의료, 교육 관리',
    relationship: '안정적이고 신뢰롭지만 변화에 느릴 수 있음. 헌신적인 파트너',
    today: '꼼꼼하게 정리하고 기반을 다지기 좋습니다. 신뢰를 쌓는 활동을 하세요',
    color: 'var(--earth)',
    cssClass: 'el-earth'
  },
  '금': {
    title: '금(金) 기질 — 결단과 완성',
    emoji: '⚔️',
    description: '쇠처럼 날카롭고 강인한 에너지입니다. 정확한 판단과 강한 의지로 목표를 완성합니다.',
    trait: '원칙적이고 정확하며 강한 결단력',
    career: '법률, 의료, 회계, 공학, 군인, 경찰, 금융',
    relationship: '정직하고 원칙적이지만 유연성이 필요. 강하고 믿음직한 파트너',
    today: '중요한 결정을 내리기 좋습니다. 정확하고 원칙적인 행동이 빛납니다',
    color: 'var(--metal)',
    cssClass: 'el-metal'
  },
  '수': {
    title: '수(水) 기질 — 지혜와 유연',
    emoji: '💧',
    description: '물처럼 흐르고 깊이 스며드는 에너지입니다. 깊은 통찰력과 유연한 적응력이 강점입니다.',
    trait: '지혜롭고 적응력 있으며 직관이 뛰어남',
    career: '연구, 철학, 상담, IT, 예술, 문학, 전략',
    relationship: '깊이 있고 공감능력이 뛰어나지만 감정 표현이 서투를 수 있음',
    today: '직관력이 높아지는 날. 깊이 생각하고 계획을 세우세요',
    color: 'var(--water)',
    cssClass: 'el-water'
  }
};

// ─────────────────────────────────────────────────────────
// 오늘 일진별 에너지 흐름 메시지 (22개 주요 일주)
// ─────────────────────────────────────────────────────────
const DAILY_PILLAR_ENERGY = {
  '갑자': '씨앗이 발아하는 날. 새로운 시작과 계획 수립에 최적입니다. 망설이던 것을 시작하세요.',
  '을축': '차분하게 기초를 다지는 날입니다. 꼼꼼한 정리와 계획이 빛을 발합니다.',
  '병인': '열정이 솟구치는 활동적인 날. 사람들과의 교류와 협력이 풍성해집니다.',
  '정묘': '감성이 풍부해지는 날. 예술적 작업과 내면 성찰에 좋습니다.',
  '무진': '든든한 기반을 구축하는 날. 장기적인 계획을 세우고 안정을 추구하세요.',
  '기사': '꼼꼼한 분석과 세밀한 작업이 빛납니다. 디테일에 집중하면 성과가 납니다.',
  '경오': '결단력이 최고조에 달하는 날. 중요한 결정과 과감한 실행이 어울립니다.',
  '신미': '우아한 완성을 추구하는 날. 마무리 작업과 미적 활동에 집중하세요.',
  '임신': '전략적 사고가 빛나는 날. 데이터 분석과 계획 수립에 에너지를 쏟으세요.',
  '계유': '직관이 날카로운 날. 조용히 집중하면 중요한 통찰을 얻을 수 있습니다.',
  '갑오': '행동력이 폭발하는 역동적인 날. 오래 미뤄온 일을 과감하게 실행하세요.',
  '을사': '언어와 소통의 힘이 강해지는 날. 중요한 발표나 협상에 어울립니다.',
  '병자': '열정과 감성이 교차하는 날. 창의적 작업과 진심 어린 소통이 빛납니다.',
  '정해': '따뜻한 연결이 이루어지는 날. 소중한 사람들과의 대화가 깊어집니다.',
  '무인': '신뢰와 책임이 빛나는 날. 중요한 약속을 지키고 의리를 다지세요.',
  '기묘': '세심한 배려가 가치를 발하는 날. 주변을 돌보고 환경을 가꾸세요.',
  '경신': '원칙과 정확성이 빛나는 날. 중요한 판단과 결정을 내리기 좋습니다.',
  '신유': '완성도와 품질에 집중하는 날. 세밀한 작업이 빛을 발합니다.',
  '임자': '깊은 지혜와 직관이 솟아나는 날. 창의적 영감과 통찰을 발휘하세요.',
  '계해': '내면의 소리에 귀 기울이는 날. 혼자만의 성찰 시간이 소중합니다.',
  '갑인': '독립적인 결단과 개척이 빛나는 날. 새로운 길을 여는 시작점입니다.',
  '을묘': '유연한 협력과 창의성이 꽃피는 날. 네트워킹과 팀워크가 열매를 맺습니다.'
};

// 오행 에너지 기본 메시지
const ELEMENT_ENERGY_MSG = {
  '목': '성장과 창조의 에너지가 흐릅니다. 새로운 것을 시작하고 앞으로 나아가기 좋은 날입니다.',
  '화': '활발하고 열정적인 에너지의 날입니다. 사람들과 소통하고 아이디어를 펼치세요.',
  '토': '안정과 신뢰의 에너지. 차분하게 기초를 다지고 중요한 관계를 돌보기 좋습니다.',
  '금': '결단력이 빛나는 날. 중요한 결정을 내리고 마무리 짓는 일에 집중하세요.',
  '수': '직관력과 통찰이 높아지는 날. 깊이 생각하고 새로운 계획을 세우세요.'
};

// ═══════════════════════════════════════════════════════════

// 별 생성
function createStars() {
  const container = document.getElementById('stars');
  for (let i = 0; i < 80; i++) {
    const star = document.createElement('div');
    star.className = 'star';
    const size = Math.random() * 2.5 + 0.5;
    star.style.cssText = `
      width:${size}px;height:${size}px;
      left:${Math.random()*100}%;top:${Math.random()*100}%;
      --dur:${2+Math.random()*4}s;
      animation-delay:${Math.random()*4}s
    `;
    container.appendChild(star);
  }
}

// 셀렉트 초기화
function initSelects() {
  const yearIds = ['birth-year','e-year','ca-year','cb-year','cpa-year','cpb-year','cal-year'];
  const monthIds = ['birth-month','e-month','ca-month','cb-month','cpa-month','cpb-month','cal-month'];
  const dayIds = ['birth-day','e-day','ca-day','cb-day','cpa-day','cpb-day','cal-day'];
  const currentYear = new Date().getFullYear();

  yearIds.forEach(id => {
    const el = document.getElementById(id);
    for (let y = currentYear; y >= 1930; y--) {
      el.innerHTML += `<option value="${y}">${y}년</option>`;
    }
    el.value = 1990;
  });
  monthIds.forEach(id => {
    const el = document.getElementById(id);
    for (let m = 1; m <= 12; m++) el.innerHTML += `<option value="${m}">${m}월</option>`;
  });
  dayIds.forEach(id => {
    const el = document.getElementById(id);
    for (let d = 1; d <= 31; d++) el.innerHTML += `<option value="${d}">${d}일</option>`;
  });
}

// 탭 전환
function switchTab(name, btn) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  btn.classList.add('active');
}

// 토스트
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

// 오행 한글
const ELEMENTS = { '木':'木 목','火':'火 화','土':'土 토','金':'金 금','水':'水 수' };
const EL_CLASS = { '木':'el-wood','火':'el-fire','土':'el-earth','金':'el-metal','水':'el-water' };

// 사주 계산
async function calcSaju() {
  const year = +document.getElementById('birth-year').value;
  const month = +document.getElementById('birth-month').value;
  const day = +document.getElementById('birth-day').value;
  const hourVal = document.getElementById('birth-hour').value;
  const gender = document.getElementById('gender').value;

  // 입력 검증
  if (!year || !month || !day) {
    showToast('⚠️ 생년월일을 모두 입력해주세요');
    return;
  }

  document.getElementById('saju-loading').style.display = 'block';
  document.getElementById('saju-result').style.display = 'none';

  try {
    const body = { birth_year: year, birth_month: month, birth_day: day, gender, lang: 'ko' };
    if (hourVal !== '') body.birth_hour = +hourVal;

    const res = await fetch(API + '/api/saju/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(15000)
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || '사주 계산 오류');

    // 결과 유효성 검증
    if (!data.pillars || !data.pillars.year || !data.pillars.month || !data.pillars.day) {
      throw new Error('사주 계산 결과가 올바르지 않습니다. 생년월일을 다시 확인해주세요.');
    }

    renderSaju(data);
  } catch(e) {
    const msg = e.name === 'TimeoutError' ? '⏱️ 응답 시간 초과. 다시 시도해주세요.' : '❌ ' + e.message;
    showToast(msg, 3500);
  } finally {
    document.getElementById('saju-loading').style.display = 'none';
  }
}

function renderSaju(data) {
  const pillars = data.pillars;
  const lunar = pillars.lunar_date;

  // 음력 정보
  if (lunar) {
    document.getElementById('lunar-info').innerHTML =
      `🌙 음력 ${lunar.lunar_year}년 ${lunar.lunar_month}월 ${lunar.lunar_day}일${lunar.is_intercalation?' (윤달)':''}`;
  }

  // 사주 기둥
  const pillarKeys = [
    { key: 'year', label: '년주(年柱)' },
    { key: 'month', label: '월주(月柱)' },
    { key: 'day', label: '일주(日柱)' },
    { key: 'hour', label: '시주(時柱)' }
  ];

  const han = {
    '갑':'甲','을':'乙','병':'丙','정':'丁','무':'戊','기':'己','경':'庚','신':'辛','임':'壬','계':'癸',
    '자':'子','축':'丑','인':'寅','묘':'卯','진':'辰','사':'巳','오':'午','미':'未','신':'申','유':'酉','술':'戌','해':'亥'
  };

  let pillarsHTML = '';
  const elementCount = {};

  pillarKeys.forEach(({key, label}) => {
    const p = pillars[key];
    if (!p) {
      pillarsHTML += `<div class="pillar-card"><div class="pillar-label">${label}</div><div class="pillar-han" style="opacity:.3">—</div><div class="pillar-ganjie">미입력</div></div>`;
      return;
    }
    const stemHan = han[p.stem] || p.stem;
    const branchHan = han[p.branch] || p.branch;
    const el = p.element || '';
    const elClass = EL_CLASS[el] || '';

    // 오행 카운트
    if (el) elementCount[el] = (elementCount[el]||0) + 1;

    pillarsHTML += `
      <div class="pillar-card">
        <div class="pillar-label">${label}</div>
        <div class="pillar-han">${stemHan}<br>${branchHan}</div>
        <div class="pillar-ganjie">${p.pillar || p.stem+p.branch}</div>
        ${el ? `<span class="element-badge ${elClass}">${ELEMENTS[el]||el}</span>` : ''}
      </div>`;
  });

  document.getElementById('pillars').innerHTML = pillarsHTML;

  // 오행 차트
  const total = Object.values(elementCount).reduce((a,b)=>a+b,0) || 1;
  const elOrder = ['木','火','土','金','水'];
  const elColors = { '木':'var(--wood)','火':'var(--fire)','土':'var(--earth)','金':'var(--metal)','水':'var(--water)' };
  const elNames = { '木':'목','火':'화','土':'토','金':'금','水':'수' };

  let chartHTML = '';
  elOrder.forEach(el => {
    const cnt = elementCount[el] || 0;
    const pct = Math.round(cnt/total*100);
    const h = Math.max(cnt * 20, 4);
    chartHTML += `
      <div class="element-bar">
        <div style="height:80px;display:flex;align-items:flex-end;justify-content:center">
          <div class="element-bar-fill" style="width:32px;height:${h}px;background:${elColors[el]}"></div>
        </div>
        <div class="element-bar-label" style="color:${elColors[el]}">${elNames[el]}<br><span style="color:var(--text-3)">${cnt}개</span></div>
      </div>`;
  });
  document.getElementById('element-chart').innerHTML = chartHTML;

  document.getElementById('disclaimer-text').textContent = data.disclaimer || pillars.disclaimer || '';
  document.getElementById('saju-result').style.display = 'block';

  // ─── 일주 해석 섹션 (기본) ───
  renderInterpretation(pillars, data.interpretation);

  showToast('✨ 사주를 확인했습니다');

  // ─── AI 상세 해석 (별도 요청, 비동기) ───
  const aiContainer = document.getElementById('ai-interpretation');
  if (aiContainer) {
    aiContainer.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-3);font-size:.85rem">🤖 AI 상세 해석 생성 중...</div>';
    const body2 = { birth_year: +document.getElementById('birth-year').value,
                    birth_month: +document.getElementById('birth-month').value,
                    birth_day: +document.getElementById('birth-day').value,
                    gender: document.getElementById('gender').value, lang: 'ko' };
    const hourV = document.getElementById('birth-hour').value;
    if (hourV !== '') body2.birth_hour = +hourV;

    fetch(API + '/api/saju/ai-interpret', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body2), signal: AbortSignal.timeout(60000)
    }).then(r => r.json()).then(aiData => {
      if (aiData && aiData.ai && Object.keys(aiData.ai).length > 0) {
        renderAiInterpretation(aiData.ai, document.getElementById('birth-year').value + '년 ' + document.getElementById('birth-month').value + '월 ' + document.getElementById('birth-day').value + '일');
      } else {
        aiContainer.innerHTML = '';
      }
    }).catch(() => {
      aiContainer.innerHTML = '';
    });
  }
}

function renderInterpretation(pillars, interpretation) {
  const dayPillar = pillars.day;
  if (!dayPillar) return;

  const dayKey = dayPillar.pillar || (dayPillar.stem + dayPillar.branch);

  // interpretation은 /calculate API의 interpretation 필드
  const interp = interpretation || {};
  const elColors = { '木':'var(--wood)','火':'var(--fire)','土':'var(--earth)','金':'var(--metal)','水':'var(--water)' };
  const elMap = {'목':'木','화':'火','토':'土','금':'金','수':'水','木':'木','火':'火','土':'土','金':'金','水':'水'};
  const primaryElHan = elMap[pillars.primary_element] || pillars.primary_element || '';
  const elColor = elColors[primaryElHan] || 'var(--gold)';

  // ─ 일주 해석 ─
  let pillarHTML = '';
  if (interp.personality) {
    const strengthsHTML = (interp.strengths || []).map(s => `<li style="margin-bottom:4px">✦ ${s}</li>`).join('');
    const challengesHTML = (interp.challenges || []).map(c => `<li style="margin-bottom:4px;color:var(--text-3)">△ ${c}</li>`).join('');
    const careerHint = interp.element_info?.career || '';
    pillarHTML = `
      <div style="background:rgba(255,255,255,.04);border-radius:12px;padding:16px;margin-bottom:12px">
        <div style="font-size:1rem;color:${elColor};font-family:'Noto Serif KR',serif;margin-bottom:8px">
          ${dayKey} 일주
        </div>
        <p style="color:var(--text);line-height:1.7;margin-bottom:12px">${interp.personality}</p>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
          <div>
            <div style="font-size:.8rem;color:var(--text-2);margin-bottom:4px">강점</div>
            <ul style="list-style:none;font-size:.85rem;color:var(--text)">${strengthsHTML}</ul>
          </div>
          <div>
            <div style="font-size:.8rem;color:var(--text-2);margin-bottom:4px">주의</div>
            <ul style="list-style:none;font-size:.85rem">${challengesHTML}</ul>
          </div>
        </div>
        ${careerHint ? `<div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border);font-size:.83rem;color:var(--text-2)">${careerHint}</div>` : ''}
      </div>`;
  } else {
    pillarHTML = `<p style="color:var(--text-2);font-size:.9rem">일주 <strong style="color:var(--gold)">${dayKey}</strong>의 에너지를 지니고 있습니다.</p>`;
  }
  document.getElementById('pillar-interpretation').innerHTML = pillarHTML;

  // ─ AI 상세 해석 (있을 경우) ─
  const ai = interp.ai || {};
  let aiHTML = '';
  if (ai.core_nature || ai.element_balance) {
    aiHTML = `<div style="margin-top:16px">
      <div style="font-size:.78rem;font-weight:700;color:var(--gold);letter-spacing:.06em;margin-bottom:12px">✦ AI 명리학 상세 분석</div>`;

    if (ai.core_nature) {
      aiHTML += `<div style="background:rgba(201,162,39,.06);border-left:3px solid var(--gold);border-radius:0 10px 10px 0;padding:14px;margin-bottom:10px">
        <div style="font-size:.72rem;color:var(--text-3);margin-bottom:6px">핵심 기질 — ${dayKey} 일주만의 특성</div>
        <p style="color:var(--text);line-height:1.75;font-size:.9rem">${ai.core_nature}</p>
      </div>`;
    }

    if (ai.element_balance) {
      aiHTML += `<div style="background:rgba(255,255,255,.04);border-radius:10px;padding:14px;margin-bottom:10px">
        <div style="font-size:.72rem;color:var(--text-3);margin-bottom:6px">오행 균형 분석</div>
        <p style="color:var(--text);line-height:1.7;font-size:.88rem">${ai.element_balance}</p>
      </div>`;
    }

    if (ai.relationship_style) {
      aiHTML += `<div style="background:rgba(255,255,255,.04);border-radius:10px;padding:14px;margin-bottom:10px">
        <div style="font-size:.72rem;color:var(--text-3);margin-bottom:6px">인간관계 스타일</div>
        <p style="color:var(--text);line-height:1.7;font-size:.88rem">${ai.relationship_style}</p>
      </div>`;
    }

    if (ai.career_direction) {
      aiHTML += `<div style="background:rgba(255,255,255,.04);border-radius:10px;padding:14px;margin-bottom:10px">
        <div style="font-size:.72rem;color:var(--text-3);margin-bottom:6px">적성과 진로 방향</div>
        <p style="color:var(--text);line-height:1.7;font-size:.88rem">${ai.career_direction}</p>
      </div>`;
    }

    if (ai.year_2026) {
      aiHTML += `<div style="background:rgba(201,162,39,.08);border:1px solid rgba(201,162,39,.3);border-radius:10px;padding:14px;margin-bottom:10px">
        <div style="font-size:.72rem;color:var(--gold);font-weight:600;margin-bottom:6px">📅 2026년 흐름</div>
        <p style="color:var(--text);line-height:1.7;font-size:.88rem">${ai.year_2026}</p>
      </div>`;
    }

    if (ai.growth_areas && ai.growth_areas.length) {
      aiHTML += `<div style="background:rgba(255,255,255,.04);border-radius:10px;padding:14px">
        <div style="font-size:.72rem;color:var(--text-3);margin-bottom:8px">성장 과제</div>
        ${ai.growth_areas.map(g => `<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px">
          <span style="color:var(--gold);flex-shrink:0">◇</span>
          <p style="color:var(--text-2);line-height:1.6;font-size:.85rem;margin:0">${g}</p>
        </div>`).join('')}
      </div>`;
    }

    aiHTML += `</div>`;
    // AI 해석이 있으면 기존 기본 해석 위에 표시
  }

  const aiContainer = document.getElementById('ai-interpretation');
  if (aiContainer) aiContainer.innerHTML = aiHTML;

  // ─ 오행 기질 분석 ─
  let elemHTML = '';
  const elInfo = interp.element_info || {};
  if (elInfo.temperament) {
    elemHTML = `
      <div style="background:rgba(255,255,255,.04);border-radius:12px;padding:16px">
        <div style="font-size:.9rem;font-weight:600;margin-bottom:8px;color:${elColor}">
          ${primaryElHan} 기운의 특성
        </div>
        <p style="color:var(--text);line-height:1.7;margin-bottom:10px">${elInfo.temperament}</p>
        <div style="display:grid;grid-template-columns:1fr;gap:8px;font-size:.85rem">
          ${elInfo.relationship ? `<div><div style="color:var(--text-3);font-size:.75rem;margin-bottom:3px">관계 패턴</div><div style="color:var(--text)">${elInfo.relationship}</div></div>` : ''}
        </div>
      </div>`;
  }
  document.getElementById('element-analysis').innerHTML = elemHTML;

  // ─ 오늘의 조언 ─
  const advice = interp.today_advice || '';
  const todayDayPillar = getTodayPillar();
  document.getElementById('today-advice').innerHTML = `
    <p style="color:var(--text);line-height:1.7;margin-bottom:0">💡 ${advice || '오늘도 자신의 기운에 맞게 차분하게 움직이세요.'}</p>
    <p style="color:var(--text-3);font-size:.8rem;margin-top:8px;padding-top:8px;border-top:1px solid var(--border)">📅 오늘 일진: ${todayDayPillar}</p>
  `;

  document.getElementById('interpretation-card').style.display = 'block';
}

function getTodayPillar() {
  // 오늘 날짜로 60갑자 일진 계산 (간이 계산법)
  const STEMS = ['갑','을','병','정','무','기','경','신','임','계'];
  const BRANCHES = ['자','축','인','묘','진','사','오','미','신','유','술','해'];
  // 기준일: 2024-01-01 = 갑자일 (간이 계산)
  const base = new Date(2024, 0, 1);
  const today = new Date();
  const diff = Math.floor((today - base) / (1000*60*60*24));
  const stemIdx = ((diff % 10) + 10) % 10;
  const branchIdx = ((diff % 12) + 12) % 12;
  return STEMS[stemIdx] + BRANCHES[branchIdx];
}

// 에너지 계산
async function calcEnergy() {
  const year = +document.getElementById('e-year').value;
  const month = +document.getElementById('e-month').value;
  const day = +document.getElementById('e-day').value;

  document.getElementById('energy-loading').style.display = 'block';
  document.getElementById('energy-result').style.display = 'none';

  try {
    const res = await fetch(API + '/api/saju/daily-energy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ birth_year: year, birth_month: month, birth_day: day, lang: 'ko' })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || '오류');

    // API에서 반환된 실제 에너지 문구 사용
    const todayEnergy = data.today_energy || '';
    const myEl = data.my_primary_element || {};
    const elHan = myEl.han || '';
    const elKorean = myEl.korean || '';
    const elColors = { '木':'var(--wood)','火':'var(--fire)','土':'var(--earth)','金':'var(--metal)','水':'var(--water)' };
    const elColor = elColors[elHan] || 'var(--gold)';
    const todayPillar = data.today_pillar || {};
    const personality = data.personality || '';
    const strengths = data.strengths || [];

    const elNames = {'木':'목(木) 에너지 — 성장·생명력','火':'화(火) 에너지 — 열정·활동','土':'토(土) 에너지 — 안정·신뢰','金':'금(金) 에너지 — 결단·명확','水':'수(水) 에너지 — 지혜·유연'};

    document.getElementById('energy-title').innerHTML =
      `<span style="color:${elColor}">${elNames[elHan] || '오늘의 에너지'}</span>`;

    // 에너지 설명: API 문구를 줄바꿈으로 분리해 단락으로 표시
    const energyParts = todayEnergy.split('\n\n').filter(Boolean);
    let energyHTML = energyParts.map((part, i) => {
      if (i === 0) return `<p style="margin-bottom:14px;font-size:1rem;line-height:1.8;color:var(--text)">${part}</p>`;
      return `<p style="margin-bottom:10px;font-size:.92rem;line-height:1.7;color:var(--text-2)">${part}</p>`;
    }).join('');

    // 오늘 일진 정보
    if (todayPillar.pillar) {
      energyHTML += `<div style="margin-top:14px;padding:12px;background:rgba(255,255,255,.04);border-radius:10px;font-size:.85rem">
        <span style="color:var(--text-3)">오늘 일진: </span>
        <span style="color:var(--gold);font-family:'Noto Serif KR',serif">${todayPillar.pillar}</span>
        <span style="color:var(--text-3);margin-left:8px">(${todayPillar.stem || ''}${todayPillar.branch || ''})</span>
      </div>`;
    }

    // 일주 성격 및 강점
    if (personality) {
      energyHTML += `<div style="margin-top:14px;padding:14px;background:rgba(201,162,39,.06);border-radius:10px;border-left:3px solid var(--gold)">
        <div style="font-size:.78rem;color:var(--text-3);margin-bottom:6px">나의 일주(${data.day_pillar_key || ''}) 기질</div>
        <p style="font-size:.9rem;color:var(--text);line-height:1.7">${personality}</p>`;
      if (strengths.length) {
        energyHTML += `<div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px">` +
          strengths.map(s => `<span style="font-size:.78rem;background:rgba(255,255,255,.06);padding:3px 10px;border-radius:50px;color:var(--text-2)">✦ ${s}</span>`).join('') +
          `</div>`;
      }
      energyHTML += `</div>`;
    }

    // 기질 설명
    if (myEl.temperament) {
      energyHTML += `<div style="margin-top:12px;font-size:.85rem;color:var(--text-2);line-height:1.6">${myEl.temperament}</div>`;
    }

    document.getElementById('energy-desc').innerHTML = energyHTML;
    document.getElementById('energy-disclaimer').textContent = data.disclaimer || '본 내용은 명리학적 자기이해 도구입니다. 실제 운세를 예측하지 않습니다.';

    // AI 에너지 상세 해석
    const aiE = data.ai || {};
    let aiEHTML = '';
    if (aiE.energy_flow || aiE.recommended_activities) {
      aiEHTML = `<div style="margin-top:20px;border-top:1px solid var(--border);padding-top:16px">
        <div style="font-size:.78rem;font-weight:700;color:var(--gold);letter-spacing:.06em;margin-bottom:12px">✦ AI 오늘의 에너지 분석</div>`;
      if (aiE.energy_flow) {
        aiEHTML += `<div style="background:rgba(255,255,255,.04);border-radius:10px;padding:14px;margin-bottom:10px">
          <div style="font-size:.72rem;color:var(--text-3);margin-bottom:6px">오늘의 에너지 흐름</div>
          <p style="color:var(--text);line-height:1.75;font-size:.9rem">${aiE.energy_flow}</p>
        </div>`;
      }
      if (aiE.recommended_activities && aiE.recommended_activities.length) {
        aiEHTML += `<div style="background:rgba(22,163,74,.06);border:1px solid rgba(22,163,74,.2);border-radius:10px;padding:14px;margin-bottom:10px">
          <div style="font-size:.72rem;color:#16a34a;font-weight:600;margin-bottom:8px">✅ 오늘 추천 활동</div>
          ${aiE.recommended_activities.map((a,i) => `<div style="display:flex;gap:8px;margin-bottom:6px">
            <span style="color:var(--gold);font-size:.8rem;flex-shrink:0">${i+1}.</span>
            <span style="color:var(--text);font-size:.87rem;line-height:1.6">${a}</span>
          </div>`).join('')}
        </div>`;
      }
      if (aiE.cautions) {
        aiEHTML += `<div style="background:rgba(239,68,68,.05);border:1px solid rgba(239,68,68,.15);border-radius:10px;padding:14px;margin-bottom:10px">
          <div style="font-size:.72rem;color:#ef4444;font-weight:600;margin-bottom:6px">⚠️ 오늘 주의할 점</div>
          <p style="color:var(--text);line-height:1.7;font-size:.87rem">${aiE.cautions}</p>
        </div>`;
      }
      if (aiE.daily_message) {
        aiEHTML += `<div style="text-align:center;padding:16px;background:rgba(201,162,39,.1);border-radius:12px;border:1px solid rgba(201,162,39,.3)">
          <div style="font-size:.72rem;color:var(--text-3);margin-bottom:6px">오늘의 한마디</div>
          <div style="font-size:1.1rem;font-weight:700;color:var(--gold);font-family:'Noto Serif KR',serif">"${aiE.daily_message}"</div>
        </div>`;
      }
      aiEHTML += `</div>`;
    }
    const aiEContainer = document.getElementById('ai-energy-detail');
    if (aiEContainer) aiEContainer.innerHTML = aiEHTML;

    document.getElementById('energy-result').style.display = 'block';
    showToast('⚡ 오늘의 에너지를 확인했습니다');
  } catch(e) {
    showToast('❌ ' + e.message);
  } finally {
    document.getElementById('energy-loading').style.display = 'none';
  }
}

// 궁합 계산
async function calcCompat() {
  const personA = {
    birth_year: +document.getElementById('ca-year').value,
    birth_month: +document.getElementById('ca-month').value,
    birth_day: +document.getElementById('ca-day').value
  };
  const personB = {
    birth_year: +document.getElementById('cb-year').value,
    birth_month: +document.getElementById('cb-month').value,
    birth_day: +document.getElementById('cb-day').value
  };

  document.getElementById('compat-loading').style.display = 'block';
  document.getElementById('compat-result').style.display = 'none';

  try {
    // 두 사람 각각 사주 계산
    const [resA, resB] = await Promise.all([
      fetch(API+'/api/saju/calculate', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({...personA,lang:'ko'}) }),
      fetch(API+'/api/saju/calculate', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({...personB,lang:'ko'}) })
    ]);
    const [dataA, dataB] = await Promise.all([resA.json(), resB.json()]);

    const elA = dataA.pillars?.primary_element || '';
    const elB = dataB.pillars?.primary_element || '';

    // 오행 궁합 점수 (상생/상극)
    const compatMatrix = {
      '木火':85,'火土':80,'土金':78,'金水':82,'水木':88,
      '木水':75,'火木':70,'土火':72,'金土':68,'水金':74,
      '木土':55,'火金':48,'土水':52,'金木':45,'水火':50,
      '木木':65,'火火':60,'土土':68,'金金':63,'水水':67
    };
    const key1 = elA+elB, key2 = elB+elA;
    const score = compatMatrix[key1] || compatMatrix[key2] || 65;

    const elColors = { '木':'var(--wood)','火':'var(--fire)','土':'var(--earth)','金':'var(--metal)','水':'var(--water)' };
    const elNames2 = {'木':'목(木)','火':'화(火)','土':'토(土)','金':'금(金)','水':'수(水)'};

    document.getElementById('compat-pillars').innerHTML = `
      <div class="pillar-card" style="border-color:${elColors[elA]||'var(--border)'}">
        <div class="pillar-label">甲 첫 번째</div>
        <div class="pillar-han" style="color:${elColors[elA]||'var(--gold)'}">${dataA.pillars?.day?.pillar || '—'}</div>
        <div class="pillar-ganjie">${elNames2[elA] || '—'} 기운</div>
      </div>
      <div class="pillar-card" style="border-color:${elColors[elB]||'var(--border)'}">
        <div class="pillar-label">乙 두 번째</div>
        <div class="pillar-han" style="color:${elColors[elB]||'var(--gold)'}">${dataB.pillars?.day?.pillar || '—'}</div>
        <div class="pillar-ganjie">${elNames2[elB] || '—'} 기운</div>
      </div>`;

    document.getElementById('compat-score-num').textContent = score;
    setTimeout(() => {
      document.getElementById('compat-bar').style.width = score+'%';
    }, 100);

    const scoreDesc = score >= 80 ? '매우 좋은 궁합입니다. 두 에너지가 서로를 보완합니다.' :
                      score >= 65 ? '무난한 궁합입니다. 서로 이해하는 노력이 필요합니다.' :
                                    '에너지 차이가 있습니다. 상대를 이해하는 소통이 중요합니다.';

    document.getElementById('compat-desc').innerHTML = `
      <p style="margin-top:8px">${scoreDesc}</p>
      <p style="margin-top:12px;font-size:.8rem;color:var(--text-3)">본 궁합 분석은 명리학적 오행 기운의 조화도를 나타내며, 실제 궁합을 판단하는 기준이 아닙니다.</p>`;

    document.getElementById('compat-result').style.display = 'block';
    showToast('💑 궁합을 분석했습니다');
  } catch(e) {
    showToast('❌ ' + e.message);
  } finally {
    document.getElementById('compat-loading').style.display = 'none';
  }
}

// 초기화 — </body> 직전에 로드되므로 DOM이 준비된 상태
// DOMContentLoaded 대신 즉시 실행 (스크립트가 </body> 직전이면 이미 DOM 완성)
createStars();
initSelects();

// 탭 버튼 이벤트 (data-tab 방식)
document.querySelectorAll('.tab[data-tab]').forEach(function(btn) {
  btn.addEventListener('click', function() {
    switchTab(this.dataset.tab, this);
  });
});

// 계산 버튼 이벤트
var calcMap = {
  'btn-calc-saju':          calcSaju,
  'btn-calc-energy':        calcEnergy,
  'btn-calc-compat':        calcCompat,
  'btn-calc-compatibility': calcCompatibility,
  'btn-calc-calendar':      calcCalendar,
};
Object.keys(calcMap).forEach(function(id) {
  var el = document.getElementById(id);
  if (el) el.addEventListener('click', calcMap[id]);
});

// ─────────────────────────────────────────────
// 상성보기 (API 기반)
// ─────────────────────────────────────────────
async function calcCompatibility() {
  const personA = {
    birth_year: +document.getElementById('cpa-year').value,
    birth_month: +document.getElementById('cpa-month').value,
    birth_day: +document.getElementById('cpa-day').value
  };
  const personB = {
    birth_year: +document.getElementById('cpb-year').value,
    birth_month: +document.getElementById('cpb-month').value,
    birth_day: +document.getElementById('cpb-day').value
  };

  document.getElementById('compatibility-loading').style.display = 'block';
  document.getElementById('compatibility-result').style.display = 'none';

  try {
    const res = await fetch(API + '/api/saju/compatibility', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ person_a: personA, person_b: personB })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || '오류');

    const elColors = { '목':'var(--wood)','화':'var(--fire)','토':'var(--earth)','금':'var(--metal)','수':'var(--water)' };
    const elNames = {'목':'목(木)','화':'화(火)','토':'토(土)','금':'금(金)','수':'수(水)'};
    const relationEmoji = {'상생':'✨', '상극':'⚡', '비화':'☯', '중립':'🔵'};

    document.getElementById('compat-api-pillars').innerHTML = `
      <div class="pillar-card" style="border-color:${elColors[data.element_a]||'var(--border)'}">
        <div class="pillar-label">🔴 첫 번째</div>
        <div class="pillar-han" style="color:${elColors[data.element_a]||'var(--gold)'}">${data.day_pillar_a||'—'}</div>
        <div class="pillar-ganjie">${elNames[data.element_a]||'—'} 기운</div>
      </div>
      <div class="pillar-card" style="border-color:${elColors[data.element_b]||'var(--border)'}">
        <div class="pillar-label">🔵 두 번째</div>
        <div class="pillar-han" style="color:${elColors[data.element_b]||'var(--gold)'}">${data.day_pillar_b||'—'}</div>
        <div class="pillar-ganjie">${elNames[data.element_b]||'—'} 기운</div>
      </div>`;

    document.getElementById('compat-api-score').textContent = data.score;
    setTimeout(() => {
      document.getElementById('compat-api-bar').style.width = data.score + '%';
    }, 100);

    document.getElementById('compat-api-relation').innerHTML =
      `${relationEmoji[data.relation]||''} ${data.relation} — ${data.level}`;
    document.getElementById('compat-api-advice').innerHTML =
      `<p style="line-height:1.7">${data.advice}</p>`;

    // AI 궁합 상세 해석
    const aiC = data.ai || {};
    let aiCHTML = '';
    if (aiC.energy_dynamics || aiC.compatibility_strengths) {
      aiCHTML = `<div style="margin-top:14px;border-top:1px solid var(--border);padding-top:14px">
        <div style="font-size:.78rem;font-weight:700;color:var(--gold);letter-spacing:.06em;margin-bottom:12px">✦ AI 궁합 상세 분석</div>`;
      if (aiC.energy_dynamics) {
        aiCHTML += `<div style="background:rgba(255,255,255,.04);border-radius:10px;padding:12px;margin-bottom:8px">
          <div style="font-size:.7rem;color:var(--text-3);margin-bottom:5px">두 사람의 에너지 역학</div>
          <p style="color:var(--text);line-height:1.7;font-size:.87rem">${aiC.energy_dynamics}</p>
        </div>`;
      }
      if (aiC.compatibility_strengths) {
        aiCHTML += `<div style="background:rgba(22,163,74,.06);border:1px solid rgba(22,163,74,.2);border-radius:10px;padding:12px;margin-bottom:8px">
          <div style="font-size:.7rem;color:#16a34a;font-weight:600;margin-bottom:5px">✅ 잘 맞는 부분</div>
          <p style="color:var(--text);line-height:1.7;font-size:.87rem">${aiC.compatibility_strengths}</p>
        </div>`;
      }
      if (aiC.potential_conflicts) {
        aiCHTML += `<div style="background:rgba(239,68,68,.05);border:1px solid rgba(239,68,68,.15);border-radius:10px;padding:12px;margin-bottom:8px">
          <div style="font-size:.7rem;color:#ef4444;font-weight:600;margin-bottom:5px">⚠️ 갈등 가능한 부분</div>
          <p style="color:var(--text);line-height:1.7;font-size:.87rem">${aiC.potential_conflicts}</p>
        </div>`;
      }
      if (aiC.relationship_advice && aiC.relationship_advice.length) {
        aiCHTML += `<div style="background:rgba(201,162,39,.06);border-radius:10px;padding:12px;margin-bottom:8px">
          <div style="font-size:.7rem;color:var(--gold);font-weight:600;margin-bottom:8px">💡 관계 발전 조언</div>
          ${aiC.relationship_advice.map((a,i) => `<div style="display:flex;gap:8px;margin-bottom:5px">
            <span style="color:var(--gold);flex-shrink:0">${i+1}.</span>
            <span style="color:var(--text);font-size:.85rem;line-height:1.6">${a}</span>
          </div>`).join('')}
        </div>`;
      }
      if (aiC.long_term_outlook) {
        aiCHTML += `<div style="background:rgba(255,255,255,.04);border-radius:10px;padding:12px">
          <div style="font-size:.7rem;color:var(--text-3);margin-bottom:5px">장기적 전망</div>
          <p style="color:var(--text);line-height:1.7;font-size:.87rem">${aiC.long_term_outlook}</p>
        </div>`;
      }
      aiCHTML += `</div>`;
    }
    const compatAiEl = document.getElementById('compat-api-advice');
    if (compatAiEl) compatAiEl.innerHTML += aiCHTML;

    document.getElementById('compat-api-disclaimer').textContent = data.disclaimer;

    document.getElementById('compatibility-result').style.display = 'block';
    showToast('🌟 상성을 분석했습니다');
  } catch(e) {
    showToast('❌ ' + e.message);
  } finally {
    document.getElementById('compatibility-loading').style.display = 'none';
  }
}

// ─────────────────────────────────────────────
// 운세달력
// ─────────────────────────────────────────────
async function calcCalendar() {
  const year = +document.getElementById('cal-year').value;
  const month = +document.getElementById('cal-month').value;
  const day = +document.getElementById('cal-day').value;

  document.getElementById('calendar-loading').style.display = 'block';
  document.getElementById('calendar-result').style.display = 'none';

  try {
    const res = await fetch(API + `/api/saju/fortune-calendar?birth_year=${year}&birth_month=${month}&birth_day=${day}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || '오류');

    const elColors = { '목':'var(--wood)','화':'var(--fire)','토':'var(--earth)','금':'var(--metal)','수':'var(--water)' };
    const elNames = {'목':'목(木)','화':'화(火)','토':'토(土)','금':'금(金)','수':'수(水)'};
    const monthNames = ['1월','2월','3월','4월','5월','6월','7월','8월','9월','10월','11월','12월'];

    document.getElementById('calendar-title').innerHTML =
      `📅 ${data.year}년 운세달력 — ${elNames[data.birth_element]||''} 일주(${data.birth_pillar||''})`;

    const currentMonth = new Date().getMonth() + 1;

    let gridHTML = '';
    data.months.forEach(m => {
      const isCurrent = m.month === currentMonth;
      const elColor = elColors[m.month_element] || 'var(--gold)';
      const scoreColor = m.luck_score >= 75 ? 'var(--wood)' : m.luck_score >= 65 ? 'var(--gold)' : 'var(--text-2)';
      gridHTML += `
        <div class="month-cal-card" data-month="${m.month}" style="cursor:pointer;background:${isCurrent?'rgba(201,162,39,.12)':'rgba(255,255,255,.04)'};border:1px solid ${isCurrent?'rgba(201,162,39,.4)':'var(--border)'};border-radius:14px;padding:14px;transition:var(--transition)" onmouseenter="this.style.background='rgba(255,255,255,.10)'" onmouseleave="this.style.background='${isCurrent?'rgba(201,162,39,.12)':'rgba(255,255,255,.04)'}'">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <span style="font-weight:600;font-size:.9rem;color:${isCurrent?'var(--gold)':'var(--text)'}">
              ${monthNames[m.month-1]}${isCurrent?' ●':''}
            </span>
            <span style="font-size:1.1rem;font-weight:700;color:${scoreColor}">${m.luck_score}</span>
          </div>
          <div style="font-size:.8rem;color:var(--gold);margin-bottom:6px">${m.theme}</div>
          <div style="font-size:.78rem;color:var(--text-2);line-height:1.5;margin-bottom:6px">${m.advice}</div>
          <div style="font-size:.72rem;color:var(--text-3)">길일 ${m.lucky_day}일 · <span style="color:${elColor}">${elNames[m.month_element]||''}</span></div>
          <div style="margin-top:8px;font-size:.72rem;color:var(--text-3);text-align:right">📆 일별 달력 보기 →</div>
        </div>`;
    });
    document.getElementById('calendar-grid').innerHTML = gridHTML;

    // 월 카드 클릭 → 일별 달력 모달
    const calYear = data.year;
    document.querySelectorAll('.month-cal-card').forEach(card => {
      card.addEventListener('click', function() {
        const m = +this.dataset.month;
        openMonthCalendar(calYear, m, year, month, day);
      });
    });

    document.getElementById('calendar-disclaimer').textContent = data.disclaimer;
    document.getElementById('calendar-result').style.display = 'block';
    showToast('📅 운세달력을 확인했습니다');
  } catch(e) {
    showToast('❌ ' + e.message);
  } finally {
    document.getElementById('calendar-loading').style.display = 'none';
  }
}

// ─────────────────────────────────────────────
// 일별 달력 모달
// ─────────────────────────────────────────────
function closeDayCalendar() {
  document.getElementById('day-calendar-modal').style.display = 'none';
  document.body.style.overflow = '';
}

async function openMonthCalendar(targetYear, targetMonth, birthYear, birthMonth, birthDay) {
  const modal = document.getElementById('day-calendar-modal');
  const loading = document.getElementById('day-cal-loading');
  const body = document.getElementById('day-cal-body');
  const detail = document.getElementById('day-cal-detail');

  document.getElementById('day-cal-title').textContent = `📅 ${targetYear}년 ${targetMonth}월 운세달력`;
  modal.style.display = 'block';
  document.body.style.overflow = 'hidden';
  loading.style.display = 'block';
  body.style.display = 'none';
  detail.style.display = 'none';

  // 모달 바깥 클릭 닫기
  modal.onclick = function(e) {
    if (e.target === modal) closeDayCalendar();
  };

  try {
    const url = `${API}/api/saju/fortune-calendar/daily?birth_year=${birthYear}&birth_month=${birthMonth}&birth_day=${birthDay}&target_year=${targetYear}&target_month=${targetMonth}`;
    const res = await fetch(url);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || '오류');

    renderDayCalendar(data, targetYear, targetMonth);
  } catch(e) {
    loading.style.display = 'none';
    body.style.display = 'block';
    document.getElementById('day-cal-grid').innerHTML = `<div style="grid-column:1/-1;text-align:center;color:var(--text-2);padding:24px">❌ ${e.message}</div>`;
  } finally {
    loading.style.display = 'none';
    body.style.display = 'block';
  }
}

function renderDayCalendar(data, targetYear, targetMonth) {
  const today = new Date();
  const todayY = today.getFullYear();
  const todayM = today.getMonth() + 1;
  const todayD = today.getDate();

  // 요일 헤더: 일월화수목금토 (Sunday-first)
  const WEEKDAYS_HDR = ['일', '월', '화', '수', '목', '금', '토'];
  const WEEKDAY_COLORS = ['var(--fire)', 'var(--text)', 'var(--text)', 'var(--text)', 'var(--text)', 'var(--text)', 'var(--water)'];
  let hdrHTML = '';
  WEEKDAYS_HDR.forEach((w, i) => {
    hdrHTML += `<div style="font-size:.72rem;font-weight:600;color:${WEEKDAY_COLORS[i]};padding:4px 0;">${w}</div>`;
  });
  document.getElementById('day-cal-weekheader').innerHTML = hdrHTML;

  // 해당 달의 1일 요일 (0=일, 1=월, ... 6=토 - Sunday-first)
  const firstDate = new Date(targetYear, targetMonth - 1, 1);
  const firstWeekday = firstDate.getDay(); // 0=Sun

  // 날짜-요일 매핑 빌드 (API weekday는 Mon-first: 0=월...6=일, JS Date weekday는 0=Sun)
  // 우리는 JS Date 기반으로 firstWeekday를 쓸것이므로 API weekday는 표시용으로만 사용
  const dayMap = {};
  (data.days || []).forEach(d => { dayMap[d.day] = d; });

  let gridHTML = '';
  // 첫 날 앞 빈칸 채우기
  for (let i = 0; i < firstWeekday; i++) {
    gridHTML += `<div></div>`;
  }

  const days = data.days || [];
  days.forEach(d => {
    const isToday = (todayY === targetYear && todayM === targetMonth && todayD === d.day);
    const isLucky = d.is_lucky;
    // 게이지: luck_score 50~90 범위를 0~100%로 정규화
    // 하지만 실제 API 범위(50~76)가 좁으므로 절대값 기준으로 표시
    const scoreRatio = Math.min(1, Math.max(0, d.luck_score / 100)); // 0~100점 기준 직관적 표시
    const barColor = d.luck_score >= 75 ? 'var(--wood)' : d.luck_score >= 65 ? 'var(--gold)' : 'var(--text-3)';
    const barWidth = Math.round(scoreRatio * 100);

    // 요일 색 (일=fire, 토=water)
    const dateObj = new Date(targetYear, targetMonth - 1, d.day);
    const jsWeekday = dateObj.getDay(); // 0=Sun
    const isHoliday = (jsWeekday === 0);
    const isSat = (jsWeekday === 6);
    const numColor = isToday ? '#0d1b2a' : isHoliday ? 'var(--fire)' : isSat ? 'var(--water)' : 'var(--text)';
    const cellBg = isToday
      ? 'var(--gold)'
      : isLucky
        ? 'rgba(201,162,39,.15)'
        : 'rgba(255,255,255,.04)';
    const cellBorder = isToday
      ? 'var(--gold)'
      : isLucky
        ? 'rgba(201,162,39,.5)'
        : 'rgba(255,255,255,.1)';

    gridHTML += `
      <div class="day-cell" data-day="${d.day}"
        style="cursor:pointer;border:1px solid ${cellBorder};border-radius:10px;padding:6px 4px;background:${cellBg};text-align:center;position:relative;transition:var(--transition)"
        onclick="selectDayCell(${d.day})">
        ${isLucky ? '<div style="position:absolute;top:2px;right:2px;font-size:.6rem">🌟</div>' : ''}
        <div style="font-size:.85rem;font-weight:700;color:${numColor};line-height:1.2">${d.day}</div>
        <div style="font-size:.65rem;color:${isToday?'#0d1b2a':'var(--text-3)'};">${d.weekday}</div>
        <div style="margin-top:4px;height:3px;border-radius:2px;background:rgba(255,255,255,.1);overflow:hidden">
          <div style="height:100%;width:${barWidth}%;background:${isToday?'rgba(13,27,42,.4)':barColor};border-radius:2px"></div>
        </div>
        <div style="font-size:.6rem;color:${isToday?'rgba(13,27,42,.7)':'var(--text-3)'};margin-top:2px">${d.luck_score}</div>
      </div>`;
  });

  document.getElementById('day-cal-grid').innerHTML = gridHTML;

  // 오늘 날짜가 이 달이면 자동 선택
  if (todayY === targetYear && todayM === targetMonth && dayMap[todayD]) {
    selectDayCell(todayD);
  }

  // dayMap을 전역에 저장해 selectDayCell에서 접근
  window._dayCellMap = dayMap;
  window._dayCalMonthLabel = `${targetYear}년 ${targetMonth}월`;
}

function selectDayCell(day) {
  const dayMap = window._dayCellMap || {};
  const monthLabel = window._dayCalMonthLabel || '';
  const d = dayMap[day];
  if (!d) return;

  // 이전 선택 해제
  document.querySelectorAll('.day-cell').forEach(el => {
    el.style.outline = '';
  });
  const cell = document.querySelector(`.day-cell[data-day="${day}"]`);
  if (cell) cell.style.outline = '2px solid var(--gold)';

  const detail = document.getElementById('day-cal-detail');
  const scoreRatio = Math.min(1, Math.max(0, d.luck_score / 100)); // 절대값 기준
  const barColor = d.luck_score >= 75 ? 'var(--wood)' : d.luck_score >= 65 ? 'var(--gold)' : 'var(--text-3)';
  const barWidth = Math.round(scoreRatio * 100);

  document.getElementById('day-cal-detail-date').innerHTML =
    `${monthLabel} ${day}일 (${d.weekday}) ${d.is_lucky ? '🌟 길일' : ''}`;
  document.getElementById('day-cal-detail-theme').textContent = d.theme;
  document.getElementById('day-cal-detail-tip').innerHTML = `💡 ${d.tip}`;

  const elNames = {'목':'木목','화':'火화','토':'土토','금':'金금','수':'水수'};
  const relColor = d.relation === '상생' ? 'var(--wood)' : d.relation === '상극' ? 'var(--fire)' : 'var(--gold)';

  document.getElementById('day-cal-detail-score').innerHTML = `
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
      <div style="font-size:.78rem;color:var(--text-3)">운 점수</div>
      <div style="flex:1;height:8px;border-radius:4px;background:rgba(255,255,255,.1);overflow:hidden">
        <div style="height:100%;width:${barWidth}%;background:${barColor};border-radius:4px;transition:width .6s ease"></div>
      </div>
      <div style="font-size:1rem;font-weight:700;color:${barColor}">${d.luck_score}점</div>
    </div>
    ${d.relation ? `
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
      <span style="font-size:.72rem;background:${relColor}20;color:${relColor};padding:2px 8px;border-radius:20px;font-weight:600">${d.relation}</span>
      <span style="font-size:.78rem;color:var(--text-2)">${d.relation_desc || ''}</span>
      ${d.day_element ? `<span style="font-size:.72rem;color:var(--text-3)">[${elNames[d.day_element]||d.day_element}일]</span>` : ''}
    </div>` : ''}
    ${d.suggest_good ? `
    <div style="background:rgba(22,163,74,.08);border:1px solid rgba(22,163,74,.2);border-radius:8px;padding:8px 10px;margin-bottom:6px">
      <div style="font-size:.72rem;color:#16a34a;font-weight:600;margin-bottom:3px">✅ 추천 활동</div>
      <div style="font-size:.78rem;color:var(--text-2)">${d.suggest_good}</div>
    </div>` : ''}
    ${d.suggest_avoid ? `
    <div style="background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.15);border-radius:8px;padding:8px 10px">
      <div style="font-size:.72rem;color:#ef4444;font-weight:600;margin-bottom:3px">⚠️ 주의 활동</div>
      <div style="font-size:.78rem;color:var(--text-2)">${d.suggest_avoid}</div>
    </div>` : ''}
  `;
  detail.style.display = 'block';
  detail.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}