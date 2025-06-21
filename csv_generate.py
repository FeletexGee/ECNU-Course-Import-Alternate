import pandas as pd
from bs4 import BeautifulSoup

# 读取 HTML 内容
file_path = input('输入文件名称：\n')
with open(file_path,'r',encoding='utf-8') as f:
    html_content = f.read()

def ECNU_course_resolve_from_HTML(html_content):    
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # 定义存储课程信息的列表
    courses = []

    # 遍历每个课程行
    for row in soup.select('tbody > tr'):
        course_name = row.get('data-coursename', '').strip()
        course_code = row.get('data-coursecode', '').strip()
        has_syllabus = row.get('data-hasteachingsyllabus', '').strip()
        
        # 课程信息
        course_info = row.select_one('td:nth-of-type(1)')
        department = course_info.select_one('li[data-original-title="开课部门"]').text.strip()
        credits = course_info.select_one('li[data-original-title="学分"]').text.strip()
        hours = course_info.select_one('li[data-original-title="学时"]').text.strip()
        required = course_info.select_one('li[data-original-title="是否必修"]').text.strip()
        
        # 教学班信息
        class_info = row.select_one('td:nth-of-type(2)')
        class_code = class_info.select_one('p.class-code').text.strip()
        class_name = class_info.select_one('p.class-name').text.strip()
        
        # 时间地点人员
        schedule = row.select_one('td:nth-of-type(3)').text.strip()
        
        # 人数信息
        actual = row.select_one('td:nth-of-type(4) p:nth-of-type(1)').text.replace('实际：', '').strip()
        limit = row.select_one('td:nth-of-type(4) p:nth-of-type(2)').text.replace('上限：', '').strip()
        
        # 教学材料
        syllabus = row.select_one('td:nth-of-type(5)').text.strip()
        
        # 添加到课程列表
        courses.append({
            '课程名称': course_name,
            '课程代码': course_code,
            '开课部门': department,
            '学分': credits,
            '学时': hours,
            '是否必修': required,
            '教学班代码': class_code,
            '教学班名称': class_name,
            '时间地点人员': schedule,
            '实际人数': actual,
            '人数上限': limit,
            '教学材料': syllabus,
            '是否有教学大纲': has_syllabus
        })

    # 转换为 DataFrame
    return pd.DataFrame(courses)

def WakeUp_Timetable_csv_formatting(Timetable):
    Formatted = pd.DataFrame(columns=['课程名称', '星期', '开始节数', '结束节数', '老师', '地点', '周数'])
    formatted_rows = []  # Temporary list to store rows before concatenation

    # Mapping for Chinese numerals to Arabic numerals
    chinese_to_arabic = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5', '六': '6', '日': '7'}

    for index, row in Timetable.iterrows():
        # Split the schedule into individual entries
        schedules = row['时间地点人员'].split(';')
        session_dict = {}  # Temporary dictionary to merge locations and teachers for the same session

        for schedule in schedules:
            schedule = schedule.strip()
            if not schedule:
                continue
            
            # Extract week range, weekday, periods, location, and teacher
            parts = schedule.split()
            week_range = parts[0].replace('~', '-')  # Replace '~' with '-'
            week_range = week_range.replace('(单)', '单').replace('(双)', '双')  # Remove parentheses around "单" and "双"
            if '单' in week_range or '双' in week_range:
                week_range = week_range.replace('周', '')  # Remove '周' for single/double weeks
            else:
                week_range = week_range.replace('周', '').replace('~', '-')  # Standardize week range

            weekday = chinese_to_arabic.get(parts[1].replace('星期', ''), parts[1])  # Convert weekday
            periods = parts[2].split('~')
            start_period = periods[0]
            end_period = periods[1].replace('节', '')  # Remove "节"
            campus = parts[3]  # 校区
            room = parts[4] if len(parts) > 5 else parts[3]  # 教室
            teacher = parts[-1]  # Teacher is always the last part

            # Merge locations and teachers for the same session
            session_key = (row['课程名称'], week_range, weekday, start_period, end_period, campus)
            if session_key not in session_dict:
                session_dict[session_key] = {'地点': room, '老师': teacher}
            else:
                if room not in session_dict[session_key]['地点']:
                    session_dict[session_key]['地点'] += f"/{room}"
                if teacher not in session_dict[session_key]['老师']:
                    session_dict[session_key]['老师'] += f"/{teacher}"

        # Append formatted rows
        for (course_name, week_range, weekday, start_period, end_period, campus), details in session_dict.items():
            formatted_rows.append({
                '课程名称': course_name,
                '周数': week_range,
                '星期': weekday,
                '开始节数': start_period,
                '结束节数': end_period,
                '地点': f"{campus} {details['地点']}",  # Retain campus and merge rooms
                '老师': details['老师']
            })
    
    Formatted = pd.concat([Formatted, pd.DataFrame(formatted_rows)], ignore_index=True)
    return Formatted
WakeUp_Timetable_csv_formatting(ECNU_course_resolve_from_HTML(html_content)).to_csv('export_to_wakeup.csv',index=False)
print('导出完成！')