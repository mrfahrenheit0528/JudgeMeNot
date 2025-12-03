import flet as ft
from services.auth_service import AuthService
from views.login_view import LoginView
from views.admin_dashboard import AdminDashboardView
from views.admin_config_view import AdminConfigView # <--- Crucial Import

def main(page: ft.Page):
    page.title = "JudgeMeNot System"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.assets_dir = "assets" # Ensure assets work globally
    
    auth_service = AuthService()

    def route_change(route):
        page.views.clear()
        
        # Get Session Data
        user_id = page.session.get("user_id")
        user_role = page.session.get("user_role")

        print(f"🚗 Navigating to: {page.route} | User: {user_role}")

        # ---------------------------------------------------------
        # ROUTE 1: LOGIN
        # ---------------------------------------------------------
        if page.route == "/login" or page.route == "/":
            page.views.append(
                ft.View(
                    "/login",
                    [LoginView(page, on_login_success)],
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                )
            )

        # ---------------------------------------------------------
        # ROUTE 2: ADMIN DASHBOARD
        # ---------------------------------------------------------
        elif page.route == "/admin":
            if user_id and user_role in ["Admin", "AdminViewer"]:
                page.views.append(
                    ft.View(
                        "/admin", 
                        [AdminDashboardView(page, on_logout)],
                        padding=0 # Remove padding so sidebar touches edges
                    )
                )
            else:
                print("⛔ Access Denied: Admin Dashboard")
                page.go("/login")
        
        # ---------------------------------------------------------
        # ROUTE 3: EVENT CONFIGURATION (The Missing Link!)
        # ---------------------------------------------------------
        elif page.route.startswith("/admin/event/"):
            # Check permissions
            if user_id and user_role == "Admin": 
                try:
                    # Extract ID: "/admin/event/5" -> "5" -> 5
                    event_id = int(page.route.split("/")[-1])
                    
                    print(f"⚙️ Loading Config for Event ID: {event_id}")
                    
                    page.views.append(
                        ft.View(
                            f"/admin/event/{event_id}",
                            [AdminConfigView(page, event_id)],
                            padding=0
                        )
                    )
                except ValueError:
                    print("❌ Error: Invalid Event ID in URL")
                    page.open(ft.SnackBar(ft.Text("Invalid Event ID")))
                    page.go("/admin")
            else:
                print("⛔ Access Denied: Event Config")
                page.go("/login")

        # ---------------------------------------------------------
        # ROUTE 4: CATCH ALL (404)
        # ---------------------------------------------------------
        else:
            print("⚠️ Unknown Route -> Redirecting to Login")
            page.go("/login")

        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    def on_login_success(user):
        # Store Session Data
        page.session.set("user_id", user.id)
        page.session.set("user_role", user.role)
        page.session.set("user_name", user.name)
        
        # Redirect based on Role
        if user.role == "Admin":
            page.go("/admin")
        elif user.role == "Judge":
            page.go("/judge") # Future route
        elif user.role == "Tabulator":
            page.go("/tabulator") # Future route
        else:
            page.go("/login")

    def on_logout(e):
        page.session.clear()
        page.go("/login")

    # Wire up the events
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Start at current route
    page.go(page.route)

if __name__ == "__main__":
    ft.app(target=main)