import os
import shutil
import re
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import tkinter as tk
from tkinter import ttk

type_map={
    1:'文字',
    3:'图片',
    34:'语音',
    37:'朋友推荐消息',
    42:'名片',
    43:'视频', #playlength 代表时间
    47:'表情包', # cdnurl 下载地址
    48:'位置信息',
    49:'文件',
    50:'视频、语音通话',
    10000:'转账，撤回，红包，收到红包，添加好友信息，新人入群通知',
    11000:'其他信息，暂不清楚'
}


def remove_empty_folder(file_folder):
    # 删除空白聊天记录
    for user in os.listdir(file_folder):
        for filename in os.listdir(os.path.join(file_folder,user)):
            if filename.endswith(".csv"):
                user_folder=os.path.join(file_folder,user,filename)
                df=pd.read_csv(user_folder)
                if df.empty:
                    empty_path=os.path.join(file_folder,user)
                    shutil.rmtree(empty_path)

def calulate_calling_time(csv_path):
    df=pd.read_csv(csv_path)

    # 解析StrContent列中的XML并提取信息
    def parse_voip_message(xml_string):
        try:
            # 解析XML
            root = ET.fromstring(xml_string)
            # 获取msg内容
            msg_content = root.find(".//msg").text.strip()
            return msg_content
        except Exception as e:
            print(f"XML解析错误: {e}")
            return None
    
    call_counts = {
        "已在其它设备接听": 0,
        "已取消": 0,
        "未应答": 0,
        "对方已取消": 0
    }
    total_duration_seconds = 0

    # 正则表达式匹配通话时长（格式：xx:xx）
    duration_pattern = r"(\d{2}):(\d{2})"

    for _ , row in df.iterrows():
        msg_content = row['StrContent']
        msg = parse_voip_message(msg_content)

        if msg:
            if "已在其它设备接听" in msg:
                call_counts["已在其它设备接听"] += 1
            
            elif "未应答" in msg:
                call_counts["未应答"] += 1
            elif "对方已取消" in msg:
                call_counts["对方已取消"] += 1
            elif "已取消" in msg:
                call_counts["已取消"] += 1
            elif "通话时长" in msg:
                # 提取通话时长（例如：01:35）
                match = re.search(duration_pattern, msg)
                if match:
                    minutes = int(match.group(1))
                    seconds = int(match.group(2))
                    total_duration_seconds += minutes * 60 + seconds

    total_duration_minutes = total_duration_seconds // 60
    total_duration_seconds = total_duration_seconds % 60
    return call_counts, total_duration_minutes, total_duration_seconds

# 统计撤回消息
def count_withdrawal_messages(file_path):
    df = pd.read_csv(file_path)
    withdrawal_pattern = r"(\S+)撤回了一条消息"  # 匹配撤回消息的正则表达式
    withdrawal_count = 0
    withdrawal_sender_count = 0

    for index, row in df.iterrows():
        if re.search(withdrawal_pattern, row['StrContent']):
            withdrawal_count += 1
            if row['IsSender'] == 1:
                withdrawal_sender_count += 1
    return withdrawal_count, withdrawal_sender_count

# 统计转账信息
def count_transfer_messages(file_path):
    df = pd.read_csv(file_path)
    transfer_pattern = r"你有一笔待接收的.*转账"  # 匹配转账信息的正则表达式
    transfer_count = 0
    transfer_sender_count = 0

    for index, row in df.iterrows():
        if re.search(transfer_pattern, row['StrContent']):
            transfer_count += 1
            if row['IsSender'] == 1:
                transfer_sender_count += 1
    return transfer_count, transfer_sender_count

# 统计添加好友信息
def count_add_friend_messages(file_path):
    df = pd.read_csv(file_path)
    add_friend_pattern = r"你已添加了"  # 匹配添加好友信息的正则表达式
    add_friend_count = 0

    for index, row in df.iterrows():
        if re.search(add_friend_pattern, row['StrContent']):
            add_friend_count += 1
    return add_friend_count

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
    plt.savefig('analysis/results/wordcloud.png')

def collect_data(file_folder,collection):
    dict={}
    group_count=0
    friend_count=0
    all_message_count = 0
    all_message_sent_count = 0
    all_data=[]
    max_chatroom_length=0
    max_chatroom_id=''
    max_person_info=0
    max_person_id=''

    # if not os.path.exists(collection):
    #     os.makedirs(collection)
    # else:
    #     shutil.rmtree(collection)
    #     os.makedirs(collection)

    for user in os.listdir(file_folder):
        for filename in os.listdir(os.path.join(file_folder,user)):
            if filename.endswith(".csv"):

                df=pd.read_csv(os.path.join(file_folder,user,filename),usecols=[2,4,5,7,9,10,11])
                length=df.shape[0]
                if "@chatroom" in user:
                    group_count += 1
                    max_chatroom_length, max_chatroom_id = max((length, user), (max_chatroom_length, max_chatroom_id))
                else:
                    friend_count += 1
                    max_person_info, max_person_id = max((length, user), (max_person_info, max_person_id))
                
                all_message_sent_count += (df['IsSender'] == 1).sum()
                
                # 分组保存各类消息
                # group_Data = df.groupby('Type')
                # for group_id, group_Data in group_Data:
                #     output_file=os.path.join(collection,str(group_id)+".csv")
                #     if os.path.exists(output_file):
                #         group_Data.to_csv(output_file,mode='a',header=False,index=False)
                #     else:
                #         group_Data.to_csv(output_file,index=False)
                
                

                # 统计聊天频率
                df['Datetime'] = pd.to_datetime(df['CreateTime'], unit='s').dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai')  # Full datetime
                df['Date'] = df['Datetime'].dt.date  # Daily granularity
                df['Hour'] = df['Datetime'].dt.hour  # Hourly granularity
                df['Weekday'] = df['Datetime'].dt.weekday  # Weekday for heatmap
                # Adjust hours for proper period categorization
                df['AdjustedHour'] = df['Hour'].apply(lambda x: x + 24 if x < 5 else x)
                df['Period'] = pd.cut(df['AdjustedHour'], 
                                    bins=[5, 12, 18, 29], 
                                    labels=['Morning', 'Afternoon', 'Evening'], 
                                    right=False)

                # Combine all data into a single DataFrame
                all_data.append(df)

    # Analysis 1: Daily chat frequency
    combined_data = pd.concat(all_data, ignore_index=False)
    # combined_data.to_csv(os.path.join(collection,'combined_data.csv'),index=False)

    all_message_count = combined_data.shape[0]

    # 
    size_info = combined_data.groupby('Type').size()
    text_message_count=size_info[1]
    img_message_count=size_info[3]
    voice_message_count=size_info[34]
    video_message_count=size_info[43]
    emoji_counts=size_info[47]
    file_counts=size_info[49]
    voice_call_count=size_info[50]
    call_counts, voice_call_duration_minute,voice_call_duration_second=calulate_calling_time(os.path.join(collection,'50.csv'))
    withdrawal_count, withdrawal_sender_count=count_withdrawal_messages(os.path.join(collection,'10000.csv'))
    add_friend_count=count_add_friend_messages(os.path.join(collection,'10000.csv'))

    start_date = combined_data['Date'].min()
    end_date = combined_data['Date'].max()
    all_dates = pd.date_range(start=start_date, end=end_date).date

    daily_counts = combined_data['Date'].value_counts().reindex(all_dates, fill_value=0).sort_index()

    most_active_day = daily_counts.idxmax()

    #analysis word
    file_path = 'analysis/results/1.csv'  # 替换为你的CSV文件路径
    stopwords_file = 'analysis/stopwords.txt'  # 停用词文件路径
    stopwords = load_stopwords(stopwords_file)  # 加载停用词
    df = pd.read_csv(file_path)
    # 统计文字数量
    total_length, sent_length, received_length, cattle_house_count = count_text_length(df)
    # 词频统计
    word_freq = get_word_frequency(df, stopwords)
    # 绘制词云图
    plot_wordcloud(word_freq)


    #  Draw daily chat frequency plot and save
    
    # Create a heatmap-friendly DataFrame for GitHub-style contribution activity
    daily_counts_df = daily_counts.reset_index()
    daily_counts_df.columns = ['Date', 'MessageCount']
    daily_counts_df['Week'] = daily_counts_df['Date'].apply(lambda x: x.isocalendar()[1])
    daily_counts_df['Weekday'] = daily_counts_df['Date'].apply(lambda x: x.isocalendar()[2])

    heatmap_data = daily_counts_df.pivot(index='Weekday', columns='Week', values='MessageCount').fillna(0)

    # Plotting the heatmap
    plt.figure(figsize=(12, 6))
    sns.heatmap(heatmap_data, cmap="YlGn", linewidths=.5, cbar=True, square=True,annot=False)
    plt.xticks([],[])
    plt.yticks([], [])
    plt.title("Chat Activity Heatmap (GitHub-style)")
    plt.savefig('analysis/results/daily_chat_frequency.png', dpi=300, bbox_inches='tight')
    plt.close()


    # Analysis 2: Period chat frequency (Morning, Afternoon, Evening)
    period_counts = combined_data['Period'].value_counts()
    most_active_period = period_counts.idxmax()

    # Analysis 3: Earliest and latest chat days
    grouped_dates = combined_data.groupby('Date')
    early_time=grouped_dates.apply(lambda x: x['Datetime'].min().time()).min()
    latest_time=grouped_dates.apply(lambda x: x['Datetime'].max().time()).max()
    
    # Save all results to result.txt
    with open('analysis/results/result.txt', 'w', encoding='utf-8') as f:
        f.write("=== 聊天分析结果 ===\n\n")

        # 写入好友和群聊人数
        f.write("1. 好友和群聊人数\n")
        f.write(f"好友人数：{friend_count}\n")
        f.write(f"聊天最多的好友是 {max_person_id} ,共有 {max_person_info} 条消息\n")
        f.write(f"群聊人数：{group_count}\n")
        f.write(f"聊天最多的群聊是 {max_chatroom_id} ,共有 {max_chatroom_length} 条消息\n")
        f.write(f"这一年新添加了{add_friend_count}个好友\n\n")
        
        # 写入发出消息总数
        f.write("2. 消息总数\n")
        f.write(f"这一年的消息总数：{all_message_count}，总文字数{total_length},其中来自你发送的消息共有{all_message_sent_count}条，总文字数{sent_length}，牛马指数（回复收到的次数）：{cattle_house_count}\n")

        f.write(f"文字消息总数：{text_message_count}\n")
        f.write(f"图片消息总数：{img_message_count}\n")
        f.write(f"表情包总数为：{emoji_counts}\n")
        f.write(f"语音总数：{voice_message_count}\n")
        f.write(f"视频总数：{video_message_count}\n")
        f.write(f"通话总数：{voice_call_count},其中通话时长为{voice_call_duration_minute}分{voice_call_duration_second}秒\n")
        f.write(f"文件总数：{file_counts}\n")
        f.write(f"撤回消息总数：{withdrawal_count}\n")
        f.write(f"你撤回的消息数量为：{withdrawal_sender_count}\n\n")


        # 写入每日聊天频率
        f.write("3. 每日聊天频率\n")
        f.write(f"最活跃的一天是 {most_active_day}，发送了 {daily_counts.max()} 条消息\n\n")
        
        # 写入时段分析
        f.write("4. 时段分析\n")
        f.write(f"最活跃的时段是{most_active_period}，共发送了 {period_counts.max()} 条消息\n")
        f.write("各时段消息数量：\n")
        for period, count in period_counts.items():
            f.write(f"{period}: {count} 条消息\n")
        f.write("\n")
        
        # 写入时间范围 待更改！！！
        f.write("5. 聊天时间范围\n")
        f.write(f"最早的聊天日期: {early_time}\n"   )
        f.write(f"最晚的聊天日期: {latest_time}\n\n")
    dict['friend_count']=friend_count
    dict['group_count']=group_count
    dict['total_length']=total_length
    dict['sent_length']=sent_length
    dict['cattle_house_count']=cattle_house_count
    dict['max_person_id']=max_person_id
    dict['max_person_info']=max_person_info
    dict['max_chatroom_id']=max_chatroom_id
    dict['max_chatroom_length']=max_chatroom_length
    dict['add_friend_count']=add_friend_count
    dict['all_message_count']=all_message_count
    dict['all_message_sent_count']=all_message_sent_count
    dict['text_message_count']=text_message_count
    dict['img_message_count']=img_message_count
    dict['emoji_counts']=emoji_counts
    dict['voice_message_count']=voice_message_count
    dict['video_message_count']=video_message_count
    dict['voice_call_count']=voice_call_count
    dict['voice_call_duration_minute']=voice_call_duration_minute
    dict['voice_call_duration_second']=voice_call_duration_second
    dict['file_counts']=file_counts
    dict['withdrawal_count']=withdrawal_count
    dict['withdrawal_sender_count']=withdrawal_sender_count
    dict['daily_counts']=daily_counts
    dict['period_counts']=period_counts
    dict['most_active_day']=most_active_day
    dict['most_active_period']=most_active_period
    dict['early_time']=early_time
    dict['latest_time']=latest_time

    return dict
def display_results(dict):
    # 创建主窗口
    root = tk.Tk()
    root.title("聊天分析结果")
    root.geometry("600x500")

    # 创建滚动区域
    canvas = tk.Canvas(root)
    scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
    canvas.config(yscrollcommand=scrollbar.set)

    # 创建一个Frame容器，用于承载所有的内容
    frame = tk.Frame(canvas)

    # 将frame添加到canvas
    canvas.create_window((0, 0), window=frame, anchor="nw")

    # 配置滚动条
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # 更新canvas的滚动区域
    def on_frame_configure(event):
        canvas.config(scrollregion=canvas.bbox("all"))
    frame.bind("<Configure>", on_frame_configure)

    # ---------------------------- 编写UI内容 ----------------------------

    def add_section(frame, title, content):
        """为每一部分添加标题和内容"""
        section_title = tk.Label(frame, text=title, font=("Arial", 14, "bold"))
        section_title.pack(anchor="w", padx=10, pady=10)

        section_content = tk.Label(frame, text=content, font=("Arial", 12))
        section_content.pack(anchor="w", padx=10, pady=5)

    # 1. 好友和群聊人数
    add_section(frame, "1. 好友和群聊人数", 
                f"今年聊天好友数：{dict['friend_count']}\n聊天最多的好友是 {dict['max_person_id']}, 共 {dict['max_person_info']} 条消息\n"
                f"今年聊天群聊数：{dict['group_count']}\n聊天最多的群聊是 {dict['max_chatroom_id']}, 共 {dict['max_chatroom_length']} 条消息\n"
                f"这一年新添加了{dict['add_friend_count']}个好友")

    # 2. 消息总数
    add_section(frame, "2. 消息总数",
                f"这一年的消息总数：{dict['all_message_count']}，总文字数{dict['total_length']}\n其中来自你发送的消息共有{dict['all_message_sent_count']}条，总文字数{dict['sent_length']}\n牛马指数（回复收到的次数）：{dict['cattle_house_count']}\n"
                f"文字消息总数：{dict['text_message_count']}\n图片消息总数：{dict['img_message_count']}\n"
                f"表情包总数为：{dict['emoji_counts']}\n语音总数：{dict['voice_message_count']}\n视频总数：{dict['video_message_count']}\n"
                f"通话总数：{dict['voice_call_count']}, 通话时长：{dict['voice_call_duration_minute']}分{dict['voice_call_duration_second']}秒\n"
                f"文件总数：{dict['file_counts']}\n撤回消息总数：{dict['withdrawal_count']}\n你撤回的消息数量：{dict['withdrawal_sender_count']}")

    # 3. 每日聊天频率
    add_section(frame, "3. 每日聊天频率",
                f"最活跃的一天是 {dict['most_active_day']}，发送了 {dict['daily_counts'].max()} 条消息")

    # 4. 时段分析
    add_section(frame, "4. 时段分析",
                f"最活跃的时段是 {dict['most_active_period']}，共发送了 {dict['period_counts'].max()} 条消息\n"
                f"各时段消息数量：")
    for period, count in dict['period_counts'].items():
        add_section(frame, "", f"{period}: {count} 条消息")

    # 5. 聊天时间范围
    add_section(frame, "5. 聊天时间范围",
                f"最早的聊天日期: {dict['early_time']}\n最晚的聊天日期: {dict['latest_time']}")

    # 启动窗口
    root.mainloop()


if __name__ == "__main__":
    file_folder='data/聊天记录'
    collection='analysis/results'
    remove_empty_folder(file_folder)
    dict=collect_data(file_folder,collection)
    display_results(dict)