from playwright.sync_api import sync_playwright
import json
import time
from datetime import datetime
import requests

# Server酱配置 - 支持多个SendKey
SERVERCHAN_SENDKEYS = [
    "SCT289346TquqwvKt2hb5zNQjJtFyHrCdJ",  # 第一个用户的SendKey
    "SCT289376TCeoFNBvYVpnCtcGCELSuqwG6"
    # "YOUR_SENDKEY_2_HERE",  # 第二个用户的SendKey
    # "YOUR_SENDKEY_3_HERE",  # 第三个用户的SendKey
    # 可以继续添加更多SendKey
]

def send_to_wechat(title, content):
    """使用Server酱发送消息到多个微信用户"""
    if not SERVERCHAN_SENDKEYS:
        print("⚠️ 请先设置至少一个Server酱的SendKey")
        return False
    
    success_count = 0
    for sendkey in SERVERCHAN_SENDKEYS:
        if sendkey == "YOUR_SENDKEY_2_HERE" or sendkey == "YOUR_SENDKEY_3_HERE":
            continue  # 跳过未配置的SendKey
            
        url = f"https://sctapi.ftqq.com/{sendkey}.send"
        data = {
            "title": title,
            "desp": content
        }
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                success_count += 1
                print(f"✅ 微信通知发送成功 (SendKey: {sendkey[:8]}...)")
            else:
                print(f"❌ 微信通知发送失败 (SendKey: {sendkey[:8]}...): {response.text}")
        except Exception as e:
            print(f"❌ 微信通知发送出错 (SendKey: {sendkey[:8]}...): {str(e)}")
    
    return success_count > 0  # 只要有一个发送成功就返回True

def check_ticket_availability(playwright):
    browser = None
    try:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 100, 'height': 100})
        page = context.new_page()
        # 设置窗口位置到屏幕右下角
        page.evaluate('window.moveTo(window.screen.width - 150, window.screen.height - 150)')

        # 目标详情页 URL
        detail_url = "https://detail.damai.cn/item.htm?spm=a2oeg.search_category.0.0.405c6da8qInG0t&id=949054108704&clicktitle=2025林丹杯羽毛球公开赛(西安站)"
        page.goto(detail_url)

        # 等待页面加载完成（等待body元素出现）
        page.wait_for_selector("body", timeout=60000)  # 增加超时时间到60秒
        
        # 给页面一些额外的加载时间
        page.wait_for_timeout(3000)
        
        # 检查是否存在"提交缺货登记"文字
        has_shortage = page.get_by_text("提交缺货登记").count() > 0
        
        return has_shortage
    except Exception as e:
        print(f"浏览器操作出错: {str(e)}")
        return None
    finally:
        if browser:
            browser.close()


if __name__ == "__main__":
    if not SERVERCHAN_SENDKEYS or all(key in ["YOUR_SENDKEY_2_HERE", "YOUR_SENDKEY_3_HERE"] for key in SERVERCHAN_SENDKEYS):
        print("⚠️ 请先在代码中的 SERVERCHAN_SENDKEYS 列表中添加你的SendKey")
        print("获取SendKey: https://sct.ftqq.com/")
        exit(1)

    print("开始监控票务状态...")
    print("程序将每90秒检查一次，每小时汇总发送结果")
    print("如果检测到有票，将立即发送通知")
    
    check_count = 0  # 用于记录检查次数
    detail_url = "https://detail.damai.cn/item.htm?spm=a2oeg.search_category.0.0.405c6da8qInG0t&id=949054108704&clicktitle=2025林丹杯羽毛球公开赛(西安站)"
    
    # 用于记录每小时的检查结果
    hourly_results = []
    last_send_hour = datetime.now().hour
    
    with sync_playwright() as playwright:
        while True:
            try:
                current_time = datetime.now()
                check_count += 1
                print(f"\n第 {check_count} 次检查:")
                
                is_sold_out = check_ticket_availability(playwright)
                
                # 准备本次检查的结果
                if is_sold_out is not None:
                    if is_sold_out:
                        status = "❌ 无票"
                        result = {
                            'time': current_time.strftime("%Y-%m-%d %H:%M:%S"),
                            'status': status,
                            'count': check_count
                        }
                        hourly_results.append(result)
                        print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] 当前无票，显示'提交缺货登记'")
                    else:
                        status = "✅ 有票"
                        result = {
                            'time': current_time.strftime("%Y-%m-%d %H:%M:%S"),
                            'status': status,
                            'count': check_count
                        }
                        hourly_results.append(result)
                        print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] 当前有票！")
                        
                        # 有票时立即发送通知
                        title_msg = "🎉 发现有票！立即购买！"
                        message = f"检查时间：{current_time.strftime('%Y-%m-%d %H:%M:%S')}\n第 {check_count} 次检查\n\n购票链接：{detail_url}"
                        send_to_wechat(title_msg, message)
                else:
                    status = "⚠️ 检查失败"
                    result = {
                        'time': current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'status': status,
                        'count': check_count
                    }
                    hourly_results.append(result)
                    print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] 状态检查失败")
                
                # 检查是否需要发送每小时汇总
                if current_time.hour != last_send_hour and hourly_results:
                    # 准备汇总信息
                    summary = f"过去一小时内共检查 {len(hourly_results)} 次\n\n"
                    for result in hourly_results:
                        summary += f"[{result['status']}] {result['time']} (第{result['count']}次检查)\n"
                    
                    # 发送汇总通知
                    send_to_wechat(
                        f"林丹杯门票监控汇总 ({last_send_hour}:00-{current_time.hour}:00)", 
                        summary
                    )
                    
                    # 清空并更新记录
                    hourly_results = []
                    last_send_hour = current_time.hour
                
                # 等待90秒
                print("等待90秒后进行下一次检查...")
                time.sleep(90)
                
            except KeyboardInterrupt:
                print("\n程序已终止")
                # 发送最后的汇总
                if hourly_results:
                    summary = f"最后一批结果，共 {len(hourly_results)} 次检查\n\n"
                    for result in hourly_results:
                        summary += f"[{result['status']}] {result['time']} (第{result['count']}次检查)\n"
                    send_to_wechat("⚠️ 监控程序已停止运行", f"停止时间：{current_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n{summary}")
                else:
                    send_to_wechat("⚠️ 监控程序已停止运行", f"停止时间：{current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                break
            except Exception as e:
                error_msg = f"程序运行错误: {str(e)}"
                print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] {error_msg}")
                hourly_results.append({
                    'time': current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    'status': "❌ 错误",
                    'count': check_count
                })
                time.sleep(90)  # 发生错误时也等待90秒后继续
