Script Description

This Python script automates handling orders on FL.ru using Selenium and undetected_chromedriver.

Key Features:
Order Collection – scans project pages and collects order links.
LLM-Based Processing – uses the Groq API to generate:
-short company replies,
-cost estimates,
-completion time estimates,
-order category classification.
Automatic Web Interaction – smooth scrolling, element clicking, and form filling using pyautogui.
Result Storage – all processed orders are saved to results.json to avoid data loss on reruns.

Technical Details:
Uses undetected_chromedriver to bypass anti-bot protections.
Employs screenshots and pyautogui for accurate element positioning.
Handles multiple order categories and subcategories for precise classification.
