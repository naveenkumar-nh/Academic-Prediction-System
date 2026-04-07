import re

with open('frontend/python_ui/templates/login.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove CSS
content = re.sub(r'        /\* ===== FORGOT PASSWORD MODAL ===== \*/.*?\.modal-step-2\s*\{.*?\n        \}\n', '', content, flags=re.DOTALL)

# Remove HTML Form Link
content = re.sub(r'                <div style="text-align: center;">\s*<a href="javascript:void\(0\);" onclick="openForgotModal\(\);" class="forgot-link">Forgot Password\?</a>\s*</div>\n', '', content)

# Remove Modal HTML
content = re.sub(r'    <!-- FORGOT PASSWORD MODAL -->.*?</div>\s*</div>\n', '', content, flags=re.DOTALL)

# Remove JS
content = re.sub(r'        /\* ===== FORGOT PASSWORD MODAL JS ===== \*/.*?\n        }\);\n', '', content, flags=re.DOTALL)

# Remove Empowering Education block
content = re.sub(r'                <div class="welcome-address">\s*<h3>Empowering Education with AI</h3>\s*<p>.*?</p>\s*</div>\n', '', content, flags=re.DOTALL)

with open('frontend/python_ui/templates/login.html', 'w', encoding='utf-8') as f:
    f.write(content)
