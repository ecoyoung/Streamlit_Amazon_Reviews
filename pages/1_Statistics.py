import streamlit as st
import pandas as pd
from utils import (
    calculate_review_stats,
    create_pie_chart,
    analyze_by_group,
    create_rating_heatmap,
    create_rating_trend_chart,
    save_fig_to_html
)
import plotly.express as px

st.set_page_config(
    page_title="Amazon评论分析 - 统计分析",
    page_icon="📈",
    layout="wide"
)

def create_overall_trend_chart(df):
    """创建整体评分趋势图"""
    df['Month'] = df['Date'].dt.to_period('M').astype(str)
    trend_data = df.groupby('Month')['Rating'].mean().reset_index()
    
    fig = px.line(trend_data, 
                  x='Month', 
                  y='Rating',
                  title='整体评分趋势',
                  labels={'Rating': '平均评分', 'Month': '月份'})
    
    fig.update_xaxes(tickangle=45)
    return fig

def main():
    st.title("Amazon评论分析 - 统计分析")
    st.write("第二步：上传预处理后的数据文件进行统计分析")
    
    uploaded_file = st.file_uploader("选择预处理后的Excel文件", type=['xlsx'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            
            # 验证是否是预处理后的文件
            required_columns = ['ID', 'Asin', 'Title', 'Content', 'Model', 'Rating', 'Date', 'Review Type']
            if not all(col in df.columns for col in required_columns):
                st.error("请上传预处理后的文件！预处理后的文件应包含以下列：" + ", ".join(required_columns))
                return
            
            # 显示评论类型统计和占比
            st.subheader("整体评论分析")
            stats_df, review_counts, review_percentages = calculate_review_stats(df)
            
            col1, col2 = st.columns([1, 1])
            with col1:
                st.write("评论类型统计：")
                st.dataframe(stats_df)
            
            with col2:
                pie_chart = create_pie_chart(review_counts)
                st.plotly_chart(pie_chart, use_container_width=True)
            
            # 添加详细分析部分
            st.subheader("详细分析")
            analysis_type = st.selectbox(
                "选择分析维度",
                ["按Asin分析", "按Asin+Model组合分析"]
            )
            
            if analysis_type == "按Asin分析":
                group_by = 'Asin'
            else:
                group_by = ['Asin', 'Model']
            
            # 获取分组分析结果
            asin_stats, rating_dist_pct, group_by_trend = analyze_by_group(df, group_by)
            
            # 显示ASIN维度的统计信息
            st.write("ASIN评分统计信息：")
            st.dataframe(asin_stats)
            
            # 显示ASIN评分分布热力图
            st.subheader("Asin评分分布热力图")
            heatmap = create_rating_heatmap(rating_dist_pct, "Asin的评分分布(%)")
            st.plotly_chart(heatmap, use_container_width=True)
            
            # 创建并显示时间趋势图
            st.subheader("评分趋势分析")
            
            # 添加ASIN选择功能
            all_asins = sorted(df['Asin'].unique())
            
            # 创建一个选择框来选择是否查看特定ASIN
            view_specific = st.radio(
                "选择查看方式",
                ["查看整体趋势", "查看特定ASIN趋势"]
            )
            
            if view_specific == "查看特定ASIN趋势":
                # 多选框选择ASIN
                selected_asins = st.multiselect(
                    "选择要查看的ASIN（可多选）",
                    all_asins,
                    help="不选择则显示所有ASIN"
                )
                
                if selected_asins:
                    if analysis_type == "按Asin分析":
                        filtered_df = df[df['Asin'].isin(selected_asins)]
                        trend_chart = create_rating_trend_chart(filtered_df, 'Asin')
                    else:
                        filtered_df = df[df['Asin'].isin(selected_asins)]
                        filtered_df['Group'] = filtered_df['Asin'] + ' - ' + filtered_df['Model']
                        trend_chart = create_rating_trend_chart(filtered_df, 'Group')
                else:
                    # 如果没有选择ASIN，显示所有ASIN的趋势
                    trend_chart = create_rating_trend_chart(df, group_by_trend)
            else:
                # 显示整体趋势
                trend_chart = create_overall_trend_chart(df)
            
            st.plotly_chart(trend_chart, use_container_width=True)
            
            # 添加图表下载按钮
            st.subheader("图表下载")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                pie_html = save_fig_to_html(pie_chart, "pie_chart.html")
                st.download_button(
                    label="下载评论分布饼图",
                    data=pie_html,
                    file_name="review_distribution_pie.html",
                    mime="text/html"
                )
            
            with col2:
                heatmap_html = save_fig_to_html(heatmap, "heatmap.html")
                st.download_button(
                    label="下载评分分布热力图",
                    data=heatmap_html,
                    file_name="asin_rating_heatmap.html",
                    mime="text/html"
                )
            
            with col3:
                trend_html = save_fig_to_html(trend_chart, "trend_chart.html")
                st.download_button(
                    label="下载评分趋势图",
                    data=trend_html,
                    file_name="rating_trend.html",
                    mime="text/html"
                )
                    
        except Exception as e:
            st.error(f"处理文件时出错: {str(e)}")

if __name__ == "__main__":
    main() 