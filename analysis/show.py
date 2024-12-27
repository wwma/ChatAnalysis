import tkinter as tk
from tkinter import ttk

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
    section_title.pack(anchor="w", padx=10, pady=5)

    section_content = tk.Label(frame, text=content, font=("Arial", 12))
    section_content.pack(anchor="w", padx=10, pady=5)

# 1. 好友和群聊人数
add_section(frame, "1. 好友和群聊人数", 
            f"好友人数：{friend_count}\n聊天最多的好友是 {max_person_id}, 共 {max_person_info} 条消息\n"
            f"群聊人数：{group_count}\n聊天最多的群聊是 {max_chatroom_id}, 共 {max_chatroom_length} 条消息\n"
            f"这一年新添加了{add_friend_count}个好友")

# 2. 消息总数
add_section(frame, "2. 消息总数",
            f"这一年的消息总数：{all_message_count}\n其中来自你发送的消息共有{all_message_sent_count}条\n"
            f"文字消息总数：{text_message_count}\n图片消息总数：{img_message_count}\n"
            f"表情包总数为：{emoji_counts}\n语音总数：{voice_message_count}\n视频总数：{video_message_count}\n"
            f"通话总数：{voice_call_count}, 通话时长：{voice_call_duration_minute}分{voice_call_duration_second}秒\n"
            f"文件总数：{file_counts}\n撤回消息总数：{withdrawal_count}\n你撤回的消息数量：{withdrawal_sender_count}")

# 3. 每日聊天频率
add_section(frame, "3. 每日聊天频率",
            f"最活跃的一天是 {most_active_day}，发送了 {daily_counts.max()} 条消息")

# 4. 时段分析
add_section(frame, "4. 时段分析",
            f"最活跃的时段是 {most_active_period}，共发送了 {period_counts.max()} 条消息\n"
            f"各时段消息数量：")
for period, count in period_counts.items():
    add_section(frame, "", f"{period}: {count} 条消息")

# 5. 聊天时间范围
add_section(frame, "5. 聊天时间范围",
            f"最早的聊天日期: {early_time}\n最晚的聊天日期: {latest_time}")

# 启动窗口
root.mainloop()
