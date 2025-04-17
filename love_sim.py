import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont  # 이미지 생성을 위해 추가
import io  # 이미지를 메모리에서 다루기 위해 추가
import sqlite3 # 누적 카운트를 위해 추가 (st.connection에서 내부적으로 사용)
import os # 파일 경로 처리를 위해 추가

# --- 페이지 기본 설정 ---
st.set_page_config(page_title="연애 확률 시뮬레이터 v2.2", page_icon="💖")

st.title("💖 연애 확률 시뮬레이터 v2.2")
st.caption("결과 이미지 공유✨ + 캐릭터 반응🤩 + 누적 카운트🔥")
st.markdown("---")

# --- NEW: 누적 카운트 표시 ---
# Streamlit Secrets 또는 환경 변수에 DATABASE_URL 설정 필요 (로컬 테스트용 임시 경로)
# 예: secrets.toml 파일에 [connections.sim_counter_db] url = "sqlite:///./simulation_counter.db" 추가
# 또는 직접 경로 지정 (단, Streamlit Cloud 배포 시 이 방식은 초기화될 수 있음)
DB_PATH = "simulation_counter.db"

# 데이터베이스 연결 설정 (st.connection 사용 권장)
# st.connection은 Streamlit 1.30.0 이상 필요
try:
    conn = st.connection("sim_counter_db", type="sql", url=f"sqlite:///{DB_PATH}")
    with conn.session as s:
        s.execute("""
            CREATE TABLE IF NOT EXISTS counts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                count INTEGER DEFAULT 0
            );
        """)
        # 초기 데이터 삽입 (최초 실행 시)
        result = s.execute("SELECT count FROM counts WHERE id = 1;").fetchone()
        if result is None:
            s.execute("INSERT INTO counts (id, count) VALUES (1, 0);")
            s.commit()

    # 현재 카운트 가져오기
    current_count_result = conn.query("SELECT count FROM counts WHERE id = 1;", ttl=0) # 캐시 사용 안 함
    # DataFrame에서 값 추출 확인
    if not current_count_result.empty:
        current_count = current_count_result['count'].iloc[0]
    else:
        # 만약 테이블은 있으나 데이터가 없다면 0으로 초기화 (예외 처리)
        with conn.session as s:
            s.execute("INSERT OR IGNORE INTO counts (id, count) VALUES (1, 0);")
            s.commit()
        current_count = 0

    st.info(f"🔥 지금까지 총 **{current_count:,}번**의 연애 확률이 시뮬레이션 되었습니다!")

except Exception as e:
    st.warning(f"누적 카운트 기능을 불러오는 중 오류 발생: {e}. 로컬 환경에서는 정상 작동하지 않을 수 있습니다.")
    current_count = 0 # 오류 시 카운트 0으로 가정

st.markdown("---") # 구분선 추가

st.write("""
새로운 사람을 만나는 것과 연애를 시작하는 것은 조금 다른 문제죠? 🤔\n
이 시뮬레이터는 당신의 노력과 환경에 따라 **'의미 있는 새로운 만남'**이 생길 확률과,
그 만남이 **'실제 연애'**로 이어질 확률을 각각 예측해 봅니다. (기간: 3개월 / 6개월 / 1년)\n
**어떤 변수를 조절해야 할지 '감'을 잡고, 진짜 원리는 책에서 확인하세요!** 💪
""")

st.markdown("---")

# --- 변수 입력 (기존과 동일) ---
# (기존의 st.expander 내용들은 여기에 그대로 유지)
with st.expander("1️⃣ 기본 정보 & 자기 인식 (Baseline)", expanded=True):
    col1_1, col1_2 = st.columns(2)
    with col1_1:
        solo_duration = st.selectbox("현재 연애 상태 (솔로 기간)", ["6개월 미만", "6개월~2년", "2년 이상", "모태솔로"])
        gender = st.radio("성별", ["여성", "남성"])
    with col1_2:
        age_group = st.selectbox("나이대", ["20대 초반", "20대 중후반", "30대 초반", "30대 중후반", "40대+"])
        exp_level = st.radio("연애 경험", ["있음", "없음"])

    appearance_self = st.slider(
        "나의 외모 매력도 (스스로 평가)", 1, 10, 5,
        help="솔직하게! 1점(음...) ~ 10점(내가 봐도 연예인급)"
    )
    appearance_others = st.slider(
        "나의 외모 매력도 (주변 평가 기반)", 1, 10, 5,
        help="친구나 가족의 피드백을 종합해 보세요. (뼈 때려도 괜찮아요!)"
    )
    appearance_score = (appearance_self + appearance_others) / 2
    st.info(f"📊 종합 외모 매력도: **{appearance_score:.1f}점**")

with st.expander("2️⃣ 외모 & 매력 관리 노력 (Attractiveness Upgrade)"):
    style_effort = st.select_slider("스타일링/패션 개선 노력", ["거의 안 함", "가끔 신경 씀", "적극 투자/컨설팅"], value="가끔 신경 씀")
    skin_hair_care = st.select_slider("피부/헤어 관리 수준", ["기본만", "주기적 관리", "시술/전문 관리"], value="주기적 관리")
    body_care_effort = st.select_slider("다이어트/운동 (체형 관리)", ["안 함", "주 1-2회", "주 3회 이상", "PT/식단 병행"], value="주 1-2회")
    manner_effort = st.select_slider("표정/자세/말투 개선 노력", ["의식 안 함", "가끔 노력", "적극 교정/학습"], value="가끔 노력")
    health_care = st.select_slider("건강 관리 (금연/절주 등)", ["관리 안 함", "노력 중", "성공/비해당"], value="노력 중")

with st.expander("3️⃣ 환경 & 네트워크 (Environment & Network)"):
    col3_1, col3_2 = st.columns(2)
    with col3_1:
        activity_range = st.selectbox("주요 활동 반경", ["집-회사 위주", "동네 중심", "시내/핫플 자주 감", "지역/해외 이동 잦음"])
        network_size = st.number_input("소개 가능한 친구/지인 수", 0, 50, 3)
    with col3_2:
        work_gender_ratio = st.slider("직장 내 이성 비율 (%)", 0, 100, 50)
        network_quality = st.slider("친구/지인의 소개 적극성", 1, 5, 3)
    living_env = st.radio("주거 환경", ["부모님과 거주", "자취/독립"])

with st.expander("4️⃣ 적극성 & 마인드셋 (Proactiveness & Mindset)"):
    col4_1, col4_2 = st.columns(2)
    with col4_1:
        proactiveness = st.select_slider("새로운 만남 시도 빈도", ["거의 없음", "분기 1회", "월 1회", "주 1회 이상"], value="월 1회")
        resilience = st.slider("거절/실패 회복탄력성", 1, 5, 3)
    with col4_2:
        confidence = st.slider("자기 자신감 수준 (내면)", 1, 10, 6)
        openness = st.slider("타인에 대한 개방성/호기심", 1, 5, 3)

    # --- 필터링 세분화 입력 ---
    st.markdown("**🚫 연애 상대 필터링 분석 (나의 '절대 기준' 체크!)**")
    high_filters = st.number_input("높은 장벽 필터 개수 (이거 아니면 절대 불가!)", 0, 10, 2, key='high_filters', help="예: 최소 키 180cm, 특정 종교, 흡연 절대 반대, 연봉 1억 이상 등")
    medium_filters = st.number_input("중간 장벽 필터 개수 (매우 중요, 약간 타협 가능)", 0, 10, 3, key='medium_filters', help="예: 비슷한 가치관, 안정적 직업, 수도권 거주 등")
    low_filters = st.number_input("낮은 장벽 필터 개수 (선호하지만 필수는 아님)", 0, 10, 5, key='low_filters', help="예: 특정 취미 공유, MBTI 궁합, 연락 빈도 등")

    # 가중치 부여 (높은 장벽 페널티를 크게 설정)
    total_filters_weighted = (high_filters * 5.0) + (medium_filters * 2.0) + (low_filters * 0.5)
    st.info(f"✔️ 총 필터 가중치 점수: **{total_filters_weighted:.1f}점** (점수가 낮을수록 기회가 많아져요!)")
    # ----

    apply_sim_result = st.checkbox("시뮬레이션 결과를 참고하여 노력할 의향이 있음")

with st.expander("5️⃣ 활동 & 라이프스타일 (Activities & Lifestyle)"):
    st.write("주로 참여하거나, 앞으로 참여하고 싶은 활동을 선택하세요 (최대 2개)")
    activities_options = {
        "선택 안 함": 0, "집콕(영화/게임/독서 등)": -5, "스터디/외국어 학원": 5,
        "공연/전시/사진/글쓰기": 10, "봉사활동/종교활동": 15, "요가/필라테스": 10,
        "등산/여행 동호회": 15, "러닝 크루 (건강+균형)": 20, "댄스/음악/미술 학원": 12,
        "헬스장(주로 혼자)": 3, "축구/농구/야구 동호회": 8, "주짓수/격투기/서핑": 25,
        "게임/IT 동아리": 5, "자동차/바이크 동호회": 8
    }
    activity1 = st.selectbox("활동 1", options=list(activities_options.keys()))
    activity2 = st.selectbox("활동 2", options=list(activities_options.keys()))
    activity_freq = st.select_slider("선택한 활동 참여 빈도", ["월 1회 미만", "월 1-2회", "주 1회", "주 2회 이상"], value="월 1-2회")
    new_activity_try = st.select_slider("새로운 활동 시도 적극성", ["안 함", "연 1-2회", "분기 1회", "적극적"], value="연 1-2회")


st.markdown("---")

# --- 시뮬레이션 로직 (기존과 동일) ---
def calculate_base_score_v2(params):
    score = 50
    # ... (기존 로직 유지) ...
    score += (params['appearance'] - 5) * 3.0
    if params['activity_range'] == "집-회사 위주": score -= 5
    elif params['activity_range'] == "시내/핫플 자주 감": score += 3
    elif params['activity_range'] == "지역/해외 이동 잦음": score += 6
    score += params['network_size'] * 0.8
    score += (params['network_quality'] - 3) * 1.5
    score += (params['work_gender_ratio'] / 100 - 0.5) * 10
    if params['living_env'] == "자취/독립": score += 3
    if params['proactiveness'] == "거의 없음": score -= 10
    elif params['proactiveness'] == "월 1회": score += 3
    elif params['proactiveness'] == "주 1회 이상": score += 8
    score += (params['resilience'] - 3) * 2.0
    score += (params['confidence'] - 6) * 2.5
    score += (params['openness'] - 3) * 2.0
    filter_penalty = (params['high_filters'] * 5.0) + (params['medium_filters'] * 2.0) + (params['low_filters'] * 0.5)
    score -= filter_penalty
    return max(0, min(100, score))

def calculate_encounter_prob_v2(base_score, params):
    activity_score = 0
    activity_score += params['activities_options'][params['activity1']]
    activity_score += params['activities_options'][params['activity2']]
    if params['activity_freq'] == "월 1-2회": activity_score *= 1.2
    elif params['activity_freq'] == "주 1회": activity_score *= 1.5
    elif params['activity_freq'] == "주 2회 이상": activity_score *= 1.8
    if params['new_activity_try'] == "분기 1회": activity_score += 5
    elif params['new_activity_try'] == "적극적": activity_score += 10
    total_score = base_score + activity_score
    prob = 1 / (1 + np.exp(-(total_score - 60) / 15))
    prob = max(0.05, min(0.95, prob))
    if params['apply_sim_result']: prob *= 1.05
    return prob * 100

def calculate_relationship_prob_v2(encounter_prob, base_score, params):
    charm_upgrade_score = 0
    if params['style_effort'] == "가끔 신경 씀": charm_upgrade_score += 3
    elif params['style_effort'] == "적극 투자/컨설팅": charm_upgrade_score += 8
    if params['skin_hair_care'] == "주기적 관리": charm_upgrade_score += 3
    elif params['skin_hair_care'] == "시술/전문 관리": charm_upgrade_score += 7
    if params['body_care_effort'] == "주 1-2회": charm_upgrade_score += 2
    elif params['body_care_effort'] == "주 3회 이상": charm_upgrade_score += 5
    elif params['body_care_effort'] == "PT/식단 병행": charm_upgrade_score += 9
    if params['manner_effort'] == "가끔 노력": charm_upgrade_score += 2
    elif params['manner_effort'] == "적극 교정/학습": charm_upgrade_score += 6
    if params['health_care'] == "노력 중": charm_upgrade_score += 1
    elif params['health_care'] == "성공/비해당": charm_upgrade_score += 4
    conversion_factor = (base_score + charm_upgrade_score) / 200
    conversion_factor = 0.1 + conversion_factor * 0.6
    conversion_factor = max(0.1, min(0.7, conversion_factor))
    prob = (encounter_prob / 100) * conversion_factor * 100
    return max(0.0, min(encounter_prob, prob))

def apply_time_decay_v2(prob, months):
    if months == 3: decay_factor = 0.6
    elif months == 6: decay_factor = 1.0
    else: decay_factor = 1.3
    return min(99.0, prob * decay_factor)

# --- NEW: 결과 이미지 생성 함수 ---
def create_result_image(encounter_prob, relationship_prob, character_emoji, book_promo=True):
    width, height = 600, 400
    background_color = (255, 240, 245) # 연한 핑크 배경
    img = Image.new('RGB', (width, height), color=background_color)
    d = ImageDraw.Draw(img)

    # 폰트 설정 (Streamlit Cloud에서 사용 가능한 폰트 확인 필요, 예: Noto Sans KR)
    # 로컬에서는 설치된 폰트 경로 지정 가능
    # 여기서는 기본 폰트 사용 (Pillow 내장)
    try:
        # Noto Sans KR 같은 한글 폰트 로드 시도 (파일 경로 필요)
        # font_path = "path/to/NotoSansKR-Bold.otf"
        # title_font = ImageFont.truetype(font_path, 36)
        # text_font = ImageFont.truetype(font_path, 24)
        # small_font = ImageFont.truetype(font_path, 18)
        # emoji_font = ImageFont.truetype(font_path, 60) # 이모지 크기

        # 기본 폰트로 대체 (한글 깨질 수 있음)
        title_font = ImageFont.load_default().font # 기본 폰트는 크기 조절 불가
        text_font = ImageFont.load_default().font
        small_font = ImageFont.load_default().font
        emoji_font = ImageFont.load_default().font

        # 폰트 로딩 실패 시 예외처리 필요
    except IOError:
        st.error("폰트 파일을 로드할 수 없습니다. 기본 폰트를 사용합니다.")
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        emoji_font = ImageFont.load_default()

    # 제목
    title_text = "💖 나의 연애 확률 (6개월) 💖"
    # title_bbox = d.textbbox((0, 0), title_text, font=title_font)
    # title_x = (width - (title_bbox[2] - title_bbox[0])) / 2
    d.text((50, 30), title_text, fill=(255, 20, 147), font=title_font) # 딥핑크

    # 결과 확률
    prob_text_meet = f"✨ 새로운 만남: {encounter_prob:.1f}%"
    prob_text_love = f"💖 연애 시작: {relationship_prob:.1f}%"
    d.text((50, 100), prob_text_meet, fill=(0, 0, 0), font=text_font)
    d.text((50, 140), prob_text_love, fill=(0, 0, 0), font=text_font)

    # 캐릭터 이모지
    # emoji_bbox = d.textbbox((0,0), character_emoji, font=emoji_font)
    # emoji_x = width - (emoji_bbox[2] - emoji_bbox[0]) - 50
    d.text((450, 90), character_emoji, fill=(0, 0, 0), font=emoji_font)

    # 책 홍보 문구 (선택적)
    if book_promo:
        promo_text1 = "더 자세한 원리는?"
        promo_text2 = "『시뮬레이션된 베스트셀러』에서 확인!"
        hashtag_text = "#연애시뮬레이터 #시뮬레이션된베스트셀러"
        d.text((50, 250), promo_text1, fill=(105, 105, 105), font=small_font) # 회색
        d.text((50, 280), promo_text2, fill=(105, 105, 105), font=small_font)
        d.text((50, 320), hashtag_text, fill=(255, 20, 147), font=small_font) # 딥핑크

    # 앱 출처 표시
    app_credit = "love-sim.streamlit.app (가상)" # 실제 앱 주소로 변경
    d.text((width - 200, height - 30), app_credit, fill=(150, 150, 150), font=small_font)

    # 이미지를 BytesIO 객체로 변환
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr

# --- 입력값 정리 ---
params = {
    'solo_duration': solo_duration, 'gender': gender, 'age_group': age_group, 'exp_level': exp_level,
    'appearance': appearance_score,
    'style_effort': style_effort, 'skin_hair_care': skin_hair_care, 'body_care_effort': body_care_effort, 'manner_effort': manner_effort, 'health_care': health_care,
    'activity_range': activity_range, 'work_gender_ratio': work_gender_ratio, 'network_size': network_size, 'network_quality': network_quality, 'living_env': living_env,
    'proactiveness': proactiveness, 'resilience': resilience, 'confidence': confidence, 'openness': openness,
    'high_filters': high_filters, 'medium_filters': medium_filters, 'low_filters': low_filters,
    'apply_sim_result': apply_sim_result,
    'activities_options': activities_options, 'activity1': activity1, 'activity2': activity2, 'activity_freq': activity_freq, 'new_activity_try': new_activity_try
}

# --- 결과 계산 및 출력 ---
if st.button("🔮 시뮬레이션 실행!"):

    # --- NEW: 누적 카운트 업데이트 ---
    try:
        with conn.session as s:
            s.execute("UPDATE counts SET count = count + 1 WHERE id = 1;")
            s.commit()
        # 페이지 새로고침 없이 카운트 즉시 반영 (선택적)
        # current_count += 1
        # st.experimental_rerun() # 또는 최신 버전에서는 st.rerun()
    except Exception as e:
        st.warning(f"누적 카운트 업데이트 중 오류 발생: {e}")

    st.subheader("📊 기간별 예측 확률 변화")
    base_score = calculate_base_score_v2(params)
    encounter_prob_base = calculate_encounter_prob_v2(base_score, params)
    relationship_prob_base = calculate_relationship_prob_v2(encounter_prob_base, base_score, params)

    results = {'기간': [], '만남 확률 (%)': [], '연애 시작 확률 (%)': []}
    for months in [3, 6, 12]:
        encounter_p = apply_time_decay_v2(encounter_prob_base, months)
        relationship_p = apply_time_decay_v2(relationship_prob_base, months)
        relationship_p = min(encounter_p, relationship_p) # 연애 확률이 만남 확률보다 높을 수 없음
        results['기간'].append(f"{months}개월")
        results['만남 확률 (%)'].append(round(encounter_p, 1))
        results['연애 시작 확률 (%)'].append(round(relationship_p, 1))

    results_df = pd.DataFrame(results).set_index('기간')
    relationship_prob_6m = results_df.loc['6개월', '연애 시작 확률 (%)'] # 핵심 결과 (6개월)

    # --- NEW: 캐릭터 반응 ---
    if relationship_prob_6m < 15:
        character_emoji = "😭"
        result_comment = "아직은 조금 더 노력이 필요해요! 🌱"
    elif relationship_prob_6m < 35:
        character_emoji = "🤔"
        result_comment = "가능성이 보입니다! 조금만 더 힘내봐요! 💪"
    elif relationship_prob_6m < 60:
        character_emoji = "😊"
        result_comment = "오! 꽤 높은 확률이에요! 좋은 예감이 드는데요? ✨"
    else:
        character_emoji = "🥰"
        result_comment = "와우! 연애 임박! 곧 좋은 소식 기대할게요! 💖"

    st.markdown(f"### {character_emoji} {result_comment}") # 결과 코멘트 표시
    st.markdown("---") # 구분선

    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.metric("🌟 만남 확률 (6개월)", f"{results_df.loc['6개월', '만남 확률 (%)']:.1f}%")
    with col_res2:
        st.metric("💖 연애 시작 확률 (6개월)", f"{relationship_prob_6m:.1f}%")

    st.line_chart(results_df)
    with st.expander("📅 기간별 상세 확률 보기"):
        st.dataframe(results_df)

    st.markdown("---")
    st.subheader("💡 주요 영향 요인 분석")
    st.write(f"- **만남 기회:** 주로 **활동**('{params['activity1']}', '{params['activity2']}')과 **적극성**('{params['proactiveness']}')이 영향을 미쳐요.")
    st.write(f"- **관계 발전:** **매력 관리**(외모:{params['appearance']:.1f}, 스타일:{params['style_effort']} 등), **자신감**({params['confidence']}점), 그리고 **필터링**(가중치:{total_filters_weighted:.1f}점)이 중요해요.")
    if total_filters_weighted > 15:
        st.warning(f"🚨 특히 **높은 장벽 필터({params['high_filters']}개)**가 많으면 연애 시작 확률이 크게 낮아질 수 있어요! 한두 개만 줄여보는 건 어때요?")

    st.markdown("---")
    st.subheader("🎯 추천 액션 레시피")
    # (기존 추천 액션 레시피 로직 유지)
    if relationship_prob_6m < 20:
        st.info("🌱 **씨앗 뿌리기 단계:** 지금은 만남 기회를 늘리는 게 중요해요! '주짓수'나 '러닝 크루' 같은 새로운 활동에 도전해보거나, '소개 가능한 친구' 수를 늘려보는 건 어떨까요? **'높은 장벽 필터'**도 점검해보세요!")
    elif relationship_prob_6m < 50:
        st.info("💪 **매력 발산 단계:** 만남은 어느 정도 생기고 있어요! 이제 만난 사람과 관계를 발전시킬 차례. '스타일링'에 투자하거나, '자신감'을 높이는 노력이 필요해요. **'중간 장벽 필터'**를 조금 완화하는 것도 방법!")
    else:
        st.success("🚀 **연애 임박 단계:** 확률이 아주 높아요! 지금처럼 꾸준히 노력하면서, 만나는 사람들과 진솔하게 교류하는 데 집중하세요. 좋은 결과가 있을 거예요! **'낮은 장벽 필터'**는 너무 신경 쓰지 마세요!")

    st.markdown("---")

    # --- 7. 결과 공유 (인스타 최적화 - 이미지 생성 & 다운로드) ---
    st.subheader("💌 결과 공유 & 더 알아보기")

    # --- NEW: 결과 이미지 생성 및 다운로드 버튼 ---
    try:
        result_image_bytes = create_result_image(
            results_df.loc['6개월', '만남 확률 (%)'],
            relationship_prob_6m,
            character_emoji
        )
        st.image(result_image_bytes, caption="✨ 인스타 스토리에 공유할 내 결과 이미지 ✨")
        st.download_button(
            label="💾 결과 이미지 다운로드",
            data=result_image_bytes,
            file_name=f"my_love_chance_{relationship_prob_6m:.0f}.png",
            mime="image/png"
        )
        st.info("☝️ 이미지를 다운로드해서 인스타그램 스토리에 공유해보세요!")
    except Exception as e:
        st.error(f"결과 이미지 생성 중 오류 발생: {e}. 텍스트로 공유해주세요.")
        # 이미지 생성 실패 시 기존 텍스트 공유 방식 유지
        st.info("👇 아래 텍스트를 복사해서 인스타 스토리에 공유해보세요! (결과 화면 스크린샷과 함께!)")
        share_text_insta = f"""
        🔮 내 6개월 연애 확률은? 🔮
        만남: {results_df.loc['6개월', '만남 확률 (%)']:.1f}% / 시작: {relationship_prob_6m:.1f}% {character_emoji}
        🔥 '{params['activity1']}' 활동 선택! 확률 UP! 🔥
        🤔 근데 왜 이런 결과가? 비밀은 책에! #시뮬레이션된베스트셀러
        👇 너도 해봐! [앱링크] #연애시뮬레이터 #연애확률 #궁금하면책으로
        """
        st.code(share_text_insta, language=None)

    # --- 책 판매 연계 (기존과 동일) ---
    st.markdown("---")
    st.subheader("📚 변수 설정의 비밀? 책에서 확인하세요!")
    # st.image("your_book_cover_image.jpg", width=150) # 책 표지 이미지
    st.write(f"""
    이 시뮬레이터는 『시뮬레이션된 베스트셀러』에 담긴 **데이터 기반 의사결정 원리**의 맛보기 버전입니다.\n
    - **외모, 활동, 필터링... 각 변수의 정확한 가중치**는 어떻게 설정되었을까요?
    - '자신감'과 '적극성'은 확률에 **얼마나, 어떻게 상호작용**할까요?
    - 이 **시뮬레이터의 로직 자체**는 어떻게 더 정교하게 만들 수 있을까요?\n
    단순히 확률을 아는 것을 넘어, 당신의 **삶 전체를 설계하는 방법**을 배우고 싶다면?\n
    **모든 핵심 원리와 설계 비밀**은 책 속에 담겨 있습니다.
    """)
    book_purchase_link = "https://www.yes24.com" # 실제 링크로 변경
    st.link_button("👉 『시뮬레이션된 베스트셀러』 구매하고 설계자 되기!", book_purchase_link)

    # --- 작가의 한마디 (기존과 동일) ---
    st.text_area(
        "작가의 한마디 📝 (밸런스 잡기!)",
        "저는 10년간 연애 후 10년간 결혼 생활을 해 왔습니다. 어찌 보면 연애 세포는 제로에 가까운 사람이지만, 이 시뮬레이터는 '이렇게도 생각해볼 수 있다'는 사고 확장을 위한 것입니다.\n\n"
        "타로카드처럼 재미로 보시되, 절대적 진리로 믿진 마세요! 여러분의 매력, 노력, 그리고 시뮬레이션에 없는 '우연한 만남'의 가능성이 훨씬 중요합니다. 단골 카페에서, 혹은 홍대 펍에서 운명이 기다릴 수도 있으니까요 😉\n\n"
        "중요한 건 데이터로 사고하는 '연습'을 통해, 내 삶의 변수를 직접 설계해보려는 '의지'입니다. 자, 이제 어떤 변수를 바꿔보시겠어요?",
        height=200,
        key="author_note_final"
    )

else:
    st.info("☝️ 위의 변수들을 입력하고 '시뮬레이션 실행!' 버튼을 눌러 결과를 확인하세요!")
