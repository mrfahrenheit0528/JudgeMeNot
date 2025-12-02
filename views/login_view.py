"""
I need you to build the Login Screen using Flet. 
It needs a Username field, a Password field (masked), and a 'Login' button. When the button is clicked, 
it should check if the fields are empty. If not, print 'Attempting login...' to the console. 
Don't worry about the database connection yet; I will wire that up.

We will stick to Standard Login first to ensure the core tabulation works. 
If we have time in the final week, we will add the Google Login button as an enhancement.
"""

import flet as ft

def LoginView(page: ft.Page, on_login_success):
    # 1. Create the Text Fields
    user_input = ft.TextField(label="Username", width=300)
    pass_input = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)
    
    # 2. Define the Click Action
    def login_clicked(e):
        if not user_input.value or not pass_input.value:
            page.snack_bar = ft.SnackBar(ft.Text("Please enter both username and password!"))
            page.snack_bar.open = True
            page.update()
        else:
            # TODO: Call the actual auth service here later
            print(f"Login attempt: {user_input.value}")
            # For now, just simulate success if they type "admin"
            if user_input.value == "admin":
                on_login_success() # This switches the page

    # 3. Create the Layout (Center of screen)
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Welcome Back!", size=30, weight="bold"),
                user_input,
                pass_input,
                ft.ElevatedButton("Login", on_click=login_clicked)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        ),
        alignment=ft.alignment.center,
        expand=True
    )

ft.app(target=LoginView)