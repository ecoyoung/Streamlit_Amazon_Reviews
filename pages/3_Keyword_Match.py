import streamlit as st

# 设置页面配置必须是第一个st命令
st.set_page_config(
    page_title="Amazon评论分析 - 关键词匹配",
    page_icon="🔍",
    layout="wide"
)

import pandas as pd
import json
import os
from collections import defaultdict

def load_categories():
    """从文件加载已保存的类别和关键词"""
    if os.path.exists('categories.json'):
        with open('categories.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_categories(categories):
    """保存类别和关键词到文件"""
    with open('categories.json', 'w', encoding='utf-8') as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)

def match_keywords(text, keywords):
    """检查文本是否包含关键词列表中的任何词"""
    if pd.isna(text):
        return False
    text = str(text).lower()
    return any(keyword.lower().strip() in text for keyword in keywords)

def analyze_reviews(df, categories):
    """分析评论并进行分类"""
    # 创建结果DataFrame
    results = pd.DataFrame()
    results['Content'] = df['Content']
    results['Original Review Type'] = df['Review Type']
    
    # 为每个类别创建一列
    for category in categories:
        keywords = [k.strip() for k in categories[category].split(',')]
        results[f'Is {category}'] = df['Content'].apply(
            lambda x: match_keywords(x, keywords)
        )
    
    # 统计每个类别的匹配数量
    stats = {}
    for category in categories:
        matched = results[f'Is {category}'].sum()
        stats[category] = {
            'matched': int(matched),
            'percentage': round(matched / len(df) * 100, 2)
        }
    
    return results, stats

def main():
    st.title("Amazon评论分析 - 关键词匹配")
    st.write("第四步：根据自定义关键词对评论进行分类")
    
    # 加载已保存的类别
    categories = load_categories()
    
    # 类别管理部分
    st.subheader("类别管理")
    
    # 添加新类别
    col1, col2 = st.columns([2, 1])
    with col1:
        new_category = st.text_input("输入新类别名称")
    with col2:
        if st.button("添加类别") and new_category:
            if new_category not in categories:
                categories[new_category] = ""
                save_categories(categories)
                st.success(f"已添加类别: {new_category}")
            else:
                st.warning("该类别已存在！")
    
    # 显示和编辑现有类别
    if categories:
        st.subheader("现有类别和关键词")
        edited_categories = {}
        
        for category in categories:
            col1, col2, col3 = st.columns([2, 6, 1])
            
            with col1:
                st.write(f"**{category}**")
            
            with col2:
                keywords = st.text_input(
                    "关键词（用逗号分隔）",
                    value=categories[category],
                    key=f"keywords_{category}",
                    help="输入多个关键词，用逗号分隔"
                )
                edited_categories[category] = keywords
            
            with col3:
                if st.button("删除", key=f"delete_{category}"):
                    del categories[category]
                    save_categories(categories)
                    st.rerun()
        
        # 如果关键词有修改，保存更新
        if edited_categories != categories:
            categories = edited_categories
            save_categories(categories)
        
        # 文件上传和分析
        st.subheader("评论分析")
        uploaded_file = st.file_uploader("选择预处理后的Excel文件", type=['xlsx'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                
                # 验证文件格式
                required_columns = ['Content', 'Review Type']
                if not all(col in df.columns for col in required_columns):
                    st.error("请上传包含Content和Review Type列的预处理文件！")
                    return
                
                # 分析评论
                results, stats = analyze_reviews(df, categories)
                
                # 显示统计信息
                st.subheader("匹配统计")
                stats_df = pd.DataFrame([
                    {
                        '类别': category,
                        '匹配数量': stats[category]['matched'],
                        '匹配比例': f"{stats[category]['percentage']}%"
                    }
                    for category in stats
                ])
                st.dataframe(stats_df)
                
                # 显示详细结果
                st.subheader("详细结果")
                st.dataframe(results)
                
                # 下载结果
                st.subheader("下载分析结果")
                
                # 转换为Excel
                excel_buffer = pd.ExcelWriter(pd.io.common.BytesIO(), engine='xlsxwriter')
                results.to_excel(excel_buffer, index=False)
                excel_buffer.close()
                excel_data = excel_buffer.handles.handle.getvalue()
                
                st.download_button(
                    label="下载Excel文件",
                    data=excel_data,
                    file_name="keyword_match_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            except Exception as e:
                st.error(f"处理文件时出错: {str(e)}")
    else:
        st.info("请先添加类别和关键词")

if __name__ == "__main__":
    main() 