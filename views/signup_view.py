import flet as ft
from services.auth_service import AuthService
from components.dialogs import show_about_dialog, show_contact_dialog

def SignupView(page: ft.Page):
    auth_service = AuthService()
    page.bgcolor = ft.Colors.WHITE
    
    # ---------------------------------------------------------
    # 1. HEADER (Copied from LoginView for consistency)
    # ---------------------------------------------------------
    header_logo = ft.Container(
        width=40, height=40, border_radius=50, bgcolor="transparent",
        border=ft.border.all(2, ft.Colors.BLUE_800), padding=5,
        content=ft.Image(src="hammer.png", fit=ft.ImageFit.CONTAIN, error_content=ft.Icon(ft.Icons.GAVEL, color=ft.Colors.BLUE_800))
    )

    header = ft.Container(
        height=70, padding=ft.padding.symmetric(horizontal=40), bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.GREY_300),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(spacing=10, controls=[header_logo, ft.Text("JUDGEMENOT", size=20, weight="bold", color=ft.Colors.BLUE_900)]),
                ft.Row(spacing=5, controls=[
                    ft.TextButton("LEADERBOARD", icon=ft.Icons.EMOJI_EVENTS, style=ft.ButtonStyle(color=ft.Colors.BLUE_800), on_click=lambda e: page.go("/leaderboard")),
                    ft.TextButton("ABOUT", style=ft.ButtonStyle(color=ft.Colors.GREY_700), on_click=lambda e: show_about_dialog(page)),
                    ft.TextButton("CONTACT", style=ft.ButtonStyle(color=ft.Colors.GREY_700), on_click=lambda e: show_contact_dialog(page)),
                ])
            ]
        )
    )

    # ---------------------------------------------------------
    # 2. FORM FIELDS (Styled like LoginView)
    # ---------------------------------------------------------
    name_field = ft.TextField(
        hint_text="Full Name", 
        width=320, height=48, 
        border_radius=8, 
        bgcolor=ft.Colors.WHITE,
        content_padding=10
    )
    
    user_field = ft.TextField(
        hint_text="Username", 
        width=320, height=48, 
        border_radius=8, 
        bgcolor=ft.Colors.WHITE, 
        prefix_icon=ft.Icons.PERSON,
        content_padding=10
    )
    
    pass_field = ft.TextField(
        hint_text="Password", 
        password=True, can_reveal_password=True, 
        width=320, height=48, 
        border_radius=8, 
        bgcolor=ft.Colors.WHITE,
        prefix_icon=ft.Icons.LOCK,
        content_padding=10
    )
    
    # FIX: Removed 'height' argument which caused the crash
    role_dropdown = ft.Dropdown(
        label="Applying as...",
        width=320, 
        # height=48,  <-- REMOVED THIS
        bgcolor=ft.Colors.WHITE,
        border_radius=8,
        content_padding=10,
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
            # UPDATED: Use page.open() for reliable SnackBars
            page.open(ft.SnackBar(ft.Text("Please fill out all fields."), bgcolor="red"))
            return
        
        # Disable button to prevent double-click
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
            # Re-enable button
            e.control.disabled = False
            e.control.text = "Create Account"
            
            # Show Success Dialog
            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Application Submitted"),
                content=ft.Column([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=60),
                    ft.Container(height=10),
                    ft.Text("Your account has been created and is PENDING ADMIN APPROVAL.", text_align="center"),
                    ft.Text("Please contact your Event Admin to activate your account.", text_align="center", size=12, color="grey")
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
            # UPDATED: Use page.open() for reliable SnackBars
            page.open(ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor="red"))
            page.update()

    # ---------------------------------------------------------
    # 4. MAIN CONTAINER (The blue box)
    # ---------------------------------------------------------
    signup_box = ft.Container(
        width=650, 
        padding=40, 
        bgcolor="#C9E4FF", # Same blue as login
        border_radius=20,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            spacing=15,
            controls=[
                ft.Text("Join the Event", size=32, weight="bold", color=ft.Colors.BLACK),
                ft.Text("Create a Judge or Tabulator profile", size=14, color="grey"),
                ft.Divider(height=20, color="transparent"),
                
                name_field,
                user_field,
                pass_field,
                role_dropdown,
                
                ft.Container(height=10),
                
                ft.ElevatedButton(
                    "Create Account", 
                    width=200, height=45, 
                    bgcolor="#64AEFF", 
                    color=ft.Colors.WHITE, 
                    on_click=on_signup_click,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                ),
                
                ft.Row([
                    ft.Text("Already have an account?"),
                    ft.TextButton("Log In", on_click=lambda e: page.go("/login"))
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=2)
            ]
        )
    )

    return ft.Column(
        expand=True, 
        controls=[
            header, 
            ft.Container(
                expand=True, 
                alignment=ft.alignment.center, 
                content=signup_box
            )
        ]
    )