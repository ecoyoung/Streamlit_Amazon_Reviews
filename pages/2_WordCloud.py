import streamlit as st

# 设置页面配置必须是第一个st命令
st.set_page_config(
    page_title="Amazon评论分析 - 词云分析",
    page_icon="☁️",
    layout="wide"
)

import pandas as pd
import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import re
import plotly.graph_objects as go
import json
import os

def load_stop_words():
    """加载停用词"""
    # 基础英文停用词
    stop_words = {
        # 人称代词
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're",
        "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves',
        'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself',
        'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
        
        # 疑问词和指示词
        'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those',
        'where', 'when', 'why', 'how', 'whose',
        
        # 常见动词和助动词
        'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
        'had', 'having', 'do', 'does', 'did', 'doing', 'will', 'would', 'shall',
        'should', 'can', 'could', 'may', 'might', 'must', 'ought', 'need', 'dare',
        
        # 介词和连词
        'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while',
        'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
        'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from',
        'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further',
        'then', 'once', 'here', 'there', 'all', 'any', 'both', 'each',
        
        # 常见副词和形容词
        'just', 'now', 'only', 'very', 'really', 'quite', 'rather', 'somewhat',
        'more', 'most', 'much', 'many', 'some', 'such', 'no', 'nor', 'not',
        'too', 'very', 'same', 'different', 'other', 'another', 'like', 'unlike',
        
        # 时间相关词
        'today', 'tomorrow', 'yesterday', 'now', 'later', 'earlier', 'soon',
        'already', 'yet', 'still', 'always', 'never', 'ever', 'often', 'sometimes',
        
        # 数量词和序数词
        'one', 'two', 'three', 'first', 'second', 'third', 'next', 'last',
        'few', 'several', 'many', 'much', 'more', 'most', 'own', 'every',
        
        # 其他常见词
        'yes', 'no', 'maybe', 'ok', 'okay', 'right', 'wrong', 'well', 'anyway',
        'however', 'although', 'though', 'despite', 'unless', 'whereas',
        'whether', 'whatever', 'whoever', 'whenever', 'wherever', 'however',
        
        # 网络用语和缩写
        'lol', 'omg', 'idk', 'tbh', 'imo', 'imho', 'fyi', 'asap', 'aka'
    }
    
    # 添加一些自定义停用词（与产品评论相关）
    custom_stop_words = {
        # 产品相关
        'amazon', 'product', 'item', 'purchase', 'bought', 'buy', 'seller',
        'shipping', 'delivery', 'arrived', 'ordered', 'received', 'return',
        'customer', 'service', 'price', 'worth', 'money', 'paid', 'cost',
        
        # 评论常用词
        'would', 'could', 'get', 'use', 'using', 'used', 'recommend',
        'recommended', 'definitely', 'probably', 'maybe', 'think', 'thought',
        'seems', 'looked', 'looks', 'looking', 'came', 'come', 'goes', 'going',
        'got', 'getting', 'make', 'makes', 'made', 'making',
        
        # 时间和状态
        'day', 'days', 'week', 'weeks', 'month', 'months', 'year', 'years',
        'time', 'times', 'ago', 'since', 'far', 'long', 'short',
        
        # 评分相关
        'star', 'stars', 'rating', 'rated', 'review', 'reviews', 'reviewed'
    }
    
    return stop_words.union(custom_stop_words)

def load_negative_words():
    """从文件加载否定词列表"""
    if os.path.exists('negative_words.json'):
        with open('negative_words.json', 'r') as f:
            return set(json.load(f))
    return set()

def save_negative_words(words):
    """保存否定词列表到文件"""
    with open('negative_words.json', 'w') as f:
        json.dump(list(words), f)

def process_text(text, stop_words, negative_words):
    """处理文本，提取词语"""
    if pd.isna(text):
        return []
    
    # 转换为小写并分词
    text = str(text).lower()
    # 使用正则表达式分词，保留字母和数字
    words = re.findall(r'\b[a-z0-9]+\b', text)
    
    # 过滤词
    filtered_words = [word for word in words 
                     if word not in stop_words 
                     and word not in negative_words
                     and len(word) > 2]  # 移除过短的词
    
    return filtered_words

def create_wordcloud(text_data, negative_words):
    """创建词云图"""
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        max_words=100,
        stopwords=negative_words
    ).generate_from_frequencies(text_data)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    return fig

def create_word_freq_table(word_freq, top_n=50):
    """创建词频统计表"""
    df = pd.DataFrame(list(word_freq.items()), columns=['Word', 'Frequency'])
    df = df.sort_values('Frequency', ascending=False).head(top_n)
    
    fig = go.Figure(data=[
        go.Table(
            header=dict(values=['词语', '频率'],
                       fill_color='paleturquoise',
                       align='left'),
            cells=dict(values=[df['Word'], df['Frequency']],
                      fill_color='lavender',
                      align='left'))
    ])
    
    return fig

def main():
    st.title("Amazon评论分析 - 词云分析")
    st.write("第三步：评论文本分析与词云图生成")
    
    # 加载停用词和否定词
    stop_words = load_stop_words()
    negative_words = load_negative_words()
    
    # 文件上传
    uploaded_file = st.file_uploader("选择预处理后的Excel文件", type=['xlsx'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            
            # 验证文件格式
            required_columns = ['Content', 'Review Type']
            if not all(col in df.columns for col in required_columns):
                st.error("请上传包含Content和Review Type列的预处理文件！")
                return
            
            # 选择评论类型
            review_type = st.selectbox(
                "选择要分析的评论类型",
                ["所有评论", "Positive评论", "Negative评论", "Neutral评论"]
            )
            
            # 添加调试信息
            st.write("数据集中的评论类型：", df['Review Type'].unique())
            
            # 根据选择筛选数据
            if review_type == "Positive评论":
                filtered_df = df[df['Review Type'].str.lower() == 'positive']
            elif review_type == "Negative评论":
                filtered_df = df[df['Review Type'].str.lower() == 'negative']
            elif review_type == "Neutral评论":
                filtered_df = df[df['Review Type'].str.lower() == 'neutral']
            else:
                filtered_df = df
            
            # 显示筛选后的数据量
            st.write(f"筛选后的评论数量：{len(filtered_df)}")
            
            # 否定词管理
            st.subheader("否定词管理")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                new_negative_word = st.text_input("输入要添加的否定词")
                if st.button("添加否定词") and new_negative_word:
                    negative_words.add(new_negative_word.lower())
                    save_negative_words(negative_words)
                    st.success(f"已添加否定词: {new_negative_word}")
            
            with col2:
                if negative_words:
                    word_to_remove = st.selectbox("选择要删除的否定词", list(negative_words))
                    if st.button("删除否定词") and word_to_remove:
                        negative_words.remove(word_to_remove)
                        save_negative_words(negative_words)
                        st.success(f"已删除否定词: {word_to_remove}")
            
            # 显示当前否定词列表
            if negative_words:
                st.write("当前否定词列表：", ", ".join(sorted(negative_words)))
            
            # 处理文本
            all_words = []
            for text in filtered_df['Content']:
                all_words.extend(process_text(text, stop_words, negative_words))
            
            # 计算词频
            word_freq = Counter(all_words)
            
            if word_freq:
                # 创建词云图
                st.subheader("词云图")
                wordcloud_fig = create_wordcloud(word_freq, negative_words)
                st.pyplot(wordcloud_fig)
                
                # 创建词频统计表
                st.subheader("词频统计表")
                freq_table = create_word_freq_table(word_freq)
                st.plotly_chart(freq_table, use_container_width=True)
            else:
                st.warning("没有找到符合条件的词语，请调整分析条件或检查数据。")
                
        except Exception as e:
            st.error(f"处理文件时出错: {str(e)}")

if __name__ == "__main__":
    main() 