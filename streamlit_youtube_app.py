import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import time
from datetime import datetime

# ✅ 유튜브 API 키 입력
API_KEY = 'AIzaSyCGFXGeKbaMQpRzOD1l41W8Jht-aSA9cJA'

youtube = build('youtube', 'v3', developerKey=API_KEY)

st.title("📺 유튜브 키워드 영상 분석기")
with st.container():
    st.markdown("""
        <div style='background-color:#03c75a; padding:20px; border-radius:10px; text-align:center; color:white'>
            🌱 <strong>호행부부 커뮤니티</strong><br>
            심리 및 관계에서 진짜 변화를 만들고 싶은 분들을 위한 성장 커뮤니티입니다.<br><br>
            <a href='https://cafe.naver.com/f-e/cafes/31468087/menus/0' target='_blank'
               style='color:white; font-weight:bold; text-decoration:none;'>
               👉 커뮤니티 바로가기
            </a>
        </div>
    """, unsafe_allow_html=True)
    
keywords_input = st.text_input("🔍 분석할 키워드를 쉼표(,)로 구분해 입력하세요", "감정 표현, 회피형 애착")
max_results = st.slider("🎯 키워드당 검색할 영상 수", 1, 20, 5)

if st.button("분석 시작", key="analysis_start"):
    keywords = [k.strip() for k in keywords_input.split(",")]
    results = []

    with st.spinner("유튜브에서 데이터를 수집 중입니다..."):
        for keyword in keywords:
            st.write(f"▶️ 키워드: `{keyword}`")
            try:
                search_response = youtube.search().list(
                    q=keyword,
                    part='snippet',
                    type='video',
                    maxResults=max_results
                ).execute()

                video_ids = [item['id']['videoId'] for item in search_response['items']]
                video_response = youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(video_ids)
                ).execute()

                for video in video_response['items']:
                    title = video['snippet']['title']
                    channel = video['snippet']['channelTitle']
                    published = video['snippet']['publishedAt']
                    video_id = video['id']
                    view_count = int(video['statistics'].get('viewCount', 0))
                    duration = video['contentDetails']['duration']
                    channel_id = video['snippet']['channelId']

                    channel_response = youtube.channels().list(
                        part='statistics',
                        id=channel_id
                    ).execute()
                    subscriber_count = int(channel_response['items'][0]['statistics'].get('subscriberCount', 0))
                    viral_index = round(view_count / subscriber_count, 2) if subscriber_count > 0 else 'N/A'

                    results.append({
                        '키워드': keyword,
                        '제목': title,
                        '채널': channel,
                        '조회수': view_count,
                        '구독자 수': subscriber_count,
                        '바이럴 지수': viral_index,
                        '길이': duration,
                        '링크': f'https://youtu.be/{video_id}',
                        '업로드 날짜': published
                    })

                time.sleep(1)  # API 호출 제한 방지

            except Exception as e:
                st.error(f"❗ 오류 발생: {e}")
                continue

    # 결과를 데이터프레임으로 변환
    df = pd.DataFrame(results)

    # 전체 결과 출력
    st.success("✅ 분석 완료!")
    st.subheader("📋 전체 분석 결과")
    st.dataframe(df)
    # 📁 날짜 포함된 엑셀 저장
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows

    today = datetime.today().strftime('%Y-%m-%d')
    file_name = f"유튜브_분석결과_{today}.xlsx"

    # 📊 요약 정보 만들기
    summary_data = {
        '분석 날짜': [today],
        '키워드 수': [df['키워드'].nunique()],
        '총 영상 수': [len(df)],
        '전체 조회수': [df['조회수'].sum()],
        '평균 조회수': [round(df['조회수'].mean(), 2)],
        '평균 바이럴 지수': [round(df[df['바이럴 지수'] != 'N/A']['바이럴 지수'].astype(float).mean(), 2)]
    }
    summary_df = pd.DataFrame(summary_data)

    # 💾 엑셀 저장
    wb = Workbook()
    ws_summary = wb.active
    ws_summary.title = "요약 리포트"

    for r in dataframe_to_rows(summary_df, index=False, header=True):
        ws_summary.append(r)

    ws_data = wb.create_sheet("전체 분석 결과")
    for r in dataframe_to_rows(df, index=False, header=True):
        ws_data.append(r)

    wb.save(file_name)

    with open(file_name, "rb") as f:
        st.download_button("📥 분석 결과 엑셀 다운로드", f.read(), file_name=file_name, mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


    # 📏 일평균 조회수 계산
    df['업로드 날짜'] = pd.to_datetime(df['업로드 날짜'])
    df['일수 경과'] = (pd.Timestamp.now(tz='UTC') - df['업로드 날짜']).dt.days + 1
    df['일평균 조회수'] = (df['조회수'] / df['일수 경과']).round(2)

    # ... 앞부분 생략 ...

    df = pd.DataFrame(results)
    df['업로드 날짜'] = pd.to_datetime(df['업로드 날짜'])
    df['일수 경과'] = (pd.Timestamp.now(tz='UTC') - df['업로드 날짜']).dt.days + 1
    df['일평균 조회수'] = (df['조회수'] / df['일수 경과']).round(2)

    # 🔥 지금 뜨는 콘텐츠 TOP 5
    st.subheader("🔥 지금 뜨는 콘텐츠 TOP 5")
    hot_df = df.sort_values(by='일평균 조회수', ascending=False).head(5)
    st.dataframe(hot_df[['키워드', '제목', '채널', '조회수', '일수 경과', '일평균 조회수', '링크']])

    # 🔥 바이럴 지수 상위 TOP 5
    st.subheader("🔥 바이럴 지수 TOP 5")
    top_df = df[df['바이럴 지수'] != 'N/A']
    top_df = top_df.sort_values(by='바이럴 지수', ascending=False).head(5)
    st.dataframe(top_df)

    # 📊 키워드별 총 조회수 그래프
    st.subheader("📊 키워드별 총 조회수 그래프")
    if not df.empty:
        keyword_views = df.groupby('키워드')['조회수'].sum().sort_values(ascending=False)
        st.bar_chart(keyword_views)

    # 📁 엑셀 저장
    today = datetime.today().strftime('%Y-%m-%d')

