import flet as ft
from services.auth_service import AuthService
from components.dialogs import show_about_dialog, show_contact_dialog

def LoginView(page: ft.Page, on_login_success_callback):
    auth = AuthService()
    page.bgcolor = "white"
    page.assets_dir = "assets"

    # ---------------------------------------------------------
    # 1. HEADER
    # ---------------------------------------------------------
    header_logo = ft.Container(
        width=40, height=40, border_radius=50, bgcolor="transparent",
        border=ft.border.all(2, "black"), padding=5,
        content=ft.Image(src="hammer.png", fit=ft.ImageFit.CONTAIN, error_content=ft.Icon(ft.Icons.GAVEL, color="black"))
    )

    header = ft.Container(
        height=70, padding=ft.padding.symmetric(horizontal=20), bgcolor="#80C1FF",
        shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.GREY_300),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(spacing=10, controls=[
                    header_logo, 
                    ft.Text("JUDGEMENOT", size=20, weight="bold", color="black")
                ]),
                ft.Row(spacing=5, controls=[
                    ft.TextButton("LEADERBOARD", icon=ft.Icons.EMOJI_EVENTS, style=ft.ButtonStyle(color="black"), on_click=lambda e: page.go("/leaderboard")),
                    ft.TextButton("ABOUT", style=ft.ButtonStyle(color="black"), on_click=lambda e: show_about_dialog(page)),
                    ft.TextButton("CONTACT", style=ft.ButtonStyle(color="black"), on_click=lambda e: show_contact_dialog(page)),
                ])
            ]
        )
    )

    # ---------------------------------------------------------
    # 2. LOGIN FORM LOGIC
    # ---------------------------------------------------------
    user_input = ft.TextField(
        label="Username", 
        width=280, 
        height=40, 
        border_radius=8, 
        bgcolor="white", 
        prefix_icon=ft.Icons.PERSON,
        border_color="#64AEFF",
        focused_border_color="#2E1437",
        text_size=13,
        content_padding=10,
        dense=True
    )
    
    pass_input = ft.TextField(
        label="Password", 
        password=True, 
        can_reveal_password=True, 
        width=280, 
        height=40, 
        border_radius=8, 
        bgcolor="white",
        prefix_icon=ft.Icons.LOCK,
        border_color="#64AEFF",
        focused_border_color="#2E1437",
        text_size=13,
        content_padding=10,
        dense=True
    )
    
    error_text = ft.Text("", color="red", size=11, text_align="center")

    def forgot_password_clicked(e):
        page.client_storage.remove("user_id") 
        info_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Password Recovery"),
            content=ft.Text("Please contact your System Administrator to reset your password.", text_align="center"),
            actions=[ft.TextButton("OK", on_click=lambda e: page.close(info_dialog))]
        )
        page.open(info_dialog)

    def login_clicked(e):
        if not user_input.value or not pass_input.value:
            error_text.value = "Please fill all fields."; error_text.update(); return
        
        user = auth.login(user_input.value, pass_input.value)
        if user == "DISABLED":
            error_text.value = "Account is disabled."; error_text.update()
        elif user == "PENDING":
             error_text.value = "Account pending Admin approval."; error_text.update()
        elif user:
            on_login_success_callback(user)
        else:
            error_text.value = "Invalid credentials."; error_text.update()

    def on_google_login_click(e):
        dlg = ft.AlertDialog(
            title=ft.Text("Coming Soon"),
            content=ft.Text("Google Sign-In is disabled."),
            actions=[ft.TextButton("OK", on_click=lambda e: page.close(dlg))]
        )
        page.open(dlg)

    # ---------------------------------------------------------
    # 3. LAYOUT ASSEMBLY
    # ---------------------------------------------------------
    login_box = ft.Container(
        width=350,
        height=500, # FIXED HEIGHT
        padding=20,
        bgcolor="#C9E4FF", 
        border_radius=15,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, "black"), offset=ft.Offset(0, 5)),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER, 
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=40, color="#64AEFF"),
                ft.Text("Welcome Back!", size=22, weight="bold", color="#1A1A1A"),
                ft.Text("Please sign in", size=12, color="grey"),
                
                ft.Divider(height=10, color="transparent"),
                
                user_input, 
                pass_input,
                
                ft.Container(
                    content=ft.TextButton("Forgot password?", style=ft.ButtonStyle(color="#4A4A4A", text_style=ft.TextStyle(size=11)), on_click=forgot_password_clicked),
                    alignment=ft.alignment.center_right,
                    width=280
                ),
                
                error_text,
                
                ft.ElevatedButton(
                    "LOGIN", 
                    width=280, height=38, 
                    bgcolor="#64AEFF", color="white", 
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), elevation=2),
                    on_click=login_clicked
                ),
                
                ft.Row(
                    controls=[
                        ft.Container(expand=True, height=1, bgcolor="grey"),
                        ft.Text("OR", size=10, color="grey"),
                        ft.Container(expand=True, height=1, bgcolor="grey"),
                    ], 
                    width=280,
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                
                ft.ElevatedButton(
                    "Google Sign-In", 
                    icon=ft.Icons.LOGIN, 
                    on_click=on_google_login_click, 
                    width=280, height=38,
                    bgcolor="white", color="black",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), elevation=1)
                ),
                
                ft.Row([
                    ft.Text("New user?", size=11),
                    ft.TextButton("Create Account", on_click=lambda e: page.go("/signup"), style=ft.ButtonStyle(color="#64AEFF", text_style=ft.TextStyle(size=11)))
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=2)
            ]
        )
    )

    return ft.Column(
        expand=True, 
        spacing=0, # FIX: REMOVES THE WHITE BAR GAP
        controls=[
            header, 
            ft.Container(
                expand=True, 
                alignment=ft.alignment.center, 
                content=login_box,
                padding=10,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=["#DDEDFF", "#FEF2FF"]
                )
            )
        ]
    )