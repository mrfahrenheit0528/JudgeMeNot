"""
I need you to build the Login Screen using Flet. 
It needs a Username field, a Password field (masked), and a 'Login' button. When the button is clicked, 
it should check if the fields are empty. If not, print 'Attempting login...' to the console. 
Don't worry about the database connection yet; I will wire that up.

We will stick to Standard Login first to ensure the core tabulation works. 
If we have time in the final week, we will add the Google Login button as an enhancement.
"""

import flet as ft
from services.auth_service import AuthService

def LoginView(page: ft.Page, on_login_success_callback):
    auth = AuthService()
    
    user_input = ft.TextField(label="Username", width=300)
    pass_input = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)
    error_text = ft.Text("", color="red")

    def login_clicked(e):
        username = user_input.value
        password = pass_input.value
        
        if not username or not password:
            error_text.value = "Please fill all fields."
            error_text.update()
            return

        # CALL THE BACKEND
        user = auth.login(username, password)
        
        if user == "DISABLED":
            error_text.value = "Account is disabled. Contact Admin."
            error_text.update()
        elif user:
            on_login_success_callback(user) # Pass the user object back to main.py
        else:
            error_text.value = "Invalid username or password."
            error_text.update()

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("JudgeMeNot", size=40, weight="bold", color=ft.Colors.BLUE),
                ft.Text("Sign in to continue", size=16),
                ft.Divider(height=20, color="transparent"),
                user_input,
                pass_input,
                error_text,
                ft.ElevatedButton("Login", on_click=login_clicked, width=300)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        expand=True
    )