import streamlit as st

st.title("간단한 계산 & 데이터 대시보드 📊")

# 텍스트 및 기본 입력
name = st.text_input("프로젝트 또는 사용자 이름:", value="테스트")
st.write(f"현재 선택된 이름: **{name}**")

# 수치 입력과 슬라이더
val1 = st.number_input("기준 값 A 입력", value=500.0, step=2.0)
val2 = st.slider("계수 B 선택", min_value=1.0, max_value=5.0, value=2.5, step=0.1)

# 계산 결과 출력
result = val1 * val2
st.metric(label="계산 결과 (A × B)", value=f"{result:.2f}")

# 버튼 동작
if st.button("결과 확인 완료"):
    st.success("계산이 정상적으로 완료되었습니다!")