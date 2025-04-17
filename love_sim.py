# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import requests # Firebase 연동 위해 추가
import json # Firebase 응답 처리 위해 추가
# PIL, io, os, sqlite3 등은 이 버전에서는 직접 사용하지 않으므로 제거

# --- 페이지 기본 설정 ---
st.set_page_config(page_title="연애 확률 시뮬레이터 v2.4", page_icon="💖")

st.title("💖 연애 확률 시뮬레이터 v2.4")
st.caption("성별 맞춤 캐릭터 반응 & 메시지✨ + 영구 카운트🔥")
st.markdown("---")

# --- Firebase 기반 누적 카운트 설정 및 함수 ---
# Streamlit Secrets에서 Firebase DB URL 읽어오기 (.streamlit/secrets.toml 파일 필요)
# 예:
# [firebase]
# databaseURL = "https://your-project-id-default-rtdb.firebaseio.com/"
FIREBASE_DB_URL = st.secrets.get("firebase", {}).get("databaseURL")
COUNT_PATH = "/simulations/love_simulator/count.json" # Firebase Realtime DB 경로 끝에 .json 필수!

# Firebase에서 현재 카운트 읽어오는 함수
def get_firebase_count(db_url, path):
    """Firebase Realtime Database에서 카운트를 읽어옵니다."""
    if not db_url:
        return 0, "Firebase DB URL이 secrets.toml에 설정되지 않았습니다."
    try:
        response = requests.get(db_url + path)
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생
        count = response.json()
        if count is None: # 경로에 데이터가 없는 경우
             # 경로에 0으로 초기값 쓰기 시도
            try:
                init_response = requests.put(db_url + path, json=0)
                init_response.raise_for_status()
                return 0, "카운트 초기화 완료 (값이 없었음)."
            except requests.exceptions.RequestException as init_e:
                return 0, f"카운트 초기화 실패: {init_e}"
        elif isinstance(count, int):
            return count, None # 정상적으로 정수 카운트 반환
        else:
            # 데이터 형식이 정수가 아닌 경우 (예: 문자열 "null")
             try:
                init_response = requests.put(db_url + path, json=0)
                init_response.raise_for_status()
                return 0, "카운트 초기화 완료 (잘못된 형식)."
             except requests.exceptions.RequestException as init_e:
                return 0, f"카운트 초기화 실패: {init_e}"

    except requests.exceptions.RequestException as e:
        return 0, f"Firebase 연결 오류: {e}"
    except json.JSONDecodeError:
        # Firebase에서 null 값을 반환하는 경우 json() 결과가 None이 될 수 있음
        try:
            init_response = requests.put(db_url + path, json=0)
            init_response.raise_for_status()
            return 0, "카운트 초기화 완료 (JSON 오류 발생 후)."
        except requests.exceptions.RequestException as init_e:
            return 0, f"Firebase 응답 형식 오류 (JSON 아님) 및 초기화 실패: {init_e}"
    except Exception as e:
        return 0, f"카운트 로딩 중 알 수 없는 오류: {e}"

# Firebase 카운트 업데이트 함수 (간단 버전: 읽고 +1 해서 쓰기)
# 주의: 동시 접속자가 매우 많을 경우 카운트 누락 가능성 있음 (Transaction 필요할 수 있음)
def update_firebase_count(db_url, path):
    """Firebase Realtime Database의 카운트를 1 증가시킵니다."""
    if not db_url:
        return False, "Firebase DB URL이 설정되지 않았습니다."
    try:
        # 1. 현재 값 읽기
        get_response = requests.get(db_url + path)
        get_response.raise_for_status()
        current_count = get_response.json()

        # 현재 값이 null이거나 정수가 아니면 0으로 간주
        if not isinstance(current_count, int):
            current_count = 0

        # 2. 값 증가시켜서 쓰기
        new_count = current_count + 1
        put_response = requests.put(db_url + path, json=new_count)
        put_response.raise_for_status()
        return True, new_count # 성공 시 새 카운트 반환

    except requests.exceptions.RequestException as e:
        st.error(f"카운트 업데이트 실패 (Firebase 연결 오류): {e}")
        return False, f"Firebase 연결 오류: {e}"
    except json.JSONDecodeError:
         st.error("카운트 업데이트 실패 (Firebase 응답 형식 오류)")
         # 읽기 실패 시에도 0+1=1 로 업데이트 시도 (선택적)
         try:
             put_response = requests.put(db_url + path, json=1)
             put_response.raise_for_status()
             return True, 1
         except Exception as put_e:
             st.error(f"초기화 업데이트 마저 실패: {put_e}")
             return False, "Firebase 응답 형식 오류 및 초기화 실패"
    except Exception as e:
        st.error(f"카운트 업데이트 중 알 수 없는 오류: {e}")
        return False, f"알 수 없는 오류: {e}"

# --- 앱 시작 시 누적 카운트 표시 ---
current_count, error_msg = get_firebase_count(FIREBASE_DB_URL, COUNT_PATH)
if error_msg:
    st.warning(f"누적 카운트 로딩 오류: {error_msg}. (secrets.toml에 Firebase URL 확인 필요)")
else:
    st.info(f"🔥 지금까지 총 **{current_count:,}번**의 연애 확률이 시뮬레이션 되었습니다!")

st.markdown("---") # 구분선 추가

# --- 앱 소개 텍스트 ---
st.write("""
새로운 사람을 만나는 것과 연애를 시작하는 것은 조금 다른 문제죠? 🤔\n
이 시뮬레이터는 당신의 노력과 환경에 따라 **'의미 있는 새로운 만남'**이 생길 확률과,
그 만남이 **'실제 연애'**로 이어질 확률을 각각 예측해 봅니다. (기간: 3개월 / 6개월 / 1년)\n
**내 변수를 조정해서 그(녀)를 웃게 만들어 보세요!** 연애 확률이 높아지면 그(녀)가 웃어요! 😊\n
**어떤 변수를 조절해야 할지 '감'을 잡고, 진짜 원리는 책에서 확인하세요!** 💪
""")
st.markdown("---")

# --- 변수 입력 섹션 ---
with st.expander("1️⃣ 기본 정보 & 자기 인식 (Baseline)", expanded=True):
    col1_1, col1_2 = st.columns(2)
    with col1_1:
        solo_duration = st.selectbox("현재 솔로 기간", ["6개월 미만", "6개월~2년", "2년 이상", "모태솔로"], key="solo_duration")
        # *** 성별 선택 (매우 중요!) ***
        gender = st.radio("나의 성별은?", ["여성", "남성"], key="user_gender", horizontal=True)
    with col1_2:
        age_group = st.selectbox("나이대는?", ["20대 초반", "20대 중후반", "30대 초반", "30대 중후반", "40대+"], key="age_group")
        exp_level = st.radio("연애 경험은?", ["있음", "없음"], key="exp_level", horizontal=True)

    appearance_self = st.slider("나의 외모 매력도 (스스로 평가)", 1, 10, 5, key="app_self", help="솔직하게! 1점(음...) ~ 10점(내가 봐도 연예인급)")
    appearance_others = st.slider("나의 외모 매력도 (주변 평가 기반)", 1, 10, 5, key="app_others", help="친구나 가족의 피드백을 종합해 보세요. (뼈 때려도 괜찮아요!)")
    appearance_score = (appearance_self + appearance_others) / 2
    st.info(f"📊 종합 외모 매력도: **{appearance_score:.1f}점**")

with st.expander("2️⃣ 외모 & 매력 관리 노력 (Attractiveness Upgrade)"):
    style_effort = st.select_slider("스타일링/패션 개선 노력", ["거의 안 함", "가끔 신경 씀", "적극 투자/컨설팅"], value="가끔 신경 씀", key="style")
    skin_hair_care = st.select_slider("피부/헤어 관리 수준", ["기본만", "주기적 관리", "시술/전문 관리"], value="주기적 관리", key="skin")
    body_care_effort = st.select_slider("다이어트/운동 (체형 관리)", ["안 함", "주 1-2회", "주 3회 이상", "PT/식단 병행"], value="주 1-2회", key="body")
    manner_effort = st.select_slider("표정/자세/말투 개선 노력", ["의식 안 함", "가끔 노력", "적극 교정/학습"], value="가끔 노력", key="manner")
    health_care = st.select_slider("건강 관리 (금연/절주 등)", ["관리 안 함", "노력 중", "성공/비해당"], value="노력 중", key="health")

with st.expander("3️⃣ 환경 & 네트워크 (Environment & Network)"):
    col3_1, col3_2 = st.columns(2)
    with col3_1:
        activity_range = st.selectbox("주요 활동 반경", ["집-회사 위주", "동네 중심", "시내/핫플 자주 감", "지역/해외 이동 잦음"], key="act_range")
        network_size = st.number_input("소개 가능한 친구/지인 수", 0, 50, 3, key="net_size")
    with col3_2:
        work_gender_ratio = st.slider("직장 내 이성 비율 (%)", 0, 100, 50, key="work_ratio")
        network_quality = st.slider("친구/지인의 소개 적극성", 1, 5, 3, key="net_qual")
    living_env = st.radio("주거 환경", ["부모님과 거주", "자취/독립"], key="living", horizontal=True)

with st.expander("4️⃣ 적극성 & 마인드셋 (Proactiveness & Mindset)"):
    col4_1, col4_2 = st.columns(2)
    with col4_1:
        proactiveness = st.select_slider("새로운 만남 시도 빈도", ["거의 없음", "분기 1회", "월 1회", "주 1회 이상"], value="월 1회", key="proactive")
        resilience = st.slider("거절/실패 회복탄력성", 1, 5, 3, key="resil")
    with col4_2:
        confidence = st.slider("자기 자신감 수준 (내면)", 1, 10, 6, key="confid")
        openness = st.slider("타인에 대한 개방성/호기심", 1, 5, 3, key="open")

    st.markdown("**🚫 연애 상대 필터링 분석 (나의 '절대 기준' 체크!)**")
    high_filters = st.number_input("높은 장벽 필터 개수 (이거 아니면 절대 불가!)", 0, 10, 2, key='high_filters', help="예: 최소 키 180cm, 특정 종교, 흡연 절대 반대, 연봉 1억 이상 등")
    medium_filters = st.number_input("중간 장벽 필터 개수 (매우 중요, 약간 타협 가능)", 0, 10, 3, key='medium_filters', help="예: 비슷한 가치관, 안정적 직업, 수도권 거주 등")
    low_filters = st.number_input("낮은 장벽 필터 개수 (선호하지만 필수는 아님)", 0, 10, 5, key='low_filters', help="예: 특정 취미 공유, MBTI 궁합, 연락 빈도 등")
    total_filters_weighted = (high_filters * 5.0) + (medium_filters * 2.0) + (low_filters * 0.5)
    st.info(f"✔️ 총 필터 가중치 점수: **{total_filters_weighted:.1f}점** (점수가 낮을수록 그(녀)가 다가오기 쉬워요!)")
    apply_sim_result = st.checkbox("시뮬레이션 결과를 참고하여 노력할 의향이 있음", key="apply_res")

with st.expander("5️⃣ 활동 & 라이프스타일 (Activities & Lifestyle)"):
    st.write("주로 참여하거나, 앞으로 참여하고 싶은 활동을 선택하세요 (최대 2개)")
    activities_options = {
        "선택 안 함": 0, "집콕(영화/게임/독서 등)": -5, "스터디/외국어 학원": 5,
        "공연/전시/사진/글쓰기": 10, "봉사활동/종교활동": 15, "요가/필라테스": 10,
        "등산/여행 동호회": 15, "러닝 크루 (건강+균형)": 20, "댄스/음악/미술 학원": 12,
        "헬스장(주로 혼자)": 3, "축구/농구/야구 동호회": 8, "주짓수/격투기/서핑": 25,
        "게임/IT 동아리": 5, "자동차/바이크 동호회": 8
    }
    activity1 = st.selectbox("활동 1", options=list(activities_options.keys()), key="act1")
    activity2 = st.selectbox("활동 2", options=list(activities_options.keys()), key="act2")
    activity_freq = st.select_slider("선택한 활동 참여 빈도", ["월 1회 미만", "월 1-2회", "주 1회", "주 2회 이상"], value="월 1-2회", key="act_freq")
    new_activity_try = st.select_slider("새로운 활동 시도 적극성", ["안 함", "연 1-2회", "분기 1회", "적극적"], value="연 1-2회", key="new_act")

st.markdown("---")

# --- 시뮬레이션 로직 함수들 (v2.1 베이스, 변경 없음) ---
def calculate_base_score_v2(params):
    """입력 파라미터 기반으로 기본 점수 계산"""
    score = 50
    # 외모 점수 반영
    score += (params['appearance'] - 5) * 3.0
    # 활동 반경 점수
    if params['activity_range'] == "집-회사 위주": score -= 5
    elif params['activity_range'] == "시내/핫플 자주 감": score += 3
    elif params['activity_range'] == "지역/해외 이동 잦음": score += 6
    # 네트워크 점수
    score += params['network_size'] * 0.8
    score += (params['network_quality'] - 3) * 1.5
    # 직장 이성 비율 (중심 50%에서 벗어날수록 감점 효과 유사)
    score += (params['work_gender_ratio'] / 100 - 0.5) * 10 if params['work_gender_ratio'] <= 50 else (0.5 - params['work_gender_ratio'] / 100) * 10
    if params['living_env'] == "자취/독립": score += 3
    # 적극성/마인드셋 점수
    if params['proactiveness'] == "거의 없음": score -= 10
    elif params['proactiveness'] == "월 1회": score += 3
    elif params['proactiveness'] == "주 1회 이상": score += 8
    score += (params['resilience'] - 3) * 2.0
    score += (params['confidence'] - 6) * 2.5
    score += (params['openness'] - 3) * 2.0
    # 필터링 페널티
    filter_penalty = (params['high_filters'] * 5.0) + (params['medium_filters'] * 2.0) + (params['low_filters'] * 0.5)
    score -= filter_penalty
    return max(0, min(100, score)) # 0~100 사이 값 유지

def calculate_encounter_prob_v2(base_score, params):
    """기본 점수와 활동 기반으로 만남 확률 계산"""
    activity_score = 0
    activity_score += params['activities_options'].get(params['activity1'], 0) # 없는 키 접근 방지
    activity_score += params['activities_options'].get(params['activity2'], 0)
    # 활동 빈도 가중치
    if params['activity_freq'] == "월 1-2회": activity_score *= 1.2
    elif params['activity_freq'] == "주 1회": activity_score *= 1.5
    elif params['activity_freq'] == "주 2회 이상": activity_score *= 1.8
    # 새로운 활동 시도 가중치
    if params['new_activity_try'] == "분기 1회": activity_score += 5
    elif params['new_activity_try'] == "적극적": activity_score += 10
    # 시뮬레이션 결과 참고 의향 가중치
    if params['apply_sim_result']: activity_score += 3 # 약간의 추가 점수

    total_score = base_score + activity_score
    # 로지스틱 함수 변형으로 확률 계산 (0.05 ~ 0.95 사이 유지)
    prob = 1 / (1 + np.exp(-(total_score - 60) / 15)) # 중심점 60, 스케일 15 (조정 가능)
    prob = max(0.05, min(0.95, prob))
    return prob * 100

def calculate_relationship_prob_v2(encounter_prob, base_score, params):
    """만남 확률과 매력 관리 기반으로 연애 시작 확률 계산"""
    charm_upgrade_score = 0
    # 외모/매력 관리 노력 점수
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

    # 만남 -> 연애 전환 계수 계산 (기본 점수와 매력 점수 합산 기반)
    conversion_factor = (base_score + charm_upgrade_score) / 200 # 최대 1.0 가능하도록 정규화
    conversion_factor = 0.1 + conversion_factor * 0.6 # 0.1 ~ 0.7 사이로 조정 (최소 전환율 10%, 최대 70%)
    conversion_factor = max(0.1, min(0.7, conversion_factor))

    prob = (encounter_prob / 100) * conversion_factor * 100
    # 연애 확률은 만남 확률보다 클 수 없음
    return max(0.0, min(encounter_prob, prob))

def apply_time_decay_v2(prob, months):
    """시간 경과에 따른 확률 조정 (단기 < 중기 < 장기)"""
    if months == 3: decay_factor = 0.6 # 3개월 내에는 확률 낮게 조정
    elif months == 6: decay_factor = 1.0 # 6개월 기준
    else: decay_factor = 1.3 # 1년 내에는 확률 높게 조정
    return min(99.0, prob * decay_factor) # 최대 99%

# --- 성별 기반 캐릭터 이미지 선택 함수 ---
def get_character_image_path(relationship_prob, user_gender):
    """ 사용자의 성별에 따라 상대방 성별의 캐릭터 이미지 경로를 반환 """
    # 사용자가 남성이면 여성 캐릭터, 여성이면 남성 캐릭터 표시
    target_gender_prefix = "female_char" if user_gender == "남성" else "male_char"

    # 확률 구간에 따라 파일명 접미사 결정
    if relationship_prob < 15:
        suffix = "0_15.png" # 예: images/female_char_0_15.png
    elif relationship_prob < 35:
        suffix = "15_35.png"
    elif relationship_prob < 60:
        suffix = "35_60.png"
    else:
        suffix = "60_plus.png"
    # 최종 이미지 경로 반환 (images 폴더 안에 있다고 가정)
    return f"images/{target_gender_prefix}_{suffix}"

# --- 입력값 정리 (딕셔너리) ---
# 시뮬레이션 함수들에 전달하기 위해 입력 위젯들의 현재 값을 딕셔너리로 묶음
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

# --- "시뮬레이션 실행!" 버튼 클릭 시 로직 ---
if st.button("🔮 시뮬레이션 실행!"):

    # --- 1. Firebase 카운트 업데이트 시도 ---
    update_success, update_msg = update_firebase_count(FIREBASE_DB_URL, COUNT_PATH)
    if not update_success:
        # 사용자에게 오류를 알리지만, 시뮬레이션 자체는 계속 진행
        st.error(f"카운트 업데이트 중 문제 발생: {update_msg}. 결과는 계속 표시됩니다.")

    # --- 2. 결과 계산 ---
    st.subheader("📊 기간별 예측 확률 변화")
    base_score = calculate_base_score_v2(params)
    encounter_prob_base = calculate_encounter_prob_v2(base_score, params)
    relationship_prob_base = calculate_relationship_prob_v2(encounter_prob_base, base_score, params)

    results = {'기간': [], '만남 확률 (%)': [], '연애 시작 확률 (%)': []}
    for months in [3, 6, 12]:
        encounter_p = apply_time_decay_v2(encounter_prob_base, months)
        relationship_p = apply_time_decay_v2(relationship_prob_base, months)
        relationship_p = min(encounter_p, relationship_p) # 연애 확률 > 만남 확률 방지
        results['기간'].append(f"{months}개월")
        results['만남 확률 (%)'].append(round(encounter_p, 1))
        results['연애 시작 확률 (%)'].append(round(relationship_p, 1))

    results_df = pd.DataFrame(results).set_index('기간')
    relationship_prob_6m = results_df.loc['6개월', '연애 시작 확률 (%)'] # 6개월 확률이 기준

    # --- 3. 성별 기반 캐릭터 반응 표시 ---
    user_gender = params['gender'] # 사용자가 선택한 성별
    character_image_path = get_character_image_path(relationship_prob_6m, user_gender)
    pronoun_target = "그녀" if user_gender == "남성" else "그" # 상대방 지칭 대명사
    pronoun_user = "당신" # 사용자 지칭 (혹은 "나" 로 변경 가능)

    # 캐릭터 이미지 표시 시도
    try:
        st.image(character_image_path, width=150) # 너비 조절 가능
    except FileNotFoundError:
        st.error(f"캐릭터 이미지를 찾을 수 없습니다! 경로를 확인하세요: {character_image_path}. images 폴더에 해당 파일이 있나요?")
        # 이미지 로드 실패 시 대체 이모지 표시
        if relationship_prob_6m < 15: st.markdown("### 😭")
        elif relationship_prob_6m < 35: st.markdown("### 🤔")
        elif relationship_prob_6m < 60: st.markdown("### 😊")
        else: st.markdown("### 🥰")
    except Exception as img_e:
        st.error(f"캐릭터 이미지 로딩 중 오류 발생: {img_e}")
        # 기타 오류 발생 시 대체 이모지
        if relationship_prob_6m < 15: st.markdown("### 😭") #... (이모지 반복)

    # 성별 기반 결과 코멘트 생성 및 표시
    if relationship_prob_6m < 15:
        result_comment = f"{pronoun_target}를 만나려면 아직 {pronoun_user}의 준비가 더 필요해 보여요! 🌱"
    elif relationship_prob_6m < 35:
        result_comment = f"{pronoun_target}도 {pronoun_user}을 궁금해할지 몰라요! 가능성이 보이니 힘내봐요! 💪"
    elif relationship_prob_6m < 60:
        result_comment = f"오! {pronoun_target}이 {pronoun_user}에게 다가오고 있을지도? {pronoun_target}가 웃고 있어요! 😊"
    else:
        result_comment = f"와우! {pronoun_target}가 {pronoun_user}을 향해 오고 있어요! {pronoun_target}의 환한 미소! 곧 좋은 소식 기대할게요! 💖"
    st.markdown(f"**{result_comment}**") # 결과 코멘트 표시
    st.markdown("---") # 구분선

    # --- 4. 상세 결과 (메트릭, 차트, 데이터프레임) 표시 ---
    col_res1, col_res2 = st.columns(2)
    with col_res1: st.metric("🌟 만남 확률 (향후 6개월)", f"{results_df.loc['6개월', '만남 확률 (%)']:.1f}%")
    with col_res2: st.metric("💖 연애 시작 확률 (향후 6개월)", f"{relationship_prob_6m:.1f}%")

    st.line_chart(results_df)
    with st.expander("📅 기간별 상세 확률 보기"): st.dataframe(results_df)

    # --- 5. 주요 영향 요인 분석 표시 ---
    st.markdown("---")
    st.subheader("💡 주요 영향 요인 분석")
    st.write(f"- **만남 기회:** 주로 **활동**('{params['activity1']}', '{params['activity2']}')과 **적극성**('{params['proactiveness']}')이 영향을 미쳐요.")
    st.write(f"- **관계 발전:** **매력 관리**(외모:{params['appearance']:.1f}, 스타일:{params['style_effort']} 등), **자신감**({params['confidence']}점), 그리고 **필터링**(가중치:{total_filters_weighted:.1f}점)이 중요해요.")

    # 성별 기반 필터링 경고 메시지
    if total_filters_weighted >= 20: # 예시: 필터 가중치 20점 이상일 때 강한 경고
        filter_warning_text = f"🚨 **높은 장벽 필터({params['high_filters']}개)**가 너무 많아요! {pronoun_target}가 {pronoun_user}에게 다가오는 길을 스스로 막고 있는 건 아닐까요? {pronoun_target}를 위해 정말 포기할 수 없는 기준 1~2개만 남기고 나머지는 중간 필터로 내려보는 건 어때요?"
        st.warning(filter_warning_text)
    elif total_filters_weighted >= 10: # 예시: 10~20점 사이일 때 부드러운 경고
        filter_warning_text = f"⚠️ **필터(가중치:{total_filters_weighted:.1f}점)가 약간 높은 편이에요.** {pronoun_target}와의 만남 기회를 조금 더 열어두면 {pronoun_target}도 더 쉽게 다가올 수 있을 거예요. 중간 장벽 필터를 한두 개 정도 완화해보세요."
        st.warning(filter_warning_text)

    # --- 6. 성별 기반 추천 액션 레시피 표시 ---
    st.markdown("---")
    st.subheader("🎯 나만을 위한 맞춤 조언 (액션 레시피)")
    if relationship_prob_6m < 20:
        recipe_text = f"🌱 **{pronoun_target}의 눈길 끌기 단계:** 지금은 {pronoun_target}의 시선을 사로잡을 만남 기회를 늘리는 게 중요해요! '주짓수'나 '러닝 크루' 같은 새로운 활동으로 매력을 보여주거나, '소개 가능한 친구'에게 {pronoun_target}같은 사람 없는지 물어보는 건 어떨까요? **'높은 장벽 필터'**가 {pronoun_target}의 접근을 막고 있진 않은지 점검해보세요!"
        st.info(recipe_text)
    elif relationship_prob_6m < 50:
        recipe_text = f"💪 **{pronoun_target}에게 다가가기 단계:** {pronoun_target}이 {pronoun_user} 주변에 나타나기 시작했어요! 이제 관계를 발전시킬 차례. '스타일링'에 투자해서 {pronoun_target}의 시선을 끌거나, '자신감'을 높여 {pronoun_user}의 매력을 어필해요. **{pronoun_target}가 당신에게 오기 위해 준비를 마쳤지만, {pronoun_user}의 '중간 장벽 필터' 한두 개만 낮춰주면 {pronoun_target}가 웃을지도 몰라요!** 😉"
        st.info(recipe_text)
    else: # 50% 이상
        recipe_text = f"🚀 **{pronoun_target} 맞이하기 단계:** 확률이 아주 높아요! {pronoun_target}가 거의 다 왔습니다! 지금처럼 꾸준히 매력을 유지하면서, 만나는 사람들과 진솔하게 교류하는 데 집중하세요. {pronoun_target}와의 좋은 결과가 곧 있을 거예요! **'낮은 장벽 필터'**는 너무 신경 쓰지 않아도 {pronoun_target}는 당신에게 반할 거예요!"
        st.success(recipe_text)

    # --- 7. 성별 기반 결과 공유 텍스트 표시 ---
    st.markdown("---")
    st.subheader("💌 결과 공유 & 더 알아보기")
    st.info("👇 아래 텍스트를 복사해서 인스타 스토리에 공유해보세요! (결과 화면 스크린샷과 함께!)")

    # 확률 구간별 캐릭터 감정 표현 (텍스트용)
    char_feeling_text = ""
    if relationship_prob_6m < 15: char_feeling_text = f"{pronoun_target} 만나긴 멀었나... 캐릭터 눈물 😭"
    elif relationship_prob_6m < 35: char_feeling_text = f"{pronoun_target} 올까 말까 고민 중... 🤔"
    elif relationship_prob_6m < 60: char_feeling_text = f"{pronoun_target} 웃고 있다! 😊"
    else: char_feeling_text = f"{pronoun_target} 완전 반했나봐! 🥰"

    share_text_insta = f"""
    💖 향후 6개월 연애 확률: {relationship_prob_6m:.1f}% 💖
    ({char_feeling_text})
    내가 변수 조정해서 {pronoun_target} 웃게 만들기 성공?! ✨
    🔥 '{params['activity1']}' 활동 덕분인가? 🔥
    🤔 확률 올리는 비법 궁금하면? 👉 책으로!
    👇 너도 해봐! [https://lovesim.streamlit.app/]
    #연애시뮬레이터 #시뮬레이션된베스트셀러 #연애확률 #{pronoun_target}기다려 #내캐릭터는귀엽지
    """
    st.code(share_text_insta, language=None) # language=None으로 복사 버튼 생성

    # --- 8. 책 판매 연계 섹션 ---
    st.markdown("---")
    st.subheader("📚 변수 설정의 비밀? 책에서 확인하세요!")
    # st.image("your_book_cover_image.jpg", width=150) # 실제 책 표지 이미지 경로 넣기
    st.write(f"""
    이 시뮬레이터는 『시뮬레이션된 베스트셀러』에 담긴 **데이터 기반 의사결정 원리**의 맛보기 버전입니다.\n
    - **외모, 활동, 필터링... 각 변수의 정확한 가중치**는 어떻게 설정되었을까요?
    - '자신감'과 '적극성'은 확률에 **얼마나, 어떻게 상호작용**할까요?
    - 이 **시뮬레이터의 로직 자체**는 어떻게 더 정교하게 만들 수 있을까요?\n
    단순히 확률을 아는 것을 넘어, 당신의 **삶 전체를 설계하는 방법**을 배우고 싶다면?\n
    **모든 핵심 원리와 설계 비밀**은 책 속에 담겨 있습니다.
    """)
    # !!! 실제 책 구매 링크로 꼭 변경하세요 !!!
    book_purchase_link = "https://blog.naver.com/moneypuzzler/223837610193" # 예시: YES24 검색 링크
    st.link_button("👉 『시뮬레이션된 베스트셀러』소개하는 블로그 바로가기!", book_purchase_link, type="primary")

    # --- 9. 작가의 한마디 (마무리) ---
    st.markdown("---")
    st.text_area(
        "작가의 한마디 📝 ",
        "이 시뮬레이터는 '이렇게도 생각해볼 수 있다'는 사고 확장을 위한 것입니다.\n\n"
        "타로카드처럼 재미로 보시되, 절대적 진리로 믿진 마세요! 여러분의 매력, 노력, 그리고 시뮬레이션에 없는 '우연한 만남'의 가능성이 훨씬 중요합니다. 단골 카페에서, 혹은 홍대 펍에서 운명이 기다릴 수도 있으니까요 😉\n\n"
        "중요한 건 데이터로 사고하는 '연습'을 통해, 내 삶의 변수를 직접 통제 해보려는 '의지'입니다.",
        height=250, # 높이 약간 늘림
        key="author_note_final"
    )

# --- 버튼 클릭 전 초기 화면 안내 ---
else:
    st.info("☝️ 위의 변수들을 입력하고 '시뮬레이션 실행!' 버튼을 눌러 결과를 확인하세요!")
    st.markdown("---")
    # 초기 화면에도 책 홍보 살짝
    st.write("결과 예측의 비밀이 궁금하다면? 👇")
    book_purchase_link_init = "https://www.instagram.com/dimenpuzzler?igsh=MXd1d29wMGdiZjF3YQ=="
    st.link_button("『시뮬레이션된 베스트셀러』 작가 인스타가기", book_purchase_link_init)
