import requests
import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import selenium
import pyautogui

GROQ_API_KEY = 'ur_api'
RESULTS_FILE = 'results.json'

def send_groq_request(order_text, prompt_type):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    if prompt_type == "company_reply":
        prompt = f"""
        Заказ: {order_text}
        ответь на заказ от имени компании.
        Пример ответа: Здравствуйте, по стоимости разработка логотипа(если дело идет про логотип, если у тебя что то другое попытайся тоже ответить кратко) начинается от 15 т.р., далее зависит от деталей и количества вариантов, нужно будет заполнить бриф, выслать Вам?

        Ответь максимально кратко и понятно, используя только одну-две фразы. Избегай деталей и лишней информации
        БЕЗ ДЕТАЛЕЙ, БЕЗ ПРИМЕРОВ РАБОТ, ПРОСТО СКАЖИ ЧТО МЫ ГОТОВЫ ВЗЯТЬСЯ И ЕСЛИ НУЖНО КАКУТО ИНФОРМАЦИЮ УТОЧНИТЬ ДЛЯ НАЧАЛА РАБОТЫ У КЛИЕНТА, ТО ПРОСИ, НО ДЕЛАЙ ЭТО ОЧЕНЬ КОРОКТО
        """
    elif prompt_type == "days":
        prompt = f"""
        заказ: {order_text}
        ТЫ ДОЛЖЕН ТОЛЬКО СКАЗАТЬ СКОЛЬКО ЭТО ВРЕМЕНИ ЗАЙМЕТ, НИЧЕГО БОЛЬШЕ ГОВОРИТЬ НЕ НАДО, ТОЛЬКО ЦИФРА, ЕСЛИ ИНФОРМАЦИИ НЕ ДОСТАТОЧНО И ТРЕБУЕТ ОБЪЯСНЕНИЙ СО СТОРОНЫ КЛИЕНТА, ПИШИ ЧТО СРОК 11
        ЕСЛИ ИНФОРМАЦИИ ДОСТАТОЧНО И В ТЕКСТЕ НАПИСАННО КАКОЙ СРОК, ПИШИ ЕГО
        """
    elif prompt_type == "cost":
        prompt = f"""
        заказ: {order_text}
        ТЫ ДОЛЖЕН ТОЛЬКО СКАЗАТЬ СКОЛЬКО ЭТО СТОИТЬ БУДЕТ, НИЧЕГО БОЛЬШЕ ГОВОРИТЬ НЕ НАДО, ТОЛЬКО ЦИФРА, ЕСЛИ ИНФОРМАЦИИ НЕ ДОСТАТОЧНО И ТРЕБУЕТ ОБЪЯСНЕНИЙ СО СТОРОНЫ КЛИЕНТА, ПИШИ ЧТО ЦЕНА 11111
        ЕСЛИ ИНФОРМАЦИИ ДОСТАТОЧНО И ТАМ В ТЕКСТЕ НАПИСАНО КАКАЯ ЦЕНА,ПИШИ ЕЕ
        """
    else:
        prompt = f"""
        Заказ: {order_text}
        скажи к какой группе он больше всего относится.
        Логотипы
        Клиенты
        Дизайн мобильных приложений
        Дизайн сайтов
        Веб-программирование
        Сайт «под ключ»
        Верстка
        CMS (системы управления)
        Фирменный стиль
        ты должен ответить только одним из этих

        ТОЛЬКО НАХУЙ ОДНИМ СЛОВОМ, НИ БОЛЬШЕ, БЕЗ ЛИШНИХ СЛОВ ИЛИ ПОЯСНЕНИЙ, ТОЛЬКО ГОВОРИ ТЕ СЛОВА КОТОРЫЕ Я ТЕБЕ ДАЛ НА ВЫБОР И НИЧЕГО ЛИШНЕЕ
        """ #по другому он не понимает((((

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка API: {e}")
        return None

def move_mouse(elem):
    print("делаю скриншот")
    elem.screenshot("temp_elem.png")
    print("скриншот сделан")
    time.sleep(1)
    pos = pyautogui.locateCenterOnScreen("temp_elem.png", confidence=0.5)
    print(f"my coordinates are{pos}")
    if pos:
        x, y = pos
        pyautogui.moveTo(x, y, duration=1.5)
        print(f"[INFO] Клик по координатам: x={x}, y={y}")
        pyautogui.click()
    else:
        print("[WARNING] Элемент не найден на экране.")


def smooth_scroll_to_element(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", element)
    WebDriverWait(driver, 10).until(EC.visibility_of(element))
    time.sleep(1)

def load_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_results(data):
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def collect_links_on_page(driver):
    elements = driver.find_elements(By.CLASS_NAME, 'text-dark')
    links = []
    for el in elements:
        el_id = el.get_attribute('id')
        if 'prj_name_' in el_id:
            href = el.get_attribute('href')
            if href and any(x in href for x in ['dizayn', 'logo', 'sayty', 'programmirovanie', 'mobile', 'internet-magaziny', 'firmennyy-stil']):
                path = href.replace("https://www.fl.ru", "")
                links.append(path)
    return links

def process_link(driver, link, processed):
     project_id = link.split('/')[2]
     if project_id in processed:
         print(f"Уже обработан {project_id}, пропускаем.")
         return

    try:
        element = driver.find_element(By.XPATH, f"//a[contains(@href, '{link}')]")
        smooth_scroll_to_element(driver, element)
        print("scrolling to link")
        move_mouse(element)
        print("tries to click")
        element.click()
        print("elemclick")
        time.sleep(3)

        order_block = driver.find_element(By.ID, f'projectp{project_id}')
        order_text = order_block.text.strip()
        print(f"\n[{project_id}] Заказ:\n{order_text}\n")

        response = send_groq_request(order_text, "company_reply")
        category = send_groq_request(order_text, "category_identification")
        price = send_groq_request(order_text, "cost")
        duration = send_groq_request(order_text, "days")

        processed[project_id] = {
            'text': order_text,
            'reply': response,
            'category': category
        }

        print(f"Ответ: {response}\n")
        print(f"Категория: {category}\n")
        print(f"цена: {price}\n")
        print(f"срок: {duration}\n")
        save_results(processed)
        
        textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "el-descr"))
        )
        smooth_scroll_to_element(driver, textarea)
        move_mouse(textarea)
        pyautogui.write(response, interval=0.02)

        duration_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "el-time_from"))
        )
        smooth_scroll_to_element(driver, duration_input)
        move_mouse(duration_input)
        pyautogui.write(duration, interval=0.1)

        cost_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "el-cost_from"))
        )    
        smooth_scroll_to_element(driver, cost_input)
        move_mouse(cost_input)
        pyautogui.write(price, interval=0.1)

        button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Добавить примеры работ')]"))
        )
        move_mouse(button)

        category_to_text = {
            "Клиенты": "Клиенты",
            "Логотипы": "Логотипы",
            "Сайт «под ключ»": "Сайт «под ключ»",
            "Дизайн мобильных приложений": "Дизайн мобильных приложений",
            "Дизайн сайтов": "Дизайн сайтов",
            "Веб-программирование": "Веб-программирование",
            "Верстка": "Верстка",
            "CMS (системы управления)": "CMS (системы управления)",
            "Фирменный стиль": "Фирменный стиль",
        }
        button_text = category_to_text.get(category)

        if button_text:
            category_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{button_text}')]"))
            )

            smooth_scroll_to_element(driver, category_button)
            move_mouse(category_button)
            time.sleep(1)

            if category == "Клиенты":
                client_buttons_texts = ["ФОРАБАНК", "Paymo", "SaldenS"]
                for text in client_buttons_texts:
                    try:
                        btn = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{text}')]"))
                        )
                        smooth_scroll_to_element(driver, btn)
                        move_mouse(btn)
                        time.sleep(1)
                    except:
                        print(f"Кнопка '{text}' не найдена")
                if button_text:
                    category_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{button_text}')]"))
                    )

            smooth_scroll_to_element(driver, category_button)
            move_mouse(category_button)
            time.sleep(1)

            if category == "Клиенты":
                client_buttons_texts = ["ФОРАБАНК", "Paymo", "SaldenS"]
                for text in client_buttons_texts:
                    try:
                        btn = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{text}')]"))
                        )
                        smooth_scroll_to_element(driver, btn)
                        move_mouse(btn)
                        time.sleep(1)
                    except:
                        print(f"Кнопка '{text}' не найдена")

            elif category == "Логотипы":
                logo_buttons_texts = ["Ребрендинг", "Иконки", "Брендинг"]
                for text in logo_buttons_texts:
                    try:
                        btn = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{text}')]"))
                        )
                        smooth_scroll_to_element(driver, btn)
                        move_mouse(btn)
                        time.sleep(1)
                    except:
                        print(f"Кнопка '{text}' не найдена")

            elif category == "Сайт «под ключ»":
                turnkey_buttons_texts = ["Разработка сайта", "Сайт-визитка", "Магазин"]
                for text in turnkey_buttons_texts:
                    try:
                        btn = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{text}')]"))
                        )
                        smooth_scroll_to_element(driver, btn)
                        move_mouse(btn)
                        time.sleep(1)
                    except:
                        print(f"Кнопка '{text}' не найдена")

            elif category == "Дизайн мобильных приложений":
                mobile_app_buttons_texts = ["Android", "iOS", "React Native"]
                for text in mobile_app_buttons_texts:
                    try:
                        btn = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, f"//a[contains(text(), '{text}')]"))
                        )
                        smooth_scroll_to_element(driver, btn)
                        move_mouse(btn)
                        time.sleep(1)
                    except:
                        print(f"Кнопка '{text}' не найдена")


            submit_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "el-submit"))
            )

            smooth_scroll_to_element(driver, submit_button)
            move_mouse(submit_button)

        else:
            print(f"Неизвестная категория: {category}")
    except Exception as e:
        print(f"Ошибка при обработке {project_id}: {e}")
    finally:
        driver.back()
        time.sleep(5)

def click_next(driver):
    try:
        next_btn = driver.find_element(By.ID, 'PrevLink')
        print("→ Переход на следующую страницу...")
        smooth_scroll_to_element(driver, next_btn)
        move_mouse(next_btn)
        time.sleep(5)
        return True
    except:
        print("Следующая страница не найдена.")
        return False

def main():
    processed = load_results()

    options = uc.ChromeOptions()
    options.page_load_strategy = 'none'
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")

    # Используем контекстный менеджер, чтобы всегда закрывался
    with uc.Chrome(options=options) as driver:
        try:
            while len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[1])
                driver.close()
            driver.switch_to.window(driver.window_handles[0])

            driver.get('https://www.fl.ru/projects/category/dizajn')
            time.sleep(10)

            while True:
                links = collect_links_on_page(driver)
                print(f"Найдено ссылок: {len(links)}")

                for i, link in enumerate(links):
                    if i == 0:
                        continue
                    process_link(driver, link, processed)

                if not click_next(driver):
                    break

        except Exception as e:
            print(f"[CRITICAL] Ошибка в main(): {e}")
        finally:
            save_results(processed)
            print("[INFO] Скрипт завершён.")

if __name__ == "__main__":

    main()
