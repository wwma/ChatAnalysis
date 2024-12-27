import pandas as pd
import jieba
import matplotlib.pyplot as plt
from wordcloud import WordCloud


# 加载停用词列表
def load_stopwords(stopwords_file='stopwords.txt'):
    stopwords = set()
    with open(stopwords_file, 'r', encoding='utf-8') as f:
        for line in f:
            stopwords.add(line.strip())  # 去掉每行的空格和换行符
    return stopwords

# 读取CSV文件
def read_csv(file_path):
    return pd.read_csv(file_path)

# 统计总文字数量
def count_text_length(df):
    total_length = df['StrContent'].apply(len).sum()  # 总文字数
    sent_length = df[df['IsSender'] == 1]['StrContent'].apply(len).sum()  # 发送的文字数
    received_length = df[df['IsSender'] == 0]['StrContent'].apply(len).sum()  # 接收的文字数
    cattle_house_count = df[(df['StrContent'].str.contains("收到", na=False)) & (df['IsSender'] == 1)].shape[0]
    return total_length, sent_length, received_length, cattle_house_count

# 中文分词，去除停用词
def segment_text(text, stopwords):
    words = jieba.cut(text)  # 分词
    filtered_words = [word for word in words if word not in stopwords and word.strip()]  # 过滤停用词和空白
    return ' '.join(filtered_words)

# 词频统计
def get_word_frequency(df, stopwords):
    # 将所有聊天记录文本进行分词，并去除停用词
    all_text = df['StrContent'].apply(lambda x: segment_text(x, stopwords))
    
    # 词频统计
    word_freq = {}
    for text in all_text:
        for word in text.split():
            word_freq[word] = word_freq.get(word, 0) + 1
    return word_freq

# 绘制词云图
def plot_wordcloud(word_freq):
    wordcloud = WordCloud(font_path='simhei.ttf', width=800, height=600, background_color='white').generate_from_frequencies(word_freq)
    plt.figure(figsize=(10, 8))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.show()



# 输出统计结果
def display_results(total_length, sent_length, received_length, word_freq, cattle_house_count):
    print("文字统计：")
    print(f"总文字数: {total_length}")
    print(f"我发送的文字数: {sent_length}")
    print(f"我接收的文字数: {received_length}")
    print(f"回复收到的次数: {cattle_house_count}")

    print("\n词频统计（前10个）：")
    for word, freq in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{word}: {freq}")



# 主程序
def main():
    file_path = 'analysis/results/1.csv'  # 替换为你的CSV文件路径
    stopwords_file = 'analysis/stopwords.txt'  # 停用词文件路径
    stopwords = load_stopwords(stopwords_file)  # 加载停用词

    df = read_csv(file_path)

    # 统计文字数量
    total_length, sent_length, received_length, cattle_house_count = count_text_length(df)


    # 词频统计
    word_freq = get_word_frequency(df, stopwords)

    # 绘制词云图
    plot_wordcloud(word_freq)

    # 显示结果
    display_results(total_length, sent_length, received_length, word_freq, cattle_house_count)

# 运行主程序
if __name__ == "__main__":
    main()
