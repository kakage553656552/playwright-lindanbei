from playwright.sync_api import sync_playwright
import json
import time

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
    print("开始监控票务状态...")
    print("程序将每5秒检查一次，按Ctrl+C可以终止程序")
    
    check_count = 0  # 用于记录检查次数
    
    with sync_playwright() as playwright:
        while True:
            try:
                current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                check_count += 1
                print(f"\n第 {check_count} 次检查:")
                
                is_sold_out = check_ticket_availability(playwright)
                
                # 每次都打印检查结果
                if is_sold_out is not None:
                    if is_sold_out:
                        print(f"[{current_time}] ❌ 当前无票，页面显示\"提交缺货登记\"")
                    else:
                        print(f"[{current_time}] ✅ 当前有票，未发现\"提交缺货登记\"字样")
                else:
                    print(f"[{current_time}] ⚠️ 状态检查失败，将在5秒后重试")
                
                # 等待5秒
                print("等待5秒后进行下一次检查...")
                time.sleep(2)
                
            except KeyboardInterrupt:
                print("\n程序已终止")
                break
            except Exception as e:
                print(f"[{current_time}] 程序运行错误: {str(e)}")
                time.sleep(2)  # 发生错误时也等待5秒后继续
