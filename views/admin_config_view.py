import flet as ft
from core.database import SessionLocal
from models.all_models import Event

# Import the decoupled views
from views.config.pageant_config_view import PageantConfigView
from views.config.quiz_config_view import QuizConfigView

def AdminConfigView(page: ft.Page, event_id: int):
    # 1. Fetch Event to determine type
    db = SessionLocal()
    event = db.query(Event).get(event_id)
    db.close()

    if not event:
        return ft.Container(content=ft.Text("Event not found!", color="red", size=20))

    # 2. Route Logic
    # Both views now manage their own Headers and Layouts (Full Page).
    # We return them directly to avoid double headers.

    if event.event_type == "Pageant":
        return PageantConfigView(page, event_id)
    else:
        return QuizConfigView(page, event_id)