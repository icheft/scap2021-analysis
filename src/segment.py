from re import L
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from numpy.core.fromnumeric import sort
import streamlit as st
import os

from traitlets.traitlets import default
from src.component import convert_df
from src import process as ps
from gsheetsdb import connect
import pandasql as psql
import pandas as pd
import io
import numpy as np
import plotly.express as px

profile_dict = {
    '全選': [],
    '(A) 有望成為 API 交易人：程式 + 1,000 萬以上': [7, 25],
    '(B) 普通有望成為 API 交易人：程式 + 200-1,000 萬': [7, 3],
    '(C) 嘗鮮人：程式 + 200 萬以下': [7, 23],
    '(D) 大鯨魚：1,000 萬以上成交量': [13, 25],
    '(E) 小鯨魚：200-1,000 萬成交量': [13, 3],
    '(F) DROPPED：200 萬以下成交量': [13, 23],
    '鯨魚: 3000 萬以上': [0],
    '競品的用戶: 有在用永豐 + 實際寫過 API': [2, 6],
    '最理想用戶 I - 分或小時交易: 200-1000 萬成交量 + 分或小時交易 + 會寫程式 + 沒有實際用過 API': [3, 4, 7, 5],
    '最理想用戶 II - 日交易: 200-1000 萬成交量 + 日交易 + 會寫程式 + 沒有實際用過 API': [3, 1, 7, 5],
}

color_map = {
    # color_discrete_map
    '(A) 有望成為 API 交易人：程式 + 1,000 萬以上': '#9b5de5',
    '(B) 普通有望成為 API 交易人：程式 + 200-1,000 萬': '#f15bb5',
    '(C) 嘗鮮人：程式 + 200 萬以下': '#fee440',
    '(D) 大鯨魚：1,000 萬以上成交量': '#00bbf9',
    '(E) 小鯨魚：200-1,000 萬成交量': '#00f5d4',
    '(F) DROPPED：200 萬以下成交量': '#979dac',
    'All': '#266A2E'
}

df_order = {
    # category_orders
    'label': ['(A) 有望成為 API 交易人：程式 + 1,000 萬以上',
              '(B) 普通有望成為 API 交易人：程式 + 200-1,000 萬',
              '(C) 嘗鮮人：程式 + 200 萬以下',
              '(D) 大鯨魚：1,000 萬以上成交量',
              '(E) 小鯨魚：200-1,000 萬成交量',
              '(F) DROPPED：200 萬以下成交量'],
}

student_picker_lst = ['All', 'Student', 'Non-Student']


def bar_with_data(data: np.ndarray, x_name: str, y_name: str, color: str) -> None:

    value_counts = dict()
    for val in data:
        for v in val.split("\n"):  # Survey Cake format
            if v not in value_counts:
                value_counts[v] = 1
            else:
                value_counts[v] += 1

    if "其他" not in value_counts:
        value_counts["其他"] = 0

    # 把有「其他」的都算一起
    for k in value_counts:
        if k != "其他" and "其他" in k:
            value_counts["其他"] += value_counts[k]
            value_counts[k] = 0

    # 刪掉 count 是 0 的
    value_counts = dict({k: v for k, v in value_counts.items() if v})

    # 排序，並 truncate 以及算比例
    counts = list([
        v
        for _, v in sorted(value_counts.items(), key=lambda item: -item[1])
    ])
    keys = list([
        "{} ({}%)".format(
            (k if len(k) < 10 else "{} ...".format(
                k[:10])) if k != "nan" else "未填答",
            round(v / len(data) * 100, 2)
        )
        for k, v in sorted(value_counts.items(), key=lambda item: -item[1])
    ])

    dummy_dict = {x_name: [], y_name: []}
    for i in range(len(counts)):
        dummy_dict[x_name].append(keys[i])
        dummy_dict[y_name].append(counts[i])

    fig = px.bar(dummy_dict, x=x_name, y=y_name, title=x_name.upper())
    fig.update_traces(marker_color=color)
    fig.update_layout(margin=dict(b=0, l=0, r=0))

    return fig


def get_custom_feature_dict(inverse=False) -> dict:
    cfd = {0: '月交易量 3000 萬以上',
           1: '日交易',
           2: '有使用過 API trading',
           3: '月交易量 200-1000 萬',
           4: '分、小時交易',
           5: '沒使用過 API 做交易',
           6: '有在用永豐的人',
           7: '會寫程式',
           8: '僅用過套裝軟體',
           9: '擁有 Portfolio 且有五隻股票以上',
           10: '月交易量 51-200 萬',
           11: '月交易量 50 萬以下',
           12: '月交易量 51-1000 萬',
           13: '不會寫程式',
           14: '有一定程式能力（三、四級）',
           15: 'Only 男',
           16: 'Only 女',
           17: 'Unix',
           18: 'Python or Node.js',
           19: '台股交易需求',
           20: '沒有台股交易需求',
           21: '非學生',
           22: '學生',
           23: '月交易量 200 萬以下',
           24: '月交易量 200 萬以上',
           25: '月交易量 1,000 萬以上',
           }
    if inverse:
        cfd = {v: k for k, v in cfd.items()}
    return cfd


def get_dict(table_name: str) -> dict:

    return {
        0: f"SELECT * FROM {table_name} WHERE P LIKE '3,000%';",
        1: f"SELECT * FROM {table_name} WHERE O LIKE '日%';",
        2: f"SELECT * FROM {table_name} WHERE A LIKE '實際寫過程式%';",
        3: f"SELECT * FROM {table_name} WHERE P LIKE '201%';",
        4: f"SELECT * FROM {table_name} WHERE O LIKE '分、小時%';",
        5: f"SELECT * FROM {table_name} WHERE A NOT LIKE '實際寫過程式%';",
        6: f"SELECT * FROM {table_name} WHERE I LIKE '%永豐%';",
        7: f"SELECT * FROM {table_name} WHERE T NOT LIKE '完全沒寫過%';",
        8: f"SELECT * FROM {table_name} WHERE A LIKE '使用過套裝軟體%';",
        9: f"SELECT * FROM {table_name} WHERE M = '是';",
        10: f"SELECT * FROM {table_name} WHERE P LIKE '51%';",
        11: f"SELECT * FROM {table_name} WHERE P LIKE '50%';",
        12: f"SELECT * FROM {table_name} WHERE P LIKE '51%' OR P LIKE '201%'",
        13: f"SELECT * FROM {table_name} WHERE T LIKE '完全沒寫過%';",
        14: f"SELECT * FROM {table_name} WHERE (T NOT LIKE '完全沒寫過%' AND T NOT LIKE '會寫基本的程式%');",
        15: f"SELECT * FROM {table_name} WHERE W = '男';",
        16: f"SELECT * FROM {table_name} WHERE W = '女';",
        17: f"SELECT * FROM {table_name} WHERE (UPPER(S) LIKE UPPER('%mac%') OR UPPER(S) LIKE UPPER('%linux%'));",
        18: f"SELECT * FROM {table_name} WHERE (U LIKE '%Python%' OR U LIKE '%Node%');",
        19: f"SELECT * FROM {table_name} WHERE N LIKE '%台股%';",
        20: f"SELECT * FROM {table_name} WHERE N NOT LIKE '%台股%';",
        21: f"SELECT * FROM {table_name} WHERE Z <> '學生';",
        22: f"SELECT * FROM {table_name} WHERE Z = '學生';",
        23: f"SELECT * FROM {table_name} WHERE (P LIKE '50%' OR P LIKE '51%')",
        24: f"SELECT * FROM {table_name} WHERE (P NOT LIKE '50%' AND P NOT LIKE '51%')",
        25: f"SELECT * FROM {table_name} WHERE (P LIKE '1,000%' OR P LIKE '3,000%')",
    }


def sidebar_helper():
    st.sidebar.success('testing')
    pass


def default_ta():
    option = st.selectbox(
        'Choose a profile to continue',
        [key for key in profile_dict.keys()])
    return profile_dict[option]


def multi_ta_picker():
    options = st.multiselect('Choose any profile(s) to continue', options=list(
        profile_dict.keys())[1:7], default=list(profile_dict.keys())[1:6])

    option = st.selectbox('學生/非學生', options=student_picker_lst)

    return options, option


def custom_feature_form():
    customized = st.expander('Need custom input? 👉🏽')
    features = [False for _ in range(13)]
    return_obj = None
    with customized:
        with st.form("criteria_form"):
            st.write("Custom Features（我們選出的 criteria - 選項皆為 `AND`）")
            cf_dict = get_custom_feature_dict(True)
            selected = st.multiselect(
                label='特定 feature 篩選', options=cf_dict.keys())
            # for s in selected:
            #     features[cf_dict[s]]

            submitted = st.form_submit_button("Submit")
            if submitted:
                return_obj = selected

        st.markdown("""
                    <center>OR</center>
                    <br/>""", unsafe_allow_html=True)

        with st.form("query_form"):
            st.markdown("自訂 query (table name = `output_df`)")

            query = st.text_area(
                'Custom Query (in SQL)', 'SELECT * FROM output_df;')
            submitted = st.form_submit_button("Submit")
            if submitted:
                return_obj = query

        return return_obj


def multiple_choice_stats(df=None, columns=['Label', 'X_name', 'Count'], labels=[], x_names=[], y_name: str = None) -> pd.DataFrame:
    group_df = pd.DataFrame(columns=columns)

    for l_name in sorted(labels):
        cnt = dict()
        for val in df[df['label'] == l_name][y_name]:
            for ch in x_names:
                if ch in val:
                    if ch not in cnt:
                        cnt[ch] = 1
                    else:
                        cnt[ch] += 1
        # dict = {'Background': [], 'Count': []}
        for key, value in cnt.items():
            group_df = group_df.append(
                {columns[0]: l_name, columns[1]: key, columns[2]: value}, ignore_index=True)
    return group_df


def runner(df: pd.DataFrame):
    ta_criteria = default_ta()
    output_df = df.copy()
    ori_len = len(output_df)
    custom_feature = custom_feature_form()
    output_df = psql.sqldf(
        'select * from output_df;', locals())
    if custom_feature is not None:
        st.success(f'✍️ 使用 custom profile')
        query_dict = get_dict('output_df')
        if type(custom_feature) is not str:
            render_str = """"""
            for i in range(len(custom_feature)):
                query = query_dict[get_custom_feature_dict(
                    True)[custom_feature[i]]]  # no#
                output_df = psql.sqldf(
                    query, locals())
                if i == 0:
                    render_str += (
                        f'''+ 篩出「{custom_feature[i]}」: {len(output_df)} out of {ori_len} ({round(len(output_df) / ori_len * 100, 2)}%)\n''')
                else:
                    render_str += (
                        f'''+ 篩出「{custom_feature[i]}」: {len(output_df)} out of {pre_len} ({round(len(output_df) / pre_len * 100, 2)}%)\n''')
                pre_len = len(output_df)

            st.markdown(render_str, unsafe_allow_html=True)
        else:
            output_df = psql.sqldf(
                custom_feature, locals())

    else:
        st.success(f'✍️ 使用 default profile')
        query_dict = get_dict('output_df')
        for c in ta_criteria:
            output_df = psql.sqldf(
                query_dict[c], locals())

    st.markdown(
        f'''{len(output_df)} out of {ori_len} ({round(len(output_df) / ori_len * 100, 2)}%)''')
    st.write(output_df.head())
    st.download_button(
        label=f"📓 Download (.csv)",
        data=convert_df(output_df),
        file_name=f'output.csv',
        mime='text/csv',
    )

    # final target customer traits
    st.markdown('## User Profile')
    row1_1, row1_2 = st.columns(
        (1, 1))
    with row1_1:
        fig = px.bar(output_df.groupby('X').agg(
            'size').reset_index(), x='X', y=0, labels={
            '0': 'Count', 'X': 'Age'})
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

        st.plotly_chart(fig, use_container_width=True)
    with row1_2:
        fig = px.bar(output_df.groupby('W').agg(
            'size').reset_index(), x='W', y=0, labels={
            '0': 'Count', 'W': 'Gender'})
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

        st.plotly_chart(fig, use_container_width=True)

    row2_1, row2_2 = st.columns(
        (1, 1))
    with row2_1:
        fig = px.bar(output_df.groupby('P').agg(
            'size').reset_index(), x='P', y=0, labels={
            '0': 'Count', 'P': 'Frequency'})
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

        st.plotly_chart(fig, use_container_width=True)
    with row2_2:
        fig = px.bar(output_df.groupby('O').agg(
            'size').reset_index(), x='O', y=0, labels={
            '0': 'Count', 'O': 'Frequency'})
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

        st.plotly_chart(fig, use_container_width=True)

    row3_1, row3_2 = st.columns(
        (1, 1))
    with row3_1:
        study_background = [
            '商管/人文/社會相關 (e.g. 企管、財會、歷史、哲學等)', '資訊/工程/數理相關 (e.g.資工、電機、資管、土木、機械、化工等)', '醫學/生物/農業相關 (e.g. 醫科、護理、森林、生科等)', '藝術/傳播相關 (e.g. 傳播、音樂、設計等)']
        sb_cnt = dict()
        for val in output_df['Y']:
            for ch in study_background:
                if ch in val:
                    if ch not in sb_cnt:
                        sb_cnt[ch] = 1
                    else:
                        sb_cnt[ch] += 1
        sb_dict = {'Background': [], 'Count': []}
        for key, value in sb_cnt.items():
            sb_dict['Background'].append(key)
            sb_dict['Count'].append(value)
        fig = px.bar(sb_dict, x='Background', y='Count')
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

        st.plotly_chart(fig, use_container_width=True)

    with row3_2:
        fig = px.bar(output_df.groupby('Z').agg(
            'size').reset_index(), x='Z', y=0, labels={
            '0': 'Count', 'Z': 'Occupation'})
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

        st.plotly_chart(fig, use_container_width=True)

    st.markdown('#### Channels')

    learn_investment_ch = ['資訊平台（如鉅亨網、 Investing.com、 Tradingview 等',
                           'Podcast', '券商', 'YouTuber', '新聞（如 Yahoo 新聞、實體報紙、 LineToday 等）', '書籍', '自行 Google', '社群平台']

    learn_coding_ch = ['國內線上學習平台（如量化通、HaHow 等）', '看 Medium 文章',
                       '閱讀書籍', '國外線上學習平台（如 Cousera、Udemy、edX 等）', 'YouTube 頻道', '學校上課']

    # this is probably the dumbest way, but I am not in the stackoverflow mode
    lich_cnt = dict()
    for val in output_df['R']:
        for ch in learn_investment_ch:
            if ch in val:
                if ch not in lich_cnt:
                    lich_cnt[ch] = 1
                else:
                    lich_cnt[ch] += 1
    lcch_cnt = dict()
    for val in output_df['V']:
        for ch in learn_coding_ch:
            if ch in val:
                if ch not in lcch_cnt:
                    lcch_cnt[ch] = 1
                else:
                    lcch_cnt[ch] += 1

    lcch_dict = {'Channel': [], 'Count': []}
    for key, value in lcch_cnt.items():
        lcch_dict['Channel'].append(key)
        lcch_dict['Count'].append(value)

    lich_dict = {'Channel': [], 'Count': []}
    for key, value in lich_cnt.items():
        lich_dict['Channel'].append(key)
        lich_dict['Count'].append(value)

    row4_1, row4_2 = st.columns(
        (1, 1))
    with row4_1:
        st.write('程式學習管道')
        fig = px.bar(lcch_dict, x='Channel', y='Count')
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

        st.plotly_chart(fig, use_container_width=True)

    with row4_2:
        st.write('投資理財管道')
        fig = px.bar(lich_dict, x='Channel', y='Count')
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

        st.plotly_chart(fig, use_container_width=True)

    load_more_charts = st.checkbox(
        '要載入全部圖檔嗎？ (會吃大量記憶體 🥵 + 需要重新提交 custom selected features 😔)')
    if load_more_charts:
        more_chart = st.expander('More charts 🙈')

        with more_chart:
            for key in output_df.columns[:-10]:
                if key == "id":
                    # Skip first col
                    continue
                try:
                    st.plotly_chart(bar_with_data(
                        output_df[key].to_numpy().flatten(),
                        x_name=ps.column_loader()[key],
                        y_name='Frequency'
                    ), use_container_width=True)
                except:
                    st.write(f'{ps.column_loader()[key]} ({key}) is skipped.')


def report_runner(df: pd.DataFrame):
    ta_criteria, student_flag = multi_ta_picker()
    ori_len = len(df)
    queries = [profile_dict[opt] for opt in ta_criteria]

    query_dict = get_dict('df')
    if student_flag == student_picker_lst[1]:
        df = psql.sqldf(
            query_dict[22], locals())
    elif student_flag == student_picker_lst[2]:
        df = psql.sqldf(
            query_dict[21], locals())

    for i, qs in enumerate(queries):
        query_dict = get_dict('tmp_df')
        tmp_df = df.copy()
        for q in qs:
            tmp_df = psql.sqldf(
                query_dict[q], locals())
        tmp_df = tmp_df.assign(label=ta_criteria[i])
        if i == 0:
            output_df = tmp_df
        else:
            output_df = output_df.append(tmp_df).reset_index(drop=True)
    if len(queries) == 0:
        st.info('No queries given. Displaying all results...')
        output_df = df
        output_df = output_df.assign(label='All')
        ta_criteria = ['All']

    st.markdown(
        f'''{len(output_df)} out of {ori_len} ({round(len(output_df) / ori_len * 100, 2)}%)''')
    st.write(output_df)

    st.download_button(
        label=f"📓 Download (.csv)",
        data=convert_df(output_df),
        file_name=f'output.csv',
        mime='text/csv',
    )

    # final target customer traits
    st.markdown('## User Profile')

    st.markdown('Basic Information')
    fig = px.pie(output_df.groupby(['label']).agg(
        'size').reset_index().sort_values('label'), values=0, names='label', color='label', color_discrete_map=color_map, labels={
        '0': 'Count', 'X': 'Age', 'label': 'Label'})
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    fig.update_traces(textposition='inside', textinfo='percent+label')

    st.plotly_chart(fig, use_container_width=True)

    st.markdown('#### Age')
    fig = px.bar(output_df.groupby(['label', 'X']).agg(
        'size').reset_index().sort_values('X'), x='X', y=0, color='label', barmode='group',
        labels={
        '0': 'Count', 'X': 'Age', 'label': 'Label'},
        color_discrete_map=color_map,
        category_orders=df_order)
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

    st.plotly_chart(fig, use_container_width=True)

    st.markdown('#### Gender')
    fig = px.bar(output_df.groupby(['label', 'W']).agg(
        'size').reset_index(), x='W', y=0, labels={
        '0': 'Count', 'W': 'Gender', 'label': 'Label'}, barmode='group', color='label', color_discrete_map=color_map,
        category_orders=df_order)
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

    st.plotly_chart(fig, use_container_width=True)

    st.markdown('#### 交易量')
    fig = px.bar(output_df.groupby(['label', 'P']).agg(
        'size').reset_index(), x='P', y=0, labels={
        '0': 'Count', 'P': '交易量', 'label': 'Label'}, color='label', color_discrete_map=color_map,
        category_orders=df_order)
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

    st.plotly_chart(fig, use_container_width=True)

    st.markdown('#### 交易頻率')
    fig = px.bar(output_df.groupby(['label', 'O']).agg(
        'size').reset_index(), x='O', y=0, labels={
        '0': 'Count', 'O': '交易頻率', 'label': 'Label'}, barmode='group', color='label', color_discrete_map=color_map,
        category_orders=df_order)
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

    st.plotly_chart(fig, use_container_width=True)

    st.markdown('#### 教育背景')
    sb_group_df = multiple_choice_stats(output_df, columns=['Label', 'Background', 'Count'], labels=ta_criteria, x_names=[
        '商管/人文/社會相關 (e.g. 企管、財會、歷史、哲學等)', '資訊/工程/數理相關 (e.g.資工、電機、資管、土木、機械、化工等)', '醫學/生物/農業相關 (e.g. 醫科、護理、森林、生科等)', '藝術/傳播相關 (e.g. 傳播、音樂、設計等)'], y_name='Y')
    fig = px.bar(sb_group_df, x='Background', y='Count', barmode='group', color='Label', color_discrete_map=color_map,
                 category_orders=df_order)
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

    st.plotly_chart(fig, use_container_width=True)

    st.markdown('#### 職業')
    fig = px.bar(output_df.groupby(['label', 'Z']).agg(
        'size').reset_index(), x='Z', y=0, labels={
        '0': 'Count', 'Z': 'Occupation', 'label': 'Label'}, barmode='group', color='label', color_discrete_map=color_map,
        category_orders=df_order)
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

    st.plotly_chart(fig, use_container_width=True)

    st.markdown('### Channels')

    learn_investment_ch = ['資訊平台（如鉅亨網、 Investing.com、 Tradingview 等',
                           'Podcast', '券商', 'YouTuber', '新聞（如 Yahoo 新聞、實體報紙、 LineToday 等）', '書籍', '自行 Google', '社群平台']

    learn_coding_ch = ['國內線上學習平台（如量化通、HaHow 等）', '看 Medium 文章',
                       '閱讀書籍', '國外線上學習平台（如 Cousera、Udemy、edX 等）', 'YouTube 頻道', '學校上課']

    lich_group_df = multiple_choice_stats(output_df, columns=[
                                          'Label', 'Channel', 'Count'], labels=ta_criteria, x_names=learn_investment_ch, y_name='R')
    lcch_group_df = multiple_choice_stats(output_df, columns=[
                                          'Label', 'Channel', 'Count'], labels=ta_criteria, x_names=learn_coding_ch, y_name='V')

    st.markdown('##### 程式學習管道')

    fig = px.bar(lich_group_df, x='Channel', y='Count', barmode='group', color='Label', color_discrete_map=color_map,
                 category_orders=df_order)
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

    st.plotly_chart(fig, use_container_width=True)

    st.markdown('##### 投資理財管道')
    fig = px.bar(lcch_group_df, x='Channel', y='Count', barmode='group', color='Label', color_discrete_map=color_map,
                 category_orders=df_order)
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))

    st.plotly_chart(fig, use_container_width=True)

    if len(queries) <= 1:
        load_more_charts = st.checkbox(
            '要載入全部圖檔嗎？ (會吃大量記憶體 🥵）')
        if load_more_charts:
            more_chart = st.expander('More charts 🙈')

            with more_chart:
                for key in output_df.columns[:-10]:
                    if key == "id":
                        # Skip first col
                        continue
                    try:

                        st.plotly_chart(bar_with_data(
                            output_df[key].to_numpy().flatten(),
                            x_name=ps.column_loader()[key],
                            y_name='Frequency', color=color_map[ta_criteria[0]]), use_container_width=True)

                    except:
                        st.write(
                            f'{ps.column_loader()[key]} ({key}) is skipped.')
