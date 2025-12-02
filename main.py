import flet as ft
from services.auth_service import AuthService
# Import Views (We will create placeholder files for these next)
from views.login_view import LoginView
from views.admin_dashboard import AdminDashboardView
# from judge_system.views.judge_view import JudgeView (Future)

def main(page: ft.Page):
    page.title = "JudgeMeNot System"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Initialize Auth Service
    auth_service = AuthService()

    # ---------------------------------------------------------
    # 1. NAVIGATION LOGIC (The "Traffic Controller")
    # ---------------------------------------------------------
    def route_change(route):
        page.views.clear()
        
        # LOGIC: Check if user is logged in
        user_id = page.session.get("user_id")
        user_role = page.session.get("user_role")

        print(f"🚗 Navigating to: {page.route} | User: {user_role}")

        # --- ROUTE: LOGIN ---
        if page.route == "/login" or page.route == "/":
            page.views.append(
                ft.View(
                    "/login",
                    [LoginView(page, on_login_success)], # We pass the callback
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
            )

        # --- ROUTE: ADMIN DASHBOARD ---
        elif page.route == "/admin":
            if user_id and user_role in ["Admin", "AdminViewer"]:
                page.views.append(
                    ft.View(
                        "/admin",
                        [AdminDashboardView(page, on_logout)],
                    )
                )
            else:
                # Security: Redirect unauthorized access back to login
                page.go("/login")

        # --- CATCH ALL ---
        else:
            page.go("/login")

        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    # ---------------------------------------------------------
    # 2. CALLBACKS (Connecting UI to Logic)
    # ---------------------------------------------------------
    def on_login_success(user):
        """Called by LoginView when authentication passes"""
        # Store Session Data
        page.session.set("user_id", user.id)
        page.session.set("user_role", user.role)
        page.session.set("user_name", user.name)
        
        # Redirect based on Role
        if user.role == "Admin":
            page.go("/admin")
        elif user.role == "Judge":
            page.go("/judge")
        elif user.role == "Tabulator":
            page.go("/tabulator")
        else:
            page.go("/login")

    def on_logout(e):
        page.session.clear()
        page.go("/login")

    # ---------------------------------------------------------
    # 3. STARTUP
    # ---------------------------------------------------------
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)

if __name__ == "__main__":
    ft.app(target=main)