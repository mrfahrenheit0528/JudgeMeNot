import flet as ft
from services.auth_service import AuthService
from components.dialogs import show_about_dialog, show_contact_dialog

def SignupView(page: ft.Page):
    auth_service = AuthService()
    page.bgcolor = "white"
    
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
                ft.Row(spacing=10, controls=[header_logo, ft.Text("JUDGEMENOT", size=20, weight="bold", color="black")]),
                ft.Row(spacing=5, controls=[
                    ft.TextButton("LEADERBOARD", icon=ft.Icons.EMOJI_EVENTS, style=ft.ButtonStyle(color="black"), on_click=lambda e: page.go("/leaderboard")),
                    ft.TextButton("ABOUT", style=ft.ButtonStyle(color="black"), on_click=lambda e: show_about_dialog(page)),
                    ft.TextButton("CONTACT", style=ft.ButtonStyle(color="black"), on_click=lambda e: show_contact_dialog(page)),
                ])
            ]
        )
    )

    # ---------------------------------------------------------
    # 2. FORM FIELDS
    # ---------------------------------------------------------
    name_field = ft.TextField(
        label="Full Name", 
        width=280, height=40, 
        border_radius=8, 
        bgcolor="white",
        prefix_icon=ft.Icons.BADGE,
        border_color="#64AEFF",
        focused_border_color="#2E1437",
        text_size=13,
        content_padding=10,
        dense=True
    )
    
    user_field = ft.TextField(
        label="Username", 
        width=280, height=40, 
        border_radius=8, 
        bgcolor="white", 
        prefix_icon=ft.Icons.PERSON,
        border_color="#64AEFF",
        focused_border_color="#2E1437",
        text_size=13,
        content_padding=10,
        dense=True
    )
    
    pass_field = ft.TextField(
        label="Password", 
        password=True, can_reveal_password=True, 
        width=280, height=40, 
        border_radius=8, 
        bgcolor="white",
        prefix_icon=ft.Icons.LOCK,
        border_color="#64AEFF",
        focused_border_color="#2E1437",
        text_size=13,
        content_padding=10,
        dense=True
    )
    
    role_dropdown = ft.Dropdown(
        label="Applying as...",
        width=280,
        bgcolor="white",
        border_radius=8,
        border_color="#64AEFF",
        prefix_icon=ft.Icons.WORK,
        text_size=13,
        content_padding=10,
        dense=True,
        options=[
            ft.dropdown.Option("Judge"),
            ft.dropdown.Option("Tabulator"),
        ]
    )

    # ---------------------------------------------------------
    # 3. LOGIC
    # ---------------------------------------------------------
    def on_signup_click(e):
        if not role_dropdown.value or not all([name_field.value, user_field.value, pass_field.value]):
            page.open(ft.SnackBar(ft.Text("Please fill out all fields."), bgcolor="red"))
            return
        
        e.control.disabled = True
        e.control.text = "Processing..."
        page.update()

        success, msg = auth_service.register_self_service(
            name=name_field.value, 
            username=user_field.value, 
            password=pass_field.value, 
            role=role_dropdown.value
        )

        if success:
            e.control.disabled = False
            e.control.text = "Create Account"
            
            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Application Submitted", color="green"),
                content=ft.Column([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=60),
                    ft.Container(height=10),
                    ft.Text("Account Pending Admin Approval.", text_align="center"),
                ], tight=True, horizontal_alignment="center"),
                actions=[
                    ft.TextButton("Back to Login", on_click=lambda x: page.go("/login"))
                ],
                actions_alignment=ft.MainAxisAlignment.CENTER,
            )
            page.open(dlg)
        else:
            e.control.disabled = False
            e.control.text = "Create Account"
            page.open(ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor="red"))
            page.update()

    # ---------------------------------------------------------
    # 4. MAIN CONTAINER
    # ---------------------------------------------------------
    signup_box = ft.Container(
        width=350, 
        height=520, # FIXED HEIGHT
        padding=20, 
        bgcolor="#C9E4FF", 
        border_radius=15,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, "black"), offset=ft.Offset(0, 5)),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            alignment=ft.MainAxisAlignment.CENTER, 
            spacing=8, 
            controls=[
                ft.Icon(ft.Icons.APP_REGISTRATION, size=40, color="#64AEFF"),
                ft.Text("Join the Event", size=22, weight="bold", color="#1A1A1A"),
                ft.Text("Create Profile", size=12, color="grey"),
                ft.Divider(height=10, color="transparent"),
                
                name_field,
                user_field,
                pass_field,
                role_dropdown,
                
                ft.Container(height=5),
                
                ft.ElevatedButton(
                    "Create Account", 
                    width=280, height=38, 
                    bgcolor="#64AEFF", 
                    color=ft.Colors.WHITE, 
                    on_click=on_signup_click,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), elevation=2)
                ),
                
                ft.Row([
                    ft.Text("Already have an account?", size=11),
                    ft.TextButton("Log In", on_click=lambda e: page.go("/login"), style=ft.ButtonStyle(color="#64AEFF", text_style=ft.TextStyle(size=11)))
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
                content=signup_box,
                padding=10,
                # ADDED PURPLE GRADIENT BACKGROUND
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=["#FFEABD", "#FFBBDB"]
                )
            )
        ]
    )