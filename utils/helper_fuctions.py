# --- Helper: tắt overlay/backdrop nếu có ---
def turn_off_overlay_if_any(page):
    """Tắt overlay/backdrop nếu đang che màn hình."""
    try:
        # thử selector common cho backdrop
        backdrop = page.locator("[data-selenium='backdrop']")
        if backdrop.count() > 0 and backdrop.first.is_visible():
            print("INFO: 🛡️ Tìm thấy backdrop, đang cố gắng tắt...")

            # 1) click backdrop (thường đóng popup)
            try:
                backdrop.first.click()
                page.wait_for_timeout(300)
                print("INFO: ✅ Đã click backdrop để đóng.")
                return
            except Exception as e_click:
                print(f"WARNING: ⚠️ Click backdrop không được: {e_click}")

            # 2) gửi ESC
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
                print("INFO: ✅ Đã gửi phím Escape để đóng overlay.")
                return
            except Exception as e_esc:
                print(f"WARNING: ⚠️ Gửi ESC không được: {e_esc}")

            # 3) disable pointer-events bằng JS (biện pháp mạnh)
            try:
                page.evaluate("""
                () => {
                    const b = document.querySelector("[data-selenium='backdrop']");
                    if (b) {
                        b.style.pointerEvents = 'none';
                        b.style.opacity = '0';
                    }
                }
                """)
                page.wait_for_timeout(200)
                print("INFO: ✅ Đã tắt pointer-events của backdrop bằng JS.")
            except Exception as e_js:
                print(f"ERROR: ❌ Không thể chỉnh backdrop bằng JS: {e_js}")

    except Exception as e:
        print(f"INFO: ⚡ Không tìm thấy hoặc xử lý được overlay/backdrop: {e}")


# --- Helper: click thử theo nhiều chiến lược ---
def try_click_with_strategies(page, locator):
    """
    Thử click theo thứ tự:
      1) normal click (nếu visible + enabled)
      2) force click
      3) return False (caller có thể thử JS click)
    """
    try:
        if locator.is_visible() and locator.is_enabled():
            try:
                locator.click(timeout=10000)
                print("INFO: ✅ Click thành công bằng locator.")
                return True
            except Exception as e:
                print("WARNING: locator.click() failed:", e)

        # force click
        try:
            locator.click(force=True, timeout=3000)
            print("INFO: ✅ Click bằng force succeeded.")
            return True
        except Exception as e2:
            print("WARNING: force click failed:", e2)

    except Exception as e_all:
        print("WARNING: try_click_with_strategies error:", e_all)
    return False


# --- Hàm chính: xử lý & click 'Read all reviews' ---
def click_read_all_reviews(page):
    """
    Flow:
      1) Thử text-based locator
      2) Nếu không thành công -> xử lý overlay/backdrop
      3) Thử lại và fallback JS click bằng XPath
    """
    print("INFO: 🧠 Xử lý nút 'Read all reviews' (text-based selector)...")

    # Playwright text locator (thường bền hơn)
    text_locator = page.get_by_text("Read all reviews")
    # fallback attribute selector
    attr_selector = "span[label='Read all reviews']"
    attr_locator = page.locator(attr_selector)

    page.wait_for_timeout(300)  # allow DOM settle

    # 1) Thử text locator
    try:
        if try_click_with_strategies(page, text_locator):
            return True
    except Exception as e:
        print("WARNING: text locator attempt error:", e)

    # 2) Thử attribute locator
    try:
        if try_click_with_strategies(page, attr_locator):
            return True
    except Exception as e:
        print("WARNING: attr locator attempt error:", e)

    # 3) Nếu chưa clickable => xử lý overlay/backdrop rồi thử lại
    print("INFO: ⚠️ Nút chưa clickable — kiểm tra overlay/backdrop...")
    turn_off_overlay_if_any(page)
    page.wait_for_timeout(300)

    # 4) Thử lại text then attr
    try:
        if try_click_with_strategies(page, text_locator):
            return True
    except:
        pass
    try:
        if try_click_with_strategies(page, attr_locator):
            return True
    except:
        pass

    # 5) Cuối cùng: JS click bằng XPath (bỏ qua pointer events)
    try:
        print("INFO: 🔧 Thử JS click bằng XPath")
        clicked = page.evaluate("""() => {
            const el = document.evaluate("//span[normalize-space(text())='Read all reviews']", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (el) { el.click(); return true; }
            return false;
        }""")
        page.wait_for_timeout(200)
        if clicked:
            print("INFO: ✅ Đã click bằng JS (XPath).")
            return True
        else:
            print("WARNING: JS click không tìm thấy element bằng XPath.")
    except Exception as e:
        print("ERROR: ❌ JS click (XPath) failed:", e)

    print("ERROR: ❌ Không thể click 'Read all reviews' bằng mọi phương án.")
    return False

