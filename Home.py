import streamlit as st
import pandas as pd
import io
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import plotly.figure_factory as ff
from utils import process_data, get_download_data

def calculate_review_stats(df):
    """计算评论类型的统计信息"""
    # 计算各类型数量
    review_counts = df['Review Type'].value_counts()
    
    # 计算百分比
    review_percentages = (review_counts / len(df) * 100).round(2)
    
    # 合并统计信息
    stats_df = pd.DataFrame({
        '数量': review_counts,
        '占比(%)': review_percentages
    })
    
    return stats_df, review_counts, review_percentages

def create_pie_chart(review_counts, title='评论类型分布'):
    """创建饼图"""
    fig = px.pie(
        values=review_counts.values,
        names=review_counts.index,
        title=title,
        color_discrete_map={
            'positive': '#2ECC71',
            'neutral': '#F1C40F',
            'negative': '#E74C3C',
            'unknown': '#95A5A6'
        }
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def analyze_by_group(df, group_by):
    """按指定字段进行分组分析"""
    # 始终计算ASIN维度的统计信息
    asin_stats = df.groupby('Asin').agg({
        'Rating': ['count', 'mean', 'std'],
        'Review Type': lambda x: x.value_counts().to_dict()
    }).round(2)
    
    # 重命名列
    asin_stats.columns = ['评论数量', '平均评分', '标准差', '评论类型分布']
    
    # 计算ASIN的评分分布
    rating_dist = df.groupby(['Asin', 'Rating']).size().unstack(fill_value=0)
    rating_dist_pct = rating_dist.div(rating_dist.sum(axis=1), axis=0) * 100
    
    # 如果是Asin+Model分析，创建组合数据用于时间趋势图
    if isinstance(group_by, list):
        df['Group'] = df['Asin'] + ' - ' + df['Model']
        group_by_trend = 'Group'
    else:
        group_by_trend = 'Asin'
    
    return asin_stats, rating_dist_pct, group_by_trend

def create_rating_trend_chart(df, group_by):
    """创建评分趋势图"""
    # 按时间和分组计算平均评分
    df['Month'] = df['Date'].dt.to_period('M').astype(str)
    trend_data = df.groupby(['Month', group_by])['Rating'].mean().reset_index()
    
    # 创建趋势图
    title = 'Asin-Model组合随时间的平均评分变化' if group_by == 'Group' else 'Asin随时间的平均评分变化'
    
    fig = px.line(trend_data, 
                  x='Month', 
                  y='Rating', 
                  color=group_by,
                  title=title,
                  labels={'Rating': '平均评分', 'Month': '月份'})
    
    fig.update_xaxes(tickangle=45)
    return fig

def create_rating_heatmap(rating_dist_pct, title):
    """创建评分分布热力图"""
    fig = go.Figure(data=go.Heatmap(
        z=rating_dist_pct.values,
        x=rating_dist_pct.columns,
        y=rating_dist_pct.index,
        colorscale='RdYlGn',
        text=rating_dist_pct.round(1).values,
        texttemplate='%{text}%',
        textfont={"size": 10},
        hoverongaps=False))
    
    fig.update_layout(
        title=title,
        xaxis_title='评分',
        yaxis_title='产品',
        height=max(300, len(rating_dist_pct) * 30))
    
    return fig

def save_fig_to_html(fig, filename):
    """保存图表为HTML文件"""
    return fig.to_html()

def main():
    st.set_page_config(
        page_title="Amazon评论分析工具",
        page_icon="📊",
        layout="wide"
    )

    st.title("Amazon评论分析工具 - 数据预处理")
    st.write("第一步：上传Excel文件进行数据预处理")
    
    uploaded_file = st.file_uploader("选择Excel文件", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            
            # 显示原始数据信息
            st.subheader("原始数据信息")
            st.write(f"总行数: {len(df)}")
            st.write(f"总列数: {len(df.columns)}")
            st.write("原始列名:", list(df.columns))
            st.write("原始数据预览：")
            st.dataframe(df.head())
            
            if st.button("数据处理"):
                processed_df = process_data(df)
                if processed_df is not None:
                    st.session_state.processed_df = processed_df
                    
                    st.subheader("处理后的数据信息")
                    st.write(f"处理后行数: {len(processed_df)}")
                    st.write(f"处理后列数: {len(processed_df.columns)}")
                    st.write("处理后列名:", list(processed_df.columns))
                    st.write("处理后的数据预览：")
                    st.dataframe(processed_df)
                    
                    # 下载处理后的数据
                    st.subheader("下载处理后的数据")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 选择评论类型
                        review_type = st.selectbox(
                            "选择要下载的评论类型",
                            ["全部评论", "positive", "neutral", "negative"]
                        )
                    
                    with col2:
                        # 选择下载格式
                        file_format = st.radio("选择下载格式", ["Excel", "TXT"])
                    
                    # 根据选择筛选数据
                    if review_type != "全部评论":
                        download_df = processed_df[
                            processed_df['Review Type'] == review_type.lower()
                        ]
                    else:
                        download_df = processed_df
                    
                    # 准备下载按钮
                    if file_format == "Excel":
                        file_data = get_download_data(download_df, 'excel')
                        st.download_button(
                            label="下载Excel文件",
                            data=file_data,
                            file_name=f"amazon_reviews_{review_type.lower()}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        file_data = get_download_data(download_df, 'txt')
                        st.download_button(
                            label="下载TXT文件",
                            data=file_data,
                            file_name=f"amazon_reviews_{review_type.lower()}.txt",
                            mime="text/plain"
                        )
                    
                    st.success('数据处理完成！请点击左侧边栏的"统计分析"进行下一步分析。')
                            
        except Exception as e:
            st.error(f"处理文件时出错: {str(e)}")

if __name__ == "__main__":
    main() 